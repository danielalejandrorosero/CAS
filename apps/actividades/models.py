from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.usuarios.models import Usuario
from apps.asistencia.models import Ficha, ResultadoAprendizaje
import uuid
import os




def upload_archivo_actividad(instance, filename):
    """Funcion para definir la ruta de subida de archivos de actividades."""

    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('actividades', str(instance.actividad.id), filename)



class TipoActividad(models.Model):
    """TIpos de actividiad que se pueden crear en el sistema."""

    TIPOS_CHOICES = [
        ('CONSULTA', 'Consulta'),
        ('TRABAJO', 'Trabajo'),
        ('PROYECTO', 'Proyecto'),
        ('VALORACION', 'Valoración'),
        ('TALLER', 'Taller'),
        ('EXPOSICION', 'Exposición'),
        ('PRACTICA', 'Práctica'),
        ('EXAMEN', 'Examen'),
        ('QUIZ', 'Quiz'),
        ('INVESTIGACION', 'Investigación'),
    ]


    nombre = models.CharField(max_length=50, choices=TIPOS_CHOICES, unique=True, verbose_name="Tipo de Actividad")

    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        db_table = 'tipo_actividad'
        verbose_name = "Tipo de Actividad"
        verbose_name_plural = "Tipos de Actividades"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return self.nombre



class Actividad(models.Model):


    MODALIDAD_CHOICES = [
        ('INDIVIDUAL', 'Individual'),
        ('GRUPAL', 'Grupal'),
        ('MIXTA', 'Mixta'),
    ]

    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('PUBLICADA', 'Publicada'),
        ('EN_PROGRESO', 'En Progreso'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]


    titulo = models.CharField(max_length=255, verbose_name="Título")

    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    tipo_actividad = models.ForeignKey(TipoActividad, on_delete=models.CASCADE, related_name='actividades')


    instructor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='actividades',
        limit_choices_to={'rol__nombre': 'INSTRUCTOR'}
    )

    resultado_aprendizaje = models.ForeignKey(
        ResultadoAprendizaje,
        on_delete=models.CASCADE,
        related_name='actividades'
    )

    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='actividades')


    #fechas y tiempos

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_entrega = models.DateTimeField()
    fecha_limite = models.DateTimeField(null=True, blank=True, help_text="Fecha límite para entrega tardía")


    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES, default='INDIVIDUAL')
    numero_integrantes_grupo = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Solo aplica para actividades grupales"
    )


    permite_entrega_tardia = models.BooleanField(default=True)
    penalizacion_tardanza = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de penalización por entrega tardía"
    )


    #valoracion

    puntaje_maximo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        validators=[MinValueValidator(0.1), MaxValueValidator(100)]
    )
    criterios_evaluacion = models.TextField(
        blank=True,
        null=True,
        help_text="Criterios de evaluación y rúbricas"
    )


    # estado y visibilidad

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    es_obligatoria = models.BooleanField(default=True)
    visible_para_aprendices = models.BooleanField(default=True)
    requiere_archivo = models.BooleanField(default=False)

    # Observaciones
    observaciones_instructor = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        db_table = 'actividades'
        indexes = [
            models.Index(fields=['instructor', 'ficha']),
            models.Index(fields=['fecha_entrega']),
            models.Index(fields=['estado']),
            models.Index(fields=['resultado_aprendizaje']),
            models.Index(fields=['visible_para_aprendices']),
        ]
        ordering = ['-fecha_creacion']

    def clean(self):
        from django.core.exceptions import ValidationError

        # Validar fechas
        if self.fecha_entrega <= self.fecha_inicio:
            raise ValidationError('La fecha de entrega debe ser posterior a la fecha de inicio.')

        if self.fecha_limite and self.fecha_limite <= self.fecha_entrega:
            raise ValidationError('La fecha límite debe ser posterior a la fecha de entrega.')

        # Validar modalidad grupal
        if self.modalidad == 'GRUPAL' and self.numero_integrantes_grupo <= 1:
            raise ValidationError('Para actividades grupales debe especificar más de 1 integrante.')

    def save(self, *args, **kwargs):
        self.clean()

        # Establecer fecha de publicación si cambia a publicada
        if self.estado == 'PUBLICADA' and not self.fecha_publicacion:
            self.fecha_publicacion = timezone.now()

        super().save(*args, **kwargs)

    @property
    def esta_vencida(self):
        """Verifica si la actividad está vencida"""
        fecha_limite = self.fecha_limite if self.fecha_limite else self.fecha_entrega
        return timezone.now() > fecha_limite

    @property
    def acepta_entregas(self):
        """Verifica si aún acepta entregas"""
        if not self.permite_entrega_tardia:
            return timezone.now() <= self.fecha_entrega

        fecha_limite = self.fecha_limite if self.fecha_limite else self.fecha_entrega
        return timezone.now() <= fecha_limite

    @property
    def total_entregas(self):
        """Cuenta el total de entregas realizadas"""
        return self.entregas.count()

    @property
    def entregas_pendientes(self):
        """Cuenta las entregas pendientes"""
        total_aprendices = self.get_aprendices_asignados().count()
        return total_aprendices - self.total_entregas

    def get_aprendices_asignados(self):
        """Obtiene los aprendices asignados a esta actividad"""
        if hasattr(self, '_aprendices_asignados'):
            # Si hay una asignación específica
            return self._aprendices_asignados
        else:
            # Por defecto, todos los aprendices activos de la ficha
            return self.ficha.get_aprendices_activos()

    def __str__(self):
        return f"{self.titulo} - {self.ficha.numero} - {self.resultado_aprendizaje.nombre}"

    def __repr__(self):
        return f"<Actividad: {self.titulo} - {self.ficha.numero} - {self.resultado_aprendizaje.nombre}>"


