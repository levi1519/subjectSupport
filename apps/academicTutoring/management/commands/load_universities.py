from django.core.management.base import BaseCommand
from apps.academicTutoring.models import Institution

ECUADOR_UNIVERSITIES = [
    ("Universidad Central del Ecuador", "Pichincha", "Quito"),
    ("Pontificia Universidad Católica del Ecuador", "Pichincha", "Quito"),
    ("Universidad San Francisco de Quito", "Pichincha", "Quito"),
    ("Universidad de las Américas", "Pichincha", "Quito"),
    ("Universidad Tecnológica Equinoccial", "Pichincha", "Quito"),
    ("Universidad Internacional del Ecuador", "Pichincha", "Quito"),
    ("Universidad Politécnica Salesiana", "Pichincha", "Quito"),
    ("Universidad Andina Simón Bolívar", "Pichincha", "Quito"),
    ("FLACSO Ecuador", "Pichincha", "Quito"),
    ("Universidad de Guayaquil", "Guayas", "Guayaquil"),
    ("Escuela Superior Politécnica del Litoral (ESPOL)", "Guayas", "Guayaquil"),
    ("Universidad Católica de Santiago de Guayaquil", "Guayas", "Guayaquil"),
    ("Universidad Casa Grande", "Guayas", "Guayaquil"),
    ("Universidad Estatal de Milagro (UNEMI)", "Guayas", "Milagro"),
    ("Universidad Agraria del Ecuador", "Guayas", "Guayaquil"),
    ("Universidad de Cuenca", "Azuay", "Cuenca"),
    ("Universidad del Azuay", "Azuay", "Cuenca"),
    ("Universidad Politécnica Salesiana Sede Cuenca", "Azuay", "Cuenca"),
    ("Universidad Técnica de Ambato", "Tungurahua", "Ambato"),
    ("Universidad Regional Autónoma de los Andes (UNIANDES)", "Tungurahua", "Ambato"),
    ("Universidad Técnica de Machala", "El Oro", "Machala"),
    ("Universidad Técnica de Manabí", "Manabí", "Portoviejo"),
    ("Escuela Superior Politécnica Agropecuaria de Manabí", "Manabí", "Calceta"),
    ("Universidad Laica Eloy Alfaro de Manabí", "Manabí", "Manta"),
    ("Universidad Técnica del Norte", "Imbabura", "Ibarra"),
    ("Universidad Técnica de Cotopaxi", "Cotopaxi", "Latacunga"),
    ("Universidad Nacional de Loja", "Loja", "Loja"),
    ("Universidad Técnica Particular de Loja (UTPL)", "Loja", "Loja"),
    ("Universidad Estatal de Bolívar", "Bolívar", "Guaranda"),
    ("Universidad Técnica de Babahoyo", "Los Ríos", "Babahoyo"),
    ("Universidad Técnica Luis Vargas Torres de Esmeraldas", "Esmeraldas", "Esmeraldas"),
    ("Universidad Estatal Amazónica", "Pastaza", "Puyo"),
    ("Universidad Nacional de Chimborazo", "Chimborazo", "Riobamba"),
    ("Escuela Superior Politécnica de Chimborazo (ESPOCH)", "Chimborazo", "Riobamba"),
    ("Universidad Estatal de Galápagos", "Galápagos", "Puerto Baquerizo Moreno"),
    ("Universidad Técnica de Santa Elena", "Santa Elena", "La Libertad"),
    ("Universidad Estatal Península de Santa Elena (UPSE)", "Santa Elena", "La Libertad"),
    ("Universidad de Otavalo", "Imbabura", "Otavalo"),
    ("Universidad Intercultural de las Nacionalidades y Pueblos Indígenas", "Chimborazo", "Riobamba"),
    ("Universidad Yachay Tech", "Imbabura", "Urcuquí"),
    ("Universidad Ikiam", "Napo", "Tena"),
    ("Universidad de las Fuerzas Armadas (ESPE)", "Pichincha", "Sangolquí"),
    ("Universidad Particular de Especialidades Espíritu Santo", "Guayas", "Guayaquil"),
    ("Universidad Metropolitana", "Guayas", "Guayaquil"),
    ("Universidad Tecnológica ECOTEC", "Guayas", "Guayaquil"),
    ("Universidad Tecnológica Empresarial de Guayaquil", "Guayas", "Guayaquil"),
    ("Universidad Politécnica Salesiana Sede Guayaquil", "Guayas", "Guayaquil"),
    ("Universidad del Pacífico", "Pichincha", "Quito"),
    ("Universidad Hemisferios", "Pichincha", "Quito"),
    ("Instituto Tecnológico Superior Espíritu Santo", "Guayas", "Guayaquil"),
]


class Command(BaseCommand):
    help = 'Carga universidades de Ecuador en la base de datos'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for name, province, city in ECUADOR_UNIVERSITIES:
            _, was_created = Institution.objects.get_or_create(
                name=name,
                defaults={
                    'type': 'universidad',
                    'province': province,
                    'city': city,
                    'is_manual': False,
                    'needs_review': False,
                    'active': True,
                }
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'{created} universidades creadas, {skipped} ya existian.'
            )
        )
