from django.urls import path
from . import views


urlpatterns = [ 
    path('', views.landing_page, name='landing'),    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('activar/<uidb64>/<token>/', views.activar_cuenta, name='activar_cuenta'),
    path('activacion-pendiente/<str:email>/', views.activacion_pendiente, name='activacion_pendiente'),
    path('reenviar-activacion/<str:email>/', views.reenviar_activacion, name='reenviar_activacion'),

]
