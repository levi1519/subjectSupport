from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_add_knowledge_document_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='tutorprofile',
            name='hourly_rate_updated_at',
            field=models.DateTimeField(
                blank=True, null=True,
                verbose_name='Tarifa actualizada el'
            ),
        ),
    ]
