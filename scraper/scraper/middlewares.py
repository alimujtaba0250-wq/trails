# Custom Scrapy downloader and spider middlewares go here

from scrapy import signals


class ScraperSpiderMiddleware:
    # Spider middleware — process spider input/output/exceptions here

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class ScraperDownloaderMiddleware:
    # Downloader middleware — process requests/responses/exceptions here

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
