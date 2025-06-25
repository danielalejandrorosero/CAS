from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import (
    TipoNotificacion,
    Notificacion,
    ConfiguracionNotificacion,
    HistorialNotificacion
)


class TipoNotificacionSerializer(serializers.ModelSerializer):
    """Serializer para tipos de notificaciones"""
    
    class Meta:
        model = TipoNotificacion
        fields = ['id', 'nombre', 'descripcion', 'activo']
        read_only_fields = ['id']


class NotificacionSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones"""
    
    tipo_nombre = serializers.CharField(source='tipo.get_nombre_display', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    tiempo_transcurrido = serializers.SerializerMethodField()
    objeto_relacionado_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Notificacion
        fields = [
            'id',
            'usuario',
            'usuario_nombre',
            'tipo',
            'tipo_nombre',
            'titulo',
            'mensaje',
            'leida',
            'fecha_creacion',
            'fecha_lectura',
            'tiempo_transcurrido',
            'objeto_relacionado_info',
            'datos_extra',
            'enviada_push',
            'enviada_email'
        ]
        read_only_fields = [
            'id',
            'fecha_creacion',
            'fecha_lectura',
            'usuario_nombre',
            'tipo_nombre',
            'tiempo_transcurrido',
            'objeto_relacionado_info'
        ]
    
    def get_tiempo_transcurrido(self, obj):
        """Calcula el tiempo transcurrido desde la creación"""
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        return timesince(obj.fecha_creacion, timezone.now())
    
    def get_objeto_relacionado_info(self, obj):
        """Información del objeto relacionado"""
        if obj.objeto_relacionado:
            return {
                'tipo': obj.content_type.model,
                'id': obj.object_id,
                'nombre': str(obj.objeto_relacionado)
            }
        return None


class NotificacionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear notificaciones"""
    
    class Meta:
        model = Notificacion
        fields = [
            'usuario',
            'tipo',
            'titulo',
            'mensaje',
            'content_type',
            'object_id',
            'datos_extra'
        ]
    
    def validate(self, data):
        """Validaciones personalizadas"""
        # Validar que si se proporciona content_type, también se proporcione object_id
        content_type = data.get('content_type')
        object_id = data.get('object_id')
        
        if content_type and not object_id:
            raise serializers.ValidationError(
                "Si se proporciona content_type, también debe proporcionarse object_id"
            )
        
        if object_id and not content_type:
            raise serializers.ValidationError(
                "Si se proporciona object_id, también debe proporcionarse content_type"
            )
        
        return data


class ConfiguracionNotificacionSerializer(serializers.ModelSerializer):
    """Serializer para configuración de notificaciones"""
    
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = ConfiguracionNotificacion
        fields = [
            'id',
            'usuario',
            'usuario_nombre',
            'notificaciones_push',
            'notificaciones_email',
            'nueva_actividad',
            'actividad_valorada',
            'citacion_comite',
            'alta_inasistencia',
            'bajo_rendimiento',
            'recordatorios',
            'hora_inicio',
            'hora_fin',
            'dias_activos',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
        read_only_fields = [
            'id',
            'usuario_nombre',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
    
    def validate_dias_activos(self, value):
        """Valida que los días activos sean válidos"""
        if value:
            for dia in value:
                if not isinstance(dia, int) or dia < 0 or dia > 6:
                    raise serializers.ValidationError(
                        "Los días deben ser números enteros entre 0 (Lunes) y 6 (Domingo)"
                    )
        return value
    
    def validate(self, data):
        """Validaciones adicionales"""
        hora_inicio = data.get('hora_inicio')
        hora_fin = data.get('hora_fin')
        
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            raise serializers.ValidationError(
                "La hora de inicio debe ser anterior a la hora de fin"
            )
        
        return data


class HistorialNotificacionSerializer(serializers.ModelSerializer):
    """Serializer para historial de notificaciones"""
    
    notificacion_titulo = serializers.CharField(source='notificacion.titulo', read_only=True)
    usuario_nombre = serializers.CharField(source='notificacion.usuario.get_full_name', read_only=True)
    
    class Meta:
        model = HistorialNotificacion
        fields = [
            'id',
            'notificacion',
            'notificacion_titulo',
            'usuario_nombre',
            'metodo_envio',
            'estado',
            'fecha_envio',
            'mensaje_error'
        ]
        read_only_fields = [
            'id',
            'fecha_envio',
            'notificacion_titulo',
            'usuario_nombre'
        ]


class NotificacionResumenSerializer(serializers.Serializer):
    """Serializer para resumen de notificaciones del usuario"""
    
    total = serializers.IntegerField()
    no_leidas = serializers.IntegerField()
    leidas = serializers.IntegerField()
    por_tipo = serializers.DictField()
    ultimas_5 = NotificacionSerializer(many=True)


class MarcarLeidaSerializer(serializers.Serializer):
    """Serializer para marcar notificaciones como leídas"""
    
    notificacion_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Lista de IDs de notificaciones a marcar como leídas"
    )
    
    def validate_notificacion_ids(self, value):
        """Valida que las notificaciones existan"""
        usuario = self.context['request'].user
        notificaciones_existentes = Notificacion.objects.filter(
            id__in=value,
            usuario=usuario
        ).values_list('id', flat=True)
        
        ids_inexistentes = set(value) - set(notificaciones_existentes)
        if ids_inexistentes:
            raise serializers.ValidationError(
                f"Las siguientes notificaciones no existen o no pertenecen al usuario: {list(ids_inexistentes)}"
            )
        
        return value