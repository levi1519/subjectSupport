from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('academicTutoring', '0019_classsession_tutor_ai_context')]
    operations = [
        migrations.AddField(
            model_name='platformconfig',
            name='session_reminder_hours',
            field=models.IntegerField(
                default=24,
                verbose_name='Horas de anticipación para recordatorio de sesión',
                help_text='Muestra banner al tutor cuando tiene sesiones en las próximas N horas'
            ),
        ),
    ]
