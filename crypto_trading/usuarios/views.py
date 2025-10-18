from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import UsuarioPersonalizado
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required

#METODOS PARA TRABAJAR CON EMAIL 
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings

# Create your views here.
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            usuario = UsuarioPersonalizado.objects.get(email=email)
        except UsuarioPersonalizado.DoesNotExist:
            usuario = None

        if usuario is not None:
            if not usuario.is_active:
                messages.warning(request, 'Tu cuenta aún no está activada. Revisa tu correo o solicita un nuevo enlace.')
                return redirect('activacion_pendiente', email=usuario.email)

            user = authenticate(request, username=usuario.username, password=password)

            if user is not None:
                # ✅ Si el usuario tiene 2FA activado
                if user.two_factor_enabled:
                    code = user.generate_two_factor_code()
                    send_mail(
                        subject='Código de verificación - CryptoTrade',
                        message=f'Tu código de verificación es: {code}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    # Guardamos el ID del usuario en la sesión para continuar la verificación
                    request.session['pending_user_id'] = user.id
                    messages.info(request, 'Se ha enviado un código de verificación a tu correo.')
                    return redirect('verificar_codigo')

                # 🚀 Si no tiene 2FA, entra directo
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Contraseña incorrecta.')
        else:
            messages.error(request, 'No existe una cuenta registrada con ese correo.')

    return render(request, 'usuarios/login.html')


def enviar_mail_activacion(request, usuario):
    """
    Esta función construye el enlace de activación y envía el correo.
    Con console.EmailBackend, el contenido aparecerá en la terminal.
    """
    token = default_token_generator.make_token(usuario)
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    activation_link = request.build_absolute_uri(
        reverse('activar_cuenta', kwargs={'uidb64': uid, 'token': token})
    )

    # Puedes usar render_to_string con una plantilla .txt
    subject = "Activa tu cuenta en CryptoTrade"
    # plantilla de texto: templates/usuarios/emails/activation_email.txt
    message = render_to_string('usuarios/emails/activation_email.txt', {
        'user': usuario,
        'activation_link': activation_link,
    })

    # send_mail(from_email = settings.DEFAULT_FROM_EMAIL si pones None Django usa DEFAULT_FROM_EMAIL)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [usuario.email], fail_silently=False)


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

        # Crear usuario inactivo
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
            is_active=False,
            is_verified=False,
        )

        # Enviar correo de activación (a la consola)
        enviar_mail_activacion(request, usuario)

        # Redirigir a la vista "activación pendiente"
        return redirect('activacion_pendiente', email=usuario.email)

    return render(request, 'usuarios/registro.html')


def activacion_pendiente(request, email):
    """
    Muestra mensaje para activar la cuenta y opción de reenviar correo.
    """
    contexto = {'email': email}
    return render(request, 'usuarios/activacion_pendiente.html', contexto)

# -----------------------------------
# Vista para reenviar el correo
# -----------------------------------
def reenviar_activacion(request, email):
    try:
        usuario = UsuarioPersonalizado.objects.get(email=email)
    except UsuarioPersonalizado.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        return redirect('registro')

    if usuario.is_active:
        messages.info(request, "Tu cuenta ya está activada.")
        return redirect('login')

    enviar_mail_activacion(request, usuario)
    messages.success(request, "Se ha reenviado el enlace de activación a tu correo.")
    return redirect('activacion_pendiente', email=email)



# -----------------------------------
# Activar cuenta desde enlace
# -----------------------------------
def activar_cuenta(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        usuario = UsuarioPersonalizado.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UsuarioPersonalizado.DoesNotExist):
        usuario = None

    if usuario is not None and default_token_generator.check_token(usuario, token):
        usuario.is_active = True
        usuario.is_verified = True
        usuario.save()
        messages.success(request, "Tu cuenta ha sido activada correctamente. Ya puedes iniciar sesión.")
        return redirect('login')
    else:
        messages.error(request, "El enlace de activación no es válido o ha expirado.")
        return redirect('registro')
    


def logout_view(request):
    logout(request)
    return redirect('login')


def landing_page(request):
    return render(request, 'usuarios/landing.html')



# VERIFICAR CÓDIGO 2FA
def verificar_codigo_view(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('login')

    usuario = UsuarioPersonalizado.objects.get(id=user_id)

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')
        if codigo_ingresado == usuario.two_factor_code:
            usuario.two_factor_code = None  # Limpia el código
            usuario.save()
            login(request, usuario)
            del request.session['pending_user_id']
            return redirect('dashboard')
        else:
            messages.error(request, 'Código incorrecto. Intenta nuevamente.')

    return render(request, 'usuarios/verificar_codigo.html', {'email': usuario.email})

@login_required
def configurar_2fa_view(request):
    user = request.user
    if request.method == 'POST':
        opcion = request.POST.get('opcion')
        user.two_factor_enabled = (opcion == 'activar')
        user.save()
        msg = "Autenticación en dos pasos activada." if opcion == 'activar' else "Autenticación en dos pasos desactivada."
        messages.success(request, msg)
    return render(request, 'usuarios/configurar_2fa.html', {'user': user})

# usuarios/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def perfil_view(request):
    user = request.user

    #Actualizar datos personales
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user.nombre = request.POST.get('nombre')
            user.apellido = request.POST.get('apellido')
            user.telefono = request.POST.get('telefono')
            user.direccion = request.POST.get('direccion')
            user.fecha_nacimiento = request.POST.get('fecha_nacimiento')
            user.save()
            messages.success(request, "Datos personales actualizados correctamente.")
            return redirect('perfil')

        #Activar o desactivar 2FA
        elif 'toggle_2fa' in request.POST:
            user.two_factor_enabled = not user.two_factor_enabled
            user.save()

            if user.two_factor_enabled:
                messages.success(request, "Autenticación en dos pasos ACTIVADA.")
            else:
                messages.info(request, "Autenticación en dos pasos DESACTIVADA.")

            return redirect('perfil')

    return render(request, 'usuarios/perfil.html')
