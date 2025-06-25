from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from apps.usuarios.models import Usuario


class TipoNotificacion(models.Model):
    """Tipos de notificaciones disponibles en el sistema"""
    TIPOS_CHOICES = [
        ('NUEVA_ACTIVIDAD', 'Nueva Actividad'),
        ('ACTIVIDAD_VALORADA', 'Actividad Valorada'),
        ('CITACION_COMITE', 'Citación a Comité'),
        ('ALTA_INASISTENCIA', 'Alta Inasistencia'),
        ('BAJO_RENDIMIENTO', 'Bajo Rendimiento'),
        ('RECORDATORIO', 'Recordatorio'),
        ('SISTEMA', 'Sistema'),
    ]
    
    nombre = models.CharField(max_length=50, choices=TIPOS_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Tipo de Notificación'
        verbose_name_plural = 'Tipos de Notificaciones'
    
    def __str__(self):
        return self.get_nombre_display()


class Notificacion(models.Model):
    """Modelo principal para las notificaciones del sistema"""
    
    # Usuario que recibe la notificación
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='notificaciones'
    )
    
    # Tipo de notificación
    tipo = models.ForeignKey(
        TipoNotificacion, 
        on_delete=models.CASCADE
    )
    
    # Título y contenido de la notificación
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    
    # Referencia genérica al objeto relacionado (actividad, citación, etc.)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    objeto_relacionado = GenericForeignKey('content_type', 'object_id')
    
    # Estado de la notificación
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    
    # Metadatos adicionales
    datos_extra = models.JSONField(default=dict, blank=True)
    
    # Configuración de envío
    enviada_push = models.BooleanField(default=False)
    enviada_email = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', 'leida']),
            models.Index(fields=['tipo', 'fecha_creacion']),
        ]
    
    def __str__(self):
        return f'{self.titulo} - {self.usuario.get_full_name()}'
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if not self.leida:
            from django.utils import timezone
            self.leida = True
            self.fecha_lectura = timezone.now()
            self.save(update_fields=['leida', 'fecha_lectura'])


class ConfiguracionNotificacion(models.Model):
    """Configuración de notificaciones por usuario"""
    
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='config_notificaciones'
    )
    
    # Configuraciones generales
    notificaciones_push = models.BooleanField(default=True)
    notificaciones_email = models.BooleanField(default=True)
    
    # Configuraciones por tipo
    nueva_actividad = models.BooleanField(default=True)
    actividad_valorada = models.BooleanField(default=True)
    citacion_comite = models.BooleanField(default=True)
    alta_inasistencia = models.BooleanField(default=True)
    bajo_rendimiento = models.BooleanField(default=True)
    recordatorios = models.BooleanField(default=True)
    
    # Horarios de notificación
    hora_inicio = models.TimeField(default='07:00')
    hora_fin = models.TimeField(default='22:00')
    
    # Días de la semana (JSON con días activos)
    dias_activos = models.JSONField(
        default=list,
        help_text='Lista de días de la semana activos (0=Lunes, 6=Domingo)'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Notificación'
        verbose_name_plural = 'Configuraciones de Notificaciones'
    
    def __str__(self):
        return f'Config. Notif. - {self.usuario.get_full_name()}'
    
    def puede_recibir_notificacion(self, tipo_notificacion):
        """Verifica si el usuario puede recibir un tipo específico de notificación"""
        from django.utils import timezone
        
        # Verificar si las notificaciones están habilitadas
        if not self.notificaciones_push and not self.notificaciones_email:
            return False
        
        # Verificar tipo específico
        tipo_map = {
            'NUEVA_ACTIVIDAD': self.nueva_actividad,
            'ACTIVIDAD_VALORADA': self.actividad_valorada,
            'CITACION_COMITE': self.citacion_comite,
            'ALTA_INASISTENCIA': self.alta_inasistencia,
            'BAJO_RENDIMIENTO': self.bajo_rendimiento,
            'RECORDATORIO': self.recordatorios,
        }
        
        if tipo_notificacion in tipo_map and not tipo_map[tipo_notificacion]:
            return False
        
        # Verificar horario
        now = timezone.now().time()
        if not (self.hora_inicio <= now <= self.hora_fin):
            return False
        
        # Verificar día de la semana
        if self.dias_activos:
            dia_actual = timezone.now().weekday()
            if dia_actual not in self.dias_activos:
                return False
        
        return True


class HistorialNotificacion(models.Model):
    """Historial de notificaciones enviadas para auditoría"""
    
    notificacion = models.ForeignKey(
        Notificacion,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    
    metodo_envio = models.CharField(
        max_length=20,
        choices=[
            ('PUSH', 'Notificación Push'),
            ('EMAIL', 'Correo Electrónico'),
            ('SMS', 'Mensaje de Texto'),
        ]
    )
    
    estado = models.CharField(
        max_length=20,
        choices=[
            ('ENVIADO', 'Enviado'),
            ('FALLIDO', 'Fallido'),
            ('PENDIENTE', 'Pendiente'),
        ],
        default='PENDIENTE'
    )
    
    fecha_envio = models.DateTimeField(auto_now_add=True)
    mensaje_error = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Historial de Notificación'
        verbose_name_plural = 'Historial de Notificaciones'
        ordering = ['-fecha_envio']
    
    def __str__(self):
        return f'{self.notificacion.titulo} - {self.metodo_envio} - {self.estado}'