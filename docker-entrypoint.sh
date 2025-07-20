#!/bin/sh
set -e  # fail fast

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
