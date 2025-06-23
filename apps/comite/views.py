from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import CitacionComite, ArchivoAdjuntoCitacion, SeguimientoCitacion
from .serializers import (
    CitacionComiteListSerializer,
    CitacionComiteDetailSerializer,
    CitacionComiteCreateUpdateSerializer,
    CitacionComiteEstadoSerializer,
    CitacionAprendizSerializer,
    ArchivoAdjuntoCitacionSerializer,
    SeguimientoCitacionSerializer
)
from apps.usuarios.models import Usuario
from apps.asistencia.models import Ficha, AsignacionInstructor
from apps.usuarios.views import IsAdminOrInstructor, IsAprendiz


class CitacionComiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de citaciones a comité
    
    Endpoints:
    - GET /api/comite/citaciones/ - Listar citaciones (instructores/admin)
    - POST /api/comite/citaciones/ - Crear citación (instructores)
    - GET /api/comite/citaciones/{id}/ - Detalle de citación
    - PUT/PATCH /api/comite/citaciones/{id}/ - Actualizar citación
    - DELETE /api/comite/citaciones/{id}/ - Eliminar citación
    - POST /api/comite/citaciones/{id}/cambiar_estado/ - Cambiar estado
    - GET /api/comite/citaciones/mis_citaciones/ - Citaciones del instructor
    - GET /api/comite/citaciones/pendientes/ - Citaciones pendientes
    - GET /api/comite/citaciones/vencidas/ - Citaciones vencidas
    - GET /api/comite/citaciones/estadisticas/ - Estadísticas de citaciones
    """
    
    queryset = CitacionComite.objects.select_related(
        'aprendiz', 'instructor_citante', 'ficha', 'resultado_aprendizaje'
    ).prefetch_related(
        'archivos_adjuntos', 'seguimientos'
    ).filter(activo=True)
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Filtros disponibles
    filterset_fields = {
        'estado': ['exact', 'in'],
        'motivo': ['exact', 'in'],
        'prioridad': ['exact', 'in'],
        'fecha_creacion': ['gte', 'lte', 'exact'],
        'fecha_citacion': ['gte', 'lte', 'exact'],
        'ficha': ['exact'],
        'instructor_citante': ['exact'],
        'requiere_seguimiento': ['exact']
    }
    
    # Campos de búsqueda
    search_fields = [
        'numero_citacion',
        'aprendiz__documento',
        'aprendiz__nombres',
        'aprendiz__apellidos',
        'motivo_detallado',
        'observaciones_instructor'
    ]
    
    # Ordenamiento
    ordering_fields = [
        'fecha_creacion', 'fecha_citacion', 'prioridad', 'estado'
    ]
    ordering = ['-fecha_creacion']
    
    def get_serializer_class(self):
        """Selecciona el serializer según la acción"""
        if self.action == 'list':
            return CitacionComiteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CitacionComiteCreateUpdateSerializer
        elif self.action == 'cambiar_estado':
            return CitacionComiteEstadoSerializer
        return CitacionComiteDetailSerializer
    
    def get_permissions(self):
        """Permisos según la acción"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrInstructor]
        elif self.action in ['cambiar_estado', 'estadisticas']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrInstructor]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtra citaciones según el rol del usuario"""
        user = self.request.user
        queryset = self.queryset
        
        if user.rol == 'ADMINISTRADOR':
            # Administradores ven todas las citaciones
            return queryset
        elif user.rol == 'INSTRUCTOR':
            # Instructores ven citaciones de sus fichas
            fichas_instructor = AsignacionInstructor.objects.filter(
                instructor=user, activo=True
            ).values_list('resultado_aprendizaje__ficha', flat=True)
            
            return queryset.filter(
                Q(instructor_citante=user) | Q(ficha__in=fichas_instructor)
            )
        else:
            # Aprendices no pueden acceder a este endpoint
            return queryset.none()
    
    def perform_create(self, serializer):
        """Asigna el instructor citante al crear"""
        serializer.save(instructor_citante=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Cambiar estado de la citación"""
        citacion = self.get_object()
        serializer = CitacionComiteEstadoSerializer(
            citacion, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            # Actualizar fechas según el estado
            estado = serializer.validated_data.get('estado')
            if estado == 'NOTIFICADA' and not citacion.fecha_notificacion:
                serializer.save(fecha_notificacion=timezone.now())
            elif estado == 'REALIZADA' and not citacion.fecha_realizacion:
                serializer.save(fecha_realizacion=timezone.now())
            else:
                serializer.save()
            
            return Response({
                'message': f'Estado cambiado a {estado}',
                'citacion': CitacionComiteDetailSerializer(citacion).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def mis_citaciones(self, request):
        """Citaciones creadas por el instructor actual"""
        if request.user.rol != 'INSTRUCTOR':
            return Response(
                {'error': 'Solo instructores pueden acceder a este endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        citaciones = self.get_queryset().filter(instructor_citante=request.user)
        
        # Aplicar filtros y búsqueda
        citaciones = self.filter_queryset(citaciones)
        
        page = self.paginate_queryset(citaciones)
        if page is not None:
            serializer = CitacionComiteListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CitacionComiteListSerializer(citaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Citaciones pendientes de notificar"""
        citaciones = self.get_queryset().filter(
            estado__in=['PENDIENTE', 'NOTIFICADA']
        )
        
        # Aplicar filtros
        citaciones = self.filter_queryset(citaciones)
        
        page = self.paginate_queryset(citaciones)
        if page is not None:
            serializer = CitacionComiteListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CitacionComiteListSerializer(citaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """Citaciones vencidas (fecha de citación pasada y no realizadas)"""
        citaciones = self.get_queryset().filter(
            fecha_citacion__lt=timezone.now(),
            estado__in=['PENDIENTE', 'NOTIFICADA']
        )
        
        # Aplicar filtros
        citaciones = self.filter_queryset(citaciones)
        
        page = self.paginate_queryset(citaciones)
        if page is not None:
            serializer = CitacionComiteListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CitacionComiteListSerializer(citaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de citaciones"""
        queryset = self.get_queryset()
        
        # Estadísticas generales
        total_citaciones = queryset.count()
        pendientes = queryset.filter(estado='PENDIENTE').count()
        notificadas = queryset.filter(estado='NOTIFICADA').count()
        realizadas = queryset.filter(estado='REALIZADA').count()
        canceladas = queryset.filter(estado='CANCELADA').count()
        vencidas = queryset.filter(
            fecha_citacion__lt=timezone.now(),
            estado__in=['PENDIENTE', 'NOTIFICADA']
        ).count()
        
        # Estadísticas por motivo
        por_motivo = queryset.values('motivo').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Estadísticas por prioridad
        por_prioridad = queryset.values('prioridad').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Estadísticas por instructor
        por_instructor = queryset.values(
            'instructor_citante__nombres',
            'instructor_citante__apellidos'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        return Response({
            'resumen': {
                'total_citaciones': total_citaciones,
                'pendientes': pendientes,
                'notificadas': notificadas,
                'realizadas': realizadas,
                'canceladas': canceladas,
                'vencidas': vencidas
            },
            'por_motivo': list(por_motivo),
            'por_prioridad': list(por_prioridad),
            'por_instructor': list(por_instructor)
        })


class CitacionAprendizViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para que los aprendices consulten sus citaciones
    
    Endpoints:
    - GET /api/comite/mis-citaciones/ - Citaciones del aprendiz
    - GET /api/comite/mis-citaciones/{id}/ - Detalle de citación
    - GET /api/comite/mis-citaciones/pendientes/ - Citaciones pendientes
    - GET /api/comite/mis-citaciones/proximas/ - Citaciones próximas
    """
    
    serializer_class = CitacionAprendizSerializer
    permission_classes = [permissions.IsAuthenticated, IsAprendiz]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    filterset_fields = {
        'estado': ['exact', 'in'],
        'motivo': ['exact', 'in'],
        'prioridad': ['exact', 'in'],
        'fecha_creacion': ['gte', 'lte'],
        'fecha_citacion': ['gte', 'lte']
    }
    
    ordering_fields = ['fecha_creacion', 'fecha_citacion', 'prioridad']
    ordering = ['-fecha_creacion']
    
    def get_queryset(self):
        """Solo citaciones del aprendiz actual"""
        return CitacionComite.objects.select_related(
            'instructor_citante', 'ficha', 'resultado_aprendizaje'
        ).filter(
            aprendiz=self.request.user,
            activo=True
        )
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Citaciones pendientes del aprendiz"""
        citaciones = self.get_queryset().filter(
            estado__in=['PENDIENTE', 'NOTIFICADA']
        )
        
        serializer = self.get_serializer(citaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def proximas(self, request):
        """Citaciones próximas (en los próximos 7 días)"""
        fecha_limite = timezone.now() + timezone.timedelta(days=7)
        
        citaciones = self.get_queryset().filter(
            fecha_citacion__gte=timezone.now(),
            fecha_citacion__lte=fecha_limite,
            estado__in=['PENDIENTE', 'NOTIFICADA']
        ).order_by('fecha_citacion')
        
        serializer = self.get_serializer(citaciones, many=True)
        return Response(serializer.data)


class ArchivoAdjuntoCitacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de archivos adjuntos de citaciones
    
    Endpoints:
    - GET /api/comite/archivos/ - Listar archivos
    - POST /api/comite/archivos/ - Subir archivo
    - GET /api/comite/archivos/{id}/ - Detalle de archivo
    - DELETE /api/comite/archivos/{id}/ - Eliminar archivo
    """
    
    serializer_class = ArchivoAdjuntoCitacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Archivos según permisos del usuario"""
        user = self.request.user
        
        if user.rol == 'ADMINISTRADOR':
            return ArchivoAdjuntoCitacion.objects.all()
        elif user.rol == 'INSTRUCTOR':
            # Archivos de citaciones donde el instructor tiene acceso
            fichas_instructor = AsignacionInstructor.objects.filter(
                instructor=user, activo=True
            ).values_list('resultado_aprendizaje__ficha', flat=True)
            
            return ArchivoAdjuntoCitacion.objects.filter(
                Q(citacion__instructor_citante=user) |
                Q(citacion__ficha__in=fichas_instructor)
            )
        else:
            # Aprendices ven archivos de sus citaciones
            return ArchivoAdjuntoCitacion.objects.filter(
                citacion__aprendiz=user
            )
    
    def perform_create(self, serializer):
        """Asigna el usuario que sube el archivo"""
        serializer.save(subido_por=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Solo el que subió el archivo o admin puede eliminarlo"""
        archivo = self.get_object()
        
        if (request.user != archivo.subido_por and 
            request.user.rol != 'ADMINISTRADOR'):
            return Response(
                {'error': 'No tiene permisos para eliminar este archivo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


class SeguimientoCitacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de seguimientos de citaciones
    
    Endpoints:
    - GET /api/comite/seguimientos/ - Listar seguimientos
    - POST /api/comite/seguimientos/ - Crear seguimiento
    - GET /api/comite/seguimientos/{id}/ - Detalle de seguimiento
    - PUT/PATCH /api/comite/seguimientos/{id}/ - Actualizar seguimiento
    - DELETE /api/comite/seguimientos/{id}/ - Eliminar seguimiento
    - GET /api/comite/seguimientos/pendientes/ - Seguimientos pendientes
    """
    
    serializer_class = SeguimientoCitacionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrInstructor]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    filterset_fields = {
        'citacion': ['exact'],
        'tipo_seguimiento': ['exact', 'in'],
        'resultado': ['exact', 'in'],
        'fecha_seguimiento': ['gte', 'lte'],
        'requiere_nuevo_seguimiento': ['exact']
    }
    
    ordering_fields = ['fecha_seguimiento', 'created_at']
    ordering = ['-fecha_seguimiento']
    
    def get_queryset(self):
        """Seguimientos según permisos del usuario"""
        user = self.request.user
        
        if user.rol == 'ADMINISTRADOR':
            return SeguimientoCitacion.objects.select_related(
                'citacion', 'instructor_seguimiento'
            ).all()
        elif user.rol == 'INSTRUCTOR':
            # Seguimientos de citaciones donde el instructor tiene acceso
            fichas_instructor = AsignacionInstructor.objects.filter(
                instructor=user, activo=True
            ).values_list('resultado_aprendizaje__ficha', flat=True)
            
            return SeguimientoCitacion.objects.select_related(
                'citacion', 'instructor_seguimiento'
            ).filter(
                Q(instructor_seguimiento=user) |
                Q(citacion__instructor_citante=user) |
                Q(citacion__ficha__in=fichas_instructor)
            )
        else:
            return SeguimientoCitacion.objects.none()
    
    def perform_create(self, serializer):
        """Asigna el instructor que hace el seguimiento"""
        serializer.save(instructor_seguimiento=self.request.user)
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Seguimientos pendientes (fecha de próximo seguimiento llegada)"""
        seguimientos = self.get_queryset().filter(
            requiere_nuevo_seguimiento=True,
            fecha_proximo_seguimiento__lte=timezone.now().date()
        )
        
        serializer = self.get_serializer(seguimientos, many=True)
        return Response(serializer.data)
