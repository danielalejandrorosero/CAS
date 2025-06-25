from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .services import NotificacionService
from .models import ConfiguracionNotificacion


@receiver(post_save, sender='usuarios.Usuario')
def crear_configuracion_notificaciones(sender, instance, created, **kwargs):
    """
    Crea automáticamente la configuración de notificaciones para nuevos usuarios
    """
    if created:
        ConfiguracionNotificacion.objects.get_or_create(
            usuario=instance,
            defaults={
                'dias_activos': [0, 1, 2, 3, 4, 5, 6]  # Todos los días activos
            }
        )


@receiver(post_save, sender='actividades.Actividad')
def notificar_nueva_actividad(sender, instance, created, **kwargs):
    """
    Envía notificación cuando se crea una nueva actividad
    """
    if created:
        # Obtener aprendices relacionados con la actividad
        # Esto depende de cómo esté estructurado tu modelo de actividades
        try:
            from apps.usuarios.models import Usuario
            
            # Si la actividad tiene un campo 'grupo' o similar
            if hasattr(instance, 'grupo') and instance.grupo:
                aprendices = Usuario.objects.filter(
                    rol__nombre='APRENDIZ',
                    # Agregar filtro por grupo según tu modelo
                )
            else:
                # Si no hay grupo específico, notificar a todos los aprendices
                aprendices = Usuario.objects.filter(rol__nombre='APRENDIZ')
            
            # Enviar notificaciones
            NotificacionService.notificar_nueva_actividad(
                actividad=instance,
                usuarios=aprendices
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error enviando notificación de nueva actividad: {str(e)}")


@receiver(post_save, sender='actividades.CalificacionActividad')
def notificar_actividad_valorada(sender, instance, created, **kwargs):
    """
    Envía notificación cuando se valora una actividad
    """
    if created:
        try:
            NotificacionService.notificar_actividad_valorada(
                actividad=instance.actividad,
                usuario_aprendiz=instance.aprendiz,
                calificacion=instance.calificacion
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error enviando notificación de actividad valorada: {str(e)}")


@receiver(post_save, sender='comite.CitacionComite')
def notificar_citacion_comite(sender, instance, created, **kwargs):
    """
    Envía notificación cuando se crea una citación a comité
    """
    if created:
        try:
            NotificacionService.notificar_citacion_comite(instance)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error enviando notificación de citación a comité: {str(e)}")


@receiver(post_save, sender='asistencia.RegistroAsistencia')
def verificar_inasistencia(sender, instance, created, **kwargs):
    """
    Verifica si un aprendiz tiene alta inasistencia y envía notificación
    """
    if created and instance.estado in ['AUSENTE', 'AUSENTE_JUSTIFICADO']:
        try:
            from apps.asistencia.models import Asistencia
            from apps.usuarios.models import Usuario
            
            # Calcular porcentaje de inasistencia en los últimos 30 días
            fecha_limite = timezone.now() - timedelta(days=30)
            
            total_asistencias = Asistencia.objects.filter(
                aprendiz=instance.aprendiz,
                fecha__gte=fecha_limite
            ).count()
            
            if total_asistencias > 0:
                inasistencias = Asistencia.objects.filter(
                    aprendiz=instance.aprendiz,
                    fecha__gte=fecha_limite,
                    estado__in=['AUSENTE', 'AUSENTE_JUSTIFICADO']
                ).count()
                
                porcentaje_inasistencia = (inasistencias / total_asistencias) * 100
                
                # Si la inasistencia es mayor al 20%, enviar notificación
                if porcentaje_inasistencia > 20:
                    NotificacionService.notificar_alta_inasistencia(
                        usuario_aprendiz=instance.aprendiz,
                        porcentaje_inasistencia=round(porcentaje_inasistencia, 2)
                    )
                    
                    # También notificar a los instructores
                    instructores = Usuario.objects.filter(
                        rol__nombre='INSTRUCTOR'
                        # Agregar filtro por grupo/clase si es necesario
                    )
                    
                    for instructor in instructores:
                        NotificacionService.enviar_notificacion(
                            usuario=instructor,
                            tipo_notificacion='ALTA_INASISTENCIA',
                            titulo=f"Alerta: Alta inasistencia - {instance.aprendiz.get_full_name()}",
                            mensaje=f"El aprendiz {instance.aprendiz.get_full_name()} tiene un {porcentaje_inasistencia}% de inasistencia.",
                            objeto_relacionado=instance.aprendiz,
                            datos_extra={
                                'porcentaje': porcentaje_inasistencia,
                                'aprendiz_id': instance.aprendiz.id
                            }
                        )
                        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error verificando inasistencia: {str(e)}")


def verificar_bajo_rendimiento():
    """
    Función para verificar bajo rendimiento académico
    Esta función debe ser llamada periódicamente (ej. con Celery o cron)
    """
    try:
        from apps.usuarios.models import Usuario
        from apps.actividades.models import Calificacion
        from django.db.models import Avg
        
        # Obtener todos los aprendices
        aprendices = Usuario.objects.filter(rol__nombre='APRENDIZ')
        
        for aprendiz in aprendices:
            # Calcular promedio de calificaciones en los últimos 30 días
            fecha_limite = timezone.now() - timedelta(days=30)
            
            promedio = Calificacion.objects.filter(
                aprendiz=aprendiz,
                fecha_calificacion__gte=fecha_limite
            ).aggregate(promedio=Avg('calificacion'))['promedio']
            
            if promedio and promedio < 3.0:  # Asumiendo escala de 1-5
                NotificacionService.notificar_bajo_rendimiento(
                    usuario_aprendiz=aprendiz,
                    promedio=round(promedio, 2)
                )
                
                # También notificar a los instructores
                from apps.usuarios.models import Usuario
                instructores = Usuario.objects.filter(
                    rol__nombre='INSTRUCTOR'
                    # Agregar filtro por grupo/clase si es necesario
                )
                
                for instructor in instructores:
                    NotificacionService.enviar_notificacion(
                        usuario=instructor,
                        tipo_notificacion='BAJO_RENDIMIENTO',
                        titulo=f"Alerta: Bajo rendimiento - {aprendiz.get_full_name()}",
                        mensaje=f"El aprendiz {aprendiz.get_full_name()} tiene un promedio de {promedio}.",
                        objeto_relacionado=aprendiz,
                        datos_extra={
                            'promedio': promedio,
                            'aprendiz_id': aprendiz.id
                        }
                    )
                    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error verificando bajo rendimiento: {str(e)}")


# Función para recordatorios automáticos
def enviar_recordatorios_actividades():
    """
    Envía recordatorios de actividades próximas a vencer
    Esta función debe ser llamada diariamente
    """
    try:
        from apps.actividades.models import Actividad
        from apps.usuarios.models import Usuario
        from datetime import date
        
        # Actividades que vencen en 2 días
        fecha_recordatorio = date.today() + timedelta(days=2)
        
        actividades_proximas = Actividad.objects.filter(
            fecha_entrega=fecha_recordatorio,
            activa=True
        )
        
        for actividad in actividades_proximas:
            # Obtener aprendices que no han entregado la actividad
            # Esto depende de cómo manejes las entregas en tu modelo
            
            aprendices = Usuario.objects.filter(
                rol__nombre='APRENDIZ'
                # Agregar filtros según tu modelo
            )
            
            for aprendiz in aprendices:
                NotificacionService.enviar_notificacion(
                    usuario=aprendiz,
                    tipo_notificacion='RECORDATORIO',
                    titulo=f"Recordatorio: {actividad.titulo}",
                    mensaje=f"La actividad '{actividad.titulo}' vence en 2 días ({actividad.fecha_entrega}).",
                    objeto_relacionado=actividad
                )
                
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error enviando recordatorios: {str(e)}")


# Función para limpiar notificaciones antiguas
def limpiar_notificaciones_antiguas():
    """
    Limpia notificaciones leídas más antiguas que 30 días
    Esta función debe ser llamada semanalmente
    """
    try:
        eliminadas = NotificacionService.limpiar_notificaciones_antiguas(dias=30)
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Limpieza automática: {eliminadas} notificaciones eliminadas")
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en limpieza automática: {str(e)}")