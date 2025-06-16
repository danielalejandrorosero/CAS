from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, BasePermission, AllowAny
import os
from django.core.mail import send_mail
from .serializers import *
from .models import *


class IsAdminOrInstructor(BasePermission):
    """
    Permite acceso solo a usuarios con rol ADMINISTRADOR o INSTRUCTOR.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Verificar si el usuario tiene rol de administrador o instructor
        return request.user.es_administrador or request.user.es_instructor


class IsAprendiz(BasePermission):
    """
    Permite acceso solo a usuarios con rol APRENDIZ.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.es_aprendiz


class IsOwnerOrAdminOrInstructor(BasePermission):
    """
    Permite acceso al propietario del recurso, administradores o instructores.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return True  # Permitir acceso autenticado, verificar objeto específico en has_object_permission

    def has_object_permission(self, request, view, obj):
        # El usuario puede acceder a su propio perfil o ser admin/instructor
        return (obj == request.user or
                request.user.es_administrador or
                request.user.es_instructor)


class RegistroUsuarioView(APIView):
    # Solo admins e instructores pueden registrar nuevos usuarios
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    """
    Endpoint para registrar nuevos usuarios.
    Asigna el rol 'APRENDIZ' por defecto si no se especifica.
    """

    @extend_schema(
        request=UsuarioCreateSerializer,
        responses={201: UsuarioCreateSerializer}
    )
    def post(self, request, *args, **kwargs):
        data = request.data.copy()

        # Si no se especifica rol, asignar APRENDIZ por defecto
        if not data.get('rol'):
            try:
                rol_aprendiz = Rol.objects.get(nombre='APRENDIZ')
                data['rol'] = rol_aprendiz.id
            except Rol.DoesNotExist:
                return Response(
                    {"error": "El rol 'APRENDIZ' no existe."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = UsuarioCreateSerializer(data=data)
        if serializer.is_valid():
            usuario = serializer.save()

            # Si el rol es ADMINISTRADOR, establecer is_staff y is_superuser
            if usuario.es_administrador:
                usuario.is_staff = True
                usuario.is_superuser = True
                usuario.save(update_fields=['is_staff', 'is_superuser'])

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UsuarioDashboardSerializer}
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        data = {
            'nombre_completo': user.nombre_completo,
            'rol': user.rol.nombre,
            'foto_perfil_url': user.foto_perfil.url if user.foto_perfil else None,
            'ultimo_acceso': user.ultimo_acceso,
            'email': user.email,
        }
        if user.es_administrador:
            data.update({
                'total_usuarios': Usuario.objects.count(),
                'total_aprendices': Usuario.objects.filter(rol__nombre='APRENDIZ').count(),
                'total_instructores': Usuario.objects.filter(rol__nombre='INSTRUCTOR').count(),
                'total_activos': Usuario.objects.filter(activo=True).count(),
                'total_inactivos': Usuario.objects.filter(activo=False).count(),
                'ultimos_usuarios': UsuarioSerializer(Usuario.objects.order_by('-fecha_registro')[:10], many=True).data,
                # Puedes agregar aquí logs, estadísticas, solicitudes recientes, etc.
            })
        elif user.es_instructor:
            data.update({
                'total_aprendices': Usuario.objects.filter(rol__nombre='APRENDIZ').count(),
                'aprendices': UsuarioSerializer(Usuario.objects.filter(rol__nombre='APRENDIZ'), many=True).data,
                # Puedes agregar progreso, actividades, mensajes, etc.
            })
        elif user.es_aprendiz:
            data.update({
                'progreso': 'En desarrollo',
                'ultimas_actividades': [],
                # Puedes agregar materiales, tareas, notificaciones, etc.
            })
        return Response(data, status=status.HTTP_200_OK)


class UsuarioUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdminOrInstructor]

    @extend_schema(
        request=UsuarioUpdateSerializer,
        responses={200: UsuarioUpdateSerializer}
    )
    def put(self, request, pk, *args, **kwargs):
        try:
            usuario = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Verificar permisos a nivel de objeto
        if not (usuario == request.user or request.user.es_administrador or request.user.es_instructor):
            return Response(
                {'error': 'No tienes permisos para actualizar este usuario.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UsuarioUpdateSerializer(usuario, data=request.data, partial=True)
        if serializer.is_valid():
            usuario_actualizado = serializer.save()

            # Si se cambió el rol a ADMINISTRADOR, actualizar is_staff y is_superuser
            if 'rol' in request.data:
                if usuario_actualizado.es_administrador:
                    usuario_actualizado.is_staff = True
                    usuario_actualizado.is_superuser = True
                    usuario_actualizado.save(update_fields=['is_staff', 'is_superuser'])
                else:
                    # Si ya no es administrador, quitar privilegios
                    usuario_actualizado.is_staff = False
                    usuario_actualizado.is_superuser = False
                    usuario_actualizado.save(update_fields=['is_staff', 'is_superuser'])

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=UsuarioUpdateSerializer,
        responses={200: UsuarioUpdateSerializer}
    )
    def patch(self, request, pk, *args, **kwargs):
        # Usar la misma lógica que PUT pero con partial=True por defecto
        return self.put(request, pk, *args, **kwargs)


class EliminarUsuarioView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    @extend_schema(
        responses={204: None}
    )
    def delete(self, request, pk, *args, **kwargs):
        try:
            usuario = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Evitar que se elimine a sí mismo
        if usuario == request.user:
            return Response(
                {'error': 'No puedes eliminar tu propio usuario.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListarUsuariosView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]  # Corregido: era "permision_classes"

    @extend_schema(
        responses={200: UsuarioListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        usuarios = Usuario.objects.all().select_related('rol')  # Optimización con select_related
        serializer = UsuarioListSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PerfilUsuarioView(APIView):
    """
    Vista para que cualquier usuario autenticado pueda ver su propio perfil
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UsuarioListSerializer}
    )
    def get(self, request, *args, **kwargs):
        serializer = UsuarioListSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# dashboard de usuario




class SolicitarRecuperacionView(APIView):
    permission_classes = [AllowAny]
    """
    Vista para solicitar la recuperación de cuenta. Envía un correo con un token de recuperación.
    """

    @extend_schema(
        request=RecuperarPasswordSerializer,
        responses={200: RecuperarPasswordSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = RecuperarPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                usuario = Usuario.objects.get(email=email, activo=True)
            except Usuario.DoesNotExist:
                return Response({'error': 'Usuario no encontrado o inactivo.'}, status=status.HTTP_404_NOT_FOUND)
            token = usuario.generar_token_recuperacion()
            reset_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost')}/recuperar-password/?token={token}"
            send_mail(
                subject='Recuperación de contraseña',
                message=f'Hola {usuario.nombres},\n\nPara restablecer tu contraseña haz clic en el siguiente enlace: {reset_url}\n\nSi no solicitaste este cambio, ignora este correo.',
                from_email=os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@tusitio.com'),
                recipient_list=[usuario.email],
                fail_silently=False,
            )
            return Response({'message': 'Se ha enviado un correo con instrucciones para recuperar la contraseña.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RecuperarPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=CambiarPasswordSerializer,
        responses={200: MessageResponseSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = CambiarPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = request.data.get('token')
            usuario = Usuario.objects.filter(token_recuperacion=token, activo=True).first()
            if not usuario:
                return Response({'error': 'Token inválido o usuario no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
            if not usuario.es_token_valido():
                return Response({'error': 'El token ha expirado o no es válido.'}, status=status.HTTP_400_BAD_REQUEST)
            usuario.set_password(serializer.validated_data['password'])
            usuario.limpiar_token_recuperacion()
            usuario.save()
            return Response({'message': 'La contraseña ha sido restablecida correctamente.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
