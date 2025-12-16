# Generated manually for GeoDjango migration
# This migration creates the ServiceArea model with PostGIS support

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_notificacionexpansion_alter_tutorlead_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city_name', models.CharField(help_text='Nombre de la ciudad que cubre esta área de servicio', max_length=100, unique=True, verbose_name='Ciudad')),
                ('area', django.contrib.gis.db.models.fields.PolygonField(help_text='Polígono que define el área geográfica donde el servicio está disponible', srid=4326, verbose_name='Área de Cobertura')),
                ('activo', models.BooleanField(default=True, help_text='Si está activo, usuarios dentro del polígono tendrán acceso al servicio', verbose_name='Activo')),
                ('descripcion', models.TextField(blank=True, help_text='Descripción del área (ej: Cantón Milagro, Provincia Guayas)', null=True, verbose_name='Descripción')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última Actualización')),
            ],
            options={
                'verbose_name': 'Área de Servicio',
                'verbose_name_plural': 'Áreas de Servicio',
                'ordering': ['city_name'],
            },
        ),
    ]
