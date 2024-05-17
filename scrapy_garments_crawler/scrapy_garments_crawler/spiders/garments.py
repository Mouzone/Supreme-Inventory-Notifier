import scrapy
from scrapy_garments_crawler.items import Garment

class GarmentSpider(scrapy.Spider):
    name = "garments"
    custom_settings = {
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "proxy": {
                "server": "brd.superproxy.io:22225",
                "username": "brd-customer-hl_2b5da317-zone-residential_proxy1-country-us",
                "password": "i2663mueizt6",
            },
        }
    }

    def start_requests(self):
        url = "https://us.supreme.com/pages/shop/"
        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                errback=self.errback,
            ),
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        await page.close()

        for garment in response.css("article.product_pod"):
            garment = Garment(
                title=garment.css("h3 a::attr(title)").get(),
                price=garment.css("p.price_color::text").get(),
            )
            yield garment

    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()