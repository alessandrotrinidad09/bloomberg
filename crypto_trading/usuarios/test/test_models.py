from django.test import TestCase
from django.contrib.auth import get_user_model
from usuarios.models import UsuarioPersonalizado
from decimal import Decimal


class UsuarioPersonalizadoModelTest(TestCase):
    """Tests para el modelo UsuarioPersonalizado"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.user = UsuarioPersonalizado.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            dni='12345678',
            nombre='Test',
            apellido='User',
            telefono='123456789',
            direccion='Calle Test 123'
        )
    
    def test_create_user(self):
        """Verifica que se puede crear un usuario correctamente"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.dni, '12345678')
        self.assertEqual(self.user.nombre, 'Test')
        self.assertEqual(self.user.apellido, 'User')
        self.assertTrue(isinstance(self.user, UsuarioPersonalizado))
    
    def test_user_string_representation(self):
        """Verifica el método __str__ del modelo"""
        # Tu modelo retorna: f"{self.username} ({self.nombre} {self.apellido})"
        expected = f"{self.user.username} ({self.user.nombre} {self.user.apellido})"
        self.assertEqual(str(self.user), expected)
    
    
    
    def test_user_dni_is_unique(self):
        """Verifica que el DNI debe ser único"""
        with self.assertRaises(Exception):
            UsuarioPersonalizado.objects.create_user(
                username='test2@example.com',
                email='test2@example.com',
                password='testpass456',
                dni='12345678',  # DNI duplicado
                nombre='Test2',
                apellido='User2'
            )
    
    def test_generate_two_factor_code(self):
        """Verifica que se genera código 2FA correctamente"""
        code = self.user.generate_two_factor_code()
        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        # Verificar que el código se guardó en el usuario
        self.user.refresh_from_db()
        self.assertEqual(self.user.two_factor_code, code)
    
    def test_two_factor_enabled_default_false(self):
        """Verifica que 2FA está desactivado por defecto"""
        self.assertFalse(self.user.two_factor_enabled)
    
    def test_is_verified_default_false(self):
        """Verifica que is_verified es False por defecto"""
        new_user = UsuarioPersonalizado.objects.create_user(
            username='new@example.com',
            email='new@example.com',
            password='pass123',
            dni='87654321',
            nombre='New',
            apellido='User'
        )
        self.assertFalse(new_user.is_verified)
    
    def test_user_is_active_default_false(self):
        """Verifica que is_active es False por defecto (según tu modelo)"""
        # Tu modelo tiene is_active = False por defecto
        new_user = UsuarioPersonalizado.objects.create(
            username='inactive@example.com',
            email='inactive@example.com',
            password='pass123',
            dni='11111111',
            nombre='Inactive',
            apellido='User'
        )
        self.assertFalse(new_user.is_active)
    
    def test_username_equals_email(self):
        """Verifica que username es igual al email"""
        self.assertEqual(self.user.username, self.user.email)
    
    def test_user_can_login(self):
        """Verifica que el usuario puede autenticarse"""
        # Activar usuario primero (tu modelo tiene is_active=False por defecto)
        self.user.is_active = True
        self.user.save()
        
        from django.contrib.auth import authenticate
        user = authenticate(username='test@example.com', password='testpass123')
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')
    
    def test_user_password_is_hashed(self):
        """Verifica que la contraseña está hasheada"""
        self.assertNotEqual(self.user.password, 'testpass123')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_optional_fields(self):
        """Verifica que campos opcionales pueden ser nulos"""
        minimal_user = UsuarioPersonalizado.objects.create_user(
            username='minimal@example.com',
            email='minimal@example.com',
            password='pass123',
            dni='99999999',
            nombre='Minimal',
            apellido='User'
        )
        self.assertIsNotNone(minimal_user)
        self.assertIsNone(minimal_user.telefono)
        self.assertIsNone(minimal_user.direccion)
        self.assertIsNone(minimal_user.fecha_nacimiento)
    
    def test_balance_default_value(self):
        """Verifica que el balance por defecto es 0.0"""
        self.assertEqual(self.user.balance, Decimal('0.0'))
    
    def test_risk_profile_default_value(self):
        """Verifica que el perfil de riesgo por defecto es MOD"""
        self.assertEqual(self.user.risk_profile, 'MOD')
    
    def test_preferences_default_value(self):
        """Verifica que preferences por defecto es un dict vacío"""
        new_user = UsuarioPersonalizado.objects.create_user(
            username='prefs@example.com',
            email='prefs@example.com',
            password='pass123',
            dni='55555555',
            nombre='Prefs',
            apellido='User'
        )
        self.assertEqual(new_user.preferences, {})
    
    def test_dni_max_length(self):
        """Verifica que el DNI tiene máximo 8 caracteres"""
        self.assertEqual(self.user._meta.get_field('dni').max_length, 8)
    
    def test_nombre_max_length(self):
        """Verifica que nombre tiene máximo 30 caracteres"""
        self.assertEqual(self.user._meta.get_field('nombre').max_length, 30)
    
    def test_apellido_max_length(self):
        """Verifica que apellido tiene máximo 30 caracteres"""
        self.assertEqual(self.user._meta.get_field('apellido').max_length, 30)


