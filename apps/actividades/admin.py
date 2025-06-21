from django.contrib import admin

from .models import *


admin.site.register(Actividad)
admin.site.register(AsignacionActividad)
admin.site.register(CalificacionActividad)
admin.site.register(EntregaActividad)
admin.site.register(ArchivoActividad)
admin.site.register(TipoActividad)

# Register your models here.
