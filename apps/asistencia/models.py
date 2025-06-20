from django.core.exceptions import ValidationError
from django.db import models

from django.utils import timezone

from django.core.validators import MinValueValidator, MaxValueValidator

from apps.usuarios.models import Usuario



class Programa(models.Model):
    """Programas de formación del SENA"""

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    tipo_formacion = models.CharField(max_length=50, choices=[
        ('TECNICO', 'Técnico'),
        ('TECNOLOGO', 'Tecnólogo'),
        ('ESPECIALIZACION', 'Especialización Técnica'),
        ('CURSO_CORTO', 'Curso Corto'),
        ('COMPLEMENTARIA', 'Formación Complementaria'),
    ])









    duracion_horas = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Programa de Formación"
        verbose_name_plural = "Programas de Formación"
        db_table = 'programas'
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Ficha(models.Model):
    """Modelo para representar una ficha del SENA"""

    numero = models.CharField(max_length=20, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin_lectiva = models.DateField()
    municipio_departamento = models.CharField(max_length=100)
    centro_formacion = models.CharField(max_length=100)
    cupo_aprendices = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(1000)])
    cupo_instructores = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    lugar_realizacion = models.CharField(max_length=100)
    modalidad = models.CharField(max_length=20, choices=[
        ('PRESENCIAL', 'Presencial'),
        ('VIRTUAL', 'Virtual'),
        ('MIXTA', 'Mixta'),
    ])
    jornada = models.CharField(max_length=20, choices=[
        ('DIURNA', 'Diurna'),
        ('NOCTURNA', 'Nocturna'),
        ('MIXTA', 'Mixta'),
        ('FINES_SEMANA', 'Fines de Semana'),
    ])
    estado = models.CharField(max_length=20, choices=[
        ('LECTURA', 'En Lectura'),
        ('EJECUCION', 'En Ejecución'),
        ('TERMINADA', 'Terminada'),
        ('CANCELADA', 'Cancelada'),
    ], default='LECTURA')

    activo = models.BooleanField(default=True)
    programa = models.ForeignKey(Programa, on_delete=models.CASCADE, related_name='fichas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ficha"
        verbose_name_plural = "Fichas"
        db_table = 'fichas'
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_inicio']),
            models.Index(fields=['activo']),
        ]

    def clean(self):
        """Validaciones personalizadas"""
        if self.fecha_fin_lectiva <= self.fecha_inicio:
            raise ValidationError('La fecha de fin lectiva debe ser posterior a la fecha de inicio.')

    def save(self, *args, **kwargs):
        """Lógica personalizada al guardar"""
        # Si la ficha está terminada, se desactiva automáticamente
        if self.estado == 'TERMINADA':
            self.activo = False

        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero} - {self.municipio_departamento}"

    @property
    def duracion_dias(self):
        """Calcula la duración en días de la ficha"""
        return (self.fecha_fin_lectiva - self.fecha_inicio).days

    def get_aprendices_activos(self):
        """Obtiene todos los aprendices activos matriculados en esta ficha"""
        return Usuario.objects.filter(
            matriculas__ficha=self,
            matriculas__estado='ACTIVO',
            rol__nombre='APRENDIZ'
        )

    def get_instructores_asignados(self):
        """Obtiene todos los instructores asignados a esta ficha"""
        return Usuario.objects.filter(
            asignaciones__ficha=self,
            asignaciones__activo=True,
            rol__nombre='INSTRUCTOR'
        ).distinct()


class ResultadoAprendizaje(models.Model):
    """Modelo para representar un resultado de aprendizaje del SENA"""

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    programa = models.ForeignKey(Programa, on_delete=models.CASCADE, related_name='resultados_aprendizaje')
    horas_asignadas = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(1000)])
    trimestre = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)], default=1)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resultado de Aprendizaje"
        verbose_name_plural = "Resultados de Aprendizaje"
        db_table = 'resultados_aprendizaje'
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['programa']),
            models.Index(fields=['trimestre']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.programa.nombre})"


# ================================
# MODELOS DE MATRÍCULA Y ASIGNACIONES
# ================================

class Matricula(models.Model):
    """Modelo para representar la matrícula de un aprendiz a una ficha"""

    aprendiz = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='matriculas',
        limit_choices_to={'rol__nombre': 'APRENDIZ'}
    )
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='matriculas')
    fecha_matricula = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=[
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
        ('RETIRADO', 'Retirado'),
        ('APLAZADO', 'Aplazado'),
        ('CANCELADO', 'Cancelado'),
    ], default='ACTIVO')

    foto_perfil = models.ImageField(
        upload_to='fotos_perfil/',
        null=True,
        blank=True,
        help_text="Foto del aprendiz para identificación visual en asistencia"
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"
        db_table = 'matriculas'
        unique_together = ['aprendiz', 'ficha']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_matricula']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.aprendiz.nombres} {self.aprendiz.apellidos} - Ficha {self.ficha.numero}"


class AsignacionInstructor(models.Model):
    """Modelo para asignar instructores a fichas y resultados de aprendizaje"""

    instructor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='asignaciones',
        limit_choices_to={'rol__nombre': 'INSTRUCTOR'}
    )
    resultado_aprendizaje = models.ForeignKey(
        ResultadoAprendizaje,
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='asignaciones')
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asignación de Instructor"
        verbose_name_plural = "Asignaciones de Instructores"
        db_table = 'asignaciones_instructor'
        unique_together = ['instructor', 'resultado_aprendizaje', 'ficha']
        indexes = [
            models.Index(fields=['instructor', 'ficha']),
            models.Index(fields=['fecha_inicio']),
            models.Index(fields=['activo']),
        ]

    def clean(self):
        """Validaciones personalizadas"""
        if self.fecha_fin and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.instructor.nombres} - {self.resultado_aprendizaje.nombre} - Ficha {self.ficha.numero}"


