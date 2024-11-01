from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio import ASGIApp

from app.api.main import api_router
from app.db.database import create_db_and_tables, wait_for_db
from app.sockets.main import sio

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    wait_for_db()
    create_db_and_tables()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


app.include_router(api_router)
socket_app = ASGIApp(sio, app)
