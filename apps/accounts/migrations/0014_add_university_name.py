# Generated manually for RF-REGISTER-001

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_add_university_name'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE accounts_tutorprofile
                ADD COLUMN IF NOT EXISTS university_name VARCHAR(200) NOT NULL DEFAULT '';
                
                ALTER TABLE accounts_clientprofile
                ADD COLUMN IF NOT EXISTS university_name VARCHAR(200) NOT NULL DEFAULT '';
            """,
            reverse_sql="""
                ALTER TABLE accounts_tutorprofile
                DROP COLUMN IF EXISTS university_name;
                
                ALTER TABLE accounts_clientprofile
                DROP COLUMN IF EXISTS university_name;
            """,
        ),
    ]
