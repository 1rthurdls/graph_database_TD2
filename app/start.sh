#!/bin/sh
set -e

echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "Starting FastAPI..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