# ================================
# MODELOS DE ASISTENCIA
# ================================

class LlamadoAsistencia(models.Model):
    """Modelo para registrar los llamados de asistencia"""

    instructor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='llamados_asistencia',
        limit_choices_to={'rol__nombre': 'INSTRUCTOR'}
    )
    resultado_aprendizaje = models.ForeignKey(
        ResultadoAprendizaje,
        on_delete=models.CASCADE,
        related_name='llamados_asistencia'
    )
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='llamados_asistencia')
    fecha_hora_llamado = models.DateTimeField(auto_now_add=True)
    fecha_clase = models.DateField(default=timezone.now)
    observaciones_generales = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones generales sobre la clase o el llamado de asistencia"
    )
    duracion_clase = models.PositiveIntegerField(
        default=120,
        validators=[MinValueValidator(30), MaxValueValidator(480)],
        help_text="Duración de la clase en minutos"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Llamado de Asistencia"
        verbose_name_plural = "Llamados de Asistencia"
        db_table = 'llamados_asistencia'
        unique_together = ['instructor', 'resultado_aprendizaje', 'ficha', 'fecha_clase']
        indexes = [
            models.Index(fields=['fecha_clase']),
            models.Index(fields=['instructor', 'fecha_clase']),
            models.Index(fields=['ficha', 'fecha_clase']),
        ]

    def clean(self):
        """Validaciones personalizadas"""
        # No se puede registrar asistencia para fechas futuras
        if self.fecha_clase > timezone.now().date():
            raise ValidationError('No se puede registrar asistencia para fechas futuras.')

        # Verificar que el instructor esté asignado a ese resultado y ficha
        if not AsignacionInstructor.objects.filter(
                instructor=self.instructor,
                resultado_aprendizaje=self.resultado_aprendizaje,
                ficha=self.ficha,
                activo=True
        ).exists():
            raise ValidationError('El instructor no está asignado a este resultado de aprendizaje en esta ficha.')

    def save(self, *args, **kwargs):
        """Lógica personalizada al guardar"""
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Si es un nuevo llamado, crear automáticamente los registros de asistencia
        if is_new:
            self.crear_registros_asistencia()

    def crear_registros_asistencia(self):
        """Crea automáticamente los registros de asistencia para todos los aprendices de la ficha"""
        aprendices = self.ficha.get_aprendices_activos()
        registros = []

        for aprendiz in aprendices:
            registros.append(RegistroAsistencia(
                llamado_asistencia=self,
                aprendiz=aprendiz,
                estado='SIN REGISTRAR'  # Estado por defecto actualizado
            ))

        RegistroAsistencia.objects.bulk_create(registros)

    def get_aprendices_ficha(self):
        """Obtiene todos los aprendices matriculados activos en la ficha"""
        return self.ficha.get_aprendices_activos()

    def __str__(self):
        return f"Llamado {self.fecha_clase} - {self.resultado_aprendizaje.nombre} - Ficha {self.ficha.numero}"


class RegistroAsistencia(models.Model):
    """Modelo para registrar la asistencia individual de cada aprendiz"""

    ESTADOS_ASISTENCIA = [
        ('PRESENTE', 'Presente'),
        ('AUSENTE', 'Ausente'),
        ('JUSTIFICADO', 'Justificado'),
        ('TARDE', 'Llegó Tarde'),
    ]

    llamado_asistencia = models.ForeignKey(
        LlamadoAsistencia,
        on_delete=models.CASCADE,
        related_name='registros'
    )
    aprendiz = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='asistencias',
        limit_choices_to={'rol__nombre': 'APRENDIZ'}
    )
    estado = models.CharField(max_length=15, choices=ESTADOS_ASISTENCIA, default='PRESENTE')
    hora_registro = models.TimeField(auto_now_add=True, help_text="Hora en que se registró la asistencia")
    minutos_tarde = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(180)],
        help_text="Minutos de retraso (solo si llegó tarde)"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Observaciones específicas sobre la asistencia del aprendiz"
    )
    se_retiro_antes = models.BooleanField(
        default=False,
        help_text="Indica si el aprendiz se retiró antes de finalizar la clase"
    )
    hora_retiro = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora de retiro (si se retiró antes)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"
        db_table = 'registros_asistencia'
        unique_together = ['llamado_asistencia', 'aprendiz']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['aprendiz', 'llamado_asistencia']),
        ]

    def clean(self):
        """Validaciones personalizadas"""
        # Si llegó tarde, debe especificar minutos
        if self.estado == 'TARDE' and self.minutos_tarde <= 0:
            raise ValidationError('Si el estudiante llegó tarde, debe especificar los minutos de retraso.')

        # Si no llegó tarde, minutos_tarde debe ser 0
        if self.estado != 'TARDE' and self.minutos_tarde > 0:
            raise ValidationError('Solo se pueden registrar minutos de retraso si el estado es "Llegó Tarde".')

        # Si se retiró antes, debe tener hora de retiro
        if self.se_retiro_antes and not self.hora_retiro:
            raise ValidationError('Si el estudiante se retiró antes, debe especificar la hora de retiro.')

        # Verificar que el aprendiz esté matriculado en la ficha del llamado
        if not Matricula.objects.filter(
                aprendiz=self.aprendiz,
                ficha=self.llamado_asistencia.ficha,
                estado='ACTIVO'
        ).exists():
            raise ValidationError('El aprendiz no está matriculado activamente en esta ficha.')

    def save(self, *args, **kwargs):
        """Lógica personalizada al guardar"""
        self.clean()
        super().save(*args, **kwargs)

        # Actualizar estadísticas después de guardar
        self.actualizar_estadisticas()

    def actualizar_estadisticas(self):
        """Actualiza las estadísticas de asistencia del aprendiz"""
        estadistica, created = EstadisticaAsistencia.objects.get_or_create(
            aprendiz=self.aprendiz,
            resultado_aprendizaje=self.llamado_asistencia.resultado_aprendizaje,
            ficha=self.llamado_asistencia.ficha
        )
        estadistica.actualizar_estadisticas()

    def __str__(self):
        return f"{self.aprendiz.nombres} {self.aprendiz.apellidos} - {self.estado} - {self.llamado_asistencia.fecha_clase}"


