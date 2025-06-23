from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import CitacionComite, SeguimientoCitacion
from apps.usuarios.models import Usuario
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=CitacionComite)
def generar_numero_citacion(sender, instance, **kwargs):
    """Genera automáticamente el número de citación si no existe"""
    if not instance.numero_citacion:
        # Obtener el año actual
        año_actual = timezone.now().year
        
        # Buscar el último número de citación del año
        ultima_citacion = CitacionComite.objects.filter(
            numero_citacion__startswith=f'CIT-{año_actual}'
        ).order_by('-numero_citacion').first()
        
        if ultima_citacion:
            # Extraer el número secuencial
            try:
                ultimo_numero = int(ultima_citacion.numero_citacion.split('-')[-1])
                nuevo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                nuevo_numero = 1
        else:
            nuevo_numero = 1
        
        # Generar el nuevo número de citación
        instance.numero_citacion = f'CIT-{año_actual}-{nuevo_numero:04d}'


@receiver(post_save, sender=CitacionComite)
def manejar_cambios_citacion(sender, instance, created, **kwargs):
    """Maneja los cambios en las citaciones"""
    if created:
        # Nueva citación creada
        logger.info(f'Nueva citación creada: {instance.numero_citacion}')
        
        # Enviar notificación al aprendiz (si está configurado)
        if hasattr(settings, 'EMAIL_NOTIFICATIONS_ENABLED') and settings.EMAIL_NOTIFICATIONS_ENABLED:
            enviar_notificacion_citacion(instance)
    
    else:
        # Citación actualizada
        # Verificar si cambió el estado
        if hasattr(instance, '_state_changed'):
            logger.info(
                f'Estado de citación {instance.numero_citacion} '
                f'cambió a {instance.estado}'
            )
            
            # Si se marcó como notificada, registrar la fecha
            if instance.estado == 'NOTIFICADA' and not instance.fecha_notificacion:
                instance.fecha_notificacion = timezone.now()
                instance.save(update_fields=['fecha_notificacion'])
            
            # Si se marcó como realizada, registrar la fecha
            elif instance.estado == 'REALIZADA' and not instance.fecha_realizacion:
                instance.fecha_realizacion = timezone.now()
                instance.save(update_fields=['fecha_realizacion'])


@receiver(post_save, sender=SeguimientoCitacion)
def manejar_seguimiento_citacion(sender, instance, created, **kwargs):
    """Maneja la creación de seguimientos"""
    if created:
        logger.info(
            f'Nuevo seguimiento creado para citación '
            f'{instance.citacion.numero_citacion}'
        )
        
        # Si el seguimiento indica que se requiere otro seguimiento,
        # actualizar la citación
        if instance.requiere_nuevo_seguimiento and instance.fecha_proximo_seguimiento:
            citacion = instance.citacion
            citacion.requiere_seguimiento = True
            citacion.fecha_seguimiento = instance.fecha_proximo_seguimiento
            citacion.save(update_fields=['requiere_seguimiento', 'fecha_seguimiento'])


def enviar_notificacion_citacion(citacion):
    """Envía notificación por email al aprendiz sobre la citación"""
    try:
        if citacion.aprendiz.email:
            asunto = f'Citación a Comité - {citacion.numero_citacion}'
            
            # Contexto para el template
            contexto = {
                'citacion': citacion,
                'aprendiz': citacion.aprendiz,
                'instructor': citacion.instructor_citante,
                'ficha': citacion.ficha,
                'fecha_citacion': citacion.fecha_citacion,
                'motivo': citacion.get_motivo_display(),
                'motivo_detallado': citacion.motivo_detallado,
                'prioridad': citacion.get_prioridad_display(),
            }
            
            # Renderizar el mensaje
            mensaje_html = render_to_string(
                'comite/emails/notificacion_citacion.html',
                contexto
            )
            mensaje_texto = render_to_string(
                'comite/emails/notificacion_citacion.txt',
                contexto
            )
            
            # Enviar email
            send_mail(
                subject=asunto,
                message=mensaje_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[citacion.aprendiz.email],
                html_message=mensaje_html,
                fail_silently=False
            )
            
            logger.info(
                f'Notificación enviada a {citacion.aprendiz.email} '
                f'para citación {citacion.numero_citacion}'
            )
            
    except Exception as e:
        logger.error(
            f'Error enviando notificación para citación '
            f'{citacion.numero_citacion}: {str(e)}'
        )


