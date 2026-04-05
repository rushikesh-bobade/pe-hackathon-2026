#!/bin/bash
set -e

echo "🚀 Starting URL Shortener..."

# Run the database seeder (idempotent — safe to run every boot)
echo "📦 Running database seeder..."
python seed.py

# Start the production server
echo "🌐 Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 60 run:app
