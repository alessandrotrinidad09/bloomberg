from django.test import TestCase

# Create your tests here.

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from unittest.mock import patch, MagicMock
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .models import UsuarioPersonalizado


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            dni='12345678',
            is_active=True
        )
    
    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/login.html')
    
    def test_login_successful(self):
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('inicio'))
    
    def test_login_with_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('activacion_pendiente', kwargs={'email': self.user.email}))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('no está activada' in str(m) for m in messages))
    
    def test_login_with_incorrect_password(self):
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('incorrecta' in str(m) for m in messages))
    
    def test_login_with_nonexistent_email(self):
        response = self.client.post(reverse('login'), {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('No existe una cuenta' in str(m) for m in messages))
    
    @patch('usuarios.views.send_mail')
    def test_login_with_2fa_enabled(self, mock_send_mail):
        self.user.two_factor_enabled = True
        self.user.save()
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('verificar_codigo'))
        self.assertTrue(mock_send_mail.called)


class RegistroViewTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_registro_view_get(self):
        response = self.client.get(reverse('registro'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/registro.html')
    
    @patch('usuarios.views.enviar_mail_activacion')
    def test_registro_successful(self, mock_enviar_mail):
        response = self.client.post(reverse('registro'), {
            'nombre': 'John',
            'apellido': 'Doe',
            'email': 'john@example.com',
            'dni': '87654321',
            'telefono': '123456789',
            'direccion': 'Test Address',
            'fecha_nacimiento': '1990-01-01',
            'password': 'securepass123',
            'password2': 'securepass123'
        })
        self.assertTrue(UsuarioPersonalizado.objects.filter(email='john@example.com').exists())
        self.assertTrue(mock_enviar_mail.called)
        self.assertRedirects(response, reverse('activacion_pendiente', kwargs={'email': 'john@example.com'}))
    
    def test_registro_passwords_do_not_match(self):
        response = self.client.post(reverse('registro'), {
            'nombre': 'John',
            'apellido': 'Doe',
            'email': 'john@example.com',
            'dni': '87654321',
            'password': 'securepass123',
            'password2': 'differentpass'
        })
        self.assertRedirects(response, reverse('registro'))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('no coinciden' in str(m) for m in messages))
    
    def test_registro_email_already_exists(self):
        UsuarioPersonalizado.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='pass123',
            dni='11111111'
        )
        response = self.client.post(reverse('registro'), {
            'nombre': 'John',
            'apellido': 'Doe',
            'email': 'existing@example.com',
            'dni': '99999999',
            'password': 'securepass123',
            'password2': 'securepass123'
        })
        self.assertRedirects(response, reverse('registro'))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('correo ya está registrado' in str(m) for m in messages))
    
    def test_registro_dni_already_exists(self):
        UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='pass123',
            dni='12345678'
        )
        response = self.client.post(reverse('registro'), {
            'nombre': 'John',
            'apellido': 'Doe',
            'email': 'newuser@example.com',
            'dni': '12345678',
            'password': 'securepass123',
            'password2': 'securepass123'
        })
        self.assertRedirects(response, reverse('registro'))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('DNI ya está registrado' in str(m) for m in messages))


class ActivacionCuentaTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            dni='12345678',
            is_active=False,
            is_verified=False
        )
    
    def test_activacion_pendiente_view(self):
        response = self.client.get(reverse('activacion_pendiente', kwargs={'email': self.user.email}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/activacion_pendiente.html')
        self.assertContains(response, self.user.email)
    
    @patch('usuarios.views.enviar_mail_activacion')
    def test_reenviar_activacion_successful(self, mock_enviar_mail):
        response = self.client.get(reverse('reenviar_activacion', kwargs={'email': self.user.email}))
        self.assertTrue(mock_enviar_mail.called)
        self.assertRedirects(response, reverse('activacion_pendiente', kwargs={'email': self.user.email}))
    
    def test_reenviar_activacion_user_not_found(self):
        response = self.client.get(reverse('reenviar_activacion', kwargs={'email': 'nonexistent@example.com'}))
        self.assertRedirects(response, reverse('registro'))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('no encontrado' in str(m) for m in messages))
    
    def test_reenviar_activacion_already_active(self):
        self.user.is_active = True
        self.user.save()
        response = self.client.get(reverse('reenviar_activacion', kwargs={'email': self.user.email}))
        self.assertRedirects(response, reverse('login'))
    
    def test_activar_cuenta_successful(self):
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(reverse('activar_cuenta', kwargs={'uidb64': uid, 'token': token}))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_verified)
        self.assertRedirects(response, reverse('login'))
    
    def test_activar_cuenta_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(reverse('activar_cuenta', kwargs={'uidb64': uid, 'token': 'invalid-token'}))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertRedirects(response, reverse('registro'))


