from requests_html import HTMLSession

# rewrite using async
def scrape_items():
    r = session.get("https://us.supreme.com/collections/all")
    r.html.render(sleep=1, keep_page=True, scrolldown=1)

    items = r.html.find("ul.collection-ul > li > a")
    for item in items:
        title = item.attrs["data-cy-title"]
        link = "https://us.supreme.com" + item.attrs["href"]
        scrape_item(title, link)


def scrape_item(title, url):
    r = session.get(url)
    r.html.render(sleep=1, keep_page=True, scrolldown=1)

    add_to_cart_classes = r.html.find("div.js-add-to-cart", first=True).attrs['class']
    in_stock = "display-none" not in add_to_cart_classes
    if in_stock:
        image_link = r.html.find("div.swiper-slide-active > img.js-product-image", first=True).attrs["src"]
        variant = r.html.find("h1.product-title + div + div > div", first=True).text
        price = r.html.find("div[data-cy=product-price]", first=True).text
        sizes_html = r.html.find("select > option")
        sizes = [element.text for element in sizes_html]

# write it to csv file with image_link, variant, sizes, price, link
def write_to_csv():
    pass

session = HTMLSession()
scrape_items()



