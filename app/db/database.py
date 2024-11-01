import time
from os import getenv

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_URL = (
    f"postgresql://"
    f"{getenv('POSTGRES_USER')}:"
    f"{getenv('POSTGRES_PASSWORD')}"
    f"@localhost:5432/{getenv('POSTGRES_DB')}"
)  # TODO check if local or docker?
engine = create_engine(DATABASE_URL)


def wait_for_db():
    while True:
        try:
            with engine.connect():
                print("Database connected!")
                break
        except Exception as e:
            print(e)
            print("Waiting for the database...")
            time.sleep(2)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
