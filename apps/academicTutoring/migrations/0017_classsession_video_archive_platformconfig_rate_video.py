from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academicTutoring', '0016_platformconfig_session_material_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='classsession',
            name='recording_url',
            field=models.URLField(
                blank=True, null=True, max_length=500,
                verbose_name='URL del video de la clase'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='video_uploaded_at',
            field=models.DateTimeField(
                blank=True, null=True,
                verbose_name='Video subido el'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='video_expires_at',
            field=models.DateTimeField(
                blank=True, null=True,
                verbose_name='Video disponible hasta'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='is_archived',
            field=models.BooleanField(
                default=False,
                verbose_name='Sesión archivada'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='archived_at',
            field=models.DateTimeField(
                blank=True, null=True,
                verbose_name='Archivada el'
            ),
        ),
        migrations.AddField(
            model_name='platformconfig',
            name='video_retention_days',
            field=models.IntegerField(
                default=7,
                verbose_name='Días de retención del video'
            ),
        ),
        migrations.AddField(
            model_name='platformconfig',
            name='session_archive_days',
            field=models.IntegerField(
                default=30,
                verbose_name='Días para archivar sesión completada'
            ),
        ),
        migrations.AddField(
            model_name='platformconfig',
            name='hourly_rate_min',
            field=models.DecimalField(
                max_digits=5, decimal_places=2, default=5.00,
                verbose_name='Tarifa mínima por hora (USD)'
            ),
        ),
        migrations.AddField(
            model_name='platformconfig',
            name='hourly_rate_cooldown_days',
            field=models.IntegerField(
                default=30,
                verbose_name='Días de bloqueo para cambio de tarifa'
            ),
        ),
    ]
