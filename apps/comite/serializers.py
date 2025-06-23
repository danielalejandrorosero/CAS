from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from .models import CitacionComite, ArchivoAdjuntoCitacion, SeguimientoCitacion
from apps.usuarios.models import Usuario
from apps.asistencia.models import Ficha, ResultadoAprendizaje


class ArchivoAdjuntoCitacionSerializer(serializers.ModelSerializer):
    """Serializer para archivos adjuntos de citaciones"""
    
    subido_por_nombre = serializers.CharField(source='subido_por.get_full_name', read_only=True)
    tamaño_archivo = serializers.SerializerMethodField()
    
    class Meta:
        model = ArchivoAdjuntoCitacion
        fields = [
            'id', 'archivo', 'nombre_original', 'descripcion',
            'subido_por', 'subido_por_nombre', 'fecha_subida', 'tamaño_archivo'
        ]
        read_only_fields = ['subido_por', 'fecha_subida']
    
    def get_tamaño_archivo(self, obj):
        """Obtiene el tamaño del archivo en formato legible"""
        if obj.archivo:
            size = obj.archivo.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "0 B"


class SeguimientoCitacionSerializer(serializers.ModelSerializer):
    """Serializer para seguimientos de citaciones"""
    
    instructor_nombre = serializers.CharField(source='instructor_seguimiento.get_full_name', read_only=True)
    tipo_seguimiento_display = serializers.CharField(source='get_tipo_seguimiento_display', read_only=True)
    resultado_display = serializers.CharField(source='get_resultado_display', read_only=True)
    
    class Meta:
        model = SeguimientoCitacion
        fields = [
            'id', 'citacion', 'instructor_seguimiento', 'instructor_nombre',
            'tipo_seguimiento', 'tipo_seguimiento_display', 'fecha_seguimiento',
            'observaciones', 'resultado', 'resultado_display', 'acciones_tomadas',
            'requiere_nuevo_seguimiento', 'fecha_proximo_seguimiento',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_fecha_seguimiento(self, value):
        """Valida que la fecha de seguimiento no sea futura"""
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "La fecha de seguimiento no puede ser futura."
            )
        return value
    
    def validate(self, data):
        """Validaciones adicionales"""
        if data.get('requiere_nuevo_seguimiento') and not data.get('fecha_proximo_seguimiento'):
            raise serializers.ValidationError({
                'fecha_proximo_seguimiento': 'Debe especificar la fecha del próximo seguimiento.'
            })
        
        if data.get('fecha_proximo_seguimiento') and data.get('fecha_proximo_seguimiento') <= timezone.now().date():
            raise serializers.ValidationError({
                'fecha_proximo_seguimiento': 'La fecha del próximo seguimiento debe ser futura.'
            })
        
        return data


