FROM python:3.12-slim-bookworm

WORKDIR /code

COPY ./pyproject.toml /code/pyproject.toml

RUN pip install --no-cache-dir /code

COPY ./app /code/app

COPY ./ui /code/ui

COPY ./.streamlit /code/.streamlit

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["python3", "-m", "streamlit", "run", "ui/main.py", "--server.port=8501", "--server.address=0.0.0.0"]