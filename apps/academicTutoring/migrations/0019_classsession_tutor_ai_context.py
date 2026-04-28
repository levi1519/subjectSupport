from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('academicTutoring', '0018_classsession_ratings')]
    operations = [
        migrations.AddField(
            model_name='classsession',
            name='tutor_ai_context',
            field=models.TextField(
                blank=True, null=True,
                verbose_name='Contexto para IA',
                help_text='Indicaciones opcionales del tutor para orientar la generación del simulacro'
            ),
        ),
    ]
