from django.utils import timezone
from rest_framework import serializers


from .models import Programa, Ficha, ResultadoAprendizaje, Matricula, AsignacionInstructor, LlamadoAsistencia, RegistroAsistencia


class ProgramaSerializer(serializers.ModelSerializer):
    """Serializador para el modelo de programa de formacion"""

    total_fichas = serializers.SerializerMethodField()
    total_resultados = serializers.SerializerMethodField()

    class Meta:
        model = Programa
        fields = ['id', 'codigo', 'nombre', 'tipo_formacion', 'duracion_horas', 'activo', 'total_fichas',
                  'total_resultados', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_fichas', 'total_resultados']

    def get_total_fichas(self, obj):
        return obj.fichas.count()

    def get_total_resultados(self, obj):
        return obj.resultados_aprendizaje.count()  # el total de resultados de aprendizaje


class ResultadoAprendizajeSerializer(serializers.ModelSerializer):
    """Serializador para el modelo de resultado de aprendizaje"""

    programa_nombre = serializers.CharField(source='programa.nombre', read_only=True)
    total_asignaciones = serializers.SerializerMethodField()  # el total de asignacion es de un resultado de aprendizaje sirve para

    class Meta:
        model = ResultadoAprendizaje
        fields = [
            'id',
            'codigo',
            'nombre',
            'descripcion',
            'programa',
            'programa_nombre',
            'horas_asignadas',
            'trimestre',
            'activo',
            'created_at',
            'updated_at',
            'total_asignaciones',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'programa_nombre',
            'total_asignaciones',
        ]

    def get_total_asignaciones(self, obj):
        return obj.asignaciones.count()


class FichaSerializer(serializers.ModelSerializer):
    """Serializador para el modelo de ficha"""

    class Meta:
        model = Ficha
        fields = ['id', 'numero', 'municipio_departamento', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class FichaSerializer(serializers.ModelSerializer):
    """Serializador para el modelo de ficha"""
    programa_nombre = serializers.CharField(source='programa.nombre', read_only=True)
    programa_codigo = serializers.CharField(source='programa.codigo', read_only=True)
    duracion_dias = serializers.SerializerMethodField()
    total_aprendices = serializers.SerializerMethodField()
    total_instructores = serializers.SerializerMethodField()

    class Meta:
        model = Ficha
        fields = [
            'id',
            'numero',
            'fecha_inicio',
            'fecha_fin_lectiva',
            'municipio_departamento',
            'centro_formacion',
            'duracion_dias',
            'cupo_aprendices',
            'total_aprendices',
            'total_instructores',
            'programa_nombre',
            'programa_codigo',
            'cupo_instructores',
            'lugar_realizacion',
            'modalidad',
            'jornada',
            'estado',
            'activo',
            'programa',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'programa_nombre',
            'programa_codigo',
            'duracion_dias',
            'total_aprendices',
            'total_instructores',
        ]

    def get_duracion_dias(self, obj):
        return (obj.fecha_fin_lectiva - obj.fecha_inicio).days


    def get_total_aprendices(self, obj):
        return obj.matriculas.filter(activo=True).count()

    def get_total_instructores(self, obj):
        return obj.asignaciones.filter(activo=True).count()

    def validate(self, attrs):
        if attrs.get('fecha_fin_lectiva') and attrs.get('fecha_inicio'):
            if attrs['fecha_fin_lectiva'] <= attrs['fecha_inicio']:
                raise serializers.ValidationError(
                    "La fecha de fin lectiva debe ser posterior a la fecha de inicio."
                )
        return attrs


# SERIALIZADOR PARA MATRICULAS Y ASISTENCIA

class MatriculaSerializer(serializers.ModelSerializer):
    """Serializador para el modelo de matriculas"""

    aprendiz_nombre = serializers.CharField(source='aprendiz.get_full_name', read_only=True)
    aprendiz_documento = serializers.CharField(source='aprendiz.documento', read_only=True)
    ficha_numero = serializers.CharField(source='ficha.numero', read_only=True)
    programa_nombre = serializers.CharField(source='ficha.programa.nombre', read_only=True)
    foto_perfil_url = serializers.SerializerMethodField()

    class Meta:
        model = Matricula
        fields = [
            'id',
            'aprendiz',
            'aprendiz_nombre',
            'aprendiz_documento',
            'ficha',
            'ficha_numero',
            'programa_nombre',
            'fecha_matricula',
            'estado',
            'activo',
            'foto_perfil',
            'created_at',
            'updated_at',
            'foto_perfil_url',
        ]
        read_only_fields = [
            'id',
            'fecha_matricula',
            'created_at',
            'updated_at',
            'aprendiz_nombre',
            'aprendiz_documento',
            'ficha_numero',
            'programa_nombre',
        ]

    def get_foto_perfil_url(self, obj):
        if obj.foto_perfil:
            return obj.foto_perfil.url
        return None

    def validate(self, attrs):

        if attrs.get('aprendiz') and not attrs['aprendiz'].es_aprendiz:
            raise serializers.ValidationError("para matricularse debe ser un aprendiz.")

        if attrs.get('ficha'):
            matriculas_activas = attrs['ficha'].matriculas.filter(activo=True)
            if matriculas_activas.count() >= attrs['ficha'].cupo_aprendices:
                raise serializers.ValidationError("El cupo de aprendices para esta ficha ha sido alcanzado.")

        return attrs


class AsignacionInstructorSerializer(serializers.ModelSerializer):
    instructor_nombre = serializers.CharField(source='instructor.nombre_completo', read_only=True)

    instructor_documento = serializers.CharField(source='instructor.documento', read_only=True)

    resultado_nombre = serializers.CharField(source='resultado_aprendizaje.programa.nombre', read_only=True)

    resultado_codigo = serializers.CharField(source='resultado_aprendizaje.programa.codigo', read_only=True)

    ficha_numero = serializers.CharField(source='ficha.numero', read_only=True)

    programa_nombre = serializers.CharField(source='ficha.programa.nombre', read_only=True)

    class Meta:
        model = AsignacionInstructor

        fields = [
            'id',
            'instructor',
            'instructor_nombre',
            'instructor_documento',
            'resultado_aprendizaje',
            'resultado_nombre',
            'resultado_codigo',
            'ficha',
            'ficha_numero',
            'programa_nombre',
            'fecha_inicio',
            'fecha_fin',
            'activo',
            'created_at',
            'updated_at',
        ]

        read__only_fields = [
            'id',
            'created_at',
            'updated_at',
            'instructor_nombre',
            'instructor_documento',
            'resultado_nombre',
            'resultado_codigo',
            'ficha_numero',
            'programa_nombre',
        ]

        def validate(self, attrs):

            # validar que el usuario sea instructor
            if attrs.get('instructor') and not attrs['instructor'].es_instructor:
                raise serializers.ValidationError("para asignar un instructor debe ser un instructor.")

            # validar que el resultado de aprendizaje pertenezca al programa de la ficha
            if attrs.get('ficha') and attrs.get('resultado_aprendizaje') and attrs['ficha'].programa != attrs[
                'resultado_aprendizaje'].programa:
                raise serializers.ValidationError(
                    "El resultado de aprendizaje debe pertenecer al programa de la ficha.")
            return attrs

class LlamadoAsistenciaSerializer(serializers.ModelSerializer):
    """Serializador para el modelo LlamadoAsistencia"""


    instructor_nombre = serializers.CharField(source='asignacion_instructor.instructor.nombre_completo', read_only=True)
    resultado_nombre = serializers.CharField(source='asignacion_instructor.resultado_aprendizaje.nombre', read_only=True)
    resultado_codigo = serializers.CharField(source='asignacion_instructor.resultado_aprendizaje.codigo', read_only=True)

    ficha_numero = serializers.CharField(source='asignacion_instructor.ficha.numero', read_only=True)

    programa_nombre = serializers.CharField(source='asignacion_instructor.ficha.programa.nombre', read_only=True)

    total_registros = serializers.SerializerMethodField()



    class Meta:
        model = LlamadoAsistencia
        fields = [
            'id', 'instructor', 'instructor_nombre', 'resultado_aprendizaje',
            'resultado_nombre', 'resultado_codigo', 'ficha', 'ficha_numero',
            'programa_nombre', 'fecha_hora_llamado', 'fecha_clase',
            'observaciones_generales', 'duracion_clase', 'total_registros',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'fecha_hora_llamado', 'created_at', 'updated_at',
            'instructor_nombre', 'resultado_nombre', 'resultado_codigo',
            'ficha_numero', 'programa_nombre', 'total_registros'
        ]

    def get_total_registros(self, obj):
        return obj.registros.count()


    def validate(self, attrs):
        if attrs.get('fecha_clase') and attrs['fecha_clase'] > timezone.now().date():
            raise serializers.ValidationError(
                "No se puede registrar asistencia para fechas futuras."
            )

        if all([attrs.get('instructor'), attrs.get('resultado_aprendizaje'), attrs.get('ficha')]):
            if not AsignacionInstructor.objects.filter(
                    instructor=attrs['instructor'],
                    resultado_aprendizaje=attrs['resultado_aprendizaje'],
                    ficha=attrs['ficha'],
                    activo=True
            ).exists():
                raise serializers.ValidationError(
                    "El instructor no está asignado a este resultado de aprendizaje en esta ficha."
                )

        return attrs

class RegistroAsistenciaSerializer(serializers.ModelSerializer):
    """SERIALIZADOR PARA EL MODELO DE REGISTRO DE ASISTENCIA"""

    aprendiz_nombre = serializers.CharField(source='aprendiz.nombre_completo', read_only=True)
    aprendiz_documento = serializers.CharField(source='aprendiz.documento', read_only=True)
    aprendiz_foto = serializers.SerializerMethodField()
    fecha_clase = serializers.DateField(source='llamado_asistencia.fecha_clase', read_only=True)
    resultado_nombre = serializers.CharField(source='llamado_asistencia.resultado_aprendizaje.nombre', read_only=True)



    class Meta:
        model = RegistroAsistencia
        fields = [
            'id', 'llamado_asistencia', 'aprendiz', 'aprendiz_nombre',
            'aprendiz_documento', 'aprendiz_foto', 'fecha_clase', 'resultado_nombre',
            'estado', 'hora_registro', 'minutos_tarde', 'observaciones',
            'se_retiro_antes', 'hora_retiro', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'hora_registro', 'created_at', 'updated_at',
            'aprendiz_nombre', 'aprendiz_documento', 'aprendiz_foto',
            'fecha_clase', 'resultado_nombre'
        ]

    def get_aprendiz_foto(self, obj):
        # Buscar foto en matrícula primero
        matricula = Matricula.objects.filter(
            aprendiz=obj.aprendiz,
            ficha=obj.llamado_asistencia.ficha
        ).first()

        if matricula and matricula.foto_perfil:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(matricula.foto_perfil.url)
            return matricula.foto_perfil.url

        # Si no hay foto en matrícula, usar la del usuario
        if obj.aprendiz.foto_perfil:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.aprendiz.foto_perfil.url)
            return obj.aprendiz.foto_perfil.url

        return None

    def validate(self, attrs):
        # Si llegó tarde, debe especificar minutos
        if attrs.get('estado') == 'TARDE' and attrs.get('minutos_tarde', 0) <= 0:
            raise serializers.ValidationError(
                "Si el estudiante llegó tarde, debe especificar los minutos de retraso."
            )

        # Si no llegó tarde, minutos_tarde debe ser 0
        if attrs.get('estado') != 'TARDE' and attrs.get('minutos_tarde', 0) > 0:
            raise serializers.ValidationError(
                "Solo se pueden registrar minutos de retraso si el estado es 'Llegó Tarde'."
            )

        # Si se retiró antes, debe tener hora de retiro
        if attrs.get('se_retiro_antes') and not attrs.get('hora_retiro'):
            raise serializers.ValidationError(
                "Si el estudiante se retiró antes, debe especificar la hora de retiro."
            )

        return attrs


# serializers.py

