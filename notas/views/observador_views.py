# notas/views/observador_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
# --- INICIO: Se añade la importación de 'reverse' ---
from django.urls import reverse
# --- FIN ---

try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from ..forms import RegistroObservadorForm, FichaEstudianteForm

from ..models import (
    Docente, Estudiante, Curso, FichaEstudiante, 
    AsignacionDocente, RegistroObservador, Notificacion # Se añade Notificacion
)

def es_docente_o_superuser(user):
    return user.is_superuser or user.groups.filter(name='Docentes').exists()

@login_required
@user_passes_test(es_docente_o_superuser)
def observador_selector_vista(request):
    user = request.user
    cursos = []
    estudiantes = Estudiante.objects.none()

    if user.is_superuser:
        cursos = Curso.objects.all().order_by('nombre')
    else:
        try:
            docente = Docente.objects.get(user=user)
            cursos_ids = AsignacionDocente.objects.filter(docente=docente).values_list('curso_id', flat=True).distinct()
            cursos = Curso.objects.filter(id__in=cursos_ids).order_by('nombre')
        except Docente.DoesNotExist:
            messages.error(request, "Su perfil no está asociado a un docente.")
            return redirect('dashboard')

    curso_seleccionado_id = request.GET.get('curso_id')
    if curso_seleccionado_id:
        estudiantes = Estudiante.objects.filter(
            curso_id=curso_seleccionado_id, is_active=True
        ).select_related('user', 'curso').order_by('user__last_name', 'user__first_name')

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        if estudiante_id:
            return redirect('vista_detalle_observador', estudiante_id=estudiante_id)

    context = {
        'cursos': cursos,
        'estudiantes': estudiantes,
        'curso_seleccionado_id': curso_seleccionado_id,
        'page_title': 'Seleccionar Estudiante para Observador'
    }
    return render(request, 'notas/observador/selector.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def vista_detalle_observador(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    ficha, created = FichaEstudiante.objects.get_or_create(estudiante=estudiante)
    registros = RegistroObservador.objects.filter(estudiante=estudiante)
    context = {
        'estudiante': estudiante,
        'ficha': ficha,
        'registros': registros,
        'page_title': f"Observador de {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/detalle_observador.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def crear_registro_observador_vista(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    
    # --- INICIO: CORRECCIÓN PARA MANEJAR ADMIN SIN PERFIL DOCENTE ---
    # Si el usuario es superuser pero no tiene perfil de docente, se usa como 'None'
    # Si no es superuser, se exige que tenga perfil de docente.
    docente = None
    if not request.user.is_superuser:
        docente = get_object_or_404(Docente, user=request.user)
    else:
        # Opcional: si un admin puede tener perfil, se puede buscar.
        # Si no, se queda como None y el registro se guarda sin docente.
        docente = Docente.objects.filter(user=request.user).first()
    # --- FIN ---

    if request.method == 'POST':
        form = RegistroObservadorForm(request.POST)
        if form.is_valid():
            nuevo_registro = form.save(commit=False)
            nuevo_registro.estudiante = estudiante
            nuevo_registro.docente_reporta = docente # Puede ser None si es un admin sin perfil
            nuevo_registro.save()
            
            # --- INICIO: SE AÑADE LA NOTIFICACIÓN ---
            try:
                # Se genera la URL a la que el estudiante será redirigido al hacer clic.
                url_destino = reverse('mi_observador')
            except:
                url_destino = '#' # URL de fallback por si acaso

            Notificacion.objects.create(
                destinatario=estudiante.user,
                mensaje="Tienes una nueva anotación en tu observador.",
                tipo='OBSERVADOR',
                url=url_destino
            )
            # --- FIN ---

            messages.success(request, f"Observación para {estudiante.user.get_full_name()} guardada correctamente.")
            return redirect('vista_detalle_observador', estudiante_id=estudiante.id)
    else:
        form = RegistroObservadorForm()

    context = {
        'form': form,
        'estudiante': estudiante,
        'page_title': f"Nueva Observación para {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/crear_registro.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def editar_ficha_vista(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    ficha, created = FichaEstudiante.objects.get_or_create(estudiante=estudiante)

    if request.method == 'POST':
        form = FichaEstudianteForm(request.POST, request.FILES, instance=ficha)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ficha de {estudiante.user.get_full_name()} actualizada correctamente.")
            return redirect('vista_detalle_observador', estudiante_id=estudiante.id)
    else:
        form = FichaEstudianteForm(instance=ficha)
    
    context = {
        'form': form,
        'estudiante': estudiante,
        'page_title': f"Editando Ficha de {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/editar_ficha.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def generar_observador_pdf_vista(request, estudiante_id):
    if not PDF_SUPPORT:
        return HttpResponse("Error: La librería 'WeasyPrint' no está instalada en el servidor.", status=500)
            
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    ficha, _ = FichaEstudiante.objects.get_or_create(estudiante=estudiante)
    registros = RegistroObservador.objects.filter(estudiante=estudiante)

    context = {
        'estudiante': estudiante,
        'ficha': ficha,
        'registros': registros,
    }
    
    html_string = render_to_string('notas/observador/observador_pdf.html', context)
    base_url = request.build_absolute_uri()
    pdf_file = HTML(string=html_string, base_url=base_url).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="observador_{estudiante.user.username}.pdf"'
    
    return response
