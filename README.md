# Agents Framework

---
### Running the Application

#### Locally:
1. Install requirements
    ```bash
    pip install .
    ```
2. Start the API:
    ```bash
    uvicorn app.main:socket_app --reload
    ```
3. Start the UI:
   ```bash
   python3 -m streamlit run ui/main.py
   ```
4. The app is available on:
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
    pip install .[dev]
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