class CitacionComiteListSerializer(serializers.ModelSerializer):
    """Serializer para listar citaciones (vista resumida)"""
    
    aprendiz_nombre = serializers.CharField(source='aprendiz.get_full_name', read_only=True)
    aprendiz_documento = serializers.CharField(source='aprendiz.documento', read_only=True)
    instructor_nombre = serializers.CharField(source='instructor_citante.get_full_name', read_only=True)
    ficha_numero = serializers.CharField(source='ficha.numero', read_only=True)
    motivo_display = serializers.CharField(source='get_motivo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    dias_hasta_citacion = serializers.ReadOnlyField()
    esta_vencida = serializers.ReadOnlyField()
    
    class Meta:
        model = CitacionComite
        fields = [
            'id', 'numero_citacion', 'aprendiz', 'aprendiz_nombre', 'aprendiz_documento',
            'instructor_citante', 'instructor_nombre', 'ficha', 'ficha_numero',
            'motivo', 'motivo_display', 'estado', 'estado_display',
            'prioridad', 'prioridad_display', 'fecha_creacion', 'fecha_citacion',
            'dias_hasta_citacion', 'esta_vencida', 'requiere_seguimiento'
        ]


class CitacionComiteDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles completos de citaciones"""
    
    aprendiz_info = serializers.SerializerMethodField()
    instructor_info = serializers.SerializerMethodField()
    ficha_info = serializers.SerializerMethodField()
    resultado_aprendizaje_info = serializers.SerializerMethodField()
    motivo_display = serializers.CharField(source='get_motivo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    archivos_adjuntos = ArchivoAdjuntoCitacionSerializer(many=True, read_only=True)
    seguimientos = SeguimientoCitacionSerializer(many=True, read_only=True)
    dias_hasta_citacion = serializers.ReadOnlyField()
    esta_vencida = serializers.ReadOnlyField()
    
    class Meta:
        model = CitacionComite
        fields = [
            'id', 'numero_citacion', 'aprendiz', 'aprendiz_info',
            'instructor_citante', 'instructor_info', 'ficha', 'ficha_info',
            'resultado_aprendizaje', 'resultado_aprendizaje_info',
            'motivo', 'motivo_display', 'motivo_detallado',
            'estado', 'estado_display', 'prioridad', 'prioridad_display',
            'fecha_creacion', 'fecha_citacion', 'fecha_notificacion', 'fecha_realizacion',
            'observaciones_instructor', 'observaciones_comite',
            'requiere_seguimiento', 'fecha_seguimiento',
            'archivos_adjuntos', 'seguimientos',
            'dias_hasta_citacion', 'esta_vencida',
            'activo', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'numero_citacion', 'fecha_creacion', 'fecha_notificacion',
            'fecha_realizacion', 'created_at', 'updated_at'
        ]
    
    def get_aprendiz_info(self, obj):
        """Información completa del aprendiz"""
        return {
            'id': obj.aprendiz.id,
            'documento': obj.aprendiz.documento,
            'nombres': obj.aprendiz.nombres,
            'apellidos': obj.aprendiz.apellidos,
            'email': obj.aprendiz.email,
            'telefono': obj.aprendiz.telefono,
            'foto_perfil': obj.aprendiz.foto_perfil.url if obj.aprendiz.foto_perfil else None
        }
    
    def get_instructor_info(self, obj):
        """Información del instructor citante"""
        return {
            'id': obj.instructor_citante.id,
            'documento': obj.instructor_citante.documento,
            'nombres': obj.instructor_citante.nombres,
            'apellidos': obj.instructor_citante.apellidos,
            'email': obj.instructor_citante.email
        }
    
    def get_ficha_info(self, obj):
        """Información de la ficha"""
        return {
            'id': obj.ficha.id,
            'numero': obj.ficha.numero,
            'programa': obj.ficha.programa.nombre if obj.ficha.programa else None,
            'jornada': obj.ficha.get_jornada_display(),
            'estado': obj.ficha.get_estado_display()
        }
    
    def get_resultado_aprendizaje_info(self, obj):
        """Información del resultado de aprendizaje"""
        if obj.resultado_aprendizaje:
            return {
                'id': obj.resultado_aprendizaje.id,
                'codigo': obj.resultado_aprendizaje.codigo,
                'descripcion': obj.resultado_aprendizaje.descripcion,
                'competencia': obj.resultado_aprendizaje.competencia.nombre if obj.resultado_aprendizaje.competencia else None
            }
        return None


class CitacionComiteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar citaciones"""
    
    archivos_adjuntos_data = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = CitacionComite
        fields = [
            'aprendiz', 'instructor_citante', 'ficha', 'resultado_aprendizaje',
            'motivo', 'motivo_detallado', 'prioridad', 'fecha_citacion',
            'observaciones_instructor', 'requiere_seguimiento', 'fecha_seguimiento',
            'archivos_adjuntos_data'
        ]
    
    def validate_fecha_citacion(self, value):
        """Valida que la fecha de citación sea futura"""
        if value <= timezone.now():
            raise serializers.ValidationError(
                "La fecha de citación debe ser futura."
            )
        return value
    
    def validate(self, data):
        """Validaciones adicionales"""
        # Validar que el aprendiz pertenezca a la ficha
        aprendiz = data.get('aprendiz')
        ficha = data.get('ficha')
        
        if aprendiz and ficha:
            from apps.asistencia.models import Matricula
            if not Matricula.objects.filter(aprendiz=aprendiz, ficha=ficha, activo=True).exists():
                raise serializers.ValidationError({
                    'aprendiz': 'El aprendiz no está matriculado en la ficha seleccionada.'
                })
        
        # Validar que el instructor tenga acceso a la ficha
        instructor = data.get('instructor_citante')
        if instructor and ficha:
            from apps.asistencia.models import AsignacionInstructor
            if not AsignacionInstructor.objects.filter(
                instructor=instructor, 
                resultado_aprendizaje__ficha=ficha, 
                activo=True
            ).exists():
                raise serializers.ValidationError({
                    'instructor_citante': 'El instructor no tiene acceso a esta ficha.'
                })
        
        # Validar seguimiento
        if data.get('requiere_seguimiento') and not data.get('fecha_seguimiento'):
            raise serializers.ValidationError({
                'fecha_seguimiento': 'Debe especificar la fecha de seguimiento.'
            })
        
        if data.get('fecha_seguimiento') and data.get('fecha_seguimiento') <= timezone.now().date():
            raise serializers.ValidationError({
                'fecha_seguimiento': 'La fecha de seguimiento debe ser futura.'
            })
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Crear citación con archivos adjuntos"""
        archivos_data = validated_data.pop('archivos_adjuntos_data', [])
        citacion = CitacionComite.objects.create(**validated_data)
        
        # Crear archivos adjuntos
        for archivo in archivos_data:
            ArchivoAdjuntoCitacion.objects.create(
                citacion=citacion,
                archivo=archivo,
                nombre_original=archivo.name,
                subido_por=self.context['request'].user
            )
        
        return citacion
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Actualizar citación"""
        archivos_data = validated_data.pop('archivos_adjuntos_data', [])
        
        # Actualizar campos de la citación
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Agregar nuevos archivos adjuntos
        for archivo in archivos_data:
            ArchivoAdjuntoCitacion.objects.create(
                citacion=instance,
                archivo=archivo,
                nombre_original=archivo.name,
                subido_por=self.context['request'].user
            )
        
        return instance


class CitacionComiteEstadoSerializer(serializers.ModelSerializer):
    """Serializer para actualizar solo el estado de la citación"""
    
    class Meta:
        model = CitacionComite
        fields = ['estado', 'observaciones_comite']
    
    def validate_estado(self, value):
        """Valida las transiciones de estado"""
        instance = self.instance
        if instance:
            estado_actual = instance.estado
            
            # Definir transiciones válidas
            transiciones_validas = {
                'PENDIENTE': ['NOTIFICADA', 'CANCELADA'],
                'NOTIFICADA': ['REALIZADA', 'CANCELADA'],
                'REALIZADA': [],  # Estado final
                'CANCELADA': []   # Estado final
            }
            
            if value not in transiciones_validas.get(estado_actual, []):
                raise serializers.ValidationError(
                    f"No se puede cambiar de {estado_actual} a {value}."
                )
        
        return value


class CitacionAprendizSerializer(serializers.ModelSerializer):
    """Serializer para que los aprendices consulten sus citaciones"""
    
    instructor_nombre = serializers.CharField(source='instructor_citante.get_full_name', read_only=True)
    ficha_numero = serializers.CharField(source='ficha.numero', read_only=True)
    resultado_aprendizaje_nombre = serializers.CharField(
        source='resultado_aprendizaje.descripcion', 
        read_only=True
    )
    motivo_display = serializers.CharField(source='get_motivo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    dias_hasta_citacion = serializers.ReadOnlyField()
    esta_vencida = serializers.ReadOnlyField()
    
    class Meta:
        model = CitacionComite
        fields = [
            'id', 'numero_citacion', 'instructor_nombre', 'ficha_numero',
            'resultado_aprendizaje_nombre', 'motivo', 'motivo_display',
            'motivo_detallado', 'estado', 'estado_display',
            'prioridad', 'prioridad_display', 'fecha_creacion', 'fecha_citacion',
            'observaciones_instructor', 'dias_hasta_citacion', 'esta_vencida'
        ]