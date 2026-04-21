#!/bin/bash
set -e

# Setear GDAL/GEOS paths dinámicamente (igual que el start command)
export GDAL_LIBRARY_PATH=$(find /nix/store -name "libgdal.so" 2>/dev/null | head -1)
export GEOS_LIBRARY_PATH=$(find /nix/store -name "libgeos_c.so" 2>/dev/null | head -1)

echo "GDAL: $GDAL_LIBRARY_PATH"
echo "GEOS: $GEOS_LIBRARY_PATH"

echo "Running collectstatic..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate

echo "Build complete."
