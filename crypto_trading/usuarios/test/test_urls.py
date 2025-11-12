from django.test import SimpleTestCase
from django.urls import reverse, resolve
from usuarios.views import (
    login_view, registro_view, logout_view, 
    activar_cuenta, landing_page, perfil_view,
    inicio_view, monedas_view, inversiones_view
)


class TestUrls(SimpleTestCase):
    def test_login_url_resolves(self):
        url = reverse('login')
        self.assertEqual(resolve(url).func, login_view)
    
    def test_registro_url_resolves(self):
        url = reverse('registro')
        self.assertEqual(resolve(url).func, registro_view)
    
    def test_logout_url_resolves(self):
        url = reverse('logout')
        self.assertEqual(resolve(url).func, logout_view)
    
    def test_landing_url_resolves(self):
        url = reverse('landing')
        self.assertEqual(resolve(url).func, landing_page)
    
    def test_perfil_url_resolves(self):
        url = reverse('perfil')
        self.assertEqual(resolve(url).func, perfil_view)
    
    def test_inicio_url_resolves(self):
        url = reverse('inicio')
        self.assertEqual(resolve(url).func, inicio_view)
    
    def test_monedas_url_resolves(self):
        url = reverse('monedas')
        self.assertEqual(resolve(url).func, monedas_view)
    
    def test_inversiones_url_resolves(self):
        url = reverse('inversiones')
        self.assertEqual(resolve(url).func, inversiones_view)
