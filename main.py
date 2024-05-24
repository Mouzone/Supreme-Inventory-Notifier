from requests_html import AsyncHTMLSession
import collections
import json

async def scrape_items():
    try:
        print(f"Start rendering home")
        r = await asession.get("https://us.supreme.com/collections/all")
        await r.html.arender()
        print(f"Finish rendering home")

        items_elements = r.html.find("ul.collection-ul > li > a")
        print(f"Finish collecting links")
        links = collections.deque([(element.attrs["data-cy-title"], element.attrs["href"]) for element in items_elements])
        garments = []
        print(f"{len(links)} links to scrape")

        while links:
            title, link = links.pop()
            print(f"Scraping: {title}")
            result = await scrape_item(title, link)
            print(f"Finished Scraping: {title, result["variant"]}")
            garments.append(result)
            print(f"{len(garments)} links scraped")

        print("Finished Scraping All")
        return garments
    except Exception as e:
        print(f"Error in scrape_items: {e}")


async def scrape_item(title, url):
    BASE_URL = "https://us.supreme.com"
    try:
        print(f"Opening: {title}")
        r = await asession.get(BASE_URL + url)
        await r.html.arender()
        print(f"Opened: {title}")

        image_link = r.html.find("div.swiper-slide-active > img.js-product-image", first=True).attrs["src"]
        variant = r.html.find("h1.product-title + div + div > div", first=True).text
        price = r.html.find("div[data-cy=product-price]", first=True).text
        sizes_html = r.html.find("select > option")
        sizes = [element.text for element in sizes_html]
        add_to_cart_classes = r.html.find("div.js-add-to-cart", first=True).attrs['class']
        in_stock = "display-none" not in add_to_cart_classes
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


asession = AsyncHTMLSession()
items = asession.run(scrape_items)

with open("output.json", "w") as json_file:
    json_output = json.dumps(items[0])
    json_file.write(json_output)

print("JSON data has been written to 'output.json' file.")