class EstadisticaAsistencia(models.Model):
    """Modelo para mantener estadísticas de asistencia por aprendiz y resultado de aprendizaje"""

    aprendiz = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='estadisticas_asistencia',
        limit_choices_to={'rol__nombre': 'APRENDIZ'}
    )
    resultado_aprendizaje = models.ForeignKey(
        ResultadoAprendizaje,
        on_delete=models.CASCADE,
        related_name='estadisticas_asistencia'
    )
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='estadisticas_asistencia')

    total_clases = models.PositiveIntegerField(default=0)
    clases_presentes = models.PositiveIntegerField(default=0)
    clases_ausentes = models.PositiveIntegerField(default=0)
    clases_justificadas = models.PositiveIntegerField(default=0)
    clases_tarde = models.PositiveIntegerField(default=0)

    porcentaje_asistencia = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Estadística de Asistencia"
        verbose_name_plural = "Estadísticas de Asistencia"
        db_table = 'estadisticas_asistencia'
        unique_together = ['aprendiz', 'resultado_aprendizaje', 'ficha']
        indexes = [
            models.Index(fields=['aprendiz', 'ficha']),
            models.Index(fields=['porcentaje_asistencia']),
        ]

    def calcular_porcentaje(self):
        """Calcula el porcentaje de asistencia"""
        if self.total_clases > 0:
            # Las clases justificadas y tarde cuentan como asistencia
            clases_efectivas = self.clases_presentes + self.clases_justificadas + self.clases_tarde
            self.porcentaje_asistencia = round((clases_efectivas / self.total_clases) * 100, 2)
        else:
            self.porcentaje_asistencia = 0.00
        return self.porcentaje_asistencia

    def actualizar_estadisticas(self):
        """Actualiza las estadísticas basándose en los registros de asistencia"""
        registros = RegistroAsistencia.objects.filter(
            aprendiz=self.aprendiz,
            llamado_asistencia__resultado_aprendizaje=self.resultado_aprendizaje,
            llamado_asistencia__ficha=self.ficha
        )

        self.total_clases = registros.count()
        self.clases_presentes = registros.filter(estado='PRESENTE').count()
        self.clases_ausentes = registros.filter(estado='AUSENTE').count()
        self.clases_justificadas = registros.filter(estado='JUSTIFICADO').count()
        self.clases_tarde = registros.filter(estado='TARDE').count()

        self.calcular_porcentaje()
        self.save()

    @property
    def nivel_riesgo(self):
        """Determina el nivel de riesgo basado en el porcentaje de asistencia"""
        if self.porcentaje_asistencia >= 90:
            return 'BAJO'
        elif self.porcentaje_asistencia >= 80:
            return 'MEDIO'
        elif self.porcentaje_asistencia >= 70:
            return 'ALTO'
        else:
            return 'CRITICO'

    def __str__(self):
        return f"{self.aprendiz.nombres} - {self.resultado_aprendizaje.nombre} - {self.porcentaje_asistencia}%"

