#!/bin/bash
set -e

SQL_FILE="/app/secunda_assignment/storage/sql/init.sql"
DB_HOST="db"
DB_USER="${POSTGRES_USER}"
DB_NAME="${POSTGRES_DB}"

echo "Waiting for PostgreSQL to be ready at $DB_HOST..."

until pg_isready -h $DB_HOST -U $DB_USER -d $DB_NAME; do
  echo "Database is unavailable, retrying...";
  sleep 1;
done

echo "Database is ready, importing $SQL_FILE..."

psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f $SQL_FILE

echo "Database initialization complete."
