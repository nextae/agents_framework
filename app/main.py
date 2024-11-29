from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio import ASGIApp

from app.api.errors import NotFoundError
from app.api.exception_handlers import not_found_error_handler
from app.api.main import api_router
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

app.include_router(api_router)
app.add_exception_handler(NotFoundError, not_found_error_handler)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


socket_app = ASGIApp(sio, app)
