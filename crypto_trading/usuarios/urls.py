from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --- Rutas generales ---
    path('', views.landing_page, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    
    # --- Rutas de activación y verificación ---
    path('activar/<uidb64>/<token>/', views.activar_cuenta, name='activar_cuenta'),
    path('activacion-pendiente/<str:email>/', views.activacion_pendiente, name='activacion_pendiente'),
    path('reenviar-activacion/<str:email>/', views.reenviar_activacion, name='reenviar_activacion'),
    path('verificar-codigo/', views.verificar_codigo_view, name='verificar_codigo'),
    
    # --- Rutas de usuario y soporte ---
    path('perfil/', views.perfil_view, name='perfil'),
    path('contacto/', views.contacto, name='contacto'),
    
    # RUTA DEL CENTRO DE AYUDA (La única novedad aquí)
    path('ayuda/', views.centro_ayuda, name='centro_ayuda'),
    path('ayuda/<str:tema>/', views.articulo_ayuda, name='articulo_ayuda'),

    # --- Rutas del Panel de Trading ---
    path('panel/', views.inicio_view, name='inicio'),
    path('monedas/', views.monedas_view, name='monedas'),
    path('inversiones/', views.inversiones_view, name='inversiones'),

    # --- Restablecimiento de Contraseña ---
    path('password/reset/', auth_views.PasswordResetView.as_view(
            template_name='usuarios/password_reset_form.html',
            email_template_name='usuarios/emails/password_reset_email.txt',
            subject_template_name='usuarios/emails/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done')
        ), name='password_reset'),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(
            template_name='usuarios/password_reset_done.html'
        ), name='password_reset_done'),
    path('password/reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
            template_name='usuarios/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete')
        ), name='password_reset_confirm'),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
            template_name='usuarios/password_reset_complete.html'
        ), name='password_reset_complete'),

    path('privacidad/', views.privacidad, name='privacidad'),
    path('terminos/', views.terminos, name='terminos'),
]