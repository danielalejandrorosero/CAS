from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import RegistroUsuarioView, UsuarioUpdateView, EliminarUsuarioView, ListarUsuariosView, SolicitarRecuperacionView, RecuperarPasswordView

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('actualizar/<int:pk>/', UsuarioUpdateView.as_view(), name='actualizar_usuario'),
    path('eliminar/<int:pk>/', EliminarUsuarioView.as_view(), name='eliminar_usuario'),
    path('listar/', ListarUsuariosView.as_view(), name='listar_usuarios'),
    path('solicitar-recuperacion/', SolicitarRecuperacionView.as_view(), name='solicitar_recuperacion'),
    path('recuperar-password/', RecuperarPasswordView.as_view(), name='recuperar_password'),
]