def notificar_citaciones_proximas():
    """Función para notificar citaciones próximas (para usar en tareas programadas)"""
    from datetime import timedelta
    
    # Buscar citaciones que son en los próximos 3 días
    fecha_limite = timezone.now().date() + timedelta(days=3)
    
    citaciones_proximas = CitacionComite.objects.filter(
        estado='NOTIFICADA',
        fecha_citacion__lte=fecha_limite,
        fecha_citacion__gte=timezone.now().date()
    ).select_related('aprendiz', 'instructor_citante', 'ficha')
    
    for citacion in citaciones_proximas:
        try:
            if citacion.aprendiz.email:
                asunto = f'Recordatorio: Citación a Comité - {citacion.numero_citacion}'
                
                contexto = {
                    'citacion': citacion,
                    'aprendiz': citacion.aprendiz,
                    'dias_restantes': citacion.dias_hasta_citacion,
                    'es_recordatorio': True
                }
                
                mensaje_html = render_to_string(
                    'comite/emails/recordatorio_citacion.html',
                    contexto
                )
                mensaje_texto = render_to_string(
                    'comite/emails/recordatorio_citacion.txt',
                    contexto
                )
                
                send_mail(
                    subject=asunto,
                    message=mensaje_texto,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[citacion.aprendiz.email],
                    html_message=mensaje_html,
                    fail_silently=False
                )
                
                logger.info(
                    f'Recordatorio enviado para citación {citacion.numero_citacion}'
                )
                
        except Exception as e:
            logger.error(
                f'Error enviando recordatorio para citación '
                f'{citacion.numero_citacion}: {str(e)}'
            )


def notificar_citaciones_vencidas():
    """Función para notificar citaciones vencidas a los instructores"""
    # Buscar citaciones vencidas (fecha pasada y estado NOTIFICADA)
    citaciones_vencidas = CitacionComite.objects.filter(
        estado='NOTIFICADA',
        fecha_citacion__lt=timezone.now().date()
    ).select_related('aprendiz', 'instructor_citante', 'ficha')
    
    # Agrupar por instructor
    instructores_citaciones = {}
    for citacion in citaciones_vencidas:
        instructor = citacion.instructor_citante
        if instructor not in instructores_citaciones:
            instructores_citaciones[instructor] = []
        instructores_citaciones[instructor].append(citacion)
    
    # Enviar notificación a cada instructor
    for instructor, citaciones in instructores_citaciones.items():
        try:
            if instructor.email:
                asunto = f'Citaciones Vencidas - {len(citaciones)} pendientes'
                
                contexto = {
                    'instructor': instructor,
                    'citaciones': citaciones,
                    'total_citaciones': len(citaciones)
                }
                
                mensaje_html = render_to_string(
                    'comite/emails/citaciones_vencidas.html',
                    contexto
                )
                mensaje_texto = render_to_string(
                    'comite/emails/citaciones_vencidas.txt',
                    contexto
                )
                
                send_mail(
                    subject=asunto,
                    message=mensaje_texto,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instructor.email],
                    html_message=mensaje_html,
                    fail_silently=False
                )
                
                logger.info(
                    f'Notificación de citaciones vencidas enviada a {instructor.email}'
                )
                
        except Exception as e:
            logger.error(
                f'Error enviando notificación de citaciones vencidas '
                f'a {instructor.email}: {str(e)}'
            )