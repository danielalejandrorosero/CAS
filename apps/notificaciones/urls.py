from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    # Tipos de notificaciones
    path('tipos/', views.TipoNotificacionListView.as_view(), name='tipos-list'),
    
    # Notificaciones del usuario
    path('', views.NotificacionListView.as_view(), name='notificaciones-list'),
    path('<int:pk>/', views.NotificacionDetailView.as_view(), name='notificacion-detail'),
    path('crear/', views.NotificacionCreateView.as_view(), name='notificacion-create'),
    
    # Resumen y estadísticas
    path('resumen/', views.resumen_notificaciones, name='resumen'),
    path('no-leidas/', views.notificaciones_no_leidas, name='no-leidas'),
    
    # Acciones sobre notificaciones
    path('marcar-leidas/', views.marcar_como_leidas, name='marcar-leidas'),
    path('marcar-todas-leidas/', views.marcar_todas_como_leidas, name='marcar-todas-leidas'),
    path('<int:pk>/eliminar/', views.eliminar_notificacion, name='eliminar'),
    
    # Configuración de notificaciones
    path('configuracion/', views.ConfiguracionNotificacionView.as_view(), name='configuracion'),
    
    # Historial (para administradores)
    path('historial/', views.HistorialNotificacionListView.as_view(), name='historial'),
    
    # Envío personalizado (para instructores/administradores)
    path('enviar/', views.enviar_notificacion_personalizada, name='enviar-personalizada'),
]