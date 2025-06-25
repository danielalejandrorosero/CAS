# Sistema de Notificaciones - Seguimiento Integral del Aprendiz

## Descripción

Este módulo implementa un sistema completo de notificaciones para la aplicación "Seguimiento Integral del Aprendiz". Permite enviar notificaciones automáticas a aprendices e instructores sobre eventos importantes del sistema.

## Características Principales

### Tipos de Notificaciones

1. **NUEVA_ACTIVIDAD**: Notifica a los aprendices cuando se crea una nueva actividad
2. **ACTIVIDAD_VALORADA**: Notifica cuando una actividad es calificada
3. **CITACION_COMITE**: Notifica sobre citaciones a comité
4. **ALTA_INASISTENCIA**: Alerta por alta inasistencia (>20% en 30 días)
5. **BAJO_RENDIMIENTO**: Alerta por bajo rendimiento académico (<3.0 promedio en 30 días)
6. **RECORDATORIO**: Recordatorios de actividades próximas a vencer
7. **SISTEMA**: Notificaciones generales del sistema

### Funcionalidades

- **Notificaciones Automáticas**: Se envían automáticamente mediante señales de Django
- **Configuración Personalizada**: Cada usuario puede configurar qué notificaciones recibir
- **Historial Completo**: Registro de todas las notificaciones enviadas
- **API REST**: Endpoints completos para gestión desde aplicaciones móviles
- **Comandos de Gestión**: Tareas automáticas para mantenimiento y envío masivo

## Estructura del Módulo

```
apps/notificaciones/
├── __init__.py
├── apps.py                 # Configuración de la app
├── models.py              # Modelos de datos
├── admin.py               # Configuración del admin
├── serializers.py         # Serializadores para API
├── views.py               # Vistas de la API
├── urls.py                # URLs de la API
├── services.py            # Lógica de negocio
├── signals.py             # Señales automáticas
├── tests.py               # Pruebas unitarias
├── management/
│   └── commands/
│       ├── enviar_recordatorios.py
│       └── inicializar_tipos_notificacion.py
└── migrations/
    └── __init__.py
```

## Modelos

### TipoNotificacion
Define los tipos de notificaciones disponibles en el sistema.

### Notificacion
Modelo principal que almacena las notificaciones enviadas a los usuarios.

### ConfiguracionNotificacion
Permite a cada usuario configurar qué tipos de notificaciones desea recibir.

### HistorialNotificacion
Registra el historial de notificaciones enviadas para auditoría.

## API Endpoints

### Tipos de Notificación
- `GET /api/notificaciones/tipos/` - Listar tipos
- `GET /api/notificaciones/tipos/{id}/` - Detalle de tipo

### Notificaciones de Usuario
- `GET /api/notificaciones/` - Listar notificaciones del usuario
- `GET /api/notificaciones/{id}/` - Detalle de notificación
- `POST /api/notificaciones/` - Crear notificación (solo instructores/admin)
- `DELETE /api/notificaciones/{id}/` - Eliminar notificación

### Acciones
- `GET /api/notificaciones/resumen/` - Resumen de notificaciones
- `POST /api/notificaciones/{id}/marcar-leida/` - Marcar como leída
- `POST /api/notificaciones/marcar-todas-leidas/` - Marcar todas como leídas

### Configuración
- `GET /api/notificaciones/configuracion/` - Obtener configuración
- `PUT /api/notificaciones/configuracion/` - Actualizar configuración

### Historial
- `GET /api/notificaciones/historial/` - Ver historial

### Envío Personalizado
- `POST /api/notificaciones/enviar/` - Enviar notificación personalizada

## Instalación y Configuración

### 1. Agregar a INSTALLED_APPS

```python
# settings.py
LOCAL_APPS = [
    # ... otras apps
    'apps.notificaciones',
]
```

### 2. Incluir URLs

```python
# urls.py
urlpatterns = [
    # ... otras URLs
    path('api/notificaciones/', include('apps.notificaciones.urls')),
]
```

### 3. Ejecutar Migraciones

```bash
python manage.py makemigrations notificaciones
python manage.py migrate
```

### 4. Inicializar Tipos de Notificación

```bash
python manage.py inicializar_tipos_notificacion
```

## Comandos de Gestión

### Enviar Recordatorios

```bash
# Ejecutar todas las tareas
python manage.py enviar_recordatorios

# Solo recordatorios
python manage.py enviar_recordatorios --tipo recordatorios

# Solo verificar bajo rendimiento
python manage.py enviar_recordatorios --tipo bajo_rendimiento

# Solo limpiar notificaciones antiguas
python manage.py enviar_recordatorios --tipo limpiar --dias-limpieza 30
```

### Inicializar Tipos

```bash
python manage.py inicializar_tipos_notificacion
```

## Señales Automáticas

El sistema incluye señales que se ejecutan automáticamente:

- **Nueva Actividad**: Se envía cuando se crea una actividad
- **Actividad Valorada**: Se envía cuando se califica una actividad
- **Citación a Comité**: Se envía cuando se crea una citación
- **Alta Inasistencia**: Se verifica al registrar asistencia

## Configuración de Tareas Periódicas

Para las tareas automáticas, se recomienda configurar un cron job:

```bash
# Ejecutar diariamente a las 8:00 AM
0 8 * * * cd /ruta/proyecto && python manage.py enviar_recordatorios

# Limpiar notificaciones semanalmente
0 2 * * 0 cd /ruta/proyecto && python manage.py enviar_recordatorios --tipo limpiar
```

## Extensibilidad

### Agregar Nuevos Tipos de Notificación

1. Agregar el tipo en `TipoNotificacion.TIPOS_CHOICES`
2. Actualizar el comando `inicializar_tipos_notificacion.py`
3. Crear la señal correspondiente en `signals.py`
4. Agregar la lógica en `services.py`

### Personalizar Plantillas

Las plantillas de notificación se pueden personalizar modificando los métodos en `NotificacionService`.

## Pruebas

```bash
# Ejecutar pruebas del módulo
python manage.py test apps.notificaciones

# Ejecutar con cobertura
coverage run --source='.' manage.py test apps.notificaciones
coverage report
```

## Consideraciones de Rendimiento

- Las notificaciones se envían de forma asíncrona cuando es posible
- Se incluye limpieza automática de notificaciones antiguas
- Los índices de base de datos optimizan las consultas frecuentes
- Se implementa paginación en las vistas de lista

## Seguridad

- Validación de permisos en todas las vistas
- Filtrado automático por usuario
- Validación de datos de entrada
- Protección contra spam de notificaciones

## Soporte

Para reportar problemas o solicitar nuevas características, contactar al equipo de desarrollo.