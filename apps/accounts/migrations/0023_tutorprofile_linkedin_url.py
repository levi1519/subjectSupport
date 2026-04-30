from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0022_tutorprofile_hourly_rate_updated_at')]
    operations = [
        migrations.AddField(
            model_name='tutorprofile',
            name='linkedin_url',
            field=models.URLField(
                blank=True, null=True,
                verbose_name='LinkedIn',
                help_text='Perfil de LinkedIn (opcional). Ej: https://linkedin.com/in/tu-nombre'
            ),
        ),
    ]
