# notas/views/boletin_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string
import datetime

try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Se añade FichaEstudiante para poder obtener el número de documento
from ..models import Curso, PeriodoAcademico, Docente, AsignacionDocente, Estudiante, FichaEstudiante
from ..boletin.logic import get_datos_boletin_curso, get_datos_boletin_final


@login_required
def selector_boletin_vista(request):
    """
    Muestra los filtros para seleccionar qué boletín generar, filtrando
    por el colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    context = {'colegio': request.colegio}
    user = request.user
    docente_seleccionado_id = request.GET.get('docente_id')

    if user.is_superuser:
        # Filtra los docentes por el colegio actual
        context['todos_los_docentes'] = Docente.objects.filter(colegio=request.colegio).order_by('user__last_name', 'user__first_name')
        context['docente_seleccionado_id'] = docente_seleccionado_id
        
        cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
        if docente_seleccionado_id:
            cursos_ids = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id, colegio=request.colegio).values_list('curso_id', flat=True).distinct()
            cursos = cursos.filter(id__in=cursos_ids)
        
        context['cursos'] = cursos
    else:
        try:
            docente_actual = get_object_or_404(Docente, user=user, colegio=request.colegio)
            cursos_ids = AsignacionDocente.objects.filter(docente=docente_actual, colegio=request.colegio).values_list('curso_id', flat=True).distinct()
            context['cursos'] = Curso.objects.filter(id__in=cursos_ids, colegio=request.colegio).order_by('nombre')
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. Su perfil no está asociado a un docente en este colegio.")
            return redirect('dashboard')

    # Filtra periodos y años por el colegio actual
    context['periodos'] = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', 'nombre')
    context['anos_lectivos'] = PeriodoAcademico.objects.filter(colegio=request.colegio).values_list('ano_lectivo', flat=True).distinct().order_by('-ano_lectivo')
    
    return render(request, 'notas/admin_tools/selector_boletin.html', context)


@login_required
def generar_boletin_vista(request):
    """
    Genera un boletín de periodo o final, asegurando que todos los datos
    correspondan al colegio actual y corrigiendo la identificación del estudiante.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if not PDF_SUPPORT:
        return HttpResponse("Error: La librería 'WeasyPrint' no está instalada.", status=500)

    curso_id = request.GET.get('curso_id')
    reporte_id = request.GET.get('reporte_id')

    if not curso_id or not reporte_id:
        return HttpResponse("Error: Debe seleccionar un curso y un tipo de reporte.", status=400)
    
    # Filtra el curso por el colegio actual para seguridad
    curso = get_object_or_404(Curso, id=curso_id, colegio=request.colegio)
    user = request.user

    es_docente_del_curso = False
    es_estudiante_del_curso = False

    if hasattr(user, 'docente') and user.docente.colegio == request.colegio:
        es_docente_del_curso = AsignacionDocente.objects.filter(docente=user.docente, curso=curso).exists()
    
    if hasattr(user, 'estudiante') and user.estudiante.colegio == request.colegio:
        es_estudiante_del_curso = user.estudiante.curso == curso

    if not (user.is_superuser or es_docente_del_curso or es_estudiante_del_curso):
        return HttpResponseForbidden("No tiene permiso para ver los boletines de este curso.")

    estudiante_especifico = user.estudiante if es_estudiante_del_curso and not user.is_superuser else None

    if reporte_id.startswith('FINAL_'):
        try:
            ano_lectivo = int(reporte_id.split('_')[1])
        except (ValueError, IndexError):
            return HttpResponse("Error: Formato de reporte final no válido.", status=400)
        
        # La lógica de boletín final ahora recibe el colegio
        boletines_data, nombres_periodos = get_datos_boletin_final(request.colegio, curso, ano_lectivo, estudiante_especifico)
        if not boletines_data:
            return HttpResponse("No se encontraron datos para generar el boletín final de este curso y año.")

        template_path = 'notas/boletin/boletin_final_pdf.html'
        pdf_filename = f'boletin_final_{curso.nombre}_{ano_lectivo}.pdf'
        context = { "boletines": boletines_data, "nombres_periodos": nombres_periodos, "curso": curso, "ano_lectivo": ano_lectivo, "colegio": request.colegio }

    else:
        try:
            # Filtra el periodo por el colegio actual
            periodo = get_object_or_404(PeriodoAcademico, id=reporte_id, colegio=request.colegio)
        except (ValueError, PeriodoAcademico.DoesNotExist):
            return HttpResponse("Error: El periodo seleccionado no es válido.", status=400)

        # La lógica de boletín de curso ahora recibe el colegio
        boletines_data = get_datos_boletin_curso(request.colegio, curso, periodo, estudiante_especifico)
        if not boletines_data:
            return HttpResponse("No se encontraron datos para generar el boletín de este periodo.")

        template_path = 'notas/boletin/boletin_pdf.html'
        pdf_filename = f'boletines_{curso.nombre}_{periodo.get_nombre_display()}.pdf'
        context = { "boletines": boletines_data, "curso": curso, "periodo": periodo, "colegio": request.colegio }

    # --- INICIO: CORRECCIÓN PARA NÚMERO DE IDENTIFICACIÓN ---
    # Iteramos sobre los datos generados para asegurar que la identificación sea correcta.
    for boletin in boletines_data:
        try:
            # Intentamos obtener la ficha y el número de documento
            ficha = FichaEstudiante.objects.get(estudiante=boletin['estudiante'])
            boletin['identificacion'] = ficha.numero_documento or boletin['estudiante'].user.username
        except FichaEstudiante.DoesNotExist:
            # Si no tiene ficha, usamos el username como fallback
            boletin['identificacion'] = boletin['estudiante'].user.username
    # --- FIN: CORRECCIÓN ---

    html_string = render_to_string(template_path, context)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
    
    return response