class UsuarioTradingFieldsTest(TestCase):
    """Tests específicos para campos de trading"""
    
    def setUp(self):
        self.user = UsuarioPersonalizado.objects.create_user(
            username='trader@example.com',
            email='trader@example.com',
            password='testpass123',
            dni='33333333',
            nombre='Trader',
            apellido='User'
        )
    
    def test_update_balance(self):
        """Verifica que se puede actualizar el balance"""
        self.user.balance = Decimal('1000.50')
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal('1000.50'))
    
    def test_risk_profile_choices(self):
        """Verifica que se pueden establecer los perfiles de riesgo"""
        # Conservador
        self.user.risk_profile = 'CON'
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.risk_profile, 'CON')
        
        # Moderado
        self.user.risk_profile = 'MOD'
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.risk_profile, 'MOD')
        
        # Agresivo
        self.user.risk_profile = 'AGR'
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.risk_profile, 'AGR')
    
    def test_preferences_json_field(self):
        """Verifica que se pueden guardar preferencias en JSON"""
        preferences = {
            'notifications': True,
            'theme': 'dark',
            'language': 'es'
        }
        self.user.preferences = preferences
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.preferences, preferences)
        self.assertTrue(self.user.preferences['notifications'])
    
    def test_balance_decimal_places(self):
        """Verifica que el balance soporta 2 decimales"""
        self.user.balance = Decimal('9999.99')
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal('9999.99'))
    
    def test_balance_max_digits(self):
        """Verifica que el balance soporta hasta 20 dígitos"""
        large_balance = Decimal('999999999999999999.99')
        self.user.balance = large_balance
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, large_balance)


class TwoFactorAuthenticationModelTest(TestCase):
    """Tests específicos para funcionalidad 2FA"""
    
    def setUp(self):
        self.user = UsuarioPersonalizado.objects.create_user(
            username='2fa@example.com',
            email='2fa@example.com',
            password='testpass123',
            dni='44444444',
            nombre='TwoFA',
            apellido='User'
        )
    
    def test_enable_two_factor_authentication(self):
        """Verifica activación de 2FA"""
        self.user.two_factor_enabled = True
        self.user.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
    
    def test_disable_two_factor_authentication(self):
        """Verifica desactivación de 2FA"""
        self.user.two_factor_enabled = True
        self.user.save()
        self.user.two_factor_enabled = False
        self.user.save()
        self.user.refresh_from_db()
        self.assertFalse(self.user.two_factor_enabled)
    
    def test_two_factor_code_generation(self):
        """Verifica generación de código 2FA"""
        code = self.user.generate_two_factor_code()
        self.user.refresh_from_db()
        self.assertEqual(self.user.two_factor_code, code)
    
    def test_two_factor_code_is_numeric(self):
        """Verifica que el código 2FA es numérico de 6 dígitos"""
        code = self.user.generate_two_factor_code()
        self.assertTrue(code.isdigit())
        self.assertEqual(len(code), 6)
    
    def test_two_factor_code_range(self):
        """Verifica que el código 2FA está en el rango correcto"""
        code = self.user.generate_two_factor_code()
        code_int = int(code)
        self.assertGreaterEqual(code_int, 100000)
        self.assertLessEqual(code_int, 999999)
    
    def test_two_factor_code_can_be_null(self):
        """Verifica que two_factor_code puede ser null"""
        self.assertIsNone(self.user.two_factor_code)


class UsuarioManagerTest(TestCase):
    """Tests para el manager del modelo UsuarioPersonalizado"""
    
    def test_create_user_with_all_fields(self):
        """Verifica creación de usuario con todos los campos"""
        user = UsuarioPersonalizado.objects.create_user(
            username='complete@example.com',
            email='complete@example.com',
            password='testpass123',
            dni='66666666',
            nombre='Complete',
            apellido='User',
            telefono='987654321',
            direccion='Av. Test 456',
            fecha_nacimiento='1995-05-15'
        )
        self.assertEqual(user.email, 'complete@example.com')
        self.assertEqual(user.nombre, 'Complete')
        self.assertEqual(user.apellido, 'User')
        self.assertEqual(user.telefono, '987654321')
        self.assertEqual(user.direccion, 'Av. Test 456')
    
    

class UsuarioVerificationTest(TestCase):
    """Tests para verificación de usuarios"""
    
    def setUp(self):
        self.user = UsuarioPersonalizado.objects.create_user(
            username='verify@example.com',
            email='verify@example.com',
            password='testpass123',
            dni='77777777',
            nombre='Verify',
            apellido='User'
        )
    
    def test_user_not_verified_by_default(self):
        """Verifica que usuarios nuevos no están verificados"""
        self.assertFalse(self.user.is_verified)
    
    def test_user_not_active_by_default(self):
        """Verifica que usuarios nuevos no están activos"""
        self.assertFalse(self.user.is_active)
    
    def test_activate_user(self):
        """Verifica activación de usuario"""
        self.user.is_active = True
        self.user.is_verified = True
        self.user.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_verified)
