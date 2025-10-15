from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import UsuarioPersonalizado
from django.contrib.auth.hashers import make_password


# Create your views here.
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Intentamos buscar usuario por email
        try:
            usuario = UsuarioPersonalizado.objects.get(email=email)
            user = authenticate(request, username=usuario.username, password=password)
        except UsuarioPersonalizado.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('dashboard')  # redirige a tu panel principal
        else:
            messages.error(request, 'Correo o contraseña incorrectos')

    return render(request, 'usuarios/login.html')

def registro_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        dni = request.POST.get('dni')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Validaciones básicas
        if password != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect('registro')

        if UsuarioPersonalizado.objects.filter(email=email).exists():
            messages.error(request, "El correo ya está registrado.")
            return redirect('registro')

        if UsuarioPersonalizado.objects.filter(dni=dni).exists():
            messages.error(request, "El DNI ya está registrado.")
            return redirect('registro')

        # Crear usuario
        usuario = UsuarioPersonalizado.objects.create(
            username=email,  
            email=email,
            dni=dni,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            direccion=direccion,
            fecha_nacimiento=fecha_nacimiento if fecha_nacimiento else None,
            password=make_password(password),
        )

        login(request, usuario)
        messages.success(request, "Registro exitoso. Bienvenido a CryptoTrade.")
        return redirect('login')

    return render(request, 'usuarios/registro.html')

def logout_view(request):
    logout(request)
    return redirect('login')