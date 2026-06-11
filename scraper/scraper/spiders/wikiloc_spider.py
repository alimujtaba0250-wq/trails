import json
import logging
import re

import scrapy

from scraper.items import TrailItem

logger = logging.getLogger(__name__)


class WikilocSpider(scrapy.Spider):
    name = "wikiloc"
    allowed_domains = ["wikiloc.com"]
    start_urls: list[str] = []

    LISTING_BASE = "https://www.wikiloc.com/trails/hiking/pakistan"

    _UA = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 1,
        "CLOSESPIDER_ITEMCOUNT": 20,
        "ROBOTSTXT_OBEY": False,
        # scrapy-impersonate: replaces the default downloader with curl_cffi
        # so every request uses a genuine Chrome TLS fingerprint (JA3/JA4)
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_impersonate.ImpersonateDownloadHandler",
            "https": "scrapy_impersonate.ImpersonateDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    }

    # ------------------------------------------------------------------ #
    # Entry point
    # ------------------------------------------------------------------ #

    def start_requests(self):
        yield scrapy.Request(
            url=self.LISTING_BASE,
            callback=self.parse_listing,
            meta={
                "page": 1,
                "impersonate": "chrome120",
            },
            dont_filter=True,
        )

    # ------------------------------------------------------------------ #
    # Listing page
    # ------------------------------------------------------------------ #

    def parse_listing(self, response):
        page = response.meta.get("page", 1)
        cards = response.css("article.trail-card-with-description")
        logger.info("Page %d — found %d trail cards", page, len(cards))

        for card in cards:
            listing_data = self._extract_listing_card(card)
            if not listing_data.get("detail_url"):
                continue

            detail_url = response.urljoin(listing_data["detail_url"])
            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_trail,
                meta={
                    "listing_data": listing_data,
                    "impersonate": "chrome120",
                },
            )

        # Follow pagination
        next_href = response.css("a.pagination__item[href*='page=']::attr(href)").getall()
        for href in next_href:
            if f"page={page + 1}" in href:
                yield scrapy.Request(
                    url=response.urljoin(href),
                    callback=self.parse_listing,
                    meta={
                        "page": page + 1,
                        "impersonate": "chrome120",
                    },
                )
                break

    def _extract_listing_card(self, card) -> dict:
        data: dict = {}

        try:
            title_el = card.css("h3.trail-card-with-description__title a")
            data["title"] = (title_el.css("::text").get() or "").strip()
            data["detail_url"] = title_el.attrib.get("href", "")
        except Exception:
            logger.exception("Error extracting title/url from listing card")

        try:
            data["near"] = (
                card.css("div.trail-card-with-description__near::text").get() or ""
            ).strip()
        except Exception:
            logger.exception("Error extracting near from listing card")

        try:
            stat_values = card.css(
                "dl.trail-card-with-description__detail__stats "
                "dd.trail-card-with-description__detail__stats__value"
            )
            data["raw_distance"] = (stat_values[0].css("::text").get() or "").strip() if len(stat_values) > 0 else ""
            data["raw_elevation_gain"] = (stat_values[1].css("::text").get() or "").strip() if len(stat_values) > 1 else ""

            if len(stat_values) > 2:
                rank_dd = stat_values[2]
                rank_text = (rank_dd.css("span::text").get() or "").strip()
                data["raw_trail_rank"] = rank_text
                # Rating lives after the | separator — second text node in the dd
                all_texts = rank_dd.css("::text").getall()
                for t in all_texts:
                    m = re.search(r"(\d+\.\d+)", t)
                    if m:
                        data["raw_rating"] = m.group(1)
                        break
        except Exception:
            logger.exception("Error extracting stats from listing card")

        try:
            data["author_name"] = (
                card.css("a.trail-card-with-description__detail__author__name::text").get() or ""
            ).strip()
        except Exception:
            logger.exception("Error extracting author from listing card")

        try:
            data["listing_description"] = (
                card.css("p.trail-card-with-description__description::text").get() or ""
            ).strip()
        except Exception:
            logger.exception("Error extracting description from listing card")

        try:
            data["thumbnail_url"] = (
                card.css("div.trail__images picture img::attr(src)").get() or ""
            ).strip()
        except Exception:
            logger.exception("Error extracting thumbnail from listing card")

        # Extract wikiloc_id from the detail URL slug (last numeric segment)
        try:
            m = re.search(r"-(\d+)$", data.get("detail_url", "").rstrip("/"))
            data["wikiloc_id"] = int(m.group(1)) if m else None
        except Exception:
            logger.exception("Error extracting wikiloc_id from URL")

        return data

    # ------------------------------------------------------------------ #
    # Detail page
    # ------------------------------------------------------------------ #

    def parse_trail(self, response):
        listing_data: dict = response.meta.get("listing_data", {})
        item = TrailItem()

        # ---- IDs & URLs ----
        item["wikiloc_id"] = listing_data.get("wikiloc_id")
        item["source_url"] = response.url
        item["activity"] = "Hiking"

        # ---- Title ----
        try:
            item["title"] = (response.css("h1::text").get() or listing_data.get("title", "")).strip()
        except Exception:
            logger.exception("Error extracting title")
            item["title"] = listing_data.get("title", "")

        # ---- Near ----
        try:
            near = (response.css("div.trail-near p::text").get() or listing_data.get("near", "")).strip()
            item["near"] = near
        except Exception:
            logger.exception("Error extracting near")
            item["near"] = listing_data.get("near", "")

        # ---- Author ----
        try:
            item["author_name"] = (
                response.css("strong.author__user-name a::text").get()
                or listing_data.get("author_name", "")
            ).strip()
        except Exception:
            logger.exception("Error extracting author_name")
            item["author_name"] = listing_data.get("author_name", "")

        try:
            author_href = response.css("a[href*='/wikiloc/user.do?id=']::attr(href)").get() or ""
            m = re.search(r"[?&]id=(\d+)", author_href)
            item["author_wikiloc_id"] = m.group(1) if m else ""
        except Exception:
            logger.exception("Error extracting author_wikiloc_id")
            item["author_wikiloc_id"] = ""

        # ---- Description ----
        try:
            parts = response.css("div.description.dont-break-out::text").getall()
            item["description"] = " ".join(p.strip() for p in parts if p.strip())
        except Exception:
            logger.exception("Error extracting description")
            item["description"] = listing_data.get("listing_description", "")

        # ---- Thumbnail ----
        try:
            item["thumbnail_url"] = (
                response.css("div.trail__images picture img::attr(src)").get()
                or listing_data.get("thumbnail_url", "")
            ).strip()
        except Exception:
            logger.exception("Error extracting thumbnail_url")
            item["thumbnail_url"] = listing_data.get("thumbnail_url", "")

        # ---- dl.data-items stats ----
        stats = self._parse_data_items(response)

        item["raw_distance"] = stats.get("Distance") or listing_data.get("raw_distance", "")
        item["elevation_gain_ft"] = None  # cleaned by pipeline
        item["raw_elevation_gain"] = stats.get("Elevation gain") or listing_data.get("raw_elevation_gain", "")
        item["difficulty"] = stats.get("Technical difficulty", "")
        item["trail_type"] = stats.get("Trail type", "")
        item["trail_rank"] = None  # set below
        item["rating"] = None

        # Store raw values for pipeline to parse
        item["raw_trail_rank"] = stats.get("TrailRank") or listing_data.get("raw_trail_rank", "")
        item["raw_rating"] = listing_data.get("raw_rating", "")
        item["raw_elevation_loss"] = stats.get("Elevation loss", "")
        item["raw_elevation_max"] = stats.get("Max elevation", "")
        item["raw_elevation_min"] = stats.get("Min elevation", "")

        # ---- dl.more-data stats ----
        more = self._parse_more_data(response)
        item["moving_time"] = more.get("Moving time", "").strip()
        item["total_time"] = more.get("Time", "").strip()
        item["raw_coordinates"] = more.get("Coordinates", "")
        item["uploaded_date"] = more.get("Uploaded", "")  # pipeline parses to date
        item["recorded_date"] = more.get("Recorded", "").strip()

        # ---- Views / Downloads ----
        try:
            hits_text = " ".join(
                t.strip()
                for t in response.css("div.trail-hits p::text").getall()
                if t.strip()
            )
            item["raw_hits"] = hits_text
        except Exception:
            logger.exception("Error extracting trail-hits")
            item["raw_hits"] = ""

        # ---- Lat / Lng (JSON-LD first, then mapData JS fallback) ----
        lat, lng = self._extract_coords(response)
        item["latitude"] = lat
        item["longitude"] = lng

        # ---- Photos ----
        item["photos"] = self._extract_photos(response)

        # ---- Waypoints ----
        item["waypoints"] = self._extract_waypoints(response)

        logger.info("Scraped trail wikiloc_id=%s title=%r", item.get("wikiloc_id"), item.get("title"))
        yield item

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _parse_data_items(self, response) -> dict:
        result = {}
        try:
            for d_item in response.css("dl.data-items div.d-item"):
                key = (d_item.css("dt::text").get() or "").strip()
                val = (d_item.css("dd::text").get() or "").strip()
                if key:
                    result[key] = val
        except Exception:
            logger.exception("Error parsing dl.data-items")
        return result

    def _parse_more_data(self, response) -> dict:
        result = {}
        try:
            for d_item in response.css("dl.more-data div.d-item"):
                key = (d_item.css("dt::text").get() or "").strip()
                val = (d_item.css("dd::text").get() or "").strip()
                if key:
                    result[key] = val
        except Exception:
            logger.exception("Error parsing dl.more-data")
        return result

    def _extract_coords(self, response) -> tuple[float | None, float | None]:
        lat, lng = None, None

        # Try JSON-LD blocks first
        try:
            ld_blocks = response.css('script[type="application/ld+json"]::text').getall()
            for block in ld_blocks:
                try:
                    data = json.loads(block)
                    entries = data if isinstance(data, list) else [data]
                    for entry in entries:
                        if entry.get("@type") == "TouristAttraction":
                            geo = entry.get("geo", {})
                            lat = float(geo["latitude"])
                            lng = float(geo["longitude"])
                            return lat, lng
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        except Exception:
            logger.exception("Error parsing JSON-LD for coords")

        # Fallback: var mapData JS block
        # Structure is {"mapData": [{..., "blat": ..., "blng": ...}, ...]}
        try:
            m = re.search(r"var mapData\s*=\s*(\{.*?\});", response.text, re.DOTALL)
            if m:
                map_data = json.loads(m.group(1))
                entries = map_data.get("mapData", [])
                if entries and isinstance(entries, list):
                    first = entries[0]
                    raw_lat = first.get("blat") or first.get("lat")
                    raw_lng = first.get("blng") or first.get("lng")
                    if raw_lat is not None and raw_lng is not None:
                        lat = float(raw_lat)
                        lng = float(raw_lng)
        except Exception:
            logger.exception("Error parsing mapData JS var for coords")

        return lat, lng

    def _extract_photos(self, response) -> list[dict]:
        photos = []
        try:
            imgs = response.css("div.trail__images picture img")
            for order, img in enumerate(imgs):
                src = (img.attrib.get("src") or "").strip()
                if not src:
                    continue
                alt = (img.attrib.get("alt") or "").strip()
                # Attempt to extract a numeric photo ID from the URL
                photo_id_match = re.search(r"/(\d+)[^/]*\.\w+$", src)
                photo_id = int(photo_id_match.group(1)) if photo_id_match else 0
                photos.append(
                    {
                        "wikiloc_photo_id": photo_id,
                        "url": src,
                        "alt_text": alt,
                        "order": order,
                    }
                )
        except Exception:
            logger.exception("Error extracting photos")
        return photos

    def _extract_waypoints(self, response) -> list[dict]:
        waypoints = []

        # Build a lat/lng map from JSON-LD Landform entries keyed by wp id
        wp_coords: dict[int, tuple[float, float]] = {}
        try:
            ld_blocks = response.css('script[type="application/ld+json"]::text').getall()
            for block in ld_blocks:
                try:
                    data = json.loads(block)
                    entries = data if isinstance(data, list) else [data]
                    for entry in entries:
                        if entry.get("@type") == "Landform":
                            geo = entry.get("geo", {})
                            wp_id_str = entry.get("@id", "")
                            m = re.search(r"(\d+)$", wp_id_str)
                            if m:
                                wp_id = int(m.group(1))
                                wp_coords[wp_id] = (
                                    float(geo.get("latitude", 0)),
                                    float(geo.get("longitude", 0)),
                                )
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        except Exception:
            logger.exception("Error parsing JSON-LD for waypoint coords")

        try:
            for order, wpcard in enumerate(response.css("div.wpcard")):
                wp = {}

                # Wikiloc WP ID from element id attr: "wp-106441128"
                raw_id = wpcard.attrib.get("id", "")
                m = re.search(r"(\d+)$", raw_id)
                wp["wikiloc_wp_id"] = int(m.group(1)) if m else 0

                wp["name"] = (wpcard.css("div.wpcard__body h3::text").get() or "").strip()
                wp["order"] = order

                # Elevation from wpcard header span
                elev_raw = (wpcard.css("div.wpcard__header span::text").get() or "").strip()
                wp["elevation_ft"] = self._parse_elevation_int(elev_raw)

                # Coords from pre-built map
                coords = wp_coords.get(wp["wikiloc_wp_id"])
                wp["lat"] = coords[0] if coords else None
                wp["lon"] = coords[1] if coords else None

                waypoints.append(wp)
        except Exception:
            logger.exception("Error extracting waypoints")

        return waypoints

    @staticmethod
    def _parse_elevation_int(raw: str) -> int | None:
        """Strip commas and non-numeric chars, return int feet or None."""
        try:
            cleaned = re.sub(r"[^\d]", "", raw.replace(",", ""))
            return int(cleaned) if cleaned else None
        except (ValueError, AttributeError):
            return None
