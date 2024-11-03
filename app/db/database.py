from os import getenv

from dotenv import load_dotenv
from sqlmodel import Session, create_engine

load_dotenv()

DATABASE_URL = (
    f"postgresql://"
    f"{getenv('POSTGRES_USER')}:"
    f"{getenv('POSTGRES_PASSWORD')}"
    f"@{getenv('POSTGRES_SERVER')}:5432/{getenv('POSTGRES_DB')}"
)
engine = create_engine(DATABASE_URL, echo=True)


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
