# notas/views/gestion_docentes_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponseNotFound
from django.utils.text import slugify
from unidecode import unidecode

from ..models import Docente, FichaDocente
from ..forms import AdminCrearDocenteForm, AdminEditarDocenteForm

def es_personal_admin(user):
    """Verifica si el usuario es superusuario."""
    return user.is_superuser

# ===============================================================
# VISTAS PARA GESTIÓN DE DOCENTES
# ===============================================================
@user_passes_test(es_personal_admin)
def gestion_docentes_vista(request):
    # Verificar que estamos en un colegio válido
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    
    # 👇 FILTRADO: Mostrar solo docentes del colegio actual
    docentes = Docente.objects.filter(colegio=request.colegio).select_related('user').order_by('user__last_name')
    
    context = {
        'docentes': docentes,
        'colegio': request.colegio # Pasar el colegio a la plantilla
    }
    return render(request, 'notas/admin_crud/gestion_docentes.html', context)

@user_passes_test(es_personal_admin)
@transaction.atomic
def crear_docente_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        form = AdminCrearDocenteForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            nombres = datos['nombres']
            apellidos = datos['apellidos']
            
            primer_nombre = unidecode(nombres.split(' ')[0].lower())
            primer_apellido = unidecode(apellidos.split(' ')[0].lower())
            username_base = f"{slugify(primer_nombre)}.{slugify(primer_apellido)}"
            
            username_final = username_base
            counter = 1
            while User.objects.filter(username=username_final).exists():
                username_final = f"{username_base}{counter}"
                counter += 1

            password_provisional = username_final

            nuevo_usuario = User.objects.create_user(
                username=username_final,
                password=password_provisional,
                first_name=nombres,
                last_name=apellidos,
                email=datos['email']
            )
            try:
                grupo_docentes, _ = Group.objects.get_or_create(name='Docentes')
                nuevo_usuario.groups.add(grupo_docentes)
            except ObjectDoesNotExist:
                messages.warning(request, "El grupo 'Docentes' no existe. Por favor, créelo en el panel de Admin.")
            
            # 👇 ASOCIACIÓN: Crear el docente para el colegio actual
            nuevo_docente = Docente.objects.create(user=nuevo_usuario, colegio=request.colegio)
            FichaDocente.objects.create(
                docente=nuevo_docente,
                numero_documento=datos.get('numero_documento')
            )

            success_message = (
                f"¡Docente '{apellidos}, {nombres}' creado con éxito!<br>"
                f"<strong>Usuario:</strong> {username_final}<br>"
                f"<strong>Contraseña Provisional:</strong> {password_provisional}"
            )
            messages.success(request, success_message, extra_tags='safe')
            return redirect('editar_docente', docente_id=nuevo_docente.id)
    else:
        form = AdminCrearDocenteForm()
    
    context = {'form': form, 'titulo': "Crear Nuevo Docente", 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_docente.html', context)


@login_required 
@transaction.atomic
def editar_docente_vista(request, docente_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    # 👇 FILTRADO: Obtener el docente solo si pertenece al colegio actual
    docente = get_object_or_404(Docente, id=docente_id, colegio=request.colegio)

    if not (es_personal_admin(request.user) or request.user.id == docente.user.id):
        raise PermissionDenied

    ficha, created = FichaDocente.objects.get_or_create(docente=docente)
    if request.method == 'POST':
        form = AdminEditarDocenteForm(request.POST, request.FILES, instance=ficha, docente=docente)
        if form.is_valid():
            form.save()
            messages.success(request, f"¡Ficha actualizada con éxito!")
            return redirect('dashboard' if request.user.id == docente.user.id else 'gestion_docentes')
    else:
        form = AdminEditarDocenteForm(instance=ficha, docente=docente)
        
    context = {'form': form, 'titulo': "Editar Ficha del Docente", 'docente': docente, 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_docente.html', context)


@user_passes_test(es_personal_admin)
@require_POST
def eliminar_docente_vista(request, docente_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    # 👇 FILTRADO: Asegurarse de que solo se puede eliminar un docente del colegio actual
    docente = get_object_or_404(Docente, id=docente_id, colegio=request.colegio)
    docente.user.delete()
    messages.success(request, f"Docente '{docente.user.get_full_name()}' eliminado permanentemente.")
    return redirect('gestion_docentes')
