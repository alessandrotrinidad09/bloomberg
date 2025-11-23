from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPersonalizado

@admin.register(UsuarioPersonalizado)
class UsuarioPersonalizadoAdmin(UserAdmin):
    # 1. Columnas que se ven en la lista de usuarios
    list_display = ('email', 'username', 'nombre', 'apellido', 'notif_marketing', 'priv_perfil_publico', 'is_active')
    
    # 2. Filtros laterales (Aquí está la magia para Marketing)
    list_filter = ('notif_marketing', 'priv_perfil_publico', 'is_active', 'is_staff')
    
    # 3. Campos de búsqueda
    search_fields = ('email', 'username', 'dni', 'nombre', 'apellido')

    # 4. Organización de los campos al editar un usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Información Financiera', {
            'fields': ('balance', 'risk_profile', 'preferences')
        }),
        ('Información Adicional', {
            'fields': ('dni', 'nombre', 'apellido', 'telefono', 'direccion', 'fecha_nacimiento')
        }),
        # Nueva sección para ver los switches en el admin
        ('Preferencias y Privacidad', {
            'fields': ('notif_inicio_sesion', 'notif_marketing', 'priv_perfil_publico', 'priv_compartir_datos')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {
            'fields': ('nombre', 'apellido', 'dni', 'telefono', 'direccion', 'fecha_nacimiento')
        }),
    )