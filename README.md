# Agents Framework

### Development
1. Install the dev dependencies
    ```bash
    pip install .[dev]
    ```
2. Setup pre-commit
    ```bash
    pre-commit install
    ```

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
