import scrapy


class TrailItem(scrapy.Item):
    wikiloc_id = scrapy.Field()
    title = scrapy.Field()
    slug = scrapy.Field()
    near = scrapy.Field()
    region_name = scrapy.Field()

    activity = scrapy.Field()
    difficulty = scrapy.Field()
    trail_type = scrapy.Field()

    distance_mi = scrapy.Field()
    distance_km = scrapy.Field()

    elevation_gain_ft = scrapy.Field()
    elevation_gain_m = scrapy.Field()
    elevation_loss_ft = scrapy.Field()
    elevation_max_ft = scrapy.Field()
    elevation_min_ft = scrapy.Field()

    trail_rank = scrapy.Field()
    rating = scrapy.Field()

    moving_time = scrapy.Field()
    total_time = scrapy.Field()
    coordinates_count = scrapy.Field()

    latitude = scrapy.Field()
    longitude = scrapy.Field()

    description = scrapy.Field()
    author_name = scrapy.Field()
    author_wikiloc_id = scrapy.Field()
    thumbnail_url = scrapy.Field()
    source_url = scrapy.Field()

    recorded_date = scrapy.Field()
    uploaded_date = scrapy.Field()

    views_count = scrapy.Field()
    downloads_count = scrapy.Field()

    # list of dicts: {wikiloc_photo_id, url, alt_text, order}
    photos = scrapy.Field()

    # list of dicts: {wikiloc_wp_id, name, lat, lon, elevation_ft, order}
    waypoints = scrapy.Field()

    # --- raw intermediate fields consumed by TrailCleaningPipeline --- #
    raw_distance = scrapy.Field()
    raw_elevation_gain = scrapy.Field()
    raw_elevation_loss = scrapy.Field()
    raw_elevation_max = scrapy.Field()
    raw_elevation_min = scrapy.Field()
    raw_trail_rank = scrapy.Field()
    raw_rating = scrapy.Field()
    raw_coordinates = scrapy.Field()
    raw_hits = scrapy.Field()
