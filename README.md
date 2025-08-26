# Agents Framework

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-010101?style=for-the-badge&logo=socket.io&logoColor=white)](https://socket.io/)
[![SQLModel](https://img.shields.io/badge/SQLModel-7E56C2?style=for-the-badge)](https://sqlmodel.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Ruff](https://img.shields.io/badge/Ruff-D7FF64?style=for-the-badge&logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![Pre-Commit](https://img.shields.io/badge/Pre--Commit-FAB040?style=for-the-badge&logo=pre-commit&logoColor=black)](https://pre-commit.com/)

---
### Running the Application
First of all, you need to create a `.env` file in the root directory of the project.
You can use the `.env.example` file as a template.

#### Locally:
1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Install requirements
    ```bash
    uv sync
    ```
3. Start the API:
    ```bash
    uv run uvicorn app.main:socket_app --reload
    ```
4. Start the UI:
   ```bash
   uv run -m streamlit run ui/main.py
   ```
5. The app is available on:
   - UI: http://127.0.0.1:8501
   - API: http://127.0.0.1:8000

#### Docker
1. Make sure you have Docker installed
2. Build the images
    ```bash
    docker build -t agents-framework:latest .
    docker build -t agents-framework-ui:latest -f ui/Dockerfile .
    ```
3. Run the app
    ```bash
   docker compose up
    ```
4. The app is available on:
   - UI: http://127.0.0.1:8501
   - API: http://127.0.0.1:8080
5. Alternatively, you can build the images and run the app with a single command using the startup script:
    ```bash
    bash run.sh
    ```

---
### Development
1. Install the dev dependencies
    ```bash
    uv sync --extra dev
    ```
2. Setup pre-commit
    ```bash
    pre-commit install
    ```

---
### Database backups and restore

#### Bash
To create a backup
```bash
./db_backup.sh backup -f file_path.sql
```
To restore a backup
```bash
./db_backup.sh restore -f file_path.sql
```
Use command below for more options
```bash
./db_backup.sh --help
```

#### Running commands inside docker manually
Change corresponding values if needed

Backup:
```bash
docker exec -t agents-db pg_dumpall -h localhost -U postgres --data-only > dump.sql
```
Restore:
```bash
cat dump.sql | docker exec -i agents-db psql -U postgres -h localhost
```
