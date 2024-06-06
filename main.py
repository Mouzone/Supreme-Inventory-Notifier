from requests_html import AsyncHTMLSession
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, insert, select
import pymysql
import os


def getconn() -> pymysql.connections.Connection:
    '''
    Access database credentials from .env file and create connection object
    :return:
    '''
    load_dotenv()

    # Create a connection pool
    instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    connector = Connector(ip_type)

    conn: pymysql.connections.Connection = connector.connect(
        instance_connection_name,
        "pymysql",
        user=db_user,
        password=db_pass,
        db=db_name,
    )
    return conn


async def scrape_items():
    '''
    Scrape from supreme home page each item and respective link, will then have variants and other data scraped
    :return:
    '''
    try:
        print(f"-Start rendering home")
        r = await asession.get("https://us.supreme.com/collections/all")
        await r.html.arender()
        print(f"-Finish rendering home")

        pool = create_engine("mysql+pymysql://", creator=getconn, poolclass=QueuePool, pool_size=200,)
        await clear_tables(pool)

        items_elements = r.html.find("ul.collection-ul > li > a")
        print(f"-Finish collecting links")
        links = [(element.attrs["data-cy-title"], element.attrs["href"]) for element in items_elements]
        print(f"{len(links)} links to scrape")

        while links:
            title, link = links.pop()
            title = title.replace("®", "")
            print(f"-Scraping: {title}")
            await scrape_item(pool, title, link)
            print(f"-Finished Scraping: {title}")
            print(f"{len(links)} links left to scrape")

        print("Finished Scraping All")

    except Exception as e:
        print(f"Error in scrape_items: {e}")


async def clear_tables(pool):
    '''
    From each table remove all rows
    :param pool:
    :return:
    '''
    conn = pool.connect()

    metadata = MetaData()
    supreme_items = Table('supreme_items', metadata, autoload_with=conn)
    supreme_variants = Table('supreme_variants', metadata, autoload_with=conn)
    supreme_sizes = Table('supreme_sizes', metadata, autoload_with=conn)

    conn.execute(supreme_items.delete())
    conn.execute(supreme_variants.delete())
    conn.execute(supreme_sizes.delete())

    conn.commit()
    return


async def scrape_item(pool, title, url):
    '''
    For each item scrape pertinent information and write to database
    :param pool:
    :param title:
    :param url:
    :return:
    '''
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
            print(f"---{title, variant} adding to database")
            await write_to_db(pool, title, price, url, variant, img_link, sizes)
        else:
            print(f"---{title, variant} not in stock")

    except Exception as e:
        print(f"Error in scrape_item for {title, url}: {e}")


async def write_to_db(pool, title, price, url, variant, img_link, sizes):
    '''
    Establish connection to db and insert to each table while getting the id from each table for the next
    :param pool:
    :param title:
    :param price:
    :param url:
    :param variant:
    :param img_link:
    :param sizes:
    :return:
    '''
    try:
        conn = pool.connect()

        metadata = MetaData()
        supreme_items = Table('supreme_items', metadata, autoload_with=conn)
        supreme_variants = Table('supreme_variants', metadata, autoload_with=conn)
        supreme_sizes = Table('supreme_sizes', metadata, autoload_with=conn)

        stmt = select(supreme_items).where(supreme_items.c.title == title)
        result = conn.execute(stmt)
        row = result.fetchone()

        if row:
            item_id = row[0]
        else:
            item_insert_stmt = insert(supreme_items).values(title=title, price=price, url=url)
            result = conn.execute(item_insert_stmt)
            item_id = result.inserted_primary_key[0]

        variant_insert_stmt = insert(supreme_variants).values(item_id=item_id, variant=variant, img_link=img_link)
        result = conn.execute(variant_insert_stmt)
        variant_id = result.inserted_primary_key[0]

        for size in sizes:
            size_insert_stmt = insert(supreme_sizes).values(item_id=item_id, variant_id=variant_id, size=size)
            conn.execute(size_insert_stmt)

        conn.commit()
        print(f"-Transaction for {title, variant} committed successfully.")

    except Exception as e:
        print(f"Error executing transaction for {title, variant}: {e}")

    finally:
        conn.close()


asession = AsyncHTMLSession()
asession.run(scrape_items)
