from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from apps.usuarios.models import Usuario
from apps.asistencia.models import Ficha, ResultadoAprendizaje
import uuid

class CitacionComite(models.Model):
    """Modelo para gestionar las citaciones a comité de aprendices"""
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('NOTIFICADA', 'Notificada'),
        ('REALIZADA', 'Realizada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    MOTIVO_CHOICES = [
        ('BAJO_RENDIMIENTO', 'Bajo Rendimiento Académico'),
        ('INASISTENCIA', 'Inasistencia Recurrente'),
        ('COMPORTAMIENTO', 'Problemas de Comportamiento'),
        ('INCUMPLIMIENTO', 'Incumplimiento de Normas'),
        ('SOLICITUD_APRENDIZ', 'Solicitud del Aprendiz'),
        ('OTRO', 'Otro Motivo'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]
    
    # Identificación única
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_citacion = models.CharField(max_length=20, unique=True, editable=False)
    
    # Relaciones principales
    aprendiz = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='citaciones_recibidas',
        limit_choices_to={'rol__nombre': 'APRENDIZ'}
    )
    instructor_citante = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='citaciones_realizadas',
        limit_choices_to={'rol__nombre': 'INSTRUCTOR'}
    )
    ficha = models.ForeignKey(
        Ficha, 
        on_delete=models.CASCADE, 
        related_name='citaciones'
    )
    resultado_aprendizaje = models.ForeignKey(
        ResultadoAprendizaje, 
        on_delete=models.CASCADE, 
        related_name='citaciones',
        null=True, 
        blank=True
    )
    
    # Información de la citación
    motivo = models.CharField(max_length=30, choices=MOTIVO_CHOICES)
    motivo_detallado = models.TextField(
        help_text="Descripción detallada del motivo de la citación"
    )
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIA')
    
    # Fechas importantes
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_citacion = models.DateTimeField(
        help_text="Fecha y hora programada para la citación"
    )
    fecha_notificacion = models.DateTimeField(null=True, blank=True)
    fecha_realizacion = models.DateTimeField(null=True, blank=True)
    
    # Información adicional
    observaciones_instructor = models.TextField(
        blank=True, 
        null=True,
        help_text="Observaciones adicionales del instructor"
    )
    observaciones_comite = models.TextField(
        blank=True, 
        null=True,
        help_text="Observaciones del comité después de la citación"
    )
    
    # Seguimiento
    requiere_seguimiento = models.BooleanField(
        default=False,
        help_text="Indica si la citación requiere seguimiento posterior"
    )
    fecha_seguimiento = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha programada para el seguimiento"
    )
    
    # Metadatos
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Citación a Comité"
        verbose_name_plural = "Citaciones a Comité"
        db_table = 'citaciones_comite'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['aprendiz', 'estado']),
            models.Index(fields=['instructor_citante']),
            models.Index(fields=['fecha_citacion']),
            models.Index(fields=['estado']),
            models.Index(fields=['motivo']),
            models.Index(fields=['prioridad']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.numero_citacion:
            # Generar número de citación único
            year = timezone.now().year
            count = CitacionComite.objects.filter(
                fecha_creacion__year=year
            ).count() + 1
            self.numero_citacion = f"CIT-{year}-{count:04d}"
        
        # Actualizar fecha de notificación si cambia a NOTIFICADA
        if self.estado == 'NOTIFICADA' and not self.fecha_notificacion:
            self.fecha_notificacion = timezone.now()
        
        # Actualizar fecha de realización si cambia a REALIZADA
        if self.estado == 'REALIZADA' and not self.fecha_realizacion:
            self.fecha_realizacion = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_citacion} - {self.aprendiz.get_full_name()} - {self.get_motivo_display()}"
    
    @property
    def dias_hasta_citacion(self):
        """Calcula los días restantes hasta la citación"""
        if self.fecha_citacion:
            delta = self.fecha_citacion.date() - timezone.now().date()
            return delta.days
        return None
    
    @property
    def esta_vencida(self):
        """Verifica si la citación está vencida"""
        if self.fecha_citacion and self.estado in ['PENDIENTE', 'NOTIFICADA']:
            return timezone.now() > self.fecha_citacion
        return False
    
    def marcar_como_notificada(self):
        """Marca la citación como notificada"""
        self.estado = 'NOTIFICADA'
        self.fecha_notificacion = timezone.now()
        self.save()
    
    def marcar_como_realizada(self, observaciones_comite=None):
        """Marca la citación como realizada"""
        self.estado = 'REALIZADA'
        self.fecha_realizacion = timezone.now()
        if observaciones_comite:
            self.observaciones_comite = observaciones_comite
        self.save()


class ArchivoAdjuntoCitacion(models.Model):
    """Modelo para archivos adjuntos a las citaciones"""
    
    citacion = models.ForeignKey(
        CitacionComite, 
        on_delete=models.CASCADE, 
        related_name='archivos_adjuntos'
    )
    archivo = models.FileField(
        upload_to='citaciones/adjuntos/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
            )
        ]
    )
    nombre_original = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    subido_por = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='archivos_citaciones_subidos'
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Archivo Adjunto de Citación"
        verbose_name_plural = "Archivos Adjuntos de Citaciones"
        db_table = 'archivos_adjuntos_citaciones'
    
    def __str__(self):
        return f"{self.nombre_original} - {self.citacion.numero_citacion}"


class SeguimientoCitacion(models.Model):
    """Modelo para el seguimiento posterior a las citaciones"""
    
    TIPO_SEGUIMIENTO_CHOICES = [
        ('ACADEMICO', 'Seguimiento Académico'),
        ('COMPORTAMENTAL', 'Seguimiento Comportamental'),
        ('ASISTENCIA', 'Seguimiento de Asistencia'),
        ('INTEGRAL', 'Seguimiento Integral'),
    ]
    
    RESULTADO_CHOICES = [
        ('MEJORA', 'Mejora Evidenciada'),
        ('ESTABLE', 'Situación Estable'),
        ('DETERIORO', 'Deterioro de la Situación'),
        ('SIN_CAMBIOS', 'Sin Cambios Significativos'),
    ]
    
    citacion = models.ForeignKey(
        CitacionComite, 
        on_delete=models.CASCADE, 
        related_name='seguimientos'
    )
    instructor_seguimiento = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='seguimientos_realizados',
        limit_choices_to={'rol__nombre': 'INSTRUCTOR'},
        null=True,
        blank=True
    )
    
    tipo_seguimiento = models.CharField(max_length=20, choices=TIPO_SEGUIMIENTO_CHOICES)
    fecha_seguimiento = models.DateField()
    observaciones = models.TextField()
    resultado = models.CharField(max_length=15, choices=RESULTADO_CHOICES)
    
    # Acciones tomadas
    acciones_tomadas = models.TextField(
        blank=True, 
        null=True,
        help_text="Acciones específicas tomadas durante el seguimiento"
    )
    
    # Próximo seguimiento
    requiere_nuevo_seguimiento = models.BooleanField(default=False)
    fecha_proximo_seguimiento = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Seguimiento de Citación"
        verbose_name_plural = "Seguimientos de Citaciones"
        db_table = 'seguimientos_citaciones'
        ordering = ['-fecha_seguimiento']
    
    def __str__(self):
        return f"Seguimiento {self.citacion.numero_citacion} - {self.fecha_seguimiento}"
