"""
Django management command para poblar las áreas de servicio (ServiceArea).

Uso:
    python manage.py populate_service_areas

Este comando crea el polígono de cobertura para el Cantón Milagro, Provincia Guayas.
El polígono es una aproximación del área urbana y rural del cantón.
"""

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon
from core.models import ServiceArea


class Command(BaseCommand):
    help = 'Popula las áreas de servicio con el polígono del Cantón Milagro'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Poblando áreas de servicio...'))

        # Polígono aproximado del Cantón Milagro, Provincia Guayas, Ecuador
        # Coordenadas en formato (longitud, latitud) - SRID 4326 (WGS84)
        # Este polígono cubre aproximadamente el área urbana y rural de Milagro

        milagro_coords = [
            (-79.65, -2.08),   # Noroeste
            (-79.53, -2.08),   # Noreste
            (-79.53, -2.20),   # Sureste
            (-79.65, -2.20),   # Suroeste
            (-79.65, -2.08),   # Cierre del polígono (mismo que inicio)
        ]

        # Crear el polígono con SRID 4326 (WGS84 - estándar GPS)
        milagro_polygon = Polygon(milagro_coords, srid=4326)

        # Crear o actualizar el ServiceArea para Milagro
        service_area, created = ServiceArea.objects.update_or_create(
            city_name='Milagro',
            defaults={
                'area': milagro_polygon,
                'activo': True,
                'descripcion': (
                    'Área de cobertura del servicio para el Cantón Milagro, '
                    'Provincia del Guayas, Ecuador. Incluye zona urbana y rural.'
                )
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ ServiceArea creada: {service_area.city_name}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ ServiceArea actualizada: {service_area.city_name}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                '\n Datos del área de servicio creada:'
            )
        )
        self.stdout.write(f'  • Ciudad: {service_area.city_name}')
        self.stdout.write(f'  • Estado: {"Activo" if service_area.activo else "Inactivo"}')
        self.stdout.write(f'  • Descripción: {service_area.descripcion}')
        self.stdout.write(f'  • Área (WKT): {service_area.area.wkt[:100]}...')

        self.stdout.write(
            self.style.MIGRATE_LABEL(
                '\n NOTA: Este polígono es una aproximación rectangular.'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '  Para mayor precisión, edita el polígono desde el admin de Django'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '  usando el widget de mapa interactivo en /admin/core/servicearea/'
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                '\n✓ Población de áreas de servicio completada exitosamente'
            )
        )
