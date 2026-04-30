#!/bin/bash
set -e

# Activate virtual environment
. /opt/venv/bin/activate

echo "=== Starting subjectSupport Application ==="

# Set up GDAL/GEOS library paths for production
GDAL_LIB=$(ldconfig -p 2>/dev/null | grep -m1 libgdal | awk -F" " '{print $(NF)}' || echo "")
GEOS_LIB=$(ldconfig -p 2>/dev/null | grep -m1 libgeos_c | awk -F" " '{print $(NF)}' || echo "")

[ -n "$GDAL_LIB" ] && export GDAL_LIBRARY_PATH=$GDAL_LIB
[ -n "$GEOS_LIB" ] && export GEOS_LIBRARY_PATH=$GEOS_LIB

echo "GDAL_LIBRARY_PATH=$GDAL_LIBRARY_PATH"
echo "GEOS_LIBRARY_PATH=$GEOS_LIBRARY_PATH"

# Run migrations before starting the app
echo "=== Running Database Migrations ==="
python manage.py migrate --noinput --verbosity=2 || {
    echo "WARNING: Migration failed, attempting to recover..."
    # If migration 0012 fails because columns already exist or don't exist,
    # we may need to fake and reapply
    python manage.py migrate --fake accounts 0011 --verbosity=2 || true
    python manage.py migrate accounts 0012 --verbosity=2 || true
}

# Show migration status for debugging
echo "=== Migration Status ==="
python manage.py showmigrations accounts

# Ensure staticfiles directory exists
echo "=== Ensuring staticfiles directory exists ==="
mkdir -p /app/staticfiles

# Collect static files
echo "=== Collecting Static Files ==="
python manage.py collectstatic --noinput --clear

# Start the application
echo "=== Starting Gunicorn ==="
exec gunicorn subjectSupport.wsgi:application --bind 0.0.0.0:8080 --workers 4 --timeout 120
