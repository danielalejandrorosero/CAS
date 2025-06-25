from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import (
    TipoNotificacion,
    Notificacion,
    ConfiguracionNotificacion,
    HistorialNotificacion
)
from .serializers import (
    TipoNotificacionSerializer,
    NotificacionSerializer,
    NotificacionCreateSerializer,
    ConfiguracionNotificacionSerializer,
    HistorialNotificacionSerializer,
    NotificacionResumenSerializer,
    MarcarLeidaSerializer
)
from .services import NotificacionService


class NotificacionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TipoNotificacionListView(generics.ListAPIView):
    """Lista todos los tipos de notificaciones activos"""
    queryset = TipoNotificacion.objects.filter(activo=True)
    serializer_class = TipoNotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]


class NotificacionListView(generics.ListAPIView):
    """Lista las notificaciones del usuario autenticado"""
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificacionPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tipo', 'leida']
    ordering_fields = ['fecha_creacion']
    ordering = ['-fecha_creacion']
    
    def get_queryset(self):
        return Notificacion.objects.filter(
            usuario=self.request.user
        ).select_related('tipo', 'usuario', 'content_type')


class NotificacionDetailView(generics.RetrieveAPIView):
    """Detalle de una notificación específica"""
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notificacion.objects.filter(
            usuario=self.request.user
        ).select_related('tipo', 'usuario', 'content_type')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Marcar como leída automáticamente al ver el detalle
        if not instance.leida:
            instance.marcar_como_leida()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NotificacionCreateView(generics.CreateAPIView):
    """Crear una nueva notificación (solo para administradores)"""
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Solo permitir a instructores y administradores crear notificaciones
        if not (self.request.user.rol.nombre in ['INSTRUCTOR', 'ADMINISTRADOR']):
            raise permissions.PermissionDenied(
                "No tienes permisos para crear notificaciones"
            )
        
        notificacion = serializer.save()
        
        # Enviar la notificación usando el servicio
        NotificacionService.enviar_notificacion(
            notificacion.usuario,
            notificacion.tipo.nombre,
            notificacion.titulo,
            notificacion.mensaje,
            objeto_relacionado=notificacion.objeto_relacionado,
            datos_extra=notificacion.datos_extra
        )


class ConfiguracionNotificacionView(generics.RetrieveUpdateAPIView):
    """Ver y actualizar configuración de notificaciones del usuario"""
    serializer_class = ConfiguracionNotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        config, created = ConfiguracionNotificacion.objects.get_or_create(
            usuario=self.request.user,
            defaults={
                'dias_activos': [0, 1, 2, 3, 4, 5, 6]  # Todos los días por defecto
            }
        )
        return config


class HistorialNotificacionListView(generics.ListAPIView):
    """Historial de notificaciones enviadas (solo para administradores)"""
    serializer_class = HistorialNotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificacionPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['metodo_envio', 'estado']
    ordering_fields = ['fecha_envio']
    ordering = ['-fecha_envio']
    
    def get_queryset(self):
        # Solo administradores pueden ver el historial completo
        if self.request.user.rol.nombre == 'ADMINISTRADOR':
            return HistorialNotificacion.objects.all().select_related(
                'notificacion__usuario', 'notificacion__tipo'
            )
        else:
            # Los usuarios solo pueden ver su propio historial
            return HistorialNotificacion.objects.filter(
                notificacion__usuario=self.request.user
            ).select_related('notificacion__usuario', 'notificacion__tipo')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def resumen_notificaciones(request):
    """Resumen de notificaciones del usuario"""
    usuario = request.user
    
    # Obtener estadísticas
    notificaciones = Notificacion.objects.filter(usuario=usuario)
    total = notificaciones.count()
    no_leidas = notificaciones.filter(leida=False).count()
    leidas = total - no_leidas
    
    # Contar por tipo
    por_tipo = notificaciones.values(
        'tipo__nombre'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    por_tipo_dict = {item['tipo__nombre']: item['count'] for item in por_tipo}
    
    # Últimas 5 notificaciones
    ultimas_5 = notificaciones.order_by('-fecha_creacion')[:5]
    
    data = {
        'total': total,
        'no_leidas': no_leidas,
        'leidas': leidas,
        'por_tipo': por_tipo_dict,
        'ultimas_5': ultimas_5
    }
    
    serializer = NotificacionResumenSerializer(data)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def marcar_como_leidas(request):
    """Marcar notificaciones como leídas"""
    serializer = MarcarLeidaSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        notificacion_ids = serializer.validated_data['notificacion_ids']
        
        # Marcar como leídas
        notificaciones = Notificacion.objects.filter(
            id__in=notificacion_ids,
            usuario=request.user,
            leida=False
        )
        
        count = 0
        for notificacion in notificaciones:
            notificacion.marcar_como_leida()
            count += 1
        
        return Response({
            'message': f'{count} notificaciones marcadas como leídas',
            'count': count
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def marcar_todas_como_leidas(request):
    """Marcar todas las notificaciones del usuario como leídas"""
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    )
    
    count = 0
    for notificacion in notificaciones:
        notificacion.marcar_como_leida()
        count += 1
    
    return Response({
        'message': f'{count} notificaciones marcadas como leídas',
        'count': count
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notificaciones_no_leidas(request):
    """Obtener solo las notificaciones no leídas"""
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).select_related('tipo', 'content_type').order_by('-fecha_creacion')
    
    serializer = NotificacionSerializer(notificaciones, many=True)
    return Response({
        'count': notificaciones.count(),
        'results': serializer.data
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def eliminar_notificacion(request, pk):
    """Eliminar una notificación específica"""
    try:
        notificacion = Notificacion.objects.get(
            pk=pk,
            usuario=request.user
        )
        notificacion.delete()
        return Response({
            'message': 'Notificación eliminada correctamente'
        })
    except Notificacion.DoesNotExist:
        return Response({
            'error': 'Notificación no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enviar_notificacion_personalizada(request):
    """Enviar una notificación personalizada (solo instructores y administradores)"""
    if request.user.rol.nombre not in ['INSTRUCTOR', 'ADMINISTRADOR']:
        return Response({
            'error': 'No tienes permisos para enviar notificaciones'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Validar datos requeridos
    required_fields = ['usuario_id', 'tipo', 'titulo', 'mensaje']
    for field in required_fields:
        if field not in request.data:
            return Response({
                'error': f'El campo {field} es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from apps.usuarios.models import Usuario
        usuario_destino = Usuario.objects.get(id=request.data['usuario_id'])
        
        # Enviar notificación
        notificacion = NotificacionService.enviar_notificacion(
            usuario=usuario_destino,
            tipo_notificacion=request.data['tipo'],
            titulo=request.data['titulo'],
            mensaje=request.data['mensaje'],
            datos_extra=request.data.get('datos_extra', {})
        )
        
        serializer = NotificacionSerializer(notificacion)
        return Response({
            'message': 'Notificación enviada correctamente',
            'notificacion': serializer.data
        })
        
    except Usuario.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error al enviar notificación: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)