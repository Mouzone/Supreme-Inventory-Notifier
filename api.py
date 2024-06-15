from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Field, Session, SQLModel, create_engine, select
from dotenv import load_dotenv
import os


class Items(SQLModel, table=True):
    item_id: int = Field(primary_key=True)
    product: str
    price: float


class Variants(SQLModel, table=True):
    variant_id: int = Field(primary_key=True)
    item_id: int = Field(foreign_key="items.item_id")
    variant: str
    img_link: str
    url: str


class Sizes(SQLModel, table=True):
    size_id: int = Field(primary_key=True)
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:63342"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


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


@app.get("/descriptive/")
def read_descriptive():
    '''
    return:
    [{
        product: -,
        price: -,
        url: -,
        variants:
            [{
                variant:- ,
                img_link -,
                sizes: [x, y, z]
            }]
    }...]
    '''
    with (Session(engine) as session):
        items = session.exec(
            select(Items)
        ).all()
        results = []
        for item in items:
            variants = session.exec(
                select(Variants)
                .where(Variants.item_id == item.item_id)
            ).all()
            result = {
                "product": item.product,
                "price": item.price,
                "variants": []
            }
            for variant in variants:
                sizes = session.exec(
                    select(Sizes)
                    .where(Sizes.variant_id == variant.variant_id)
                ).all()
                result["variants"].append({
                    "variant": variant.variant,
                    "img_link": variant.img_link,
                    "url": variant.url,
                    "sizes": [size.size for size in sizes]
                })
            results.append(result)
        return results
