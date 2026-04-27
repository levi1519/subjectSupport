from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulators', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulator',
            name='tutor_reviewed_at',
            field=models.DateTimeField(
                blank=True, null=True,
                verbose_name='Revisado por tutor el'
            ),
        ),
        migrations.AddField(
            model_name='simulator',
            name='tutor_feedback',
            field=models.TextField(
                blank=True, null=True,
                verbose_name='Comentario del tutor',
                help_text='Visible al estudiante si el simulacro es rechazado'
            ),
        ),
        migrations.AlterField(
            model_name='simulator',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Borrador'),
                    ('published', 'Publicado'),
                    ('pending_approval', 'Pendiente de aprobación'),
                    ('approved', 'Aprobado por tutor'),
                    ('rejected', 'Rechazado por tutor'),
                    ('closed', 'Cerrado'),
                ],
                default='draft',
                max_length=20,
                verbose_name='Estado'
            ),
        ),
    ]
