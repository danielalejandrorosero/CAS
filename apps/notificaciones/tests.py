from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from .models import (
    TipoNotificacion,
    Notificacion,
    ConfiguracionNotificacion,
    HistorialNotificacion
)
from .services import NotificacionService
from apps.usuarios.models import Rol, Usuario


class TipoNotificacionModelTest(TestCase):
    """Tests para el modelo TipoNotificacion"""
    
    def setUp(self):
        self.tipo = TipoNotificacion.objects.create(
            nombre='NUEVA_ACTIVIDAD',
            descripcion='Notificación de nueva actividad',
            activo=True
        )
    
    def test_str_representation(self):
        self.assertEqual(str(self.tipo), 'Nueva Actividad')
    
    def test_tipo_activo(self):
        self.assertTrue(self.tipo.activo)


class NotificacionModelTest(TestCase):
    """Tests para el modelo Notificacion"""
    
    def setUp(self):
        # Crear rol y usuario
        self.rol_aprendiz = Rol.objects.create(nombre='APRENDIZ')
        self.usuario = Usuario.objects.create(
            numero_documento='12345678',
            nombres='Juan',
            apellidos='Pérez',
            email='juan@test.com',
            rol=self.rol_aprendiz
        )
        
        # Crear tipo de notificación
        self.tipo = TipoNotificacion.objects.create(
            nombre='NUEVA_ACTIVIDAD',
            descripcion='Test',
            activo=True
        )
        
        # Crear notificación
        self.notificacion = Notificacion.objects.create(
            usuario=self.usuario,
            tipo=self.tipo,
            titulo='Test Notificación',
            mensaje='Mensaje de prueba'
        )
    
    def test_str_representation(self):
        expected = f'Test Notificación - {self.usuario.get_full_name()}'
        self.assertEqual(str(self.notificacion), expected)
    
    def test_notificacion_no_leida_por_defecto(self):
        self.assertFalse(self.notificacion.leida)
        self.assertIsNone(self.notificacion.fecha_lectura)
    
    def test_marcar_como_leida(self):
        self.notificacion.marcar_como_leida()
        self.assertTrue(self.notificacion.leida)
        self.assertIsNotNone(self.notificacion.fecha_lectura)


class ConfiguracionNotificacionModelTest(TestCase):
    """Tests para el modelo ConfiguracionNotificacion"""
    
    def setUp(self):
        self.rol_aprendiz = Rol.objects.create(nombre='APRENDIZ')
        self.usuario = Usuario.objects.create(
            numero_documento='12345678',
            nombres='Juan',
            apellidos='Pérez',
            email='juan@test.com',
            rol=self.rol_aprendiz
        )
        
        self.config = ConfiguracionNotificacion.objects.create(
            usuario=self.usuario,
            dias_activos=[0, 1, 2, 3, 4]  # Lunes a Viernes
        )
    
    def test_configuracion_por_defecto(self):
        self.assertTrue(self.config.notificaciones_push)
        self.assertTrue(self.config.notificaciones_email)
        self.assertTrue(self.config.nueva_actividad)
    
    def test_puede_recibir_notificacion(self):
        # Test con tipo habilitado
        puede = self.config.puede_recibir_notificacion('NUEVA_ACTIVIDAD')
        # El resultado depende del día y hora actual
        self.assertIsInstance(puede, bool)


