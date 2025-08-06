#!/bin/bash

echo "wait for db to start..."

while ! pg_isready -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER"; do
  sleep 2
done

echo "Start Celery"

celery -A main.celery worker --loglevel=info &

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
