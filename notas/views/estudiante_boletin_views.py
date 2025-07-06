# notas/views/estudiante_boletin_views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Estudiante, PublicacionBoletin, PeriodoAcademico, PublicacionBoletinFinal

@login_required
def mis_boletines_vista(request):
    """
    Muestra al estudiante una lista de los boletines que han sido publicados
    por la administración.
    """
    try:
        estudiante = Estudiante.objects.get(user=request.user)
    except Estudiante.DoesNotExist:
        messages.error(request, "Tu usuario no está asociado a un perfil de estudiante.")
        return render(request, 'notas/estudiante/mis_boletines.html', {'boletines_disponibles': []})

    # Obtener los periodos individuales publicados
    periodos_publicados_ids = PublicacionBoletin.objects.filter(esta_visible=True).values_list('periodo_id', flat=True)
    periodos_publicados = PeriodoAcademico.objects.filter(id__in=periodos_publicados_ids).order_by('ano_lectivo', 'fecha_inicio')
    
    boletines_disponibles = []
    for periodo in periodos_publicados:
        boletines_disponibles.append({
            'id': periodo.id,
            'texto': f"Boletín del {periodo.get_nombre_display()} - {periodo.ano_lectivo}",
        })
        
    # --- INICIO: CORRECCIÓN PARA MOSTRAR BOLETÍN FINAL ---
    # Obtener solo los informes finales que han sido publicados
    anos_finales_publicados = PublicacionBoletinFinal.objects.filter(
        esta_visible=True
    ).values_list('ano_lectivo', flat=True)

    for ano in anos_finales_publicados:
         boletines_disponibles.append({
            'id': f"FINAL_{ano}",
            'texto': f"Informe Final del Año {ano}",
        })
    # --- FIN ---

    context = {
        'boletines_disponibles': boletines_disponibles,
        'curso_id': estudiante.curso.id if estudiante.curso else None,
    }
    
    return render(request, 'notas/estudiante/mis_boletines.html', context)
