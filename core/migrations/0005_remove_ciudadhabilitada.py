# Generated manually - Remove obsolete CiudadHabilitada model
# Replaced by ServiceArea (GeoDjango)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_add_service_area_gis'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CiudadHabilitada',
        ),
    ]
