from fastapi import FastAPI
from sqlmodel import Field, Session, SQLModel, create_engine, select
import os


class Item(SQLModel, table=True):
    item_id: int = Field(default=None, primary_key=True)
    product: str
    price: float


class Variant(SQLModel, table=True):
    variant_id: int = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.item_id")
    variant: str
    img_link: str
    url: str


class Size(SQLModel, table=True):
    size_id: int = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.item_id")
    variant_id: int = Field(foreign_key="variant.variant_id")
    size: str


def get_database_url() -> str:
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_host = '127.0.0.1'
    db_name = os.environ.get("DB_NAME")
    return f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"


def create_db_and_tables():
    database_url = get_database_url()
    engine = create_engine(database_url, echo=True)
    SQLModel.metadata.create_all(engine)


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
