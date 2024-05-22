from requests_html import HTMLSession


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

    image_link = r.html.find("div.swiper-slide-active > img.js-product-image", first=True).attrs["src"]
    print(image_link)
    # get variant
    # get sizes (scrape from dropdown)
    # get price (same for all sizes


session = HTMLSession()
scrape_items()



