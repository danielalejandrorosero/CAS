from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import (
    TipoActividad, Actividad, AsignacionActividad,
    ArchivoActividad, EntregaActividad, ArchivoEntrega,
    CalificacionActividad
)
from .serializers import (
    TipoActividadSerializer, ActividadListSerializer, ActividadDetailSerializer,
    ActividadCreateUpdateSerializer, EntregaActividadListSerializer,
    EntregaActividadDetailSerializer, EntregaActividadCreateUpdateSerializer,
    CalificacionActividadSerializer, ArchivoActividadSerializer,
    ArchivoEntregaSerializer
)
from apps.usuarios.models import Usuario
from apps.asistencia.models import Ficha, ResultadoAprendizaje, Matricula


# ================================
# VISTAS PARA TIPOS DE ACTIVIDAD
# ================================

class TipoActividadListView(generics.ListAPIView):
    """
    Lista todos los tipos de actividad activos.
    """
    queryset = TipoActividad.objects.filter(activo=True)
    serializer_class = TipoActividadSerializer
    permission_classes = [permissions.IsAuthenticated]


# ================================
# VISTAS PARA ACTIVIDADES
# ================================

class ActividadListCreateView(generics.ListCreateAPIView):
    """
    Lista actividades y permite crear nuevas actividades.
    Los instructores solo ven sus actividades.
    Los aprendices ven actividades asignadas a ellos.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        queryset = Actividad.objects.select_related(
            'tipo_actividad', 'instructor', 'ficha', 'resultado_aprendizaje'
        ).annotate(
            total_entregas=Count('entregas'),
            entregas_pendientes=Count('entregas', filter=Q(entregas__estado='BORRADOR'))
        )

        if user.rol.nombre == 'INSTRUCTOR':
            # Instructores ven solo sus actividades
            queryset = queryset.filter(instructor=user)
        elif user.rol.nombre == 'APRENDIZ':
            # Aprendices ven actividades de sus fichas activas y que sean visibles
            fichas_activas = Matricula.objects.filter(
                aprendiz=user, estado='ACTIVO'
            ).values_list('ficha_id', flat=True)
            
            queryset = queryset.filter(
                Q(ficha__in=fichas_activas) &
                Q(visible_para_aprendices=True) &
                Q(estado__in=['PUBLICADA', 'EN_PROGRESO'])
            )
        else:
            # Administradores ven todas
            pass

        # Filtros opcionales
        ficha_id = self.request.query_params.get('ficha')
        if ficha_id:
            queryset = queryset.filter(ficha_id=ficha_id)

        resultado_id = self.request.query_params.get('resultado_aprendizaje')
        if resultado_id:
            queryset = queryset.filter(resultado_aprendizaje_id=resultado_id)

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        tipo_actividad = self.request.query_params.get('tipo_actividad')
        if tipo_actividad:
            queryset = queryset.filter(tipo_actividad_id=tipo_actividad)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ActividadCreateUpdateSerializer
        return ActividadListSerializer

    def perform_create(self, serializer):
        # Asignar automáticamente el instructor actual
        serializer.save(instructor=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter('ficha', OpenApiTypes.INT, description='ID de la ficha'),
            OpenApiParameter('resultado_aprendizaje', OpenApiTypes.INT, description='ID del resultado de aprendizaje'),
            OpenApiParameter('estado', OpenApiTypes.STR, description='Estado de la actividad'),
            OpenApiParameter('tipo_actividad', OpenApiTypes.INT, description='ID del tipo de actividad'),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ActividadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Detalle, actualización y eliminación de actividades.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        queryset = Actividad.objects.select_related(
            'tipo_actividad', 'instructor', 'ficha', 'resultado_aprendizaje'
        ).prefetch_related('archivos').annotate(
            total_entregas=Count('entregas'),
            entregas_pendientes=Count('entregas', filter=Q(entregas__estado='BORRADOR'))
        )

        if user.rol.nombre == 'INSTRUCTOR':
            # Instructores solo pueden ver/editar sus actividades
            return queryset.filter(instructor=user)
        elif user.rol.nombre == 'APRENDIZ':
            # Aprendices solo pueden ver actividades visibles de sus fichas
            fichas_activas = Matricula.objects.filter(
                aprendiz=user, estado='ACTIVO'
            ).values_list('ficha_id', flat=True)
            
            return queryset.filter(
                Q(ficha__in=fichas_activas) &
                Q(visible_para_aprendices=True)
            )
        else:
            # Administradores pueden ver todas
            return queryset

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ActividadCreateUpdateSerializer
        return ActividadDetailSerializer


# ================================
# VISTAS PARA ENTREGAS
# ================================

class EntregaActividadListCreateView(generics.ListCreateAPIView):
    """
    Lista entregas de actividades y permite crear nuevas entregas.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        queryset = EntregaActividad.objects.select_related(
            'actividad', 'aprendiz'
        ).prefetch_related('archivos')

        if user.rol.nombre == 'INSTRUCTOR':
            # Instructores ven entregas de sus actividades
            queryset = queryset.filter(actividad__instructor=user)
        elif user.rol.nombre == 'APRENDIZ':
            # Aprendices ven solo sus entregas
            queryset = queryset.filter(aprendiz=user)
        else:
            # Administradores ven todas
            pass

        # Filtros opcionales
        actividad_id = self.request.query_params.get('actividad')
        if actividad_id:
            queryset = queryset.filter(actividad_id=actividad_id)

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.order_by('-fecha_entrega')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EntregaActividadCreateUpdateSerializer
        return EntregaActividadListSerializer

    def perform_create(self, serializer):
        # Asignar automáticamente el aprendiz actual
        serializer.save(aprendiz=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter('actividad', OpenApiTypes.INT, description='ID de la actividad'),
            OpenApiParameter('estado', OpenApiTypes.STR, description='Estado de la entrega'),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class EntregaActividadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Detalle, actualización y eliminación de entregas.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        queryset = EntregaActividad.objects.select_related(
            'actividad', 'aprendiz'
        ).prefetch_related('archivos')

        if user.rol.nombre == 'INSTRUCTOR':
            # Instructores pueden ver entregas de sus actividades
            return queryset.filter(actividad__instructor=user)
        elif user.rol.nombre == 'APRENDIZ':
            # Aprendices solo pueden ver/editar sus entregas
            return queryset.filter(aprendiz=user)
        else:
            # Administradores pueden ver todas
            return queryset

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EntregaActividadCreateUpdateSerializer
        return EntregaActividadDetailSerializer


# ================================
# VISTAS PARA CALIFICACIONES
# ================================

class CalificacionActividadListCreateView(generics.ListCreateAPIView):
    """
    Lista calificaciones y permite crear nuevas calificaciones.
    Solo instructores pueden calificar.
    """
    serializer_class = CalificacionActividadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = CalificacionActividad.objects.select_related(
            'entrega__actividad', 'entrega__aprendiz', 'instructor'
        )

        if user.rol.nombre == 'INSTRUCTOR':
            # Instructores ven calificaciones de sus actividades
            queryset = queryset.filter(entrega__actividad__instructor=user)
        elif user.rol.nombre == 'APRENDIZ':
            # Aprendices ven sus calificaciones
            queryset = queryset.filter(entrega__aprendiz=user)
        else:
            # Administradores ven todas
            pass

        # Filtros opcionales
        actividad_id = self.request.query_params.get('actividad')
        if actividad_id:
            queryset = queryset.filter(entrega__actividad_id=actividad_id)

        aprendiz_id = self.request.query_params.get('aprendiz')
        if aprendiz_id:
            queryset = queryset.filter(entrega__aprendiz_id=aprendiz_id)

        return queryset.order_by('-fecha_calificacion')

    def perform_create(self, serializer):
        # Solo instructores pueden calificar
        if self.request.user.rol.nombre != 'INSTRUCTOR':
            raise permissions.PermissionDenied("Solo los instructores pueden calificar.")
        serializer.save(instructor=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter('actividad', OpenApiTypes.INT, description='ID de la actividad'),
            OpenApiParameter('aprendiz', OpenApiTypes.INT, description='ID del aprendiz'),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CalificacionActividadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Detalle, actualización y eliminación de calificaciones.
    """
    serializer_class = CalificacionActividadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = CalificacionActividad.objects.select_related(
            'entrega__actividad', 'entrega__aprendiz', 'instructor'
        )

        if user.rol.nombre == 'INSTRUCTOR':
            # Instructores pueden ver/editar calificaciones de sus actividades
            return queryset.filter(entrega__actividad__instructor=user)
        elif user.rol.nombre == 'APRENDIZ':
            # Aprendices solo pueden ver sus calificaciones
            return queryset.filter(entrega__aprendiz=user)
        else:
            # Administradores pueden ver todas
            return queryset

    def update(self, request, *args, **kwargs):
        # Solo instructores pueden actualizar calificaciones
        if request.user.rol.nombre != 'INSTRUCTOR':
            raise permissions.PermissionDenied("Solo los instructores pueden modificar calificaciones.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Solo instructores pueden eliminar calificaciones
        if request.user.rol.nombre != 'INSTRUCTOR':
            raise permissions.PermissionDenied("Solo los instructores pueden eliminar calificaciones.")
        return super().destroy(request, *args, **kwargs)


# ================================
# VISTAS ESPECIALES
# ================================

@extend_schema(
    description="Obtiene las actividades pendientes para un aprendiz específico",
    parameters=[
        OpenApiParameter('aprendiz_id', OpenApiTypes.INT, description='ID del aprendiz', required=True),
    ]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def actividades_pendientes_aprendiz(request, aprendiz_id):
    """
    Obtiene las actividades pendientes para un aprendiz específico.
    """
    user = request.user
    
    # Verificar permisos
    if user.rol.nombre == 'APRENDIZ' and user.id != aprendiz_id:
        return Response(
            {"error": "No tienes permisos para ver las actividades de otro aprendiz."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        aprendiz = Usuario.objects.get(id=aprendiz_id, rol__nombre='APRENDIZ')
    except Usuario.DoesNotExist:
        return Response(
            {"error": "Aprendiz no encontrado."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Obtener fichas activas del aprendiz
    fichas_activas = Matricula.objects.filter(
        aprendiz=aprendiz, estado='ACTIVO'
    ).values_list('ficha_id', flat=True)
    
    # Obtener actividades pendientes
    actividades_pendientes = Actividad.objects.filter(
        Q(ficha__in=fichas_activas) &
        Q(visible_para_aprendices=True) &
        Q(estado__in=['PUBLICADA', 'EN_PROGRESO']) &
        Q(fecha_entrega__gte=timezone.now().date())
    ).exclude(
        entregas__aprendiz=aprendiz
    ).select_related(
        'tipo_actividad', 'instructor', 'ficha', 'resultado_aprendizaje'
    ).annotate(
        total_entregas=Count('entregas'),
        entregas_pendientes=Count('entregas', filter=Q(entregas__estado='BORRADOR'))
    )
    
    serializer = ActividadListSerializer(actividades_pendientes, many=True)
    return Response(serializer.data)


@extend_schema(
    description="Obtiene el progreso de un aprendiz en todas sus actividades",
    parameters=[
        OpenApiParameter('aprendiz_id', OpenApiTypes.INT, description='ID del aprendiz', required=True),
    ]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def progreso_aprendiz(request, aprendiz_id):
    """
    Obtiene el progreso de un aprendiz en todas sus actividades.
    """
    user = request.user
    
    # Verificar permisos
    if user.rol.nombre == 'APRENDIZ' and user.id != aprendiz_id:
        return Response(
            {"error": "No tienes permisos para ver el progreso de otro aprendiz."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        aprendiz = Usuario.objects.get(id=aprendiz_id, rol__nombre='APRENDIZ')
    except Usuario.DoesNotExist:
        return Response(
            {"error": "Aprendiz no encontrado."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Obtener fichas activas del aprendiz
    fichas_activas = Matricula.objects.filter(
        aprendiz=aprendiz, estado='ACTIVO'
    ).values_list('ficha_id', flat=True)
    
    # Obtener estadísticas de entregas
    entregas = EntregaActividad.objects.filter(
        aprendiz=aprendiz,
        actividad__ficha__in=fichas_activas
    ).select_related('actividad', 'calificacion')
    
    # Calcular estadísticas
    total_entregas = entregas.count()
    entregas_calificadas = entregas.filter(calificacion__isnull=False).count()
    entregas_aprobadas = entregas.filter(calificacion__aprobada=True).count()
    
    # Promedio de calificaciones
    promedio_calificaciones = entregas.filter(
        calificacion__isnull=False
    ).aggregate(
        promedio=Avg('calificacion__puntaje_obtenido')
    )['promedio'] or 0
    
    # Actividades por resultado de aprendizaje
    actividades_por_resultado = {}
    for entrega in entregas:
        resultado = entrega.actividad.resultado_aprendizaje.nombre
        if resultado not in actividades_por_resultado:
            actividades_por_resultado[resultado] = {
                'total': 0,
                'entregadas': 0,
                'calificadas': 0,
                'aprobadas': 0,
                'promedio': 0
            }
        
        actividades_por_resultado[resultado]['total'] += 1
        actividades_por_resultado[resultado]['entregadas'] += 1
        
        if hasattr(entrega, 'calificacion') and entrega.calificacion:
            actividades_por_resultado[resultado]['calificadas'] += 1
            if entrega.calificacion.aprobada:
                actividades_por_resultado[resultado]['aprobadas'] += 1
    
    # Calcular promedios por resultado
    for resultado_data in actividades_por_resultado.values():
        if resultado_data['calificadas'] > 0:
            calificaciones_resultado = entregas.filter(
                actividad__resultado_aprendizaje__nombre=resultado,
                calificacion__isnull=False
            ).aggregate(
                promedio=Avg('calificacion__puntaje_obtenido')
            )['promedio'] or 0
            resultado_data['promedio'] = round(calificaciones_resultado, 2)
    
    data = {
        'aprendiz': {
            'id': aprendiz.id,
            'nombre_completo': aprendiz.nombre_completo,
            'documento': aprendiz.documento,
            'email': aprendiz.email
        },
        'estadisticas_generales': {
            'total_entregas': total_entregas,
            'entregas_calificadas': entregas_calificadas,
            'entregas_aprobadas': entregas_aprobadas,
            'promedio_general': round(promedio_calificaciones, 2),
            'porcentaje_aprobacion': round((entregas_aprobadas / entregas_calificadas * 100) if entregas_calificadas > 0 else 0, 2)
        },
        'progreso_por_resultado': actividades_por_resultado
    }
    
    return Response(data)


@extend_schema(
    description="Obtiene las actividades de una ficha específica",
    parameters=[
        OpenApiParameter('ficha_id', OpenApiTypes.INT, description='ID de la ficha', required=True),
        OpenApiParameter('resultado_aprendizaje', OpenApiTypes.INT, description='ID del resultado de aprendizaje'),
    ]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def actividades_por_ficha(request, ficha_id):
    """
    Obtiene las actividades de una ficha específica.
    """
    user = request.user
    
    try:
        ficha = Ficha.objects.get(id=ficha_id)
    except Ficha.DoesNotExist:
        return Response(
            {"error": "Ficha no encontrada."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verificar permisos
    if user.rol.nombre == 'APRENDIZ':
        # Verificar que el aprendiz esté matriculado en la ficha
        if not Matricula.objects.filter(
            aprendiz=user, ficha=ficha, estado='ACTIVO'
        ).exists():
            return Response(
                {"error": "No tienes acceso a las actividades de esta ficha."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Filtrar actividades
    queryset = Actividad.objects.filter(ficha=ficha)
    
    if user.rol.nombre == 'APRENDIZ':
        queryset = queryset.filter(
            visible_para_aprendices=True,
            estado__in=['PUBLICADA', 'EN_PROGRESO']
        )
    elif user.rol.nombre == 'INSTRUCTOR':
        # Instructores solo ven sus actividades en la ficha
        queryset = queryset.filter(instructor=user)
    
    # Filtro opcional por resultado de aprendizaje
    resultado_id = request.query_params.get('resultado_aprendizaje')
    if resultado_id:
        queryset = queryset.filter(resultado_aprendizaje_id=resultado_id)
    
    queryset = queryset.select_related(
        'tipo_actividad', 'instructor', 'resultado_aprendizaje'
    ).annotate(
        total_entregas=Count('entregas'),
        entregas_pendientes=Count('entregas', filter=Q(entregas__estado='BORRADOR'))
    ).order_by('-created_at')
    
    serializer = ActividadListSerializer(queryset, many=True)
    return Response(serializer.data)