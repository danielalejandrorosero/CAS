from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Usuario, Rol

# Personalización del modelo Rol en el admin
@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'created_at', 'updated_at')
    search_fields = ('nombre',)
    ordering = ('nombre',)
    list_filter = ('nombre',)

# Configuración personalizada para el modelo Usuario
@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    model = Usuario

    # Campos que se muestran en la lista del admin
    list_display = ('documento', 'email', 'nombres', 'apellidos', 'rol', 'is_staff', 'activo')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'activo')

    # Campos para buscar usuarios
    search_fields = ('documento', 'email', 'nombres', 'apellidos')

    # Orden por defecto
    ordering = ('documento',)

    # Agrupación de campos en la vista de detalle
    fieldsets = (
        (None, {'fields': ('documento', 'password')}),
        (_('Información personal'), {'fields': ('tipo_documento', 'nombres', 'apellidos', 'email', 'telefono', 'foto_perfil', 'rol')}),
        (_('Permisos'), {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Fechas'), {'fields': ('ultimo_acceso', 'fecha_registro', 'last_login')}),
        (_('Recuperación de cuenta'), {'fields': ('token_recuperacion', 'token_expiracion')}),
    )

    # Campos que se muestran al crear usuario desde el admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('documento', 'email', 'nombres', 'apellidos', 'tipo_documento', 'rol', 'password1', 'password2'),
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('ultimo_acceso', 'fecha_registro', 'last_login')

