from rest_framework import status, generics
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Avg, Sum

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import *
from apps.usuarios.views import IsAdminOrInstructor, IsAprendiz, IsOwnerOrAdminOrInstructor


class StandardResultsSetPagination(PageNumberPagination):
    """Paginación estándar para las vistas"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ==========================================
#         PROGRAMAS DE FORMACIÓN
# ==========================================

class ProgramaListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear programas de formacion"""
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    queryset = Programa.objects.filter(activo=True).order_by('nombre')
    serializer_class = ProgramaSerializer
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        tags=["PROGRAMAS DE FORMACIÓN"],
        summary="Listar y crear programas de formación",
        description="Permite listar todos los programas de formación activos y crear nuevos programas.",
        responses={
            200: ProgramaSerializer(many=True),
            201: ProgramaSerializer,
            400: OpenApiTypes.OBJECT,
        },
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Buscar por nombre o código del programa"
            ),
            OpenApiParameter(
                name='tipo_formacion',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar por tipo de formación"
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["PROGRAMAS DE FORMACIÓN"],
        summary="Crear programa de formación",
        description="Crea un nuevo programa de formación.",
        responses={
            201: ProgramaSerializer,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        tipo_formacion = self.request.query_params.get('tipo_formacion')

        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(codigo__icontains=search)
            )

        if tipo_formacion:
            queryset = queryset.filter(tipo_formacion=tipo_formacion)

        return queryset


class ProgramaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para obtener, actualizar y eliminar un programa específico"""
    queryset = Programa.objects.filter(activo=True)
    serializer_class = ProgramaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    @extend_schema(
        tags=["PROGRAMAS DE FORMACIÓN"],
        summary="Obtener programa específico",
        description="Obtiene los detalles de un programa de formación específico.",
        responses={
            200: ProgramaSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["PROGRAMAS DE FORMACIÓN"],
        summary="Actualizar programa completo",
        description="Actualiza completamente un programa de formación.",
        responses={
            200: ProgramaSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        tags=["PROGRAMAS DE FORMACIÓN"],
        summary="Actualizar programa parcial",
        description="Actualiza parcialmente un programa de formación.",
        responses={
            200: ProgramaSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        tags=["PROGRAMAS DE FORMACIÓN"],
        summary="Eliminar programa",
        description="Elimina lógicamente un programa de formación (marca como inactivo).",
        responses={
            204: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def perform_destroy(self, instance):
        # Eliminación lógica
        instance.activo = False
        instance.save()


# ==========================================
#         FICHAS DE FORMACIÓN
# ==========================================

class FichaListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear fichas"""
    queryset = Ficha.objects.filter(activo=True).order_by('-fecha_inicio')
    serializer_class = FichaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        tags=["FICHAS DE FORMACIÓN"],
        summary="Listar y crear fichas",
        description="Permite listar todas las fichas activas y crear nuevas fichas.",
        responses={
            200: FichaSerializer(many=True),
            201: FichaSerializer,
            400: OpenApiTypes.OBJECT,
        },
        parameters=[
            OpenApiParameter(
                name='programa',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filtrar por ID del programa"
            ),
            OpenApiParameter(
                name='estado',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar por estado de la ficha"
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Buscar por número de ficha o municipio"
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["FICHAS DE FORMACIÓN"],
        summary="Crear ficha de formación",
        description="Crea una nueva ficha de formación.",
        responses={
            201: FichaSerializer,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        programa = self.request.query_params.get('programa')
        estado = self.request.query_params.get('estado')
        search = self.request.query_params.get('search')

        if programa:
            queryset = queryset.filter(programa=programa)

        if estado:
            queryset = queryset.filter(estado=estado)

        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search) |
                Q(municipio_departamento__icontains=search)
            )

        return queryset


class FichaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para obtener, actualizar y eliminar una ficha específica"""
    queryset = Ficha.objects.filter(activo=True)
    serializer_class = FichaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    @extend_schema(
        tags=["FICHAS DE FORMACIÓN"],
        summary="Obtener ficha específica",
        description="Obtiene los detalles de una ficha de formación específica.",
        responses={
            200: FichaSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["FICHAS DE FORMACIÓN"],
        summary="Actualizar ficha completa",
        description="Actualiza completamente una ficha de formación.",
        responses={
            200: FichaSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        tags=["FICHAS DE FORMACIÓN"],
        summary="Actualizar ficha parcial",
        description="Actualiza parcialmente una ficha de formación.",
        responses={
            200: FichaSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        tags=["FICHAS DE FORMACIÓN"],
        summary="Eliminar ficha",
        description="Elimina lógicamente una ficha de formación (marca como inactiva).",
        responses={
            204: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def perform_destroy(self, instance):
        # Eliminación lógica
        instance.activo = False
        instance.save()



class ResultadoAprendizajeListCreateView(generics.ListCreateAPIView):
    queryset = ResultadoAprendizaje.objects.filter(activo=True)
    serializer_class = ResultadoAprendizajeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    pagination_class = StandardResultsSetPagination


    @extend_schema(
        tags=["RESULTADOS DE APRENDIZAJE"],
        summary="Listar resultados de aprendizaje",
        description="Obtiene una lista de resultados de aprendizaje.",
        responses={
            200: ResultadoAprendizajeSerializer,
            400: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs) # esto es para listar los resultados de aprendizaje

    @extend_schema(
        tags=["RESULTADOS DE APRENDIZAJE"],
        summary="Crear resultado de aprendizaje",
        description="Crea un nuevo resultado de aprendizaje.",
        responses={
            201: ResultadoAprendizajeSerializer,
            400: OpenApiTypes.OBJECT,
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')

        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(codigo__icontains=search)
            )

        return queryset

class AprendicesFichaView(generics.ListAPIView):
    """Vista para listar aprendices de una ficha con foto de perfil"""

    serializer_class = MatriculaSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]


    @extend_schema(
        tags=["FICHAS DE FORMACIÓN"],
        summary="Listar aprendices de una ficha",
        description="Obtiene una lista de aprendices matriculados en una ficha específica.",
        responses={
            200: MatriculaSerializer(many=True),
            404: OpenApiTypes.OBJECT,
        },
        parameters=[
            OpenApiParameter(
                name='ficha_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID de la ficha para filtrar los aprendices"
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


    def get_queryset(self):
        ficha_id = self.kwargs.get('ficha_id')
        search = self.request.query_params.get('search')

        queryset = Matricula.objects.filter(
            ficha_id=ficha_id,
            activo=True,
            aprendiz__rol__nombre="APRENDIZ"
        ).select_related('aprendiz', 'ficha', 'ficha__programa').order_by('aprendiz__nombres', 'aprendiz__apellidos')

        if search:
            queryset = queryset.filter(
                Q(aprendiz__nombres__icontains=search) |
                Q(aprendiz__apellidos__icontains=search) |
                Q(aprendiz__documento__icontains=search)
            )


        return queryset





class LlamadoAsistenciaListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear llamados de asistencia"""
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    serializer_class = LlamadoAsistenciaSerializer
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        tags=["LLAMADOS DE ASISTENCIA"],
        summary="Listar llamados de asistencia",
        description="Obtiene una lista de llamados de asistencia.",
        responses={
            200: LlamadoAsistenciaSerializer(many=True),
            400: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        queryset = LlamadoAsistencia.objects.filter(activo=True).order_by('-fecha_clase')
        intructor = self.request.query_params.get('instructor')
        ficha = self.request.query_params.get('ficha')
        fecha_clase = self.request.query_params.get('fecha_clase')

        if intructor:
            queryset = queryset.filter(instructor__id=intructor)
        if ficha:
            queryset = queryset.filter(ficha__id=ficha)
        if fecha_clase:
            queryset = queryset.filter(fecha=fecha_clase)
        return queryset

    def perform_create(self, serializer):
        serializer.save(fecha_hora_llamado=timezone.now())


class LlamadoAsistenciaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para obtener, actualizar y eliminar un llamado de asistencia especifico"""


    queryset = LlamadoAsistencia.objects.all()

    serializer_class = LlamadoAsistenciaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    @extend_schema(
        tags=["LLAMADOS DE ASISTENCIA"],
        summary="Obtener llamado de asistencia",
        description="Obtiene los detalles de un llamado de asistencia específico.",
        responses={
            200: LlamadoAsistenciaSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


    @extend_schema(
        tags=["LLAMADOS DE ASISTENCIA"],
        summary="Actualizar llamado de asistencia",
        description="Actualiza un llamado de asistencia específico.",
        responses={
            200: LlamadoAsistenciaSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )

    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)


    @extend_schema(
        tags=["LLAMADOS DE ASISTENCIA"],
        summary="Eliminar llamado de asistencia",
        description="Elimina lógicamente un llamado de asistencia (marca como inactivo).",
        responses={
            204: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs) # las 3 funciones sonpara el swagger



class RegistroAsistenciaListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear registros de asistencia"""


class RegistroAsistenciaListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear registros de asistencia aqui es para que el instructor pase asistencia a los aprendices y los marque como presentes o ausentes etc"""

    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    serializer_class = RegistroAsistenciaSerializer
    pagination_class = StandardResultsSetPagination


    @extend_schema(
        summary="Listar y crear registros de asistencia",
        description="Permite listar los registros de asistencia y crear nuevos.",
        parameters=[
            OpenApiParameter(name='llamado_asistencia', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                             description="Filtrar por ID del llamado de asistencia"),
            OpenApiParameter(name='aprendiz', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                             description="Filtrar por ID del aprendiz"),
            OpenApiParameter(name='estado', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                             description="Filtrar por estado de asistencia")
        ]
    )
    def get_queryset(self):
        queryset = RegistroAsistencia.objects.order_by('-hora_registro')
        llamado_asistencia = self.request.query_params.get('llamado_asistencia')
        aprendiz = self.request.query_params.get('aprendiz')
        estado = self.request.query_params.get('estado')

        if llamado_asistencia:
            queryset = queryset.filter(llamado_asistencia__id=llamado_asistencia)
        if aprendiz:
            queryset = queryset.filter(aprendiz__id=aprendiz)
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset


    def perform_create(self, serializer):

        serializer.save(hora_registro=timezone.now())



# apps/asistencia/views.py

class AprendicesPorFichaView(generics.ListAPIView):
    """Lista los aprendices de una ficha específica"""
    serializer_class = MatriculaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        tags=["FICHAS DE FORMACIÓN"],
        summary="Listar aprendices de una ficha",
        description="Lista los aprendices matriculados en una ficha específica.",
        responses={200: MatriculaSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='ficha_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID de la ficha"
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        ficha_id = self.kwargs.get('ficha_id')
        return Matricula.objects.filter(
            ficha_id=ficha_id,
            activo=True,
            aprendiz__rol__nombre="APRENDIZ"
        ).select_related('aprendiz').order_by('aprendiz__nombres', 'aprendiz__apellidos')