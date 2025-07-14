# notas/views/auth_views.py

from django.shortcuts import render, redirect
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# --- INICIO: Importaciones para la nueva vista ---
from django.contrib.auth.views import LoginView
from ..models import Colegio
# --- FIN: Importaciones para la nueva vista ---
from ..forms import CustomPasswordChangeForm


# --- INICIO: VISTA DE LOGIN PERSONALIZADA ---
# Esta vista es esencial para que tu página de login pueda mostrar el logo
# y los colores del colegio antes de que el usuario inicie sesión.
class CustomLoginView(LoginView):
    """
    Sobrescribe la vista de login para inyectar el objeto Colegio en la plantilla.
    """
    template_name = 'registration/login.html' # Asegúrate que la ruta a tu plantilla sea correcta

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Para un portal principal, tomamos el primer colegio como default.
        # En un sistema multi-subdominio, la lógica aquí sería diferente.
        context['colegio'] = Colegio.objects.first()
        return context
# --- FIN: VISTA DE LOGIN PERSONALIZADA ---


# --- TUS VISTAS EXISTENTES (SIN CAMBIOS) ---
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
        # CORRECCIÓN: Se eliminó un guion erróneo en el nombre del formulario.
        form = CustomPasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'titulo': 'Cambiar Contraseña'
    }
    return render(request, 'registration/cambiar_password.html', context)
