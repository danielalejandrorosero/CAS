from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from typing import Optional, Dict, Any, List
import logging

from .models import (
    TipoNotificacion,
    Notificacion,
    ConfiguracionNotificacion,
    HistorialNotificacion
)

logger = logging.getLogger(__name__)


class NotificacionService:
    """Servicio para manejar el envío y gestión de notificaciones"""
    
    @staticmethod
    def enviar_notificacion(
        usuario,
        tipo_notificacion: str,
        titulo: str,
        mensaje: str,
        objeto_relacionado=None,
        datos_extra: Optional[Dict[str, Any]] = None,
        forzar_envio: bool = False
    ) -> Optional['Notificacion']:
        """
        Envía una notificación a un usuario específico
        
        Args:
            usuario: Usuario destinatario
            tipo_notificacion: Tipo de notificación (debe existir en TipoNotificacion)
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            objeto_relacionado: Objeto relacionado (opcional)
            datos_extra: Datos adicionales (opcional)
            forzar_envio: Si True, ignora las configuraciones del usuario
        
        Returns:
            Notificacion creada o None si no se pudo enviar
        """
        try:
            with transaction.atomic():
                # Obtener el tipo de notificación
                try:
                    tipo = TipoNotificacion.objects.get(
                        nombre=tipo_notificacion,
                        activo=True
                    )
                except TipoNotificacion.DoesNotExist:
                    logger.error(f"Tipo de notificación '{tipo_notificacion}' no encontrado")
                    return None
                
                # Verificar configuración del usuario (si no es forzado)
                if not forzar_envio:
                    config = NotificacionService._obtener_configuracion_usuario(usuario)
                    if not config.puede_recibir_notificacion(tipo_notificacion):
                        logger.info(f"Usuario {usuario.id} no puede recibir notificaciones de tipo {tipo_notificacion}")
                        return None
                
                # Preparar datos del objeto relacionado
                content_type = None
                object_id = None
                if objeto_relacionado:
                    content_type = ContentType.objects.get_for_model(objeto_relacionado)
                    object_id = objeto_relacionado.pk
                
                # Crear la notificación
                notificacion = Notificacion.objects.create(
                    usuario=usuario,
                    tipo=tipo,
                    titulo=titulo,
                    mensaje=mensaje,
                    content_type=content_type,
                    object_id=object_id,
                    datos_extra=datos_extra or {}
                )
                
                # Intentar enviar por diferentes métodos
                if not forzar_envio:
                    config = NotificacionService._obtener_configuracion_usuario(usuario)
                    
                    # Envío push
                    if config.notificaciones_push:
                        NotificacionService._enviar_push(notificacion)
                    
                    # Envío por email
                    if config.notificaciones_email:
                        NotificacionService._enviar_email(notificacion)
                else:
                    # Si es forzado, enviar por todos los métodos
                    NotificacionService._enviar_push(notificacion)
                    NotificacionService._enviar_email(notificacion)
                
                logger.info(f"Notificación enviada a usuario {usuario.id}: {titulo}")
                return notificacion
                
        except Exception as e:
            logger.error(f"Error al enviar notificación: {str(e)}")
            return None
    
    @staticmethod
    def enviar_notificacion_masiva(
        usuarios: List,
        tipo_notificacion: str,
        titulo: str,
        mensaje: str,
        objeto_relacionado=None,
        datos_extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        Envía una notificación a múltiples usuarios
        
        Returns:
            Dict con estadísticas del envío
        """
        enviadas = 0
        fallidas = 0
        
        for usuario in usuarios:
            notificacion = NotificacionService.enviar_notificacion(
                usuario=usuario,
                tipo_notificacion=tipo_notificacion,
                titulo=titulo,
                mensaje=mensaje,
                objeto_relacionado=objeto_relacionado,
                datos_extra=datos_extra
            )
            
            if notificacion:
                enviadas += 1
            else:
                fallidas += 1
        
        return {
            'enviadas': enviadas,
            'fallidas': fallidas,
            'total': len(usuarios)
        }
    
    @staticmethod
    def _obtener_configuracion_usuario(usuario) -> ConfiguracionNotificacion:
        """Obtiene o crea la configuración de notificaciones del usuario"""
        config, created = ConfiguracionNotificacion.objects.get_or_create(
            usuario=usuario,
            defaults={
                'dias_activos': [0, 1, 2, 3, 4, 5, 6]  # Todos los días
            }
        )
        return config
    
    @staticmethod
    def _enviar_push(notificacion: Notificacion) -> bool:
        """
        Envía notificación push
        
        TODO: Implementar integración con servicio de push notifications
        (Firebase Cloud Messaging, OneSignal, etc.)
        """
        try:
            # Aquí iría la lógica para enviar push notification
            # Por ahora solo registramos en el historial
            
            HistorialNotificacion.objects.create(
                notificacion=notificacion,
                metodo_envio='PUSH',
                estado='ENVIADO'  # Cambiar a 'FALLIDO' si hay error
            )
            
            notificacion.enviada_push = True
            notificacion.save(update_fields=['enviada_push'])
            
            logger.info(f"Push notification enviada para notificación {notificacion.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando push notification: {str(e)}")
            
            HistorialNotificacion.objects.create(
                notificacion=notificacion,
                metodo_envio='PUSH',
                estado='FALLIDO',
                mensaje_error=str(e)
            )
            
            return False
    
    @staticmethod
    def _enviar_email(notificacion: Notificacion) -> bool:
        """
        Envía notificación por email
        
        TODO: Implementar envío de emails con plantillas HTML
        """
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            # Verificar que el usuario tenga email
            if not notificacion.usuario.email:
                logger.warning(f"Usuario {notificacion.usuario.id} no tiene email configurado")
                return False
            
            # Enviar email
            send_mail(
                subject=f"[SENA] {notificacion.titulo}",
                message=notificacion.mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notificacion.usuario.email],
                fail_silently=False
            )
            
            HistorialNotificacion.objects.create(
                notificacion=notificacion,
                metodo_envio='EMAIL',
                estado='ENVIADO'
            )
            
            notificacion.enviada_email = True
            notificacion.save(update_fields=['enviada_email'])
            
            logger.info(f"Email enviado para notificación {notificacion.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            
            HistorialNotificacion.objects.create(
                notificacion=notificacion,
                metodo_envio='EMAIL',
                estado='FALLIDO',
                mensaje_error=str(e)
            )
            
            return False
    
    @staticmethod
    def notificar_nueva_actividad(actividad, usuarios=None):
        """
        Notifica sobre una nueva actividad creada
        """
        if usuarios is None:
            # Obtener todos los aprendices del grupo de la actividad
            from apps.usuarios.models import Usuario
            usuarios = Usuario.objects.filter(
                rol__nombre='APRENDIZ',
                # Aquí agregar filtro por grupo/clase según tu modelo
            )
        
        titulo = f"Nueva actividad: {actividad.titulo}"
        mensaje = f"Se ha creado una nueva actividad '{actividad.titulo}' con fecha de entrega {actividad.fecha_entrega}."
        
        return NotificacionService.enviar_notificacion_masiva(
            usuarios=usuarios,
            tipo_notificacion='NUEVA_ACTIVIDAD',
            titulo=titulo,
            mensaje=mensaje,
            objeto_relacionado=actividad
        )
    
    @staticmethod
    def notificar_actividad_valorada(actividad, usuario_aprendiz, calificacion):
        """
        Notifica cuando una actividad ha sido valorada
        """
        titulo = f"Actividad valorada: {actividad.titulo}"
        mensaje = f"Tu actividad '{actividad.titulo}' ha sido valorada con: {calificacion}."
        
        return NotificacionService.enviar_notificacion(
            usuario=usuario_aprendiz,
            tipo_notificacion='ACTIVIDAD_VALORADA',
            titulo=titulo,
            mensaje=mensaje,
            objeto_relacionado=actividad,
            datos_extra={'calificacion': str(calificacion)}
        )
    
    @staticmethod
    def notificar_citacion_comite(citacion):
        """
        Notifica sobre una citación a comité
        """
        titulo = "Citación a Comité"
        mensaje = f"Has sido citado a comité. Motivo: {citacion.motivo}. Fecha: {citacion.fecha_citacion}."
        
        return NotificacionService.enviar_notificacion(
            usuario=citacion.aprendiz,
            tipo_notificacion='CITACION_COMITE',
            titulo=titulo,
            mensaje=mensaje,
            objeto_relacionado=citacion,
            forzar_envio=True  # Las citaciones siempre se envían
        )
    
    @staticmethod
    def notificar_alta_inasistencia(usuario_aprendiz, porcentaje_inasistencia):
        """
        Notifica sobre alta inasistencia
        """
        titulo = "Alerta: Alta Inasistencia"
        mensaje = f"Tu porcentaje de inasistencia es del {porcentaje_inasistencia}%. Te recomendamos mejorar tu asistencia."
        
        return NotificacionService.enviar_notificacion(
            usuario=usuario_aprendiz,
            tipo_notificacion='ALTA_INASISTENCIA',
            titulo=titulo,
            mensaje=mensaje,
            datos_extra={'porcentaje': porcentaje_inasistencia}
        )
    
    @staticmethod
    def notificar_bajo_rendimiento(usuario_aprendiz, promedio):
        """
        Notifica sobre bajo rendimiento académico
        """
        titulo = "Alerta: Bajo Rendimiento"
        mensaje = f"Tu promedio actual es {promedio}. Te sugerimos solicitar apoyo académico."
        
        return NotificacionService.enviar_notificacion(
            usuario=usuario_aprendiz,
            tipo_notificacion='BAJO_RENDIMIENTO',
            titulo=titulo,
            mensaje=mensaje,
            datos_extra={'promedio': str(promedio)}
        )
    
    @staticmethod
    def limpiar_notificaciones_antiguas(dias=30):
        """
        Elimina notificaciones leídas más antiguas que X días
        """
        from datetime import timedelta
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        notificaciones_eliminadas = Notificacion.objects.filter(
            leida=True,
            fecha_lectura__lt=fecha_limite
        ).delete()
        
        logger.info(f"Eliminadas {notificaciones_eliminadas[0]} notificaciones antiguas")
        return notificaciones_eliminadas[0]