"""
from .models import *


admin.site.register(Actividad)
admin.site.register(AsignacionActividad)
admin.site.register(CalificacionActividad)
admin.site.register(EntregaActividad)
admin.site.register(ArchivoActividad)
admin.site.register(TipoActividad)


"""

from rest_framework import serializers

from django.utils import timezone

from django.db import transaction


from .models import Actividad,AsignacionActividad,CalificacionActividad,EntregaActividad,ArchivoActividad,TipoActividad

from apps.usuarios.models import Usuario
from apps.asistencia.models import Ficha, ResultadoAprendizaje



