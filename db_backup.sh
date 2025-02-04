#!/bin/bash

# Load environment variables from .env file
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "Error: .env file not found!"
  exit 1
fi

# Check required environment variables
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_SERVER" ]; then
  echo "Error: POSTGRES_USER or POSTGRES_SERVER not defined in .env!"
  exit 1
fi

DEFAULT_CONTAINER_NAME="agents-db"
DEBUG=false
DATA_ONLY=false
BACKUP_FILE="backup.sql"
CONTAINER_NAME="$DEFAULT_CONTAINER_NAME"

show_help() {
  echo "Usage: $0 <command> [options]"
  echo ""
  echo "Commands:"
  echo "  backup           Create a backup of the database"
  echo "  restore          Restore the database from a backup"
  echo ""
  echo "Options for backup and restore:"
  echo "  -f <file_path>    Specify the backup file path (default: $BACKUP_FILE)"
  echo "  -c <container>    Specify the Docker container name (default: $DEFAULT_CONTAINER_NAME)"
  echo "  -d                Include --data-only flag for backup (optional)"
  echo "  --debug           Enable debug mode, showing inner command output"
  echo ""
  echo "Examples:"
  echo "  $0 backup -f /path/to/backup.sql -c container_name --debug"
  echo "  $0 restore -f /path/to/backup.sql -c container_name"
}

backup() {
  BACKUP_FLAG=""
  if [ "$DATA_ONLY" == "true" ]; then
    BACKUP_FLAG="--data-only"
  fi

  echo "Starting backup..."

  if [ "$DEBUG" == "true" ]; then
    docker exec -t "$CONTAINER_NAME" pg_dumpall -U "$POSTGRES_USER" $BACKUP_FLAG > "$BACKUP_FILE"
  else
    docker exec -t "$CONTAINER_NAME" pg_dumpall -U "$POSTGRES_USER" $BACKUP_FLAG > "$BACKUP_FILE" 2>/dev/null
  fi

  if [ $? -eq 0 ]; then
    echo "Backup completed successfully: $BACKUP_FILE"
  else
    echo "Backup failed! Use --debug to see inner info or use --help to view options"
    exit 1
  fi
}

restore() {
  echo "Starting restore..."

  # Ensure backup file exists before attempting restore
  if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file $BACKUP_FILE does not exist!"
    exit 1
  fi

  # Run restore command
  if [ "$DEBUG" == "true" ]; then
    cat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -h "$POSTGRES_SERVER"
  else
    cat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -h "$POSTGRES_SERVER" > /dev/null 2>&1
  fi

  if [ $? -eq 0 ]; then
    echo "Restore completed successfully."
  else
    echo "Restore failed! Use --debug to see inner info or use --help to view options"
    exit 1
  fi
}

# Check if command is provided
if [ -z "$1" ] && [ "$1" != "--help" ]; then
  echo "Error: Command (backup or restore) is required."
  show_help
  exit 1
fi

if [ "$1" == "--help" ]; then
  show_help
  exit 0
fi

COMMAND="$1"
shift

while [[ "$1" == -* ]]; do
  case $1 in
    -f)
      BACKUP_FILE="$2"
      shift 2
      ;;
    -c)
      CONTAINER_NAME="$2"
      shift 2
      ;;
    -d)
      DATA_ONLY="true"
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    *)
      show_help
      exit 1
      ;;
  esac
done

# Handle the command and pass the remaining arguments to the corresponding function
case $COMMAND in
  backup)
    backup "$@"
    ;;
  restore)
    restore "$@"
    ;;
  *)
    echo "Error: Invalid command '$COMMAND'. Please use 'backup' or 'restore'. See --help for info"
    show_help
    exit 1
    ;;
esac
