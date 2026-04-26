from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academicTutoring',
         '0017_classsession_video_archive_platformconfig_rate_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='classsession',
            name='student_rating',
            field=models.PositiveSmallIntegerField(
                null=True, blank=True,
                verbose_name='Calificación del estudiante al tutor'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='student_rating_comment',
            field=models.TextField(
                blank=True, null=True,
                verbose_name='Comentario del estudiante'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='student_rated_at',
            field=models.DateTimeField(
                null=True, blank=True,
                verbose_name='Calificado por estudiante el'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='tutor_rating',
            field=models.PositiveSmallIntegerField(
                null=True, blank=True,
                verbose_name='Calificación del tutor al estudiante'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='tutor_rating_comment',
            field=models.TextField(
                blank=True, null=True,
                verbose_name='Comentario del tutor'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='tutor_rated_at',
            field=models.DateTimeField(
                null=True, blank=True,
                verbose_name='Calificado por tutor el'
            ),
        ),
    ]
