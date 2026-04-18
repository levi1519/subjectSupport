from django.db import migrations


def add_caribe_countries(apps, schema_editor):
    CountryConfig = apps.get_model('academicTutoring', 'CountryConfig')
    caribe = [
        ('DO', 'República Dominicana'),
        ('CU', 'Cuba'),
        ('PR', 'Puerto Rico'),
    ]
    for code, name in caribe:
        CountryConfig.objects.get_or_create(
            country_code=code,
            defaults={
                'country_name': name,
                'active': True,
                'geo_restricted': False,
            }
        )


def remove_caribe_countries(apps, schema_editor):
    CountryConfig = apps.get_model('academicTutoring', 'CountryConfig')
    CountryConfig.objects.filter(
        country_code__in=['DO', 'CU', 'PR']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('academicTutoring', '0007_latam_countries'),
    ]

    operations = [
        migrations.RunPython(
            add_caribe_countries,
            remove_caribe_countries
        ),
    ]
