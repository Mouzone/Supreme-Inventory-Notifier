from requests_html import AsyncHTMLSession
import json
import asyncio

# # Create a global lock for file access
# file_lock = asyncio.Lock()


async def scrape_items(asession):
    try:
        r = await asession.get("https://us.supreme.com/collections/all")
        await r.html.arender()

        items = r.html.find("ul.collection-ul > li > a")
        return items

    except Exception as e:
        print(f"Error in scrape_items: {e}")


async def scrape_item(asession, title, url):
    BASE_URL = "https://us.supreme.com"
    try:
        r = await asession.get(BASE_URL + url)
        await r.html.arender()

        image_link = r.html.find("div.swiper-slide-active > img.js-product-image", first=True).attrs["src"]
        variant = r.html.find("h1.product-title + div + div > div", first=True).text
        price = r.html.find("div[data-cy=product-price]", first=True).text
        sizes_html = r.html.find("select > option")
        sizes = [element.text for element in sizes_html]
        add_to_cart_classes = r.html.find("div.js-add-to-cart", first=True).attrs['class']
        in_stock = "display-none" not in add_to_cart_classes
        garment = {
            "title": title,
            "image_link": image_link,
            "variant": variant,
            "price": price,
            "sizes": sizes,
            "in_stock": in_stock
        }
        return garment
        # await write_to_json(garment)
    except Exception as e:
        print(f"Error in scrape_item for {title}: {e}")
#
# # Write garment data to JSON
# async def write_to_json(garment):
#     async with file_lock:  # Ensure file access is synchronized
#         try:
#             with open("output.json", "a") as outfile:
#                 json.dump(garment, outfile)
#                 outfile.write("\n")  # Ensure each entry is on a new line
#         except Exception as e:
#             print(f"Error in write_to_json: {e}")

async def main():
    asession = AsyncHTMLSession()
    items = await scrape_items(asession)
    return items
    # tasks = (scrape_item(asession, item.attrs["data-cy-title"], item.attrs["href"]) for item in items)
    # return await asyncio.gather(*tasks)

results = asyncio.run(main())
print(results)