class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            dni='12345678'
        )
    
    def test_logout_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))


class VerificarCodigoViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            dni='12345678',
            two_factor_enabled=True
        )
        self.user.two_factor_code = '123456'
        self.user.save()
    
    def test_verificar_codigo_without_session(self):
        response = self.client.get(reverse('verificar_codigo'))
        self.assertRedirects(response, reverse('login'))
    
    def test_verificar_codigo_get(self):
        session = self.client.session
        session['pending_user_id'] = self.user.id
        session.save()
        response = self.client.get(reverse('verificar_codigo'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/verificar_codigo.html')
    
    def test_verificar_codigo_correct(self):
        session = self.client.session
        session['pending_user_id'] = self.user.id
        session.save()
        response = self.client.post(reverse('verificar_codigo'), {'codigo': '123456'})
        self.assertRedirects(response, reverse('inicio'))
    
    def test_verificar_codigo_incorrect(self):
        session = self.client.session
        session['pending_user_id'] = self.user.id
        session.save()
        response = self.client.post(reverse('verificar_codigo'), {'codigo': 'wrong'})
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('incorrecto' in str(m) for m in messages))


class Configurar2FAViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            dni='12345678'
        )
        self.client.force_login(self.user)
    
    def test_configurar_2fa_get(self):
        response = self.client.get(reverse('configurar_2fa'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/configurar_2fa.html')
    
    def test_configurar_2fa_activar(self):
        response = self.client.post(reverse('configurar_2fa'), {'opcion': 'activar'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
    
    def test_configurar_2fa_desactivar(self):
        self.user.two_factor_enabled = True
        self.user.save()
        response = self.client.post(reverse('configurar_2fa'), {'opcion': 'desactivar'})
        self.user.refresh_from_db()
        self.assertFalse(self.user.two_factor_enabled)


class PerfilViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            dni='12345678',
            nombre='Test',
            apellido='User'
        )
        self.client.force_login(self.user)
    
    def test_perfil_view_get(self):
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/perfil.html')
    
    def test_perfil_update_datos_personales(self):
        response = self.client.post(reverse('perfil'), {
            'update_profile': 'true',
            'nombre': 'Updated',
            'apellido': 'Name',
            'telefono': '987654321',
            'direccion': 'New Address',
            'fecha_nacimiento': '1995-05-15'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.nombre, 'Updated')
        self.assertEqual(self.user.apellido, 'Name')
        self.assertRedirects(response, reverse('perfil'))
    
    def test_perfil_toggle_2fa(self):
        response = self.client.post(reverse('perfil'), {'toggle_2fa': 'true'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
        self.assertRedirects(response, reverse('perfil'))


class PanelControlViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            dni='12345678'
        )
        self.client.force_login(self.user)
    
    def test_inicio_view(self):
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/inicio.html')
    
    def test_monedas_view(self):
        response = self.client.get(reverse('monedas'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/monedas.html')
    
    def test_inversiones_view(self):
        response = self.client.get(reverse('inversiones'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/inversiones.html')
    
    def test_panel_views_require_login(self):
        self.client.logout()
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 302)


class EnviarMailActivacionTest(TestCase):
    def setUp(self):
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            dni='12345678'
        )
    
    @patch('usuarios.views.send_mail')
    def test_enviar_mail_activacion(self, mock_send_mail):
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        from usuarios.views import enviar_mail_activacion
        enviar_mail_activacion(request, self.user)
        self.assertTrue(mock_send_mail.called)
        self.assertEqual(mock_send_mail.call_args[1]['recipient_list'], [self.user.email])


class LandingPageTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_landing_page_view(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/landing.html')
