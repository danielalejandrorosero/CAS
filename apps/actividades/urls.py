from django.urls import path
from .views import (
    # Tipos de actividad
    TipoActividadListView,
    
    # Actividades
    ActividadListCreateView,
    ActividadDetailView,
    
    # Entregas
    EntregaActividadListCreateView,
    EntregaActividadDetailView,
    
    # Calificaciones
    CalificacionActividadListCreateView,
    CalificacionActividadDetailView,
    
    # Vistas especiales
    actividades_pendientes_aprendiz,
    progreso_aprendiz,
    actividades_por_ficha,
)

urlpatterns = [
    # ================================
    # TIPOS DE ACTIVIDAD
    # ================================
    path('tipos/', TipoActividadListView.as_view(), name='tipos_actividad_list'),
    
    # ================================
    # ACTIVIDADES
    # ================================
    path('', ActividadListCreateView.as_view(), name='actividades_list_create'),
    path('<int:pk>/', ActividadDetailView.as_view(), name='actividad_detail'),
    
    # ================================
    # ENTREGAS
    # ================================
    path('entregas/', EntregaActividadListCreateView.as_view(), name='entregas_list_create'),
    path('entregas/<int:pk>/', EntregaActividadDetailView.as_view(), name='entrega_detail'),
    
    # ================================
    # CALIFICACIONES
    # ================================
    path('calificaciones/', CalificacionActividadListCreateView.as_view(), name='calificaciones_list_create'),
    path('calificaciones/<int:pk>/', CalificacionActividadDetailView.as_view(), name='calificacion_detail'),
    
    # ================================
    # VISTAS ESPECIALES
    # ================================
    path('pendientes/<int:aprendiz_id>/', actividades_pendientes_aprendiz, name='actividades_pendientes'),
    path('progreso/<int:aprendiz_id>/', progreso_aprendiz, name='progreso_aprendiz'),
    path('ficha/<int:ficha_id>/', actividades_por_ficha, name='actividades_por_ficha'),
]