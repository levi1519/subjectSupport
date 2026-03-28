#!/usr/bin/env bash
set -o errexit

# Encontrar GDAL dinámicamente en Nix store
export GDAL_LIBRARY_PATH=$(find /nix/store -name "libgdal.so" 2>/dev/null | head -1)
export GEOS_LIBRARY_PATH=$(find /nix/store -name "libgeos_c.so" 2>/dev/null | head -1)
echo "GDAL: $GDAL_LIBRARY_PATH"
echo "GEOS: $GEOS_LIBRARY_PATH"

pip install -r requirements.txt
python manage.py collectstatic --no-input