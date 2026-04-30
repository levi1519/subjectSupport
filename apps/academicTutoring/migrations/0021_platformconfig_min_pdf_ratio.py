from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('academicTutoring', '0020_platformconfig_reminder_hours')]
    operations = [
        migrations.AddField(
            model_name='platformconfig',
            name='min_pdf_materials_ratio',
            field=models.FloatField(
                default=0.5,
                verbose_name='Ratio mínimo de PDFs en materiales',
                help_text='Proporción mínima de PDFs respecto al total. Default=0.5 (mitad)'
            ),
        ),
    ]
