from django.contrib import admin


from .models import (
    Programa, Ficha, ResultadoAprendizaje, Matricula,
    AsignacionInstructor, LlamadoAsistencia, RegistroAsistencia,
    EstadisticaAsistencia
)


admin.site.register(Programa)
admin.site.register(Ficha)
admin.site.register(ResultadoAprendizaje)
admin.site.register(Matricula)
admin.site.register(AsignacionInstructor)
admin.site.register(LlamadoAsistencia)
admin.site.register(RegistroAsistencia)
admin.site.register(EstadisticaAsistencia)
# Register your models here.
