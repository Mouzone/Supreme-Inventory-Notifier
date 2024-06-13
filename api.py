from fastapi import FastAPI
from sqlmodel import Field, Session, SQLModel, create_engine, select
from dotenv import load_dotenv
import os


class Items(SQLModel, table=True):
    item_id: int = Field(default=None, primary_key=True)
    product: str
    price: float


class Variants(SQLModel, table=True):
    variant_id: int = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="items.item_id")
    variant: str
    img_link: str
    url: str


class Sizes(SQLModel, table=True):
    size_id: int = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="items.item_id")
    variant_id: int = Field(foreign_key="variants.variant_id")
    size: str


def get_database_url() -> str:
    load_dotenv()
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_host = os.environ.get("DB_HOST")
    db_name = os.environ.get("DB_NAME")
    return f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"


# Create the engine
engine = create_engine(get_database_url(), echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/items/")
def read_items():
    with Session(engine) as session:
        items = session.exec(select(Items)).all()
        return items


@app.get("/variants/")
def read_variants():
    with Session(engine) as session:
        variants = session.exec(select(Variants)).all()
        return variants


@app.get("/sizes/")
def read_sizes():
    with Session(engine) as session:
        sizes = session.exec(select(Sizes)).all()
        return sizes
