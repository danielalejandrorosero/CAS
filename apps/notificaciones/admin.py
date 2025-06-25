from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    TipoNotificacion, 
    Notificacion, 
    ConfiguracionNotificacion, 
    HistorialNotificacion
)


@admin.register(TipoNotificacion)
class TipoNotificacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['activo']


class HistorialNotificacionInline(admin.TabularInline):
    model = HistorialNotificacion
    extra = 0
    readonly_fields = ['fecha_envio', 'estado', 'mensaje_error']
    can_delete = False


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 
        'usuario_link', 
        'tipo', 
        'leida_badge', 
        'fecha_creacion',
        'enviada_push',
        'enviada_email'
    ]
    list_filter = [
        'tipo', 
        'leida', 
        'enviada_push', 
        'enviada_email',
        'fecha_creacion'
    ]
    search_fields = [
        'titulo', 
        'mensaje', 
        'usuario__nombres', 
        'usuario__apellidos',
        'usuario__numero_documento'
    ]
    readonly_fields = [
        'fecha_creacion', 
        'fecha_lectura', 
        'objeto_relacionado_link'
    ]
    list_per_page = 25
    date_hierarchy = 'fecha_creacion'
    inlines = [HistorialNotificacionInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'tipo', 'titulo', 'mensaje')
        }),
        ('Objeto Relacionado', {
            'fields': ('content_type', 'object_id', 'objeto_relacionado_link'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('leida', 'fecha_creacion', 'fecha_lectura')
        }),
        ('Envío', {
            'fields': ('enviada_push', 'enviada_email')
        }),
        ('Datos Adicionales', {
            'fields': ('datos_extra',),
            'classes': ('collapse',)
        })
    )
    
    def usuario_link(self, obj):
        url = reverse('admin:usuarios_usuario_change', args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.get_full_name())
    usuario_link.short_description = 'Usuario'
    
    def leida_badge(self, obj):
        if obj.leida:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Leída</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ No leída</span>'
            )
    leida_badge.short_description = 'Estado'
    
    def objeto_relacionado_link(self, obj):
        if obj.objeto_relacionado:
            try:
                model_name = obj.content_type.model
                app_label = obj.content_type.app_label
                url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.object_id])
                return format_html('<a href="{}">{}</a>', url, str(obj.objeto_relacionado))
            except:
                return str(obj.objeto_relacionado)
        return '-'
    objeto_relacionado_link.short_description = 'Objeto Relacionado'
    
    actions = ['marcar_como_leidas', 'marcar_como_no_leidas']
    
    def marcar_como_leidas(self, request, queryset):
        for notificacion in queryset:
            notificacion.marcar_como_leida()
        self.message_user(request, f'{queryset.count()} notificaciones marcadas como leídas.')
    marcar_como_leidas.short_description = 'Marcar como leídas'
    
    def marcar_como_no_leidas(self, request, queryset):
        queryset.update(leida=False, fecha_lectura=None)
        self.message_user(request, f'{queryset.count()} notificaciones marcadas como no leídas.')
    marcar_como_no_leidas.short_description = 'Marcar como no leídas'


@admin.register(ConfiguracionNotificacion)
class ConfiguracionNotificacionAdmin(admin.ModelAdmin):
    list_display = [
        'usuario_link',
        'notificaciones_push',
        'notificaciones_email',
        'nueva_actividad',
        'actividad_valorada',
        'citacion_comite'
    ]
    list_filter = [
        'notificaciones_push',
        'notificaciones_email',
        'nueva_actividad',
        'actividad_valorada',
        'citacion_comite'
    ]
    search_fields = [
        'usuario__nombres',
        'usuario__apellidos',
        'usuario__numero_documento'
    ]
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Configuración General', {
            'fields': ('notificaciones_push', 'notificaciones_email')
        }),
        ('Tipos de Notificaciones', {
            'fields': (
                'nueva_actividad',
                'actividad_valorada',
                'citacion_comite',
                'alta_inasistencia',
                'bajo_rendimiento',
                'recordatorios'
            )
        }),
        ('Horarios', {
            'fields': ('hora_inicio', 'hora_fin', 'dias_activos')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def usuario_link(self, obj):
        url = reverse('admin:usuarios_usuario_change', args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.get_full_name())
    usuario_link.short_description = 'Usuario'


@admin.register(HistorialNotificacion)
class HistorialNotificacionAdmin(admin.ModelAdmin):
    list_display = [
        'notificacion_titulo',
        'usuario_notificacion',
        'metodo_envio',
        'estado_badge',
        'fecha_envio'
    ]
    list_filter = [
        'metodo_envio',
        'estado',
        'fecha_envio'
    ]
    search_fields = [
        'notificacion__titulo',
        'notificacion__usuario__nombres',
        'notificacion__usuario__apellidos'
    ]
    readonly_fields = ['fecha_envio']
    date_hierarchy = 'fecha_envio'
    
    def notificacion_titulo(self, obj):
        return obj.notificacion.titulo
    notificacion_titulo.short_description = 'Notificación'
    
    def usuario_notificacion(self, obj):
        return obj.notificacion.usuario.get_full_name()
    usuario_notificacion.short_description = 'Usuario'
    
    def estado_badge(self, obj):
        colors = {
            'ENVIADO': 'green',
            'FALLIDO': 'red',
            'PENDIENTE': 'orange'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'