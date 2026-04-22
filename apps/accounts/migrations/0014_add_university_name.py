# Generated manually for RF-REGISTER-001

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_add_university_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='tutorprofile',
            name='university_name',
            field=models.CharField(
                max_length=200,
                blank=True,
                null=True,
                verbose_name='Universidad / Institución',
            ),
        ),
        migrations.AddField(
            model_name='clientprofile',
            name='university_name',
            field=models.CharField(
                max_length=200,
                blank=True,
                null=True,
                verbose_name='Universidad donde estudia',
            ),
        ),
    ]
