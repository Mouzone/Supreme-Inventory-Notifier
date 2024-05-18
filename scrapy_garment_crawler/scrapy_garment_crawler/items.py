# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class Garment(scrapy.Item):
    # link = scrapy.Field()
    # image = scrapy.Field()
    product = scrapy.Field()
    variant = scrapy.Field()
    # size = scrapy.Field()
    price = scrapy.Field()
    # sold_out = scrapy.Field()
