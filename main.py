from requests_html import AsyncHTMLSession

# database imports
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy.pool import QueuePool
import sqlalchemy
import pymysql
import os


def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")

    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    connector = Connector(ip_type)

    def getconn() -> pymysql.connections.Connection:
        conn: pymysql.connections.Connection = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
        )
        return conn

    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
        poolclass=QueuePool,
        pool_size=200,
    )

    print("Database connection established successfully.")
    return pool

async def scrape_items():
    try:
        print(f"-Start rendering home")
        r = await asession.get("https://us.supreme.com/collections/all")
        await r.html.arender()
        print(f"-Finish rendering home")

        items_elements = r.html.find("ul.collection-ul > li > a")
        print(f"-Finish collecting links")
        links = [(element.attrs["data-cy-title"], element.attrs["href"]) for element in items_elements]
        garments = []
        print(f"{len(links)} links to scrape")

        while links:
            title, link = links.pop()
            print(f"-Scraping: {title}")
            result = await scrape_item(title, link)
            print(f"-Finished Scraping: {title, result["variant"]}")
            garments.append(result)
            print(f"{len(garments)} links scraped")

        print("Finished Scraping All")
        return garments
    except Exception as e:
        print(f"Error in scrape_items: {e}")


async def scrape_item(title, url):
    BASE_URL = "https://us.supreme.com"
    try:
        print(f"--Opening: {title}")
        r = await asession.get(BASE_URL + url)
        await r.html.arender(sleep=1)
        print(f"--Opened: {title}")

        img_link = r.html.find("div.swiper-slide-active > img.js-product-image", first=True).attrs["src"]
        variant = r.html.find("h1.product-title + div + div > div", first=True).text
        price = r.html.find("div[data-cy=product-price]", first=True).text
        sizes_html = r.html.find("select > option")
        sizes = [element.text for element in sizes_html]

        add_to_cart_classes = r.html.find("div.js-add-to-cart", first=True).attrs['class']
        in_stock = "display-none" not in add_to_cart_classes
        # connect to database and write the entry
        if not in_stock:
            conn = pool.connect()
            try:
                # before adding check that the item was not already added
                # if so then just grab the result's key
                item_insert_stmt = sqlalchemy.text(
                    "INSERT INTO supreme_items (title, price, url) VALUES (:title, :price, :url)",
                )
                result = conn.execute(item_insert_stmt, parameters={"title": title, "price": price, "url": url})
                item_id = result.inserted_primary_key[0]

                variant_insert_stmt = sqlalchemy.text(
                    "INSERT INTO supreme_variants (item_id, variant, img_link) VALUES (:item_id, :variant, :img_link)"
                )
                result = conn.execute(variant_insert_stmt, parameters={"item_id": item_id, "variant": variant, "img_link":img_link})
                variant_id = result.inserted_primary_key[0]

                size_insert_stmt = sqlalchemy.text(
                    "INSERT INTO supreme_sizes (item_id, variant_id, size) VALUES (:item_id, :variant_id, :size)"
                )
                for size in sizes:
                    conn.execute(size_insert_stmt, parameters={"item_id":item_id, "variant_id":variant_id, "size":size})
                conn.commit()
                print(f"-Transaction for {title, variant} committed successfully.")

            except Exception as e:
                # Rollback the transaction in case of an error
                conn.rollback()
                print(f"Error executing transaction for {title, variant}: {e}")
            finally:
                # Return the connection to the pool
                conn.close()

    except Exception as e:
        print(f"Error in scrape_item for {title, url}: {e}")


pool = connect_with_connector()
asession = AsyncHTMLSession()
items = asession.run(scrape_items)
