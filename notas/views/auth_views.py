# notas/views/auth_views.py

from django.shortcuts import render, redirect
# Se eliminan imports que ya no se usan aquí
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from ..forms import CustomPasswordChangeForm

# --- INICIO DE LA CORRECCIÓN: Se elimina la vista portal_vista duplicada ---
# La lógica de login ahora reside en notas/views/portal_views.py
# --- FIN DE LA CORRECCIÓN ---

def logout_vista(request):
    """
    Maneja el proceso de cierre de sesión del usuario.
    """
    logout(request)
    return redirect('logout_confirmacion')

def logout_confirmacion_vista(request):
    """
    Muestra la página de confirmación de cierre de sesión.
    """
    return render(request, 'notas/logout_confirmacion.html')

@login_required
def cambiar_password_vista(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '¡Tu contraseña ha sido actualizada exitosamente!')
            return redirect('dashboard')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'titulo': 'Cambiar Contraseña'
    }
    return render(request, 'registration/cambiar_password.html', context)
