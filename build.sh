#!/bin/bash
set -e
echo "Running collectstatic..."
DEBUG=True python manage.py collectstatic --noinput
echo "Build complete."
