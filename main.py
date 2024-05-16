from item import Item
import scrapy
import collections

base_url = "https://us.supreme.com"
start = "/pages/shop"
links = collections.deque()
items = []

# at beginning collect all the item links synchronously

# at each item scrape, process, add to list then add the other links(variants) to the queue
# do this asynchronously since there is a network request that can be used for other things

# lastly join all the items into one csv file