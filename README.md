# Agents Framework

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
### Running the Application

#### Locally:
1. Install requirements
    ```bash
    pip install .
    ```
2. Start the app:
    ```bash
    uvicorn app.main:socket_app --reload
    ```
3. The app is available on http://127.0.0.1:8000

#### Docker
1. Build the image
    ```bash
    docker build -t agents-framework:latest .
    ```
2. Run the app
    ```bash
   docker compose up
    ```
3. The app is available on http://127.0.0.1:8080

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
docker exec -t agents_framework-database-1 pg_dumpall -h localhost -U postgres --data-only > dump.sql
```
Restore:
```bash
cat dump.sql | docker exec -i agents_framework-database-1 psql -U postgres -h localhost
```