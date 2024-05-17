import scrapy
from scrapy_playwright.page import PageMethod
from scrapy_book_crawler.items import Book
from scrapy_book_crawler.enums import BookCategory


class BooksSpider(scrapy.Spider):
    """Class for scraping books from https://books.toscrape.com/"""

    name = "books"
    category_number = BookCategory.CLASSICS

    def start_requests(self):
        url = "https://books.toscrape.com/"
        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    PageMethod(
                        "click",
                        selector=f"div.side_categories > ul > li > ul > li:nth-child({self.category_number.value}) > a",
                    ),
                    PageMethod("wait_for_selector", "article.product_pod"),
                ],
                errback=self.errback,
            ),
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        await page.screenshot(path=f"books-{self.category_number.name}.png")
        await page.close()

        for book in response.css("article.product_pod"):
            book = Book(
                title=book.css("h3 a::attr(title)").get(),
                price=book.css("p.price_color::text").get(),
            )
            yield book

    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()
