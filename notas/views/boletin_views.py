# notas/views/boletin_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string
import datetime

try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from ..models import Curso, PeriodoAcademico, Docente, AsignacionDocente, Estudiante
from ..boletin.logic import get_datos_boletin_curso, get_datos_boletin_final


@login_required
def selector_boletin_vista(request):
    """
    Muestra los filtros para seleccionar qué boletín generar.
    """
    context = {}
    user = request.user
    docente_seleccionado_id = request.GET.get('docente_id')

    if user.is_superuser:
        context['todos_los_docentes'] = Docente.objects.all().order_by('user__last_name', 'user__first_name')
        context['docente_seleccionado_id'] = docente_seleccionado_id
        
        cursos = Curso.objects.all().order_by('nombre')
        if docente_seleccionado_id:
            cursos_ids = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id).values_list('curso_id', flat=True).distinct()
            cursos = cursos.filter(id__in=cursos_ids)
        
        context['cursos'] = cursos
    else:
        try:
            docente_actual = Docente.objects.get(user=user)
            cursos_ids = AsignacionDocente.objects.filter(docente=docente_actual).values_list('curso_id', flat=True).distinct()
            context['cursos'] = Curso.objects.filter(id__in=cursos_ids).order_by('nombre')
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. Su perfil de usuario no está asociado a un docente.")
            return redirect('dashboard')

    context['periodos'] = PeriodoAcademico.objects.all().order_by('-ano_lectivo', 'nombre')
    context['anos_lectivos'] = PeriodoAcademico.objects.values_list('ano_lectivo', flat=True).distinct().order_by('-ano_lectivo')
    
    return render(request, 'notas/admin_tools/selector_boletin.html', context)


@login_required
def generar_boletin_vista(request):
    """
    Vista única que decide si generar un boletín de periodo o uno final
    basado en el parámetro 'reporte_id'.
    """
    if not PDF_SUPPORT:
        return HttpResponse("Error: La librería 'WeasyPrint' no está instalada en el servidor.", status=500)

    curso_id = request.GET.get('curso_id')
    reporte_id = request.GET.get('reporte_id')

    if not curso_id or not reporte_id:
        return HttpResponse("Error: Debe seleccionar un curso y un tipo de reporte.", status=400)
    
    curso = get_object_or_404(Curso, id=curso_id)
    user = request.user

    # --- INICIO: CORRECCIÓN DE PERMISOS ---
    es_docente_del_curso = False
    es_estudiante_del_curso = False

    if hasattr(user, 'docente'):
        es_docente_del_curso = AsignacionDocente.objects.filter(docente=user.docente, curso=curso).exists()
    
    if hasattr(user, 'estudiante'):
        es_estudiante_del_curso = user.estudiante.curso == curso

    # Se deniega el acceso si el usuario no es admin, ni un docente del curso, ni un estudiante del curso.
    if not (user.is_superuser or es_docente_del_curso or es_estudiante_del_curso):
        return HttpResponseForbidden("No tiene permiso para ver los boletines de este curso.")
    # --- FIN: CORRECCIÓN DE PERMISOS ---

    # Para la generación del boletín de un solo estudiante
    estudiante_especifico = user.estudiante if es_estudiante_del_curso and not user.is_superuser else None

    # --- LÓGICA DE DECISIÓN ---
    if reporte_id.startswith('FINAL_'):
        try:
            ano_lectivo = int(reporte_id.split('_')[1])
        except (ValueError, IndexError):
            return HttpResponse("Error: El formato del reporte final no es válido.", status=400)
        
        boletines_data, nombres_periodos = get_datos_boletin_final(curso, ano_lectivo, estudiante_especifico)
        if not boletines_data:
            return HttpResponse("No se encontraron datos para generar el boletín final de este curso y año.")

        context = { "boletines": boletines_data, "nombres_periodos": nombres_periodos, "curso": curso, "ano_lectivo": ano_lectivo }
        template_path = 'notas/boletin/boletin_final_pdf.html'
        pdf_filename = f'boletin_final_{curso.nombre}_{ano_lectivo}.pdf'

    else:
        try:
            periodo = get_object_or_404(PeriodoAcademico, id=reporte_id)
        except (ValueError, PeriodoAcademico.DoesNotExist):
            return HttpResponse("Error: El periodo seleccionado no es válido.", status=400)

        boletines_data = get_datos_boletin_curso(curso, periodo, estudiante_especifico)
        if not boletines_data:
            return HttpResponse("No se encontraron datos para generar el boletín de este periodo.")

        context = { "boletines": boletines_data, "curso": curso, "periodo": periodo }
        template_path = 'notas/boletin/boletin_pdf.html'
        pdf_filename = f'boletines_{curso.nombre}_{periodo.get_nombre_display()}.pdf'

    # Renderizado del PDF (código común)
    html_string = render_to_string(template_path, context)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
    
    return response
