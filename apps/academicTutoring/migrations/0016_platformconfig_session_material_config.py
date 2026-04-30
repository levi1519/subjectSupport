from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('academicTutoring', '0015_platformconfig_full_rewrite_institution_sessionmaterial')]
    operations = [
        migrations.AddField(
            model_name='platformconfig',
            name='require_session_material_file',
            field=models.BooleanField(
                default=False,
                verbose_name='Exigir archivo en solicitud de sesión',
                help_text='Si está marcado, el estudiante DEBE subir un archivo al solicitar una clase'
            ),
        ),
        migrations.AddField(
            model_name='platformconfig',
            name='require_session_material_url',
            field=models.BooleanField(
                default=False,
                verbose_name='Exigir URL de material en solicitud de sesión',
                help_text='Si está marcado, el estudiante DEBE ingresar una URL al solicitar una clase'
            ),
        ),
    ]
