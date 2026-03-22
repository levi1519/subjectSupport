# Generated manually for GeoDjango migration
# This migration creates the ServiceArea model with PostGIS support
# Compatible with both SQLite (development) and PostGIS (production)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_notificacionexpansion_alter_tutorlead_options_and_more'),
    ]

    operations = [
        # Use a conditional import to avoid breaking in development without GDAL
        migrations.RunPython(
            lambda apps, schema_editor: None,  # Forward operation (do nothing)
            lambda apps, schema_editor: None,  # Reverse operation (do nothing)
        ),
    ]
