from requests_html import AsyncHTMLSession, HTMLSession
import json


def scrapeItems():
    try:
        print(f"Rendering Home")
        session = HTMLSession()
        r = session.get("https://us.supreme.com/collections/all")
        r.html.render()
        print(f"Rendered Home")

        items_elements = r.html.find("ul.collection-ul > li > a")
        print(f"Collected links")
        urls = [(element.attrs["data-cy-title"], element.attrs["href"]) for element in items_elements]
        return urls

    except Exception as e:
        print(f"Error in scrape_items: {e}")


async def scrapeItem():
    BASE_URL = "https://us.supreme.com"
    if len(urls):
        title, url = urls.pop()
        try:
            r = await asession.get(BASE_URL + url)
            print(f"Rendering: {title}")
            await r.html.arender()
            print(f"Rendered: {title}")

            image_link = r.html.find("div.swiper-slide-active > img.js-product-image", first=True).attrs["src"]
            variant = r.html.find("h1.product-title + div + div > div", first=True).text
            price = r.html.find("div[data-cy=product-price]", first=True).text
            sizes_html = r.html.find("select > option")
            sizes = [element.text for element in sizes_html]
            add_to_cart_classes = r.html.find("div.js-add-to-cart", first=True).attrs['class']
            in_stock = "display-none" not in add_to_cart_classes

            print(f"Scraped: {title, variant}")
            return {
                    "title": title,
                    "image_link": image_link,
                    "variant": variant,
                    "price": price,
                    "sizes": sizes,
                    "in_stock": in_stock
                    }

        except Exception as e:
            print(f"Error in scrape_item for {title}: {e}")


def outputResults(items):
    with open("output.json", "w") as json_file:
        json_output = json.dumps(items[0])
        json_file.write(json_output)

    print("JSON data has been written to 'output.json' file.")

urls = scrapeItems()
coroutines = [scrapeItem] * len(urls)

asession = AsyncHTMLSession()
items = asession.run(*coroutines)
outputResults(items)



