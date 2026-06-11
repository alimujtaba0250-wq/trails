import os
import sys

# Add the Django project root to sys.path so the ORM is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# ---- Scrapy identity ---- #
BOT_NAME = "scraper"
SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# ---- Crawl behaviour ---- #
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True
USER_AGENT = "Mozilla/5.0 (compatible; TrailPK-Bot/1.0)"

# ---- Dev safety valve — stop after 20 items during development ---- #
CLOSESPIDER_ITEMCOUNT = 20

# ---- Pipelines ---- #
ITEM_PIPELINES = {
    "scraper.pipelines.TrailCleaningPipeline": 100,
    "scraper.pipelines.DjangoSavePipeline": 200,
}

# ---- Scrapy internals ---- #
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# ---- Logging ---- #
LOG_LEVEL = "INFO"
