from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPersonalizado

# Register your models here.
@admin.register(UsuarioPersonalizado)
class UsuarioPersonalizadoAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('dni', 'nombre', 'apellido', 'telefono', 'direccion', 'fecha_nacimiento')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('nombre','apellido','dni', 'telefono', 'direccion','fecha_nacimiento')}),
    )