class AsignacionActividad(models.Model):
    """Modelo para asignar actividades a aprendices específicos."""

    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)

    aprendiz = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='asignaciones_actividades',
        limit_choices_to={'rol__nombre': 'APRENDIZ'}
    )

    es_obligatoria = models.BooleanField(default=True, verbose_name="Es Obligatoria")
    fecha_asignacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Asignación")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Asignación de Actividad"
        verbose_name_plural = "Asignaciones de Actividades"
        db_table = 'asignaciones_actividad'
        unique_together = ['actividad', 'aprendiz']
        indexes = [
            models.Index(fields=['actividad', 'aprendiz']),
            models.Index(fields=['fecha_asignacion']),
        ]

    def __str__(self):
        return f"{self.actividad.titulo} - {self.aprendiz.nombres} {self.aprendiz.apellidos}"



class ArchivoActividad(models.Model):

    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='archivos')

    nombre = models.CharField(max_length=255, verbose_name="Nombre del Archivo")

    archivo = models.FileField(upload_to=upload_archivo_actividad, verbose_name="Archivo")

    descripcion = models.TextField(blank=True, null=True)
    es_obligatorio = models.BooleanField(default=False, help_text="Si es obligatorio para realizar la actividad")
    tamaño_archivo = models.PositiveIntegerField(default=0, help_text="Tamaño en bytes")
    tipo_archivo = models.CharField(max_length=100, blank=True)
    subido_por = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='archivos_subidos')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Archivo de Actividad"
        verbose_name_plural = "Archivos de Actividades"
        db_table = 'archivos_actividad'
        indexes = [
            models.Index(fields=['actividad']),
            models.Index(fields=['es_obligatorio']),
        ]

    def save(self, *args, **kwargs):
        if self.archivo:
            self.tamaño_archivo = self.archivo.size
            self.tipo_archivo = self.archivo.name.split('.')[-1] if '.' in self.archivo.name else ''
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {self.actividad.titulo}"



