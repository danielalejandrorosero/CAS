
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid

# Create your models here.

# Tabla de roles del sistema

class RolManager(models.Manager):
    def get_by_natural_key(self, nombre):
        return self.get(nombre=nombre)
    
class Rol(models.Model):
    ROLES_CHOICES = [
        ('ADMINISTRADOR', 'Administrador'),
        ('INSTRUCTOR', 'Instructor'),
        ('APRENDIZ', 'Aprendiz'),
    ]
    
    nombre = models.CharField(max_length=50, unique=True, choices=ROLES_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RolManager()
    
    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
    
    def __str__(self):
        return self.get_nombre_display()
    




class UsuarioManager(BaseUserManager):

    def create_user(self, documento, email, password=None, **extra_fields):
        """Crear y guardar un usuario regular"""
        if not email:
            raise ValueError('El usuario debe tener un email')
        if not documento:
            raise ValueError('El usuario debe tener un documento')
        

        email = self.normalize_email(email)
        user = self.model(email=email, documento=documento, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user 
    


    def create_superuser(self, documento, email, password, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)



        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        





        # asignar rol administrador por defecto a los superusuarios
        if not extra_fields.get('rol'):
            admin_rol, created = Rol.objects.get_or_create(
                nombre='ADMINISTRADOR',
                defaults={'descripcion': 'Rol por defecto para superusuarios'}
            )
            extra_fields['rol'] = admin_rol



        return self.create_user(documento, email, password, **extra_fields)


        
class Usuario(AbstractBaseUser, PermissionsMixin):
    """ Modelo personalizado de usuaruio basado en la """


    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
        ('PAS', 'Pasaporte'),
    ]

    documento = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message="El documento debe ser numérico",
                code='documento_numerico'
            )
        ]
    )


    tipo_documento = models.CharField(
        max_length=5,
        choices=TIPO_DOCUMENTO_CHOICES,
        default='CC'
    )
    telefono = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Formato de teléfono inválido')]
    )

    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(unique=True)


    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)


    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, default=1)  # suponiendo que el rol con id=1 existe


    ## CAMPOS DE ESTADO

    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)


    ## campos para recuperar la contraseña
    token_recuperacion = models.CharField(max_length=255, null=True, blank=True)
    token_expiracion = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




    # campos requeridos para django
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UsuarioManager()



    USERNAME_FIELD = 'documento'

    REQUIRED_FIELDS = ['email', 'nombres', 'apellidos', 'tipo_documento']



    ## indices

    class Meta:
        db_table = 'usuarios'
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        indexes = [
            models.Index(fields=['documento']),
            models.Index(fields=['email']),
            models.Index(fields=['rol']),
            models.Index(fields=['activo']),
        ]




    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    


    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.nombres} {self.apellidos}"
    
    @property
    def es_administrador(self):
        """Verifica si el usuario es administrador"""
        return self.rol.nombre == 'ADMINISTRADOR'
    
    @property
    def es_instructor(self):
        """Verifica si el usuario es instructor"""
        return self.rol.nombre == 'INSTRUCTOR'
    
    @property
    def es_aprendiz(self):
        """Verifica si el usuario es aprendiz"""
        return self.rol.nombre == 'APRENDIZ'
    
    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha del último acceso"""
        self.ultimo_acceso = timezone.now()
        self.save(update_fields=['ultimo_acceso'])
    
    def generar_token_recuperacion(self):
        """Genera un token único para recuperación de contraseña"""
        self.token_recuperacion = str(uuid.uuid4())
        self.token_expiracion = timezone.now() + timezone.timedelta(hours=24)  # Válido por 24 horas
        self.save(update_fields=['token_recuperacion', 'token_expiracion'])
        return self.token_recuperacion
    
    def es_token_valido(self):
        """Verifica si el token de recuperación es válido"""
        if not self.token_recuperacion or not self.token_expiracion:
            return False
        return timezone.now() < self.token_expiracion
    
    def limpiar_token_recuperacion(self):
        """Limpia el token de recuperación después de usarlo"""
        self.token_recuperacion = None
        self.token_expiracion = None
        self.save(update_fields=['token_recuperacion', 'token_expiracion'])



