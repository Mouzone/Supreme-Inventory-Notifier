from requests_html import AsyncHTMLSession
import os

from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy

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

        image_link = r.html.find("div.swiper-slide-active > img.js-product-image", first=True).attrs["src"]
        variant = r.html.find("h1.product-title + div + div > div", first=True).text
        price = r.html.find("div[data-cy=product-price]", first=True).text
        sizes_html = r.html.find("select > option")
        sizes = [element.text for element in sizes_html]
        add_to_cart_classes = r.html.find("div.js-add-to-cart", first=True).attrs['class']
        in_stock = "display-none" not in add_to_cart_classes
        # connect to database hopefully async and write the entry
        return {
                "title": title,
                "image_link": image_link,
                "variant": variant,
                "price": price,
                "sizes": sizes,
                "in_stock": in_stock,
                "url": url
                }

    except Exception as e:
        print(f"Error in scrape_item for {title, url}: {e}")


asession = AsyncHTMLSession()
items = asession.run(scrape_items)

def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of MySQL.

    Uses the Cloud SQL Python Connector package.
    """
    # Note: Saving credentials in environment variables is convenient, but not
    # secure - consider a more secure solution such as
    # Cloud Secret Manager (https://cloud.google.com/secret-manager) to help
    # keep secrets safe.

    instance_connection_name = os.environ[
        "INSTANCE_CONNECTION_NAME"
    ]  # e.g. 'project:region:instance'
    db_user = os.environ["DB_USER"]  # e.g. 'my-db-user'
    db_pass = os.environ["DB_PASS"]  # e.g. 'my-db-password'
    db_name = os.environ["DB_NAME"]  # e.g. 'my-database'

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
        # ...
    )
    return pool

print("JSON data has been written to 'output.json' file.")

