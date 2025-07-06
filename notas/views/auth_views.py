from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from ..forms import CustomPasswordChangeForm
def portal_vista(request):
    """
    Maneja la página del portal público, que incluye el formulario de login.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        if request.POST.get('form_type') == 'login_form':
            usuario = request.POST.get('username')
            contrasena = request.POST.get('password')
            user = authenticate(request, username=usuario, password=contrasena)
            
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        
    return render(request, 'notas/portal.html')

def logout_vista(request):
    """
    Maneja el proceso de cierre de sesión del usuario.
    CORRECCIÓN: Ahora redirige a una página de confirmación dedicada.
    """
    logout(request)
    # Ya no usamos el sistema de mensajes de Django aquí.
    return redirect('logout_confirmacion')

def logout_confirmacion_vista(request):
    """
    NUEVA VISTA: Muestra la página de confirmación de cierre de sesión.
    """
    return render(request, 'notas/logout_confirmacion.html')

@login_required
def cambiar_password_vista(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # ¡Importante para mantener al usuario logueado!
            messages.success(request, '¡Tu contraseña ha sido actualizada exitosamente!')
            return redirect('dashboard')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'titulo': 'Cambiar Contraseña'
    }
    return render(request, 'registration/cambiar_password.html', context)
