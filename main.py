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

    try:
        with pool.connect() as conn:
            result = conn.execute("SELECT 1")
            if result.scalar() == 1:
                print("Database connection established successfully.")
            else:
                print("Test query did not return expected result.")
    except Exception as e:
        print(f"Error establishing database connection: {e}")
        raise
    
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
        print(f"{len(links)} links to scrape")

        while links:
            title, link = links.pop()
            print(f"-Scraping: {title}")
            await scrape_item(title, link)
            print(f"-Finished Scraping: {title}")
            print(f"{len(links)} links left to scrape")

        print("Finished Scraping All")
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
        price = r.html.find("div[data-cy=product-price]", first=True).text.replace("$", "")
        sizes_html = r.html.find("select > option")
        sizes = [element.text for element in sizes_html]

        add_to_cart_classes = r.html.find("div.js-add-to-cart", first=True).attrs['class']
        in_stock = "display-none" not in add_to_cart_classes
        print(f"--Found all elements: {title}")

        # connect to database and write the entry
        if in_stock:
            print(f"---Connecting to Pool")
            conn = pool.connect()
            print(f"---{title, variant} adding to database")
            try:
                # before adding check that the item was not already added
                item_select_stmt = sqlalchemy.text("SELECT id FROM supreme_items WHERE title = :title")
                result = conn.execute(item_select_stmt, {"title": title})
                existing_item = result.fetchone()

                # if so then just grab the result's key
                if existing_item:
                    item_id = existing_item.inserted_primary_key[0]
                else:
                    # If the item does not exist, insert it
                    item_insert_stmt = sqlalchemy.text(
                        "INSERT INTO supreme_items (title, price, url) VALUES (:title, :price, :url)"
                    )
                    result = conn.execute(item_insert_stmt, {"title": title, "price": price, "url": url})
                    item_id = result.inserted_primary_key[0]

                variant_insert_stmt = sqlalchemy.text(
                    "INSERT INTO supreme_variants (item_id, variant, img_link) VALUES (:item_id, :variant, :img_link)"
                )
                result = conn.execute(variant_insert_stmt, parameters={"item_id": item_id, "variant": variant, "img_link": img_link})
                variant_id = result.inserted_primary_key[0]

                size_insert_stmt = sqlalchemy.text(
                    "INSERT INTO supreme_sizes (item_id, variant_id, size) VALUES (:item_id, :variant_id, :size)"
                )
                for size in sizes:
                    conn.execute(size_insert_stmt, parameters={"item_id": item_id, "variant_id": variant_id, "size": size})

                conn.commit()
                print(f"-Transaction for {title, variant} committed successfully.")

            except Exception as e:
                conn.rollback()
                print(f"Error executing transaction for {title, variant}: {e}")

            finally:
                conn.close()

    except Exception as e:
        print(f"Error in scrape_item for {title, url}: {e}")


pool = connect_with_connector()
asession = AsyncHTMLSession()
asession.run(scrape_items)
