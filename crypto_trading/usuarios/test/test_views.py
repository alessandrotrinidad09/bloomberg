from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from usuarios.models import UsuarioPersonalizado


class RegistroLoginIntegrationTest(TestCase):
    """Pruebas de flujo completo de registro y login"""
    
    @patch('usuarios.views.send_mail')
    def test_complete_registration_and_login_flow(self, mock_send_mail):
        """Test del flujo completo: registro -> activación -> login"""
        client = Client()
        
        # Paso 1: Registro
        response = client.post(reverse('registro'), {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan@example.com',
            'dni': '99999999',
            'telefono': '123456789',
            'direccion': 'Calle Test 123',
            'fecha_nacimiento': '1990-01-01',
            'password': 'securepass123',
            'password2': 'securepass123'
        })
        
        # Verificar que se redirige a activación pendiente
        self.assertRedirects(response, reverse('activacion_pendiente', kwargs={'email': 'juan@example.com'}))
        
        # Verificar que el usuario existe pero no está activo
        user = UsuarioPersonalizado.objects.get(email='juan@example.com')
        self.assertFalse(user.is_active)
        self.assertTrue(mock_send_mail.called)
        
        # Paso 2: Activar cuenta manualmente
        user.is_active = True
        user.is_verified = True
        user.save()
        
        # Paso 3: Login exitoso
        response = client.post(reverse('login'), {
            'email': 'juan@example.com',
            'password': 'securepass123'
        })
        self.assertRedirects(response, reverse('inicio'))
        
        # Verificar que el usuario está autenticado
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class TwoFactorAuthenticationFlowTest(TestCase):
    """Pruebas de flujo de autenticación de dos factores"""
    
    def setUp(self):
        self.client = Client()
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            dni='12345678',
            two_factor_enabled=False
        )
    
    @patch('usuarios.views.send_mail')
    def test_enable_2fa_and_login_with_code(self, mock_send_mail):
        """Test del flujo completo de activar 2FA y hacer login con código"""
        
        # Paso 1: Login y activar 2FA
        self.client.force_login(self.user)
        response = self.client.post(reverse('perfil'), {'toggle_2fa': 'true'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
        
        # Paso 2: Logout
        self.client.logout()
        
        # Paso 3: Intentar login con 2FA activado
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        # Verificar que se redirige a verificar código
        self.assertRedirects(response, reverse('verificar_codigo'))
        self.assertTrue(mock_send_mail.called)
        
        # Paso 4: Verificar código correcto
        self.user.refresh_from_db()
        codigo = self.user.two_factor_code
        
        response = self.client.post(reverse('verificar_codigo'), {
            'codigo': codigo
        })
        
        self.assertRedirects(response, reverse('inicio'))


class UserProfileUpdateFlowTest(TestCase):
    """Pruebas de flujo de actualización de perfil"""
    
    def setUp(self):
        self.client = Client()
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            dni='12345678',
            nombre='Nombre',
            apellido='Apellido'
        )
        self.client.force_login(self.user)
    
    def test_complete_profile_update_flow(self):
        """Test del flujo completo de actualización de perfil"""
        
        # Paso 1: Acceder al perfil
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 200)
        
        # Paso 2: Actualizar información personal
        response = self.client.post(reverse('perfil'), {
            'update_profile': 'true',
            'nombre': 'NuevoNombre',
            'apellido': 'NuevoApellido',
            'telefono': '987654321',
            'direccion': 'Nueva Dirección 456',
            'fecha_nacimiento': '1995-06-15'
        })
        
        # Verificar actualización
        self.user.refresh_from_db()
        self.assertEqual(self.user.nombre, 'NuevoNombre')
        self.assertEqual(self.user.apellido, 'NuevoApellido')
        self.assertEqual(self.user.telefono, '987654321')
        self.assertRedirects(response, reverse('perfil'))
