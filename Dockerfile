FROM python:3.11

WORKDIR /code

COPY ./pyproject.toml /code/pyproject.toml

RUN pip install --no-cache-dir /code

COPY ./app /code/app

COPY ./alembic.ini /code/alembic.ini

EXPOSE 8080

CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8080"]