from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import UsuarioPersonalizado
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _

# METODOS PARA TRABAJAR CON EMAIL
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings

from django.shortcuts import get_object_or_404
from django.http import Http404

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
                messages.warning(request, _('Tu cuenta aún no está activada. Revisa tu correo o solicita un nuevo enlace.'))
                return redirect('activacion_pendiente', email=usuario.email)

            user = authenticate(request, username=usuario.username, password=password)

            if user is not None:
                # --- LÓGICA DE 2FA ---
                if user.two_factor_enabled:
                    code = user.generate_two_factor_code()
                    send_mail(
                        subject=_('Código de verificación - CryptoTrade'),
                        message=_('Tu código de verificación es: %s') % code,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    request.session['pending_user_id'] = user.id
                    messages.info(request, _('Se ha enviado un código de verificación a tu correo.'))
                    return redirect('verificar_codigo')

                # --- INICIO DE SESIÓN DIRECTO (SIN 2FA) ---
                login(request, user)

                # [NUEVO] Lógica de Alerta de Seguridad (Historia D5)
                if user.notif_inicio_sesion:
                    send_mail(
                        subject=_('Alerta de seguridad: Nuevo inicio de sesión'),
                        message=_('Hola %(nombre)s, se detectó un nuevo inicio de sesión en tu cuenta de CryptoTrade.') % {'nombre': user.nombre},
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )

                return redirect('inicio')
            else:
                messages.error(request, _('Contraseña incorrecta.'))
        else:
            messages.error(request, _('No existe una cuenta registrada con ese correo.'))

    return render(request, 'usuarios/login.html')


def enviar_mail_activacion(request, usuario):
    token = default_token_generator.make_token(usuario)
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    activation_link = request.build_absolute_uri(
        reverse('activar_cuenta', kwargs={'uidb64': uid, 'token': token})
    )
    subject = _("Activa tu cuenta en CryptoTrade")
    message = render_to_string('usuarios/emails/activation_email.txt', {
        'user': usuario,
        'activation_link': activation_link,
    })
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

        if password != password2:
            messages.error(request, _("Las contraseñas no coinciden."))
            return redirect('registro')
        if UsuarioPersonalizado.objects.filter(email=email).exists():
            messages.error(request, _("El correo ya está registrado."))
            return redirect('registro')
        if UsuarioPersonalizado.objects.filter(dni=dni).exists():
            messages.error(request, _("El DNI ya está registrado."))
            return redirect('registro')

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
        enviar_mail_activacion(request, usuario)
        return redirect('activacion_pendiente', email=usuario.email)

    return render(request, 'usuarios/registro.html')


def activacion_pendiente(request, email):
    contexto = {'email': email}
    return render(request, 'usuarios/activacion_pendiente.html', contexto)

def reenviar_activacion(request, email):
    try:
        usuario = UsuarioPersonalizado.objects.get(email=email)
    except UsuarioPersonalizado.DoesNotExist:
        messages.error(request, _("Usuario no encontrado."))
        return redirect('registro')

    if usuario.is_active:
        messages.info(request, _("Tu cuenta ya está activada."))
        return redirect('login')

    enviar_mail_activacion(request, usuario)
    messages.success(request, _("Se ha reenviado el enlace de activación a tu correo."))
    return redirect('activacion_pendiente', email=email)


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
        messages.success(request, _("Tu cuenta ha sido activada correctamente. Ya puedes iniciar sesión."))
        return redirect('login')
    else:
        messages.error(request, _("El enlace de activación no es válido o ha expirado."))
        return redirect('registro')

def logout_view(request):
    logout(request)
    return redirect('login')

def landing_page(request):
    return render(request, 'usuarios/landing.html')

def centro_ayuda(request):
    """
    Página estática con guías, FAQs y primeros pasos.
    """
    return render(request, 'usuarios/centro_ayuda.html')


def contacto(request):
    """
    Formulario de contacto sencillo (solo UI + envío por correo).
    Usa settings.SUPPORT_EMAIL si existe; si no, DEFAULT_FROM_EMAIL.
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        asunto = request.POST.get('asunto', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()

        if not (nombre and email and asunto and mensaje):
            messages.error(request, _("Por favor, completa todos los campos."))
            return render(request, 'usuarios/contacto.html', {
                'prefill': {'nombre': nombre, 'email': email, 'asunto': asunto, 'mensaje': mensaje}
            })

        try:
            soporte = getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
            cuerpo = f"De: {nombre} <{email}>\nAsunto: {asunto}\n\nMensaje:\n{mensaje}"
            send_mail(
                subject=f"[CryptoTrade] {asunto}",
                message=cuerpo,
                from_email=settings.DEFAULT_FROM_EMAIL,   # remitente técnico
                recipient_list=[soporte],
                fail_silently=False,
            )
            messages.success(request, _("Tu mensaje fue enviado. Te responderemos en 24–48 h (días hábiles)."))
            return redirect('contacto')
        except Exception:
            messages.error(request, _("No pudimos enviar tu mensaje en este momento. Inténtalo más tarde."))

    return render(request, 'usuarios/contacto.html')

def verificar_codigo_view(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('login')

    usuario = UsuarioPersonalizado.objects.get(id=user_id)

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')
        if codigo_ingresado == usuario.two_factor_code:
            usuario.two_factor_code = None
            usuario.save()
            
            # --- INICIO DE SESIÓN CON 2FA ---
            login(request, usuario)
            del request.session['pending_user_id']

            # [NUEVO] Lógica de Alerta de Seguridad
            if usuario.notif_inicio_sesion:
                send_mail(
                    subject=_('Alerta de seguridad: Nuevo inicio de sesión'),
                    message=_('Hola %(nombre)s, accediste exitosamente con autenticación de dos factores.') % {'nombre': usuario.nombre},
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[usuario.email],
                    fail_silently=True,
                )

            return redirect('inicio')
        else:
            messages.error(request, _('Código incorrecto. Intenta nuevamente.'))

    return render(request, 'usuarios/verificar_codigo.html', {'email': usuario.email})

@login_required
def configurar_2fa_view(request):
    user = request.user
    if request.method == 'POST':
        opcion = request.POST.get('opcion')
        user.two_factor_enabled = (opcion == 'activar')
        user.save()
        msg = _("Autenticación en dos pasos activada.") if opcion == 'activar' else _("Autenticación en dos pasos desactivada.")
        messages.success(request, msg)
    return render(request, 'usuarios/configurar_2fa.html', {'user': user})

@login_required
def perfil_view(request):
    user = request.user
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user.nombre = request.POST.get('nombre')
            user.apellido = request.POST.get('apellido')
            user.telefono = request.POST.get('telefono')
            user.direccion = request.POST.get('direccion')
            user.fecha_nacimiento = request.POST.get('fecha_nacimiento')
            user.save()
            messages.success(request, _("Datos personales actualizados correctamente."))
            return redirect('perfil')

        elif 'toggle_2fa' in request.POST:
            user.two_factor_enabled = not user.two_factor_enabled
            user.save()
            if user.two_factor_enabled:
                messages.success(request, _("Autenticación en dos pasos ACTIVADA."))
            else:
                messages.info(request, _("Autenticación en dos pasos DESACTIVADA."))
            return redirect('perfil')
        
        # --- NUEVO BLOQUE: PREFERENCIAS ---
        elif 'update_preferences' in request.POST:
            # Checkboxes en HTML: si no están marcados, no envían nada.
            # Por eso verificamos si el valor es 'on'.
            user.notif_inicio_sesion = request.POST.get('notif_inicio_sesion') == 'on'
            user.notif_marketing = request.POST.get('notif_marketing') == 'on'
            user.priv_perfil_publico = request.POST.get('priv_perfil_publico') == 'on'
            user.priv_compartir_datos = request.POST.get('priv_compartir_datos') == 'on'
            
            user.save()
            messages.success(request, _("Preferencias de privacidad actualizadas correctamente."))
            return redirect('perfil')

    return render(request, 'usuarios/perfil.html')

# ==========================================================
# VISTAS PARA LAS PÁGINAS DEL PANEL DE CONTROL (AÑADIDAS)
# ==========================================================

@login_required
def inicio_view(request):
    """
    Muestra la página principal del panel (el dashboard).
    """
    return render(request, 'usuarios/inicio.html')

@login_required
def monedas_view(request):
    """
    Muestra la página de monedas disponibles para invertir.
    """
    return render(request, 'usuarios/monedas.html')

@login_required
def inversiones_view(request):
    """
    Muestra la página del portafolio de inversiones del usuario.
    """
    return render(request, 'usuarios/inversiones.html')
 

def articulo_ayuda(request, tema):
    """
    Vista dinámica con traducciones granulares para asegurar que el texto coincida
    perfectamente con el archivo .po
    """
    contenidos = {
        'seguridad': {
            'titulo': _('Seguridad y Acceso (2FA)'),
            'cuerpo': (
                f"<p>{_('La seguridad es el pilar fundamental de CryptoTrade. Para proteger tus activos y datos, implementamos autenticación de dos factores (2FA) obligatoria para operaciones críticas.')}</p>"
                f"<h3 class='text-xl font-bold text-green-400 mt-4 mb-2'>{_('¿Por qué es necesario?')}</h3>"
                f"<p>{_('El mercado cripto opera 24/7 y los riesgos de seguridad son constantes. Nuestro sistema valida tu identidad no solo con contraseña, sino con un código temporal único.')}</p>"
                f"<ul class='list-disc pl-5 mt-2 space-y-1 text-gray-400'>"
                f"<li>{_('Validación de correo electrónico para activar cuenta.')}</li>"
                f"<li>{_('Protección contra ataques de fuerza bruta.')}</li>"
                f"<li>{_('Cifrado de datos sensibles en base de datos.')}</li>"
                f"</ul>"
            )
        },
        'backtesting': {
            'titulo': _('Backtesting sin Overfitting'),
            'cuerpo': (
                f"<p>{_('Uno de los errores más comunes en principiantes es el <strong>sobreajuste (overfitting)</strong>: crear estrategias que funcionan perfecto en el pasado pero fallan en el futuro.')}</p>"
                f"<h3 class='text-xl font-bold text-green-400 mt-4 mb-2'>{_('Nuestra Metodología')}</h3>"
                f"<p>{_('CryptoTrade mitiga este riesgo separando automáticamente los datos en dos conjuntos:')}</p>"
                f"<ul class='list-disc pl-5 mt-2 space-y-1 text-gray-400'>"
                f"<li><strong>{_('Entrenamiento (In-Sample):')}</strong> {_('Para diseñar la estrategia.')}</li>"
                f"<li><strong>{_('Prueba (Out-of-Sample):')}</strong> {_('Para validarla en datos desconocidos.')}</li>"
                f"</ul>"
                f"<p class='mt-4'>{_('Esto asegura que tus resultados sean realistas y no una ilusión estadística (Bailey et al., 2014).')}</p>"
            )
        },
        'ia-shap': {
            'titulo': _('Entendiendo las Señales (SHAP)'),
            'cuerpo': (
                f"<p>{_('CryptoTrade no es una \"caja negra\". Utilizamos un modelo híbrido avanzado que combina <strong>LSTM</strong> (para tendencias temporales) y <strong>XGBoost</strong> (para patrones complejos).')}</p>"
                f"<h3 class='text-xl font-bold text-green-400 mt-4 mb-2'>{_('¿Qué es SHAP?')}</h3>"
                f"<p>{_('Usamos valores SHAP (SHapley Additive exPlanations) para decirte <em>por qué</em> el modelo sugiere comprar o vender.')}</p>"
                f"<div class='bg-gray-800 p-4 rounded-lg mt-3 border-l-4 border-green-500'>"
                f"<p class='italic text-gray-300'>\"{_('El modelo sugiere COMPRA porque el volumen aumentó un 20% y la volatilidad bajó, a pesar de que el precio actual es alto.')}\"</p>"
                f"</div>"
                f"<p class='mt-2'>{_('Esta explicabilidad es clave para tu aprendizaje financiero.')}</p>"
            )
        },
        'riesgo': {
            'titulo': _('Gestión de Riesgo Integral'),
            'cuerpo': (
                f"<p>{_('Antes de pensar en cuánto ganar, debes pensar en cuánto puedes permitirte perder. La gestión de riesgo es lo que separa a los profesionales de los aficionados.')}</p>"
                f"<h3 class='text-xl font-bold text-green-400 mt-4 mb-2'>{_('Herramientas Integradas')}</h3>"
                f"<ul class='list-disc pl-5 mt-2 space-y-1 text-gray-400'>"
                f"<li><strong>{_('Stop-Loss:')}</strong> {_('Define un límite máximo de pérdida por operación.')}</li>"
                f"<li><strong>{_('Tamaño de Posición:')}</strong> {_('Calcula cuánto invertir según tu capital total.')}</li>"
                f"<li><strong>{_('Ratio Riesgo/Beneficio:')}</strong> {_('Evalúa si la operación vale la pena antes de entrar.')}</li>"
                f"</ul>"
            )
        },
        'dashboard': {
            'titulo': _('Tu Dashboard Pro'),
            'cuerpo': (
                f"<p>{_('El panel de control centraliza toda la información crítica para la toma de decisiones en tiempo real.')}</p>"
                f"<h3 class='text-xl font-bold text-green-400 mt-4 mb-2'>{_('Métricas Clave')}</h3>"
                f"<p>{_('Visualiza el rendimiento de tu portafolio, alertas de mercado activas y el estado de tus estrategias automatizadas en una sola vista optimizada para reducir la carga cognitiva.')}</p>"
            )
        },
        'datos': {
            'titulo': _('Integridad de Datos de Mercado'),
            'cuerpo': (
                f"<p>{_('Las predicciones precisas requieren datos limpios. CryptoTrade se conecta a fuentes confiables (APIs de exchanges y agregadores) para obtener precios históricos y en tiempo real.')}</p>"
                f"<p class='mt-2'>{_('Nuestro sistema realiza una limpieza automática para eliminar \"ruido\" y anomalías que podrían afectar el rendimiento de tus modelos de IA.')}</p>"
            )
        }
    }

    articulo = contenidos.get(tema)
    
    if not articulo:
        return redirect('centro_ayuda')

    return render(request, 'usuarios/articulo_ayuda.html', {'articulo': articulo})

def privacidad(request):
    contenido_html = (
        f"<h3 class='text-xl font-bold text-green-400 mb-2'>1. { _('Protección de Datos Financieros') }</h3>"
        f"<p class='mb-4'>{ _('CryptoTrade se compromete a proteger la integridad de sus datos operativos y personales. Utilizamos cifrado de extremo a extremo para toda la información sensible, cumpliendo con los estándares de la industria financiera.') }</p>"
        
        f"<h3 class='text-xl font-bold text-green-400 mb-2'>2. { _('Recopilación de Datos de Trading') }</h3>"
        f"<p class='mb-4'>{ _('Para optimizar nuestros modelos de IA (XGBoost + LSTM), la plataforma procesa datos anonimizados sobre patrones de configuración de estrategias y resultados de backtesting. Estos datos se utilizan exclusivamente para mejorar la precisión de las señales.') }</p>"

        f"<h3 class='text-xl font-bold text-green-400 mb-2'>3. { _('Seguridad de la Cuenta') }</h3>"
        f"<p>{ _('Es responsabilidad del usuario mantener la confidencialidad de sus credenciales. Recomendamos encarecidamente mantener activada la autenticación de dos factores (2FA) en todo momento para prevenir accesos no autorizados.') }</p>"
    )
    
    return render(request, 'usuarios/legal.html', {
        'titulo': _('Política de Privacidad'),
        'contenido': contenido_html
    })

def terminos(request):
    contenido_html = (
        f"<h3 class='text-xl font-bold text-green-400 mb-2'>1. { _('Objeto del Servicio') }</h3>"
        f"<p class='mb-4'>{ _('CryptoTrade proporciona herramientas avanzadas de análisis cuantitativo, backtesting y señales generadas por Inteligencia Artificial para asistir en la toma de decisiones de trading en mercados de criptoactivos.') }</p>"

        f"<h3 class='text-xl font-bold text-green-400 mb-2'>2. { _('Uso de las Herramientas') }</h3>"
        f"<p class='mb-4'>{ _('El usuario recibe una licencia limitada para utilizar nuestro software de visualización y análisis. El usuario reconoce que las señales de IA son herramientas de apoyo basadas en probabilidades estadísticas y no garantías de rendimiento futuro.') }</p>"

        f"<h3 class='text-xl font-bold text-green-400 mb-2'>3. { _('Divulgación de Riesgos') }</h3>"
        f"<p class='mb-4'>{ _('El trading de criptomonedas implica un riesgo sustancial de pérdida. Si bien nuestras herramientas de gestión de riesgo y detección de overfitting están diseñadas para mitigar la exposición, la decisión final de ejecución y la responsabilidad financiera recaen exclusivamente en el usuario.') }</p>"

        f"<h3 class='text-xl font-bold text-green-400 mb-2'>4. { _('Disponibilidad del Servicio') }</h3>"
        f"<p>{ _('Nos esforzamos por garantizar la disponibilidad 24/7 de la plataforma y la integridad de los datos de mercado en tiempo real, sujetos a mantenimientos programados y condiciones de red.') }</p>"
    )

    return render(request, 'usuarios/legal.html', {
        'titulo': _('Términos y Condiciones'),
        'contenido': contenido_html
    })

def perfil_publico_view(request, username):
    """
    Muestra el perfil público de un trader si tiene la opción activada.
    Si está desactivada, muestra una pantalla de 'Perfil Privado'.
    """
    # Buscamos al usuario por su username (que suele ser el email en tu caso, 
    # pero funciona igual si usas un campo 'username' limpio)
    usuario_ver = get_object_or_404(UsuarioPersonalizado, username=username)
    
    # LÓGICA DEL SWITCH DE PRIVACIDAD
    if not usuario_ver.priv_perfil_publico:
        return render(request, 'usuarios/perfil_privado.html', {'usuario': usuario_ver})
    
    # Datos simulados para la demo (Tesis)
    # En el futuro, esto vendría de tu base de datos de trading
    stats = {
        'win_rate': '68%',
        'profit_total': '+15.4%',
        'trades_mes': 42,
        'ranking': 'Top 15%'
    }
    
    return render(request, 'usuarios/perfil_publico.html', {
        'usuario': usuario_ver,
        'stats': stats
    })