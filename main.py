from requests_html import AsyncHTMLSession
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, insert, select
import pymysql
import os


def getconn() -> pymysql.connections.Connection:
    """
    Access database credentials from .env file and create a connection object.
    :return: pymysql.connections.Connection object
    """
    load_dotenv()

    # Create a connection using credentials from the .env file
    db_host = '127.0.0.1'
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")

    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_pass,
        database=db_name,
    )

    return conn


async def scrape_items():
    """
    Scrape from the Supreme home page each item and its respective link.
    This will then have variants and other data scraped.
    :return: None
    """
    asession = AsyncHTMLSession()
    try:
        print("-Start rendering home")
        # render shopping collection and scrape items to process
        r = await asession.get("https://us.supreme.com/collections/all")
        await r.html.arender()
        print("-Finish rendering home")

        # get pool object for connections for future read writes to db
        pool = create_engine("mysql+pymysql://", creator=getconn, pool_size=130)
        await clear_tables(pool)

        items_elements = r.html.find('ul[data-testid="product-list"] a[data-testid="react-router-link"]')
        print("-Finish collecting links")
        links = [(element.attrs["aria-label"][:-13], element.attrs["href"]) for element in items_elements]
        print(f"{len(links)} links to scrape")

        while links:
            product, link = links.pop()
            product = product.replace("®", "")
            print(f"-Scraping: {product}")
            await scrape_item(pool, product, link, asession)
            print(f"-Finished Scraping: {product}")
            print(f"{len(links)} links left to scrape")

        print("Finished Scraping All")

    except Exception as e:
        print(f"Error in scrape_items: {e}")
    finally:
        await asession.close()


async def clear_tables(pool):
    """
    From each table remove all rows, such that the dbs will only display currently in-stock items
    :param pool: SQLAlchemy engine pool
    :return: None
    """
    conn = pool.connect()

    metadata = MetaData()
    items = Table('items', metadata, autoload_with=conn)
    variants = Table('variants', metadata, autoload_with=conn)
    sizes = Table('sizes', metadata, autoload_with=conn)

    conn.execute(sizes.delete())
    conn.execute(variants.delete())
    conn.execute(items.delete())

    conn.commit()
    conn.close()


async def scrape_item(pool, product, url, asession):
    """
    For each item scrape pertinent information and write to the database.
    :param pool: SQLAlchemy engine pool
    :param product: Product name
    :param url: Product URL
    :param asession: AsyncHTMLSession object
    :return: None
    """
    BASE_URL = "https://us.supreme.com"
    try:
        print(f"--Opening: {product}")
        # render webpage
        r = await asession.get(BASE_URL + url)
        await r.html.arender(sleep=1)
        print(f"--Opened: {product}")

        img_link = r.html.find('div[data-testid="ProductCarousel-wrapper"] img', first=True).attrs["src"]
        title_with_variant = r.html.find('div[data-testid="ProductCarousel-wrapper"] img', first=True).attrs["alt"]
        variant = ""
        if len(title_with_variant) >= 2:
            variant = title_with_variant.split("-")[1].strip()
        price = r.html.find('h3[data-testid="price"]', first=True).text.replace("$", "")
        sizes_html = r.html.find('select[aria-label="size"] option')
        clothes_sizes = [element.text for element in sizes_html]

        sold_out_button = r.html.find('button[data-testid="sold-out-button"]')
        in_stock = len(sold_out_button) == 0
        print(f"--Found all elements: {product}")

        # only add to db if in stock
        if in_stock:
            print(f"---{product}, {variant} adding to database")
            await write_to_db(pool, product, price, url, variant, img_link, clothes_sizes)
        else:
            print(f"---{product}, {variant} not in stock")

    except Exception as e:
        print(f"Error in scrape_item for {product}, {url}: {e}")


async def write_to_db(pool, product, price, url, variant, img_link, clothes_sizes):
    """
    Establish a connection to the database and insert data into each table.
    :param pool: SQLAlchemy engine pool
    :param product: Product name
    :param price: Product price
    :param url: Product URL
    :param variant: Product variant
    :param img_link: Image link
    :param clothes_sizes: List of sizes
    :return: None
    """
    try:
        conn = pool.connect()

        metadata = MetaData()
        items = Table('items', metadata, autoload_with=conn)
        variants = Table('variants', metadata, autoload_with=conn)
        sizes = Table('sizes', metadata, autoload_with=conn)

        stmt = select(items).where(items.c.product == product)
        result = conn.execute(stmt)
        row = result.fetchone()

        # write to items
        # get resulting item_id to write for other tables
        if row:
            # if this is first time product is added
            item_id = row[0]
        else:
            # add product to table
            item_insert_stmt = insert(items).values(product=product, price=price)
            result = conn.execute(item_insert_stmt)
            item_id = result.inserted_primary_key[0]

        # write to variants
        # get resulting variant_id for supreme_size table
        variant_insert_stmt = insert(variants).values(item_id=item_id, variant=variant, img_link=img_link, url=url)
        result = conn.execute(variant_insert_stmt)
        variant_id = result.inserted_primary_key[0]

        # write to sizes
        for size in clothes_sizes:
            size_insert_stmt = insert(sizes).values(item_id=item_id, variant_id=variant_id, size=size)
            conn.execute(size_insert_stmt)

        conn.commit()
        print(f"-Transaction for {product}, {variant} committed successfully.")

    except Exception as e:
        print(f"Error executing transaction for {product}, {variant}: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    asession = AsyncHTMLSession()
    asession.run(scrape_items)