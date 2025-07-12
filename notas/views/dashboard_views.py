# notas/views/dashboard_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
# 👇 IMPORTAMOS EL MODELO Docente Y LA RESPUESTA DE ERROR
from ..models import Estudiante, Docente
from django.http import HttpResponseNotFound

@login_required
def dashboard_vista(request):
    """
    Redirige a los usuarios al panel correspondiente según su rol (grupo).
    Esta es la vista principal del sitio después del login.
    """
    # 👇 PASO 1: Verificar que se ha identificado un colegio para este dominio.
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado para este dominio.</h1>")

    if not request.user.is_authenticated:
        return redirect('logout') # Se redirige a logout para limpiar sesión y luego a login
    
    # El superusuario puede ver el panel de admin de cualquier colegio que visite
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    
    # Verificamos si el usuario es un docente DE ESTE COLEGIO
    if Docente.objects.filter(user=request.user, colegio=request.colegio).exists():
        return redirect('panel_docente')

    # Verificamos si el usuario es un estudiante DE ESTE COLEGIO
    if Estudiante.objects.filter(user=request.user, colegio=request.colegio).exists():
        return redirect('panel_estudiante') 

    # Fallback si el usuario no tiene rol en ESTE colegio.
    # Podríamos mostrar un error de "Acceso denegado".
    return render(request, 'notas/dashboard.html', {'colegio': request.colegio})


@login_required
def admin_dashboard_vista(request):
    """
    Muestra el panel de administración principal.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado.</h1>")
        
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    # 👇 PASO 2: Pasar el objeto colegio a la plantilla.
    context = {
        'colegio': request.colegio
    }
    return render(request, 'notas/admin_tools/admin_dashboard.html', context)


@login_required
def docente_dashboard_vista(request):
    """
    Muestra el panel principal para el docente.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado.</h1>")

    # Verificamos que el usuario sea docente de este colegio o superusuario.
    if not (request.user.is_superuser or Docente.objects.filter(user=request.user, colegio=request.colegio).exists()):
        return redirect('dashboard')

    context = {
        'colegio': request.colegio
    }
    return render(request, 'notas/docente/dashboard_docente.html', context)


@login_required
def estudiante_dashboard_vista(request):
    """
    Muestra el panel principal para el estudiante.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado.</h1>")
        
    try:
        # 👇 PASO 3: Asegurarnos de que el estudiante pertenece al colegio actual.
        estudiante = Estudiante.objects.get(user=request.user, colegio=request.colegio)
        context = {
            'estudiante': estudiante,
            'colegio': request.colegio
        }
    except Estudiante.DoesNotExist:
        # Esto ocurre si un estudiante de otro colegio intenta acceder.
        context = {
            'estudiante': None,
            'colegio': request.colegio
        }
        # Aquí podríamos redirigir a una página de error de acceso.
        
    return render(request, 'notas/estudiante/panel_estudiante.html', context)
