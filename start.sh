#!/bin/bash
set -e

echo "=== Starting subjectSupport Application ==="

# Set up GDAL/GEOS library paths for production
GDAL_LIB=$(ldconfig -p 2>/dev/null | grep -m1 libgdal | awk -F" " "{print \$(NF)}" || echo "")
GEOS_LIB=$(ldconfig -p 2>/dev/null | grep -m1 libgeos_c | awk -F" " "{print \$(NF)}" || echo "")

[ -n "$GDAL_LIB" ] && export GDAL_LIBRARY_PATH=$GDAL_LIB
[ -n "$GEOS_LIB" ] && export GEOS_LIBRARY_PATH=$GEOS_LIB

echo "GDAL_LIBRARY_PATH=$GDAL_LIBRARY_PATH"
echo "GEOS_LIBRARY_PATH=$GEOS_LIBRARY_PATH"

# Run migrations before starting the app
echo "=== Running Database Migrations ==="
python manage.py migrate --noinput

# Collect static files
echo "=== Collecting Static Files ==="
python manage.py collectstatic --noinput

# Start the application
echo "=== Starting Gunicorn ==="
exec gunicorn subjectSupport.wsgi:application --bind 0.0.0.0:8080 --workers 4 --timeout 120
