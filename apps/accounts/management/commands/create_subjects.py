from django.core.management.base import BaseCommand
from apps.accounts.models import KnowledgeArea, Subject

class Command(BaseCommand):
    help = 'Carga areas de conocimiento y materias iniciales'

    def handle(self, *args, **options):
        areas_data = {
            'Matematicas': ['Algebra', 'Calculo', 'Geometria', 'Estadistica', 'Matematicas Discretas', 'Trigonometria'],
            'Ciencias Naturales': ['Fisica', 'Quimica', 'Biologia', 'Quimica Organica', 'Fisica Cuantica'],
            'Programacion e Informatica': ['Python', 'Java', 'JavaScript', 'C++', 'Estructuras de Datos', 'Algoritmos', 'Bases de Datos', 'Programacion Web', 'React', 'Django'],
            'Ingenieria': ['Circuitos Electricos', 'Electronica', 'Termodinamica', 'Mecanica de Fluidos', 'Resistencia de Materiales'],
            'Ciencias Sociales': ['Historia', 'Geografia', 'Filosofia', 'Economia', 'Sociologia'],
            'Idiomas': ['Ingles', 'Frances', 'Portugues', 'Aleman', 'Chino Mandarin'],
            'Administracion y Contabilidad': ['Contabilidad', 'Finanzas', 'Administracion de Empresas', 'Marketing', 'Auditoria'],
            'Derecho': ['Derecho Civil', 'Derecho Penal', 'Derecho Constitucional', 'Derecho Mercantil'],
            'Medicina y Salud': ['Anatomia', 'Fisiologia', 'Farmacologia', 'Bioquimica'],
            'Arte y Diseno': ['Diseno Grafico', 'Diseno Web', 'Ilustracion', 'Fotografia'],
        }

        created_areas = 0
        created_subjects = 0

        for area_name, subjects in areas_data.items():
            area, area_created = KnowledgeArea.objects.get_or_create(name=area_name)
            if area_created:
                created_areas += 1

            for subject_name in subjects:
                _, subj_created = Subject.objects.get_or_create(
                    name=subject_name,
                    defaults={'knowledge_area': area}
                )
                if subj_created:
                    created_subjects += 1

        self.stdout.write(self.style.SUCCESS(
            f'{created_areas} areas y {created_subjects} materias creadas.'
        ))
