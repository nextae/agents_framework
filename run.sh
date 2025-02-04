docker build -t agents-framework:latest .
docker build -t agents-framework-ui:latest -f ui/Dockerfile .
docker compose up