#!/bin/bash
set -e
echo "Running collectstatic..."
python manage.py collectstatic --noinput
echo "Running migrations..."
python manage.py migrate
echo "Build complete."
