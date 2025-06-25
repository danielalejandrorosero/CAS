from django.core.management.base import BaseCommand
from apps.notificaciones.models import TipoNotificacion


class Command(BaseCommand):
    help = 'Inicializa los tipos de notificaciones en la base de datos'
    
    def handle(self, *args, **options):
        tipos_notificacion = [
            {
                'nombre': 'NUEVA_ACTIVIDAD',
                'descripcion': 'Notificación cuando se crea una nueva actividad'
            },
            {
                'nombre': 'ACTIVIDAD_VALORADA',
                'descripcion': 'Notificación cuando una actividad es valorada'
            },
            {
                'nombre': 'CITACION_COMITE',
                'descripcion': 'Notificación de citación a comité'
            },
            {
                'nombre': 'ALTA_INASISTENCIA',
                'descripcion': 'Alerta por alta inasistencia'
            },
            {
                'nombre': 'BAJO_RENDIMIENTO',
                'descripcion': 'Alerta por bajo rendimiento académico'
            },
            {
                'nombre': 'RECORDATORIO',
                'descripcion': 'Recordatorios de actividades próximas a vencer'
            },
            {
                'nombre': 'SISTEMA',
                'descripcion': 'Notificaciones del sistema'
            },
        ]
        
        self.stdout.write('Inicializando tipos de notificaciones...')
        
        creados = 0
        actualizados = 0
        
        for tipo_data in tipos_notificacion:
            tipo, created = TipoNotificacion.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults={
                    'descripcion': tipo_data['descripcion'],
                    'activo': True
                }
            )
            
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado: {tipo.get_nombre_display()}')
                )
            else:
                # Actualizar descripción si es diferente
                if tipo.descripcion != tipo_data['descripcion']:
                    tipo.descripcion = tipo_data['descripcion']
                    tipo.save()
                    actualizados += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Actualizado: {tipo.get_nombre_display()}')
                    )
                else:
                    self.stdout.write(
                        f'- Ya existe: {tipo.get_nombre_display()}'
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nInicialización completada:\n'
                f'- Tipos creados: {creados}\n'
                f'- Tipos actualizados: {actualizados}\n'
                f'- Total tipos: {TipoNotificacion.objects.count()}'
            )
        )