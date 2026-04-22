#!/bin/bash
set -e
echo "Running database migrations..."
DEBUG=True python manage.py migrate
echo "Running collectstatic..."
DEBUG=True python manage.py collectstatic --noinput
echo "Build complete."
