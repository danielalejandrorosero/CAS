from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.actividades.models import (
    TipoActividad, Actividad, AsignacionActividad,
    ArchivoActividad, EntregaActividad, ArchivoEntrega,
    CalificacionActividad
)
from apps.usuarios.models import Usuario
from apps.asistencia.models import Ficha, ResultadoAprendizaje


# ================================
# SERIALIZERS PARA TIPOS DE ACTIVIDAD
# ================================

class TipoActividadSerializer(serializers.ModelSerializer):
    """Serializer para los tipos de actividad"""

    class Meta:
        model = TipoActividad
        fields = ['id', 'nombre', 'descripcion', 'activo', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


# ================================
# SERIALIZERS PARA ARCHIVOS
# ================================

class ArchivoActividadSerializer(serializers.ModelSerializer):
    """Serializer para archivos de actividades"""

    subido_por_nombre = serializers.CharField(source='subido_por.nombre_completo', read_only=True)
    tamaño_mb = serializers.SerializerMethodField()

    class Meta:
        model = ArchivoActividad
        fields = [
            'id', 'nombre', 'archivo', 'descripcion', 'es_obligatorio',
            'tamaño_archivo', 'tamaño_mb', 'tipo_archivo', 'subido_por',
            'subido_por_nombre', 'created_at'
        ]
        read_only_fields = ['tamaño_archivo', 'tipo_archivo', 'created_at']

    def get_tamaño_mb(self, obj):
        """Convierte el tamaño a MB para mejor visualización"""
        if obj.tamaño_archivo:
            return round(obj.tamaño_archivo / (1024 * 1024), 2)
        return 0


class ArchivoEntregaSerializer(serializers.ModelSerializer):
    """Serializer para archivos de entregas"""

    tamaño_mb = serializers.SerializerMethodField()

    class Meta:
        model = ArchivoEntrega
        fields = [
            'id', 'nombre', 'archivo', 'tamaño_archivo',
            'tamaño_mb', 'tipo_archivo', 'created_at'
        ]
        read_only_fields = ['tamaño_archivo', 'tipo_archivo', 'created_at']

    def get_tamaño_mb(self, obj):
        if obj.tamaño_archivo:
            return round(obj.tamaño_archivo / (1024 * 1024), 2)
        return 0


# ================================
# SERIALIZERS PARA ACTIVIDADES
# ================================

class ActividadListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de actividades"""

    tipo_actividad_nombre = serializers.CharField(source='tipo_actividad.get_nombre_display', read_only=True)
    instructor_nombre = serializers.CharField(source='instructor.nombre_completo', read_only=True)
    ficha_numero = serializers.CharField(source='ficha.numero', read_only=True)
    resultado_aprendizaje_nombre = serializers.CharField(source='resultado_aprendizaje.nombre', read_only=True)
    dias_para_entrega = serializers.SerializerMethodField()
    total_entregas = serializers.ReadOnlyField()
    entregas_pendientes = serializers.ReadOnlyField()

    class Meta:
        model = Actividad
        fields = [
            'id', 'titulo', 'descripcion', 'tipo_actividad_nombre',
            'instructor_nombre', 'ficha_numero', 'resultado_aprendizaje_nombre',
            'fecha_inicio', 'fecha_entrega', 'fecha_limite', 'dias_para_entrega',
            'modalidad', 'estado', 'es_obligatoria', 'visible_para_aprendices',
            'puntaje_maximo', 'total_entregas', 'entregas_pendientes',
            'created_at', 'updated_at'
        ]

    def get_dias_para_entrega(self, obj):
        """Calcula los días restantes para la entrega"""
        if obj.fecha_entrega:
            dias = (obj.fecha_entrega.date() - timezone.now().date()).days
            return dias if dias >= 0 else 0
        return None


class ActividadDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para actividades"""

    tipo_actividad_data = TipoActividadSerializer(source='tipo_actividad', read_only=True)
    instructor_nombre = serializers.CharField(source='instructor.nombre_completo', read_only=True)
    ficha_data = serializers.SerializerMethodField()
    resultado_aprendizaje_data = serializers.SerializerMethodField()
    archivos = ArchivoActividadSerializer(many=True, read_only=True)
    dias_para_entrega = serializers.SerializerMethodField()
    esta_vencida = serializers.ReadOnlyField()
    acepta_entregas = serializers.ReadOnlyField()
    total_entregas = serializers.ReadOnlyField()
    entregas_pendientes = serializers.ReadOnlyField()

    class Meta:
        model = Actividad
        fields = [
            'id', 'titulo', 'descripcion', 'tipo_actividad', 'tipo_actividad_data',
            'instructor', 'instructor_nombre', 'resultado_aprendizaje', 'resultado_aprendizaje_data',
            'ficha', 'ficha_data', 'fecha_creacion', 'fecha_publicacion',
            'fecha_inicio', 'fecha_entrega', 'fecha_limite', 'dias_para_entrega',
            'modalidad', 'numero_integrantes_grupo', 'permite_entrega_tardia',
            'penalizacion_tardanza', 'puntaje_maximo', 'criterios_evaluacion',
            'estado', 'es_obligatoria', 'visible_para_aprendices', 'requiere_archivo',
            'observaciones_instructor', 'archivos', 'esta_vencida', 'acepta_entregas',
            'total_entregas', 'entregas_pendientes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'fecha_creacion', 'fecha_publicacion', 'esta_vencida', 'acepta_entregas',
            'total_entregas', 'entregas_pendientes', 'created_at', 'updated_at'
        ]

    def get_ficha_data(self, obj):
        return {
            'id': obj.ficha.id,
            'numero': obj.ficha.numero,
            'programa': obj.ficha.programa.nombre,
            'modalidad': obj.ficha.modalidad,
            'jornada': obj.ficha.jornada
        }

    def get_resultado_aprendizaje_data(self, obj):
        return {
            'id': obj.resultado_aprendizaje.id,
            'codigo': obj.resultado_aprendizaje.codigo,
            'nombre': obj.resultado_aprendizaje.nombre,
            'trimestre': obj.resultado_aprendizaje.trimestre,
            'horas_asignadas': obj.resultado_aprendizaje.horas_asignadas
        }

    def get_dias_para_entrega(self, obj):
        if obj.fecha_entrega:
            dias = (obj.fecha_entrega.date() - timezone.now().date()).days
            return dias if dias >= 0 else 0
        return None


class ActividadCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar actividades"""

    archivos_data = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )
    aprendices_asignados = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text="Lista de IDs de aprendices para asignación específica"
    )

    class Meta:
        model = Actividad
        fields = [
            'titulo', 'descripcion', 'tipo_actividad', 'instructor',
            'resultado_aprendizaje', 'ficha', 'fecha_inicio', 'fecha_entrega',
            'fecha_limite', 'modalidad', 'numero_integrantes_grupo',
            'permite_entrega_tardia', 'penalizacion_tardanza', 'puntaje_maximo',
            'criterios_evaluacion', 'estado', 'es_obligatoria',
            'visible_para_aprendices', 'requiere_archivo', 'observaciones_instructor',
            'archivos_data', 'aprendices_asignados'
        ]

    def validate(self, data):
        """Validaciones personalizadas"""
        # Validar fechas
        if data.get('fecha_entrega') and data.get('fecha_inicio'):
            if data['fecha_entrega'] <= data['fecha_inicio']:
                raise serializers.ValidationError({
                    'fecha_entrega': 'La fecha de entrega debe ser posterior a la fecha de inicio.'
                })

        if data.get('fecha_limite') and data.get('fecha_entrega'):
            if data['fecha_limite'] <= data['fecha_entrega']:
                raise serializers.ValidationError({
                    'fecha_limite': 'La fecha límite debe ser posterior a la fecha de entrega.'
                })

        # Validar modalidad grupal
        if data.get('modalidad') == 'GRUPAL' and data.get('numero_integrantes_grupo', 1) <= 1:
            raise serializers.ValidationError({
                'numero_integrantes_grupo': 'Para actividades grupales debe especificar más de 1 integrante.'
            })

        # Validar que el instructor esté asignado a ese resultado y ficha
        instructor = data.get('instructor') or (self.instance.instructor if self.instance else None)
        resultado = data.get('resultado_aprendizaje') or (
            self.instance.resultado_aprendizaje if self.instance else None)
        ficha = data.get('ficha') or (self.instance.ficha if self.instance else None)

        if instructor and resultado and ficha:
            from apps.asistencia.models import AsignacionInstructor
            if not AsignacionInstructor.objects.filter(
                    instructor=instructor,
                    resultado_aprendizaje=resultado,
                    ficha=ficha,
                    activo=True
            ).exists():
                raise serializers.ValidationError({
                    'instructor': 'El instructor no está asignado a este resultado de aprendizaje en esta ficha.'
                })

        return data

    def create(self, validated_data):
        archivos_data = validated_data.pop('archivos_data', [])
        aprendices_asignados = validated_data.pop('aprendices_asignados', [])

        actividad = Actividad.objects.create(**validated_data)

        # Crear archivos si los hay
        self._crear_archivos(actividad, archivos_data)

        # Crear asignaciones específicas si las hay
        self._crear_asignaciones(actividad, aprendices_asignados)

        return actividad

    def update(self, instance, validated_data):
        archivos_data = validated_data.pop('archivos_data', [])
        aprendices_asignados = validated_data.pop('aprendices_asignados', [])

        # Actualizar la actividad
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Agregar nuevos archivos si los hay
        if archivos_data:
            self._crear_archivos(instance, archivos_data)

        # Actualizar asignaciones si se especifican
        if aprendices_asignados:
            # Eliminar asignaciones anteriores
            AsignacionActividad.objects.filter(actividad=instance).delete()
            self._crear_asignaciones(instance, aprendices_asignados)

        return instance

    def _crear_archivos(self, actividad, archivos_data):
        """Crea archivos asociados a la actividad"""
        usuario = self.context['request'].user
        for archivo in archivos_data:
            ArchivoActividad.objects.create(
                actividad=actividad,
                nombre=archivo.name,
                archivo=archivo,
                subido_por=usuario
            )

    def _crear_asignaciones(self, actividad, aprendices_ids):
        """Crea asignaciones específicas de la actividad"""
        asignaciones = []
        for aprendiz_id in aprendices_ids:
            try:
                aprendiz = Usuario.objects.get(id=aprendiz_id, rol__nombre='APRENDIZ')
                asignaciones.append(AsignacionActividad(
                    actividad=actividad,
                    aprendiz=aprendiz,
                    es_obligatoria=actividad.es_obligatoria
                ))
            except Usuario.DoesNotExist:
                continue

        if asignaciones:
            AsignacionActividad.objects.bulk_create(asignaciones)


# ================================
# SERIALIZERS PARA ENTREGAS
# ================================

class EntregaActividadListSerializer(serializers.ModelSerializer):
    """Serializer para listado de entregas"""

    aprendiz_nombre = serializers.CharField(source='aprendiz.nombre_completo', read_only=True)
    actividad_titulo = serializers.CharField(source='actividad.titulo', read_only=True)
    tiene_calificacion = serializers.SerializerMethodField()

    class Meta:
        model = EntregaActividad
        fields = [
            'id', 'actividad_titulo', 'aprendiz_nombre', 'fecha_entrega',
            'estado', 'es_entrega_tardia', 'tiene_calificacion', 'puede_modificar'
        ]

    def get_tiene_calificacion(self, obj):
        return hasattr(obj, 'calificacion')


class EntregaActividadDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para entregas"""

    aprendiz_data = serializers.SerializerMethodField()
    actividad_data = serializers.SerializerMethodField()
    archivos = ArchivoEntregaSerializer(many=True, read_only=True)
    calificacion = serializers.SerializerMethodField()

    class Meta:
        model = EntregaActividad
        fields = [
            'id', 'actividad', 'actividad_data', 'aprendiz', 'aprendiz_data',
            'contenido', 'fecha_entrega', 'fecha_ultima_modificacion',
            'estado', 'es_entrega_tardia', 'observaciones_aprendiz',
            'archivos', 'calificacion', 'puede_modificar'
        ]
        read_only_fields = [
            'fecha_entrega', 'fecha_ultima_modificacion', 'es_entrega_tardia', 'puede_modificar'
        ]

    def get_aprendiz_data(self, obj):
        return {
            'id': obj.aprendiz.id,
            'nombre_completo': obj.aprendiz.nombre_completo,
            'documento': obj.aprendiz.documento,
            'email': obj.aprendiz.email
        }

    def get_actividad_data(self, obj):
        return {
            'id': obj.actividad.id,
            'titulo': obj.actividad.titulo,
            'fecha_entrega': obj.actividad.fecha_entrega,
            'puntaje_maximo': obj.actividad.puntaje_maximo,
            'requiere_archivo': obj.actividad.requiere_archivo
        }

    def get_calificacion(self, obj):
        if hasattr(obj, 'calificacion'):
            return {
                'puntaje_obtenido': obj.calificacion.puntaje_obtenido,
                'porcentaje': obj.calificacion.porcentaje,
                'comentarios': obj.calificacion.comentarios,
                'fecha_calificacion': obj.calificacion.fecha_calificacion,
                'aprobada': obj.calificacion.aprobada,
                'calificacion_letra': obj.calificacion.calificacion_letra
            }
        return None


class EntregaActividadCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar entregas"""

    archivos_data = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = EntregaActividad
        fields = [
            'actividad', 'aprendiz', 'contenido', 'estado',
            'observaciones_aprendiz', 'archivos_data'
        ]

    def validate(self, data):
        """Validaciones personalizadas"""
        actividad = data.get('actividad')
        aprendiz = data.get('aprendiz')

        # Verificar que la actividad acepta entregas
        if actividad and not actividad.acepta_entregas:
            raise serializers.ValidationError({
                'actividad': 'Esta actividad ya no acepta entregas.'
            })

        # Verificar que el aprendiz esté matriculado en la ficha
        if actividad and aprendiz:
            from apps.asistencia.models import Matricula
            if not Matricula.objects.filter(
                    aprendiz=aprendiz,
                    ficha=actividad.ficha,
                    estado='ACTIVO'
            ).exists():
                raise serializers.ValidationError({
                    'aprendiz': 'El aprendiz no está matriculado activamente en esta ficha.'
                })

        return data

    def create(self, validated_data):
        archivos_data = validated_data.pop('archivos_data', [])
        entrega = EntregaActividad.objects.create(**validated_data)

        # Crear archivos si los hay
        self._crear_archivos(entrega, archivos_data)

        return entrega

    def update(self, instance, validated_data):
        archivos_data = validated_data.pop('archivos_data', [])

        # Verificar que se puede modificar
        if not instance.puede_modificar:
            raise serializers.ValidationError({
                'non_field_errors': ['Esta entrega no se puede modificar.']
            })

        # Actualizar la entrega
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Agregar nuevos archivos si los hay
        if archivos_data:
            self._crear_archivos(instance, archivos_data)

        return instance

    def _crear_archivos(self, entrega, archivos_data):
        """Crea archivos asociados a la entrega"""
        for archivo in archivos_data:
            ArchivoEntrega.objects.create(
                entrega=entrega,
                nombre=archivo.name,
                archivo=archivo
            )


# ================================
# SERIALIZERS PARA CALIFICACIONES
# ================================

class CalificacionActividadSerializer(serializers.ModelSerializer):
    """Serializer para calificaciones"""

    entrega_data = serializers.SerializerMethodField()
    instructor_nombre = serializers.CharField(source='instructor.nombre_completo', read_only=True)

    class Meta:
        model = CalificacionActividad
        fields = [
            'id', 'entrega', 'entrega_data', 'instructor', 'instructor_nombre',
            'puntaje_obtenido', 'porcentaje', 'comentarios', 'fortalezas',
            'aspectos_mejorar', 'fecha_calificacion', 'fecha_modificacion',
            'requiere_correccion', 'aprobada', 'calificacion_letra'
        ]
        read_only_fields = [
            'porcentaje', 'fecha_calificacion', 'fecha_modificacion',
            'aprobada', 'calificacion_letra'
        ]

    def get_entrega_data(self, obj):
        return {
            'id': obj.entrega.id,
            'aprendiz_nombre': obj.entrega.aprendiz.nombre_completo,
            'actividad_titulo': obj.entrega.actividad.titulo,
            'fecha_entrega': obj.entrega.fecha_entrega,
            'es_entrega_tardia': obj.entrega.es_entrega_tardia
        }

    def validate_puntaje_obtenido(self, value):
        """Validar que el puntaje no exceda el máximo de la actividad"""
        if self.instance:
            puntaje_maximo = self.instance.entrega.actividad.puntaje_maximo
        else:
            # En creación, necesitamos acceder a la entrega del validated_data
            entrega = self.initial_data.get('entrega')
            if entrega:
                try:
                    entrega_obj = EntregaActividad.objects.get(id=entrega)
                    puntaje_maximo = entrega_obj.actividad.puntaje_maximo
                except EntregaActividad.DoesNotExist:
                    raise serializers.ValidationError("La entrega especificada no existe.")
            else:
                raise serializers.ValidationError("Debe especificar una entrega.")

        if value > puntaje_maximo:
            raise serializers.ValidationError(
                f"El puntaje obtenido no puede ser mayor al puntaje máximo de la actividad ({puntaje_maximo})."
            )

        return value


# ================================
# SERIALIZERS PARA ASIGNACIONES
# ================================

class AsignacionActividadSerializer(serializers.ModelSerializer):
    """Serializer para asignaciones de actividades"""

    actividad_titulo = serializers.CharField(source='actividad.titulo', read_only=True)
    aprendiz_nombre = serializers.CharField(source='aprendiz.nombre_completo', read_only=True)

    class Meta:
        model = AsignacionActividad
        fields = [
            'id', 'actividad', 'actividad_titulo', 'aprendiz', 'aprendiz_nombre',
            'es_obligatoria', 'fecha_asignacion', 'observaciones'
        ]
        read_only_fields = ['fecha_asignacion']