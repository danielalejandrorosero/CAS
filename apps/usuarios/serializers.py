from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Usuario, Rol


class RolSerializer(serializers.ModelSerializer):
    """Serializador para el modelo del rol"""

    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion']
        read_only_fields = ['id']


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializador completo para los usuarios"""

    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    nombre_completo = serializers.CharField(source='nombre_completo', read_only=True)
    foto_perfil_url = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'documento', 'tipo_documento', 'nombres', 'apellidos',
            'email', 'telefono', 'foto_perfil', 'foto_perfil_url',
            'rol', 'rol_nombre', 'activo', 'fecha_registro',
            'ultimo_acceso', 'created_at', 'updated_at', 'nombre_completo'
        ]

        read_only_fields = [
            'id', 'fecha_registro', 'ultimo_acceso', 'created_at', 'updated_at',
            'rol_nombre', 'nombre_completo', 'foto_perfil_url'
        ]

        extra_kwargs = {
            'password': {'write_only': True},
            'foto_perfil': {'required': False}
        }

    def get_foto_perfil_url(self, obj):
        """Obtener la url completa de la foto de perfil"""
        if obj.foto_perfil:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.foto_perfil.url)
            return obj.foto_perfil.url
        return None


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializador para crear usuarios"""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )

    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = Usuario
        fields = [
            'documento', 'tipo_documento', 'nombres', 'apellidos',
            'email', 'telefono', 'foto_perfil', 'password', 'password_confirm', 'rol'
        ]
        extra_kwargs = {
            'documento': {
                'validators': [UniqueValidator(queryset=Usuario.objects.all())]
            },
            'email': {
                'validators': [UniqueValidator(queryset=Usuario.objects.all())]
            }
        }

    def validate_documento(self, value):
        """Validar que el documento no exista"""
        if Usuario.objects.filter(documento=value).exists():
            raise serializers.ValidationError("El documento ya está en uso.")
        return value

    def validate(self, attrs):
        """Validar que las contraseñas coincidan"""
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)

        if password != password_confirm:
            raise serializers.ValidationError("Las contraseñas no coinciden.")

        return attrs

    def create(self, validated_data):
        """Crear usuario con password encriptado"""
        password = validated_data.pop('password', None)
        usuario = Usuario.objects.create_user(
            password=password,
            **validated_data
        )
        return usuario


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """Serializador para actualizar usuarios sin permitir cambios de contraseña"""

    class Meta:
        model = Usuario
        fields = [
            'nombres', 'apellidos', 'email', 'telefono', 'foto_perfil'
        ]

        extra_kwargs = {
            'foto_perfil': {'required': False},
            'email': {
                'validators': [UniqueValidator(queryset=Usuario.objects.all())]
            }
        }


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializador personalizado para JWT con documento en lugar de username"""

    documento = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remover username del serializador padre
        self.fields.pop('username', None)

    def validate_documento(self, value):
        """Validar que el documento sea numérico"""
        if not value.isdigit():
            raise serializers.ValidationError("El documento debe ser numérico.")
        return value

    def validate(self, attrs):
        documento = attrs.get('documento')
        password = attrs.get('password')

        if documento and password:
            try:
                usuario = Usuario.objects.get(documento=documento, activo=True)
            except Usuario.DoesNotExist:
                raise serializers.ValidationError("Usuario no encontrado o inactivo.")

            # Autenticar el usuario
            user = authenticate(
                request=self.context.get('request'),
                username=documento,
                password=password
            )

            if not user:
                raise serializers.ValidationError("Credenciales incorrectas.")

            if not user.is_active:
                raise serializers.ValidationError("El usuario está inactivo.")

            # Actualizar último acceso
            user.actualizar_ultimo_acceso()

            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)

            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user
            }
        else:
            raise serializers.ValidationError("Debe proporcionar documento y contraseña.")

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Agregar campos personalizados al token
        token['documento'] = user.documento
        token['rol'] = user.rol.nombre if user.rol else None
        token['nombre_completo'] = user.nombre_completo
        return token

class UsuarioListSerializer(serializers.ModelSerializer):
    """Serializador para listar usuarios con campos básicos"""

    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    nombre_completo = serializers.CharField(source='nombre', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'documento', 'tipo_documento', 'nombres', 'apellidos',
            'email', 'telefono', 'foto_perfil', 'rol', 'rol_nombre',
            'activo', 'fecha_registro', 'ultimo_acceso', 'nombre_completo'
        ]
        read_only_fields = ['id', 'fecha_registro', 'ultimo_acceso']

class LoginSerializer(serializers.Serializer):
    """Serializador para el login de usuarios - mantiene compatibilidad"""

    documento = serializers.CharField(max_length=20)
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate_documento(self, value):
        """Validar que el documento sea numérico"""
        if not value.isdigit():
            raise serializers.ValidationError("El documento debe ser numérico.")
        return value

    def validate(self, attrs):
        """Validar credenciales"""
        documento = attrs.get('documento')
        password = attrs.get('password')

        if documento and password:
            try:
                usuario = Usuario.objects.get(documento=documento, activo=True)
            except Usuario.DoesNotExist:
                raise serializers.ValidationError("Usuario no encontrado o inactivo.")

            user = authenticate(
                request=self.context.get('request'),
                username=documento,
                password=password
            )

            if not user:
                raise serializers.ValidationError("Credenciales incorrectas.")

            if not user.is_active:
                raise serializers.ValidationError("El usuario está inactivo.")

            attrs['user'] = user
        else:
            raise serializers.ValidationError("Debe proporcionar documento y contraseña.")

        return attrs


class RecuperarPasswordSerializer(serializers.Serializer):
    """Serializador para la recuperación de contraseña"""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validar que el email existe en el sistema"""
        try:
            usuario = Usuario.objects.get(email=value, activo=True)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("El email no está registrado o el usuario está inactivo.")
        return value


class CambiarPasswordSerializer(serializers.Serializer):
    """Serializador para cambiar la contraseña del usuario"""

    token = serializers.CharField(write_only=True)
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_password(self, value):
        """Validar la contraseña"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError("Las contraseñas no coinciden.")
        else:
            raise serializers.ValidationError("Las contraseñas son requeridas.")

        if not attrs.get('token'):
            raise serializers.ValidationError("El token es requerido.")

        return attrs


class CambioPasswordSerializer(serializers.Serializer):
    """Serializador para cambio de contraseña con validación de contraseña actual"""

    password_actual = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    password_nueva = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    password_nueva_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_password_actual(self, value):
        user = self.context.get('request').user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual no coincide.")
        return value

    def validate_password_nueva(self, value):
        """Validar nueva contraseña"""
        try:
            validate_password(value, user=self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        password_nueva = attrs.get('password_nueva')
        password_nueva_confirm = attrs.get('password_nueva_confirm')

        if password_nueva and password_nueva_confirm:
            if password_nueva != password_nueva_confirm:
                raise serializers.ValidationError("Las nuevas contraseñas no coinciden.")
        else:
            raise serializers.ValidationError("Las nuevas contraseñas son requeridas.")

        return


class UsuarioDashboardSerializer(serializers.ModelSerializer):
    """Serializador para el perfil de usuario"""

    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    nombre_completo = serializers.CharField(read_only=True)
    foto_perfil_url = serializers.SerializerMethodField()
    tipo_documento_display = serializers.CharField(source='get_tipo_documento_display', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'documento', 'tipo_documento', 'tipo_documento_display',
            'nombres', 'apellidos', 'nombre_completo', 'email', 'telefono',
            'foto_perfil', 'foto_perfil_url', 'rol_nombre',
            'fecha_registro', 'ultimo_acceso'
        ]

        read_only_fields = ['__all__']

    def get_foto_perfil_url(self, obj):
        """Obtener la URL completa de la foto de perfil"""
        if obj.foto_perfil:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.foto_perfil.url)
            return obj.foto_perfil.url
        return None


class PerfilSerializer(serializers.ModelSerializer):
    """Serializador para el perfil de usuario"""

    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    nombre_completo = serializers.CharField(read_only=True)
    foto_perfil_url = serializers.SerializerMethodField()
    tipo_documento_display = serializers.CharField(source='get_tipo_documento_display', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'documento', 'tipo_documento', 'tipo_documento_display',
            'nombres', 'apellidos', 'nombre_completo', 'email', 'telefono',
            'foto_perfil', 'foto_perfil_url', 'rol_nombre',
            'fecha_registro', 'ultimo_acceso'
        ]

        read_only_fields = ['__all__']

    def get_foto_perfil_url(self, obj):
        """Obtener la URL completa de la foto de perfil"""
        if obj.foto_perfil:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.foto_perfil.url)
            return obj.foto_perfil.url
        return None


class LoginResponseSerializer(serializers.Serializer):
    """Serializador para respuesta de login exitoso con JWT"""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UsuarioSerializer()
    message = serializers.CharField()


class MessageResponseSerializer(serializers.Serializer):
    """Serializador para respuestas con mensaje"""

    message = serializers.CharField()
    success = serializers.BooleanField(default=True)


class ErrorResponseSerializer(serializers.Serializer):
    """Serializador para respuestas de error"""

    error = serializers.CharField()
    details = serializers.DictField(required=False)
    success = serializers.BooleanField(default=False)


class StatsSerializer(serializers.Serializer):
    """Serializador para estadísticas del dashboard"""

    total_usuarios = serializers.IntegerField()
    total_instructores = serializers.IntegerField()
    total_aprendices = serializers.IntegerField()
    usuarios_activos = serializers.IntegerField()
    usuarios_recientes = UsuarioSerializer(many=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Solicitar recuperación de contraseña (por email o documento)"""
    email = serializers.EmailField(required=False)
    documento = serializers.CharField(required=False)

    def validate(self, data):
        if not data.get('email') and not data.get('documento'):
            raise serializers.ValidationError("Debe proporcionar email o documento.")
        return data


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirmar recuperación de contraseña (token + nueva contraseña)"""
    token = serializers.CharField()
    nueva_contraseña = serializers.CharField(min_length=8, write_only=True)


class TokenRefreshSerializer(serializers.Serializer):
    """Serializador para refrescar tokens JWT"""
    refresh = serializers.CharField()


class TokenRefreshResponseSerializer(serializers.Serializer):
    """Serializador para respuesta de refresh token"""
    access = serializers.CharField()