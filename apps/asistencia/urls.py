from django.urls import path


from .views import ProgramaListCreateView,ProgramaDetailView,FichaListCreateView,FichaDetailView,ResultadoAprendizajeListCreateView,AprendicesFichaView,LlamadoAsistenciaListCreateView, LlamadoAsistenciaDetailView,RegistroAsistenciaListCreateView,AprendicesPorFichaView

urlpatterns = [

    # programas de formacion cruds
    path('programas/', ProgramaListCreateView.as_view(), name='listar_y_crear_programas'), # esta es la vista para listar y crear programas de formacion

    path('programas/<int:pk>/', ProgramaDetailView.as_view(), name='programa-detail'), # esta es la vista para obtener, actualizar y eliminar un programa de formacion

    # ficha
    path('fichas/', FichaListCreateView.as_view(), name='listar_y_crear_fichas'), # esta es la vista para listar y crear fichas de formacion


    path('fichas/<int:pk>/', FichaDetailView.as_view(), name='ficha-detail'), # esta es la vista para obtener, actualizar y eliminar una ficha


    path('resultados/', ResultadoAprendizajeListCreateView.as_view(), name='listar_y_crear_resultados'),

    path('aprendices-ficha/<int:ficha_id>/', AprendicesFichaView.as_view(), name='aprendices_ficha'), # esta es la vista para listar los aprendices de una ficha

    path('llamados-asistencia/', LlamadoAsistenciaListCreateView.as_view(), name='listar_y_crear_llamados_asistencia'), # esta es la vista para listar y crear llamados de asistencia

    path('llamados-asistencia/<int:pk>/', LlamadoAsistenciaDetailView.as_view(), name='llamado_asistencia_detail'), # esta es la vista para obtener, actualizar y eliminar un llamado de asistencia
    path('registros-asistencia/', RegistroAsistenciaListCreateView.as_view(), name='listar_y_crear_registros_asistencia'), # esta es la vista para listar y crear registros de asistencia

    path('aprendices-ficha/<int:ficha_id>/', AprendicesPorFichaView.as_view(), name='aprendices_por_ficha'), # esta es la vista para listar los aprendices de una ficha
]