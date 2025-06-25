from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.notificaciones.signals import (
    enviar_recordatorios_actividades,
    verificar_bajo_rendimiento,
    limpiar_notificaciones_antiguas
)


class Command(BaseCommand):
    help = 'Envía recordatorios automáticos y verifica alertas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['recordatorios', 'bajo_rendimiento', 'limpiar', 'todo'],
            default='todo',
            help='Tipo de tarea a ejecutar'
        )
        
        parser.add_argument(
            '--dias-limpieza',
            type=int,
            default=30,
            help='Días de antigüedad para limpiar notificaciones'
        )
    
    def handle(self, *args, **options):
        tipo = options['tipo']
        
        self.stdout.write(
            self.style.SUCCESS(f'Iniciando tareas de notificaciones: {tipo}')
        )
        
        if tipo in ['recordatorios', 'todo']:
            self.stdout.write('Enviando recordatorios de actividades...')
            try:
                enviar_recordatorios_actividades()
                self.stdout.write(
                    self.style.SUCCESS('✓ Recordatorios enviados correctamente')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error enviando recordatorios: {str(e)}')
                )
        
        if tipo in ['bajo_rendimiento', 'todo']:
            self.stdout.write('Verificando bajo rendimiento...')
            try:
                verificar_bajo_rendimiento()
                self.stdout.write(
                    self.style.SUCCESS('✓ Verificación de rendimiento completada')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error verificando rendimiento: {str(e)}')
                )
        
        if tipo in ['limpiar', 'todo']:
            dias = options['dias_limpieza']
            self.stdout.write(f'Limpiando notificaciones de más de {dias} días...')
            try:
                limpiar_notificaciones_antiguas()
                self.stdout.write(
                    self.style.SUCCESS('✓ Limpieza completada')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error en limpieza: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Tareas de notificaciones completadas')
        )