from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CitacionComiteViewSet,
    CitacionAprendizViewSet,
    ArchivoAdjuntoCitacionViewSet,
    SeguimientoCitacionViewSet
)

# Router para las APIs
router = DefaultRouter()

# Registro de ViewSets
router.register(
    r'citaciones', 
    CitacionComiteViewSet, 
    basename='citacion-comite'
)

router.register(
    r'mis-citaciones', 
    CitacionAprendizViewSet, 
    basename='citacion-aprendiz'
)

router.register(
    r'archivos', 
    ArchivoAdjuntoCitacionViewSet, 
    basename='archivo-citacion'
)

router.register(
    r'seguimientos', 
    SeguimientoCitacionViewSet, 
    basename='seguimiento-citacion'
)

app_name = 'comite'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # URLs adicionales si se necesitan
    # path('reportes/', views.reportes_citaciones, name='reportes-citaciones'),
]

# URLs disponibles:
# 
# CITACIONES (Instructores/Admin):
# GET    /api/comite/api/citaciones/                    - Listar citaciones
# POST   /api/comite/api/citaciones/                    - Crear citación
# GET    /api/comite/api/citaciones/{id}/               - Detalle de citación
# PUT    /api/comite/api/citaciones/{id}/               - Actualizar citación
# PATCH  /api/comite/api/citaciones/{id}/               - Actualizar parcial
# DELETE /api/comite/api/citaciones/{id}/               - Eliminar citación
# POST   /api/comite/api/citaciones/{id}/cambiar_estado/ - Cambiar estado
# GET    /api/comite/api/citaciones/mis_citaciones/      - Citaciones del instructor
# GET    /api/comite/api/citaciones/pendientes/          - Citaciones pendientes
# GET    /api/comite/api/citaciones/vencidas/            - Citaciones vencidas
# GET    /api/comite/api/citaciones/estadisticas/        - Estadísticas
#
# CONSULTA APRENDICES:
# GET    /api/comite/api/mis-citaciones/                 - Citaciones del aprendiz
# GET    /api/comite/api/mis-citaciones/{id}/            - Detalle de citación
# GET    /api/comite/api/mis-citaciones/pendientes/      - Citaciones pendientes
# GET    /api/comite/api/mis-citaciones/proximas/        - Citaciones próximas
#
# ARCHIVOS ADJUNTOS:
# GET    /api/comite/api/archivos/                       - Listar archivos
# POST   /api/comite/api/archivos/                       - Subir archivo
# GET    /api/comite/api/archivos/{id}/                  - Detalle de archivo
# DELETE /api/comite/api/archivos/{id}/                  - Eliminar archivo
#
# SEGUIMIENTOS:
# GET    /api/comite/api/seguimientos/                   - Listar seguimientos
# POST   /api/comite/api/seguimientos/                   - Crear seguimiento
# GET    /api/comite/api/seguimientos/{id}/              - Detalle de seguimiento
# PUT    /api/comite/api/seguimientos/{id}/              - Actualizar seguimiento
# PATCH  /api/comite/api/seguimientos/{id}/              - Actualizar parcial
# DELETE /api/comite/api/seguimientos/{id}/              - Eliminar seguimiento
# GET    /api/comite/api/seguimientos/pendientes/        - Seguimientos pendientes