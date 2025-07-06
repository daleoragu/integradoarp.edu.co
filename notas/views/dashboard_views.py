# notas/views/dashboard_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from ..models import Estudiante

@login_required
def dashboard_vista(request):
    """
    Redirige a los usuarios al panel correspondiente según su rol (grupo).
    Esta es la vista principal del sitio después del login.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    
    if request.user.groups.filter(name="Docentes").exists():
        return redirect('panel_docente')

    if request.user.groups.filter(name="Estudiantes").exists():
        return redirect('panel_estudiante') 

    # Fallback para usuarios sin un rol definido o para otros roles futuros
    return render(request, 'notas/dashboard.html')


@login_required
def admin_dashboard_vista(request):
    """
    Muestra el panel de administración principal con sus tres vistas.
    """
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    context = {}
    return render(request, 'notas/admin_tools/admin_dashboard.html', context)


@login_required
def docente_dashboard_vista(request):
    """
    Muestra el panel principal para el docente.
    """
    if not (request.user.is_superuser or request.user.groups.filter(name="Docentes").exists()):
        return redirect('dashboard')

    context = {}
    return render(request, 'notas/docente/dashboard_docente.html', context)


@login_required
def estudiante_dashboard_vista(request):
    """
    Muestra el panel principal para el estudiante.
    """
    if not request.user.groups.filter(name="Estudiantes").exists():
        return redirect('dashboard')
        
    try:
        estudiante = Estudiante.objects.get(user=request.user)
        context = {'estudiante': estudiante}
    except Estudiante.DoesNotExist:
        context = {'estudiante': None}
        
    return render(request, 'notas/estudiante/panel_estudiante.html', context)
