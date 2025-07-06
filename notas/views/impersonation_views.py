# notas/views/impersonation_views.py

from django.shortcuts import redirect, get_object_or_404
# --- CORRECCIÓN: Se añaden 'logout' y 'login_required' ---
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test, login_required

from django.contrib import messages

def es_personal_admin(user):
    """
    Verifica si el usuario es superusuario o pertenece al grupo 'Administradores'.
    """
    return user.is_superuser or user.groups.filter(name='Administradores').exists()

@user_passes_test(es_personal_admin)
def iniciar_suplantacion(request, user_id):
    """
    Inicia sesión como el usuario objetivo, guardando el ID del admin original
    en la nueva sesión.
    """
    if 'original_user_id' in request.session:
        messages.error(request, "Ya estás suplantando a un usuario. Por favor, detén la sesión actual primero.")
        return redirect('dashboard')

    try:
        usuario_objetivo = get_object_or_404(User, id=user_id)
        original_user_id = request.user.id
        
        # Se hace el login PRIMERO. Esto limpia la sesión anterior.
        login(request, usuario_objetivo, backend='django.contrib.auth.backends.ModelBackend')
        
        # Ahora, en la NUEVA sesión, guardamos el ID del admin original.
        request.session['original_user_id'] = original_user_id
        
        messages.success(request, f"Ahora estás viendo la plataforma como {usuario_objetivo.get_full_name()}.")
        return redirect('dashboard')
        
    except Exception as e:
        messages.error(request, f"No se pudo suplantar al usuario. Error: {e}")
        return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


# --- CORRECCIÓN: Se cambia el decorador a @login_required para permitir el acceso ---
@login_required
def detener_suplantacion(request):
    """
    Vuelve a la sesión del administrador original de forma segura.
    """
    original_user_id = request.session.get('original_user_id')
    
    if not original_user_id:
        messages.warning(request, "No estabas suplantando a ningún usuario.")
        return redirect('dashboard')

    try:
        admin_user = get_object_or_404(User, id=original_user_id)
        
        # Verificación de seguridad: nos aseguramos de que el usuario original sea un admin.
        if not es_personal_admin(admin_user):
            messages.error(request, "Error de seguridad: La cuenta original no tiene permisos de administrador.")
            logout(request) # Por seguridad, cerramos la sesión por completo.
            return redirect('portal')

        # Volver a iniciar sesión como el admin. Esto limpia la sesión del estudiante.
        login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')
        
        messages.info(request, "Has vuelto a tu cuenta de administrador.")
        # Ahora el redirect al panel de admin funcionará correctamente.
        return redirect('admin_dashboard')

    except Exception as e:
        messages.error(request, f"No se pudo detener la suplantación. Error: {e}")
        return redirect('dashboard')