class NotificacionServiceTest(TestCase):
    """Tests para el servicio de notificaciones"""
    
    def setUp(self):
        # Crear rol y usuario
        self.rol_aprendiz = Rol.objects.create(nombre='APRENDIZ')
        self.usuario = Usuario.objects.create(
            numero_documento='12345678',
            nombres='Juan',
            apellidos='Pérez',
            email='juan@test.com',
            rol=self.rol_aprendiz
        )
        
        # Crear tipo de notificación
        self.tipo = TipoNotificacion.objects.create(
            nombre='NUEVA_ACTIVIDAD',
            descripcion='Test',
            activo=True
        )
    
    def test_enviar_notificacion(self):
        notificacion = NotificacionService.enviar_notificacion(
            usuario=self.usuario,
            tipo_notificacion='NUEVA_ACTIVIDAD',
            titulo='Test',
            mensaje='Mensaje de prueba'
        )
        
        self.assertIsNotNone(notificacion)
        self.assertEqual(notificacion.usuario, self.usuario)
        self.assertEqual(notificacion.titulo, 'Test')
    
    def test_enviar_notificacion_tipo_inexistente(self):
        notificacion = NotificacionService.enviar_notificacion(
            usuario=self.usuario,
            tipo_notificacion='TIPO_INEXISTENTE',
            titulo='Test',
            mensaje='Mensaje de prueba'
        )
        
        self.assertIsNone(notificacion)
    
    def test_enviar_notificacion_masiva(self):
        # Crear otro usuario
        usuario2 = Usuario.objects.create(
            numero_documento='87654321',
            nombres='María',
            apellidos='García',
            email='maria@test.com',
            rol=self.rol_aprendiz
        )
        
        resultado = NotificacionService.enviar_notificacion_masiva(
            usuarios=[self.usuario, usuario2],
            tipo_notificacion='NUEVA_ACTIVIDAD',
            titulo='Test Masivo',
            mensaje='Mensaje masivo'
        )
        
        self.assertEqual(resultado['total'], 2)
        self.assertEqual(resultado['enviadas'], 2)
        self.assertEqual(resultado['fallidas'], 0)


class NotificacionAPITest(APITestCase):
    """Tests para la API de notificaciones"""
    
    def setUp(self):
        # Crear rol y usuario
        self.rol_aprendiz = Rol.objects.create(nombre='APRENDIZ')
        self.usuario = Usuario.objects.create(
            numero_documento='12345678',
            nombres='Juan',
            apellidos='Pérez',
            email='juan@test.com',
            rol=self.rol_aprendiz
        )
        
        # Crear tipo de notificación
        self.tipo = TipoNotificacion.objects.create(
            nombre='NUEVA_ACTIVIDAD',
            descripcion='Test',
            activo=True
        )
        
        # Crear notificación
        self.notificacion = Notificacion.objects.create(
            usuario=self.usuario,
            tipo=self.tipo,
            titulo='Test API',
            mensaje='Mensaje de prueba API'
        )
        
        # Autenticar usuario
        self.client.force_authenticate(user=self.usuario)
    
    def test_listar_notificaciones(self):
        url = reverse('notificaciones:notificaciones-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_detalle_notificacion(self):
        url = reverse('notificaciones:notificacion-detail', kwargs={'pk': self.notificacion.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['titulo'], 'Test API')
        
        # Verificar que se marcó como leída
        self.notificacion.refresh_from_db()
        self.assertTrue(self.notificacion.leida)
    
    def test_resumen_notificaciones(self):
        url = reverse('notificaciones:resumen')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['no_leidas'], 1)
    
    def test_marcar_como_leidas(self):
        url = reverse('notificaciones:marcar-leidas')
        data = {'notificacion_ids': [self.notificacion.id]}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        
        # Verificar que se marcó como leída
        self.notificacion.refresh_from_db()
        self.assertTrue(self.notificacion.leida)
    
    def test_configuracion_notificaciones(self):
        url = reverse('notificaciones:configuracion')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['notificaciones_push'])
    
    def test_actualizar_configuracion(self):
        url = reverse('notificaciones:configuracion')
        data = {
            'notificaciones_push': False,
            'nueva_actividad': False
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['notificaciones_push'])
        self.assertFalse(response.data['nueva_actividad'])
    
    def test_notificaciones_no_leidas(self):
        url = reverse('notificaciones:no-leidas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_eliminar_notificacion(self):
        url = reverse('notificaciones:eliminar', kwargs={'pk': self.notificacion.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Notificacion.objects.filter(pk=self.notificacion.pk).exists())


class NotificacionPermissionsTest(APITestCase):
    """Tests para permisos de la API"""
    
    def test_acceso_sin_autenticacion(self):
        url = reverse('notificaciones:notificaciones-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_crear_notificacion_sin_permisos(self):
        # Crear usuario aprendiz
        rol_aprendiz = Rol.objects.create(nombre='APRENDIZ')
        usuario = Usuario.objects.create(
            numero_documento='12345678',
            nombres='Juan',
            apellidos='Pérez',
            email='juan@test.com',
            rol=rol_aprendiz
        )
        
        self.client.force_authenticate(user=usuario)
        
        url = reverse('notificaciones:notificaciones-create')
        data = {
            'usuario': usuario.id,
            'tipo': 1,
            'titulo': 'Test',
            'mensaje': 'Mensaje'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)