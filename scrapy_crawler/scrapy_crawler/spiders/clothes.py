import scrapy


class ClothesSpider(scrapy.Spider):
    name = "clothes"
    allowed_domains = ["us.supreme.com"]
    start_urls = ["https://us.supreme.com/pages/shop"]

    def parse(self, response):
        pass
