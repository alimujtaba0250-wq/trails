import asyncio
import logging
import re
from datetime import datetime

from django.utils.text import slugify

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Pipeline 1 — data cleaning / normalisation
# --------------------------------------------------------------------------- #

class TrailCleaningPipeline:
    """Parse raw strings from the spider into typed Python values."""

    def process_item(self, item):
        self._clean_distance(item)
        self._clean_elevations(item)
        self._clean_rank_and_rating(item)
        self._clean_near_and_region(item)
        self._clean_dates(item)
        self._clean_hits(item)
        self._clean_coordinates_count(item)
        self._clean_description(item)
        self._build_slug(item)
        return item

    # ---- distance -------------------------------------------------------- #

    def _clean_distance(self, item) -> None:
        raw = item.get("raw_distance") or item.get("distance_mi") or ""
        try:
            # e.g. "3.45mi", "12.43mi", "5.2 mi"
            m = re.search(r"([\d.]+)", str(raw))
            if m:
                mi = float(m.group(1))
                item["distance_mi"] = mi
                item["distance_km"] = round(mi * 1.60934, 2)
            else:
                item["distance_mi"] = None
                item["distance_km"] = None
        except (ValueError, TypeError):
            item["distance_mi"] = None
            item["distance_km"] = None

    # ---- elevations ------------------------------------------------------ #

    def _clean_elevations(self, item) -> None:
        mapping = {
            "elevation_gain_ft": item.get("raw_elevation_gain", ""),
            "elevation_loss_ft": item.get("raw_elevation_loss", ""),
            "elevation_max_ft":  item.get("raw_elevation_max", ""),
            "elevation_min_ft":  item.get("raw_elevation_min", ""),
        }
        for field, raw in mapping.items():
            item[field] = self._parse_ft(raw)

        # Compute metric equivalents
        gain = item.get("elevation_gain_ft")
        item["elevation_gain_m"] = round(gain / 3.28084) if gain is not None else None

    @staticmethod
    def _parse_ft(raw: str) -> int | None:
        """Strip commas, unit letters; return int or None.
        Handles: '404 ft', '3274f', '8,575 ft', '8,201ft', '404'.
        """
        try:
            cleaned = re.sub(r"[^\d]", "", str(raw).replace(",", ""))
            return int(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None

    # ---- trail rank / rating --------------------------------------------- #

    def _clean_rank_and_rating(self, item) -> None:
        raw_rank = str(item.get("raw_trail_rank") or "")
        try:
            m = re.search(r"(\d+)", raw_rank)
            item["trail_rank"] = int(m.group(1)) if m else None
        except (ValueError, TypeError):
            item["trail_rank"] = None

        raw_rating = str(item.get("raw_rating") or "")
        try:
            m = re.search(r"(\d+\.\d+)", raw_rating)
            item["rating"] = float(m.group(1)) if m else None
        except (ValueError, TypeError):
            item["rating"] = None

    # ---- near / region --------------------------------------------------- #

    def _clean_near_and_region(self, item) -> None:
        near = str(item.get("near") or "").strip()
        # Strip leading "near " (case-insensitive)
        near = re.sub(r"^near\s+", "", near, flags=re.IGNORECASE)
        # Strip trailing " (Pakistan)"
        near = re.sub(r"\s*\(Pakistan\)\s*$", "", near, flags=re.IGNORECASE).strip()
        item["near"] = near

        # Derive region_name: last comma-separated segment, e.g.
        # "Fairy Meadow, Gilgit-Baltistan" → "Gilgit-Baltistan"
        if not item.get("region_name"):
            parts = [p.strip() for p in near.split(",") if p.strip()]
            item["region_name"] = parts[-1] if parts else ""

    # ---- dates ----------------------------------------------------------- #

    def _clean_dates(self, item) -> None:
        raw_uploaded = str(item.get("uploaded_date") or "").strip()
        if raw_uploaded:
            try:
                item["uploaded_date"] = datetime.strptime(raw_uploaded, "%B %d, %Y").date()
            except ValueError:
                try:
                    # Try "June 2022" → first of the month
                    item["uploaded_date"] = datetime.strptime(raw_uploaded, "%B %Y").date()
                except ValueError:
                    item["uploaded_date"] = None
        else:
            item["uploaded_date"] = None

    # ---- views / downloads ----------------------------------------------- #

    def _clean_hits(self, item) -> None:
        raw = str(item.get("raw_hits") or "")
        try:
            views_m = re.search(r"Viewed\s+([\d,]+)\s+times?", raw, re.IGNORECASE)
            item["views_count"] = int(views_m.group(1).replace(",", "")) if views_m else None
        except (ValueError, AttributeError):
            item["views_count"] = None

        try:
            dl_m = re.search(r"downloaded\s+([\d,]+)\s+times?", raw, re.IGNORECASE)
            item["downloads_count"] = int(dl_m.group(1).replace(",", "")) if dl_m else None
        except (ValueError, AttributeError):
            item["downloads_count"] = None

    # ---- coordinates count ----------------------------------------------- #

    def _clean_coordinates_count(self, item) -> None:
        raw = str(item.get("raw_coordinates") or "")
        try:
            m = re.search(r"(\d+)", raw)
            item["coordinates_count"] = int(m.group(1)) if m else None
        except (ValueError, TypeError):
            item["coordinates_count"] = None

    # ---- description ----------------------------------------------------- #

    def _clean_description(self, item) -> None:
        desc = item.get("description")
        if isinstance(desc, list):
            desc = " ".join(str(p).strip() for p in desc if str(p).strip())
        item["description"] = (str(desc or "")).strip()

    # ---- slug ------------------------------------------------------------ #

    def _build_slug(self, item) -> None:
        if not item.get("slug"):
            title = item.get("title") or ""
            wid = item.get("wikiloc_id") or ""
            item["slug"] = slugify(f"{title}-{wid}")[:550]


# --------------------------------------------------------------------------- #
# Pipeline 2 — Django ORM persistence
# --------------------------------------------------------------------------- #

class DjangoSavePipeline:
    """Persist cleaned items to PostgreSQL via the Django ORM."""

    def open_spider(self):
        import sys
        import os
        import django

        if "/app" not in sys.path:
            sys.path.insert(0, "/app")

        os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.base"
        try:
            django.setup()
            logger.info("Django setup complete (settings: %s)", os.environ["DJANGO_SETTINGS_MODULE"])
        except RuntimeError:
            # Already set up (e.g. during tests)
            pass

    async def process_item(self, item, spider):
        # Run all ORM work in a thread-pool executor so Django's synchronous
        # DB calls don't block Scrapy's asyncio event loop.
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._save_item, item, spider)

    def _save_item(self, item, spider):
        from apps.trails.models import Region, Trail, TrailPhoto, Waypoint

        wikiloc_id = item.get("wikiloc_id")
        if not wikiloc_id:
            logger.warning("Skipping item with no wikiloc_id: %r", item.get("title"))
            return item

        # ---- Region ---- #
        region = None
        region_name = (item.get("region_name") or "").strip()
        if region_name:
            try:
                region, created = Region.objects.get_or_create(
                    name=region_name,
                    defaults={"slug": slugify(region_name)},
                )
                if created:
                    logger.info("Created region: %s", region_name)
            except Exception:
                logger.exception("Error get_or_create Region(%s)", region_name)

        # ---- Trail ---- #
        trail_defaults = {
            "title":              item.get("title", ""),
            "slug":               item.get("slug", ""),
            "region":             region,
            "near":               item.get("near", ""),
            "activity":           item.get("activity", "Hiking"),
            "difficulty":         item.get("difficulty", ""),
            "trail_type":         item.get("trail_type", ""),
            "distance_mi":        item.get("distance_mi"),
            "distance_km":        item.get("distance_km"),
            "elevation_gain_ft":  item.get("elevation_gain_ft"),
            "elevation_gain_m":   item.get("elevation_gain_m"),
            "elevation_loss_ft":  item.get("elevation_loss_ft"),
            "elevation_max_ft":   item.get("elevation_max_ft"),
            "elevation_min_ft":   item.get("elevation_min_ft"),
            "trail_rank":         item.get("trail_rank"),
            "rating":             item.get("rating"),
            "moving_time":        item.get("moving_time", ""),
            "total_time":         item.get("total_time", ""),
            "coordinates_count":  item.get("coordinates_count"),
            "latitude":           item.get("latitude"),
            "longitude":          item.get("longitude"),
            "description":        item.get("description", ""),
            "author_name":        item.get("author_name", ""),
            "author_wikiloc_id":  item.get("author_wikiloc_id", ""),
            "thumbnail_url":      item.get("thumbnail_url", ""),
            "source_url":         item.get("source_url", ""),
            "recorded_date":      item.get("recorded_date", ""),
            "uploaded_date":      item.get("uploaded_date"),
            "views_count":        item.get("views_count"),
            "downloads_count":    item.get("downloads_count"),
        }

        try:
            trail, created = Trail.objects.update_or_create(
                wikiloc_id=wikiloc_id,
                defaults=trail_defaults,
            )
            action = "Created" if created else "Updated"
            logger.info("%s trail wikiloc_id=%s: %s", action, wikiloc_id, trail.title)
        except Exception:
            logger.exception("Error saving Trail wikiloc_id=%s", wikiloc_id)
            return item

        # ---- Photos ---- #
        try:
            photo_objs = [
                TrailPhoto(
                    trail=trail,
                    wikiloc_photo_id=p.get("wikiloc_photo_id", 0),
                    url=p.get("url", ""),
                    alt_text=p.get("alt_text", ""),
                    order=p.get("order", 0),
                )
                for p in (item.get("photos") or [])
                if p.get("url")
            ]
            if photo_objs:
                TrailPhoto.objects.bulk_create(photo_objs, ignore_conflicts=True)
                logger.info("Saved %d photos for trail %s", len(photo_objs), wikiloc_id)
        except Exception:
            logger.exception("Error bulk-creating photos for trail %s", wikiloc_id)

        # ---- Waypoints ---- #
        try:
            wp_objs = [
                Waypoint(
                    trail=trail,
                    wikiloc_wp_id=w.get("wikiloc_wp_id", 0),
                    name=w.get("name", ""),
                    latitude=w.get("lat") or 0.0,
                    longitude=w.get("lon") or 0.0,
                    elevation_ft=w.get("elevation_ft"),
                    order=w.get("order", 0),
                )
                for w in (item.get("waypoints") or [])
                if w.get("wikiloc_wp_id")
            ]
            if wp_objs:
                Waypoint.objects.bulk_create(wp_objs, ignore_conflicts=True)
                logger.info("Saved %d waypoints for trail %s", len(wp_objs), wikiloc_id)
        except Exception:
            logger.exception("Error bulk-creating waypoints for trail %s", wikiloc_id)

        return item
