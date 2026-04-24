import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')

import django
django.setup()

from apps.accounts.models import TutorProfile, KnowledgeArea

print('=== CIUDADES ===')
for c in TutorProfile.objects.exclude(city='').exclude(city=None).values_list('city', 'country').distinct():
    print(c)

print('=== AREAS ===')
for area in KnowledgeArea.objects.prefetch_related('subjects').all():
    print(area.name)
    for s in area.subjects.all():
        print('  ' + s.name)