def upload_entrega_actividad(instance, filename):
    """Función para definir la ruta de subida de entregas"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('entregas', str(instance.actividad.id), str(instance.aprendiz.id), filename)


class EntregaActividad(models.Model):
    """Modelo para las entregas de actividades por parte de los aprendices"""

    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('ENTREGADA', 'Entregada'),
        ('REVISADA', 'Revisada'),
        ('CALIFICADA', 'Calificada'),
        ('DEVUELTA', 'Devuelta para Corrección'),
    ]

    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='entregas')
    aprendiz = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='entregas_realizadas',
        limit_choices_to={'rol__nombre': 'APRENDIZ'}
    )

    # Contenido de la entrega
    contenido = models.TextField(blank=True, null=True, help_text="Texto de la entrega")

    # Fechas importantes
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    fecha_ultima_modificacion = models.DateTimeField(auto_now=True)

    # Estado
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    es_entrega_tardia = models.BooleanField(default=False)

    # Observaciones
    observaciones_aprendiz = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Entrega de Actividad"
        verbose_name_plural = "Entregas de Actividades"
        db_table = 'entregas_actividad'
        unique_together = ['actividad', 'aprendiz']
        indexes = [
            models.Index(fields=['actividad', 'aprendiz']),
            models.Index(fields=['fecha_entrega']),
            models.Index(fields=['estado']),
            models.Index(fields=['es_entrega_tardia']),
        ]
        ordering = ['-fecha_entrega']

    def save(self, *args, **kwargs):
        # Verificar si es entrega tardía
        if self.estado == 'ENTREGADA':
            self.es_entrega_tardia = timezone.now() > self.actividad.fecha_entrega

        super().save(*args, **kwargs)

    @property
    def puede_modificar(self):
        """Verifica si el aprendiz puede modificar la entrega"""
        return self.estado in ['BORRADOR', 'DEVUELTA']

    def __str__(self):
        return f"{self.actividad.titulo} - {self.aprendiz.nombres} {self.aprendiz.apellidos}"


class ArchivoEntrega(models.Model):
    """Modelo para archivos adjuntos en las entregas"""

    entrega = models.ForeignKey(EntregaActividad, on_delete=models.CASCADE, related_name='archivos')
    nombre = models.CharField(max_length=200)
    archivo = models.FileField(upload_to=upload_entrega_actividad)
    tamaño_archivo = models.PositiveIntegerField(default=0)
    tipo_archivo = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Archivo de Entrega"
        verbose_name_plural = "Archivos de Entregas"
        db_table = 'archivos_entrega'
        indexes = [
            models.Index(fields=['entrega']),
        ]

    def save(self, *args, **kwargs):
        if self.archivo:
            self.tamaño_archivo = self.archivo.size
            self.tipo_archivo = self.archivo.name.split('.')[-1] if '.' in self.archivo.name else ''
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {self.entrega}"


class CalificacionActividad(models.Model):
    """Modelo para las calificaciones de las actividades"""

    entrega = models.OneToOneField(
        EntregaActividad,
        on_delete=models.CASCADE,
        related_name='calificacion'
    )
    instructor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='calificaciones_dadas',
        limit_choices_to={'rol__nombre': 'INSTRUCTOR'}
    )

    # Calificación
    puntaje_obtenido = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Retroalimentación
    comentarios = models.TextField(blank=True, null=True)
    fortalezas = models.TextField(blank=True, null=True)
    aspectos_mejorar = models.TextField(blank=True, null=True)

    # Fechas
    fecha_calificacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    # Estado
    requiere_correccion = models.BooleanField(default=False)
    aprobada = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Calificación de Actividad"
        verbose_name_plural = "Calificaciones de Actividades"
        db_table = 'calificaciones_actividad'
        indexes = [
            models.Index(fields=['instructor']),
            models.Index(fields=['fecha_calificacion']),
            models.Index(fields=['aprobada']),
        ]

    # python
    def clean(self):
        super().clean()
        if (
                self.puntaje_obtenido is not None and
                self.entrega and
                self.entrega.actividad and
                self.entrega.actividad.puntaje_maximo is not None
        ):
            if self.puntaje_obtenido > self.entrega.actividad.puntaje_maximo:
                raise ValidationError("El puntaje obtenido no puede ser mayor al puntaje máximo de la actividad.")

    def save(self, *args, **kwargs):
        self.clean()

        # Calcular porcentaje
        if self.entrega.actividad.puntaje_maximo > 0:
            self.porcentaje = (self.puntaje_obtenido / self.entrega.actividad.puntaje_maximo) * 100

        # Aplicar penalización por tardanza si corresponde
        if self.entrega.es_entrega_tardia and self.entrega.actividad.penalizacion_tardanza > 0:
            penalizacion = (self.porcentaje * self.entrega.actividad.penalizacion_tardanza) / 100
            self.porcentaje = max(0, self.porcentaje - penalizacion)
            self.puntaje_obtenido = (self.porcentaje * self.entrega.actividad.puntaje_maximo) / 100

        # Determinar si está aprobada (generalmente 60% o más)
        self.aprobada = self.porcentaje >= 60.0

        super().save(*args, **kwargs)

        # Actualizar estado de la entrega
        self.entrega.estado = 'DEVUELTA' if self.requiere_correccion else 'CALIFICADA'
        self.entrega.save(update_fields=['estado'])

    @property
    def calificacion_letra(self):
        """Convierte el porcentaje a calificación letra"""
        if self.porcentaje >= 90:
            return 'A'
        elif self.porcentaje >= 80:
            return 'B'
        elif self.porcentaje >= 70:
            return 'C'
        elif self.porcentaje >= 60:
            return 'D'
        else:
            return 'F'

    def __str__(self):
        return f"{self.entrega} - {self.puntaje_obtenido}/{self.entrega.actividad.puntaje_maximo}"