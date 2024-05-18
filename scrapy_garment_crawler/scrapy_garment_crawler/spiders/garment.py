import scrapy
from scrapy_garment_crawler.items import Garment
from scrapy_playwright.page import PageMethod

class GarmentSpider(scrapy.Spider):
    name = "garment"
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
        url = "https://us.supreme.com/collections/all"
        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                errback=self.errback,
                playwright_page_methods=[
                    PageMethod("wait_for_selector", 'li.small-thumbs'),
                    PageMethod("waitForNavigation"),   # Wait for navigation to complete
                ]
            ),
        )

    # parse collection page
    async def parse(self, response):
        page = response.meta["playwright_page"]
        await page.close()
        base_url = "https://us.supreme.com/"
        for link in response.css("a[data-navigate]::attr(href)"):
            yield response.follow(base_url + link, callback=self.parse_item_page)

    async def parse_item_page(self, response):
        garment = Garment(
            product=response.css("h1.product-title::text").get(),
            variant=response.css("div.js-variant").get(),
            price=response.css("div.js-sale-price-wrapper::text").get()
        )
        yield garment

    # async def parse_item_page(self, response):
    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()