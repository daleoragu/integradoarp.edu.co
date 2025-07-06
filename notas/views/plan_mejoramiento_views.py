# notas/views/plan_mejoramiento_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from decimal import Decimal
from ..models import (
    Docente, AsignacionDocente, PeriodoAcademico, Estudiante,
    Calificacion, PlanDeMejoramiento, Observacion
)

@login_required
def plan_mejoramiento_vista(request):
    """
    Gestiona la interfaz para planes de mejoramiento.
    """
    context = {}
    user = request.user
    docente_seleccionado_id = request.GET.get('docente_id')
    asignacion_seleccionada_id_str = request.GET.get('asignacion_id')
    periodo_seleccionado_id_str = request.GET.get('periodo_id')

    # Lógica para determinar qué asignaciones mostrar
    if user.is_superuser:
        context['todos_los_docentes'] = Docente.objects.all().order_by('user__last_name', 'user__first_name')
        if docente_seleccionado_id:
            asignaciones_docente = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id)
        else:
            asignaciones_docente = AsignacionDocente.objects.all()
    else:
        try:
            docente_actual = Docente.objects.get(user=user)
            asignaciones_docente = AsignacionDocente.objects.filter(docente=docente_actual)
            context['docente_actual'] = docente_actual
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado.")
            return redirect('dashboard')

    context['asignaciones'] = asignaciones_docente.select_related('curso', 'materia').order_by('curso__nombre', 'materia__nombre')
    context['periodos'] = PeriodoAcademico.objects.all().order_by('-ano_lectivo', 'nombre')
    context['docente_seleccionado_id'] = docente_seleccionado_id
    context['asignacion_seleccionada_id'] = asignacion_seleccionada_id_str
    context['periodo_seleccionado_id'] = periodo_seleccionado_id_str
    context['estudiantes_para_nivelar_data'] = []
    context['plazo_nivelaciones_cerrado'] = False

    # Lógica para procesar el guardado de datos (POST)
    if request.method == 'POST':
        docente_que_reporta = Docente.objects.filter(user=request.user).first()
        asignacion_id = request.POST.get('asignacion_id')
        periodo_id = request.POST.get('periodo_id')
        
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)

        if not periodo.nivelaciones_activas:
            messages.error(request, f"No se pueden guardar los cambios. El plazo para las nivelaciones de '{periodo}' está cerrado.")
            return redirect(request.get_full_path())
            
        try:
            asignacion = AsignacionDocente.objects.get(id=asignacion_id)
            docente_asignado = asignacion.docente
            if not user.is_superuser and asignacion.docente != docente_que_reporta:
                raise Exception("Permiso denegado para esta asignación.")
            
            estudiantes_en_formulario = request.POST.getlist('estudiante_id')

            for est_id in estudiantes_en_formulario:
                estudiante = Estudiante.objects.get(id=est_id)
                nota_str = request.POST.get(f'nota_nivelacion_{est_id}', '').strip()
                desc_plan = request.POST.get(f'descripcion_plan_{est_id}', '').strip()

                if nota_str:
                    nota_nivelacion = Decimal(nota_str.replace(',', '.'))
                    
                    if not (Decimal('1.0') <= nota_nivelacion <= Decimal('5.0')):
                        messages.warning(request, f"Nota para {estudiante} ({nota_nivelacion}) está fuera de rango y no fue guardada.")
                        continue

                    PlanDeMejoramiento.objects.update_or_create(
                        estudiante=estudiante,
                        asignacion=asignacion,
                        periodo_recuperado=periodo,
                        defaults={'nota_recuperacion': nota_nivelacion, 'descripcion_plan': desc_plan}
                    )
                    
                    Calificacion.objects.update_or_create(
                        estudiante=estudiante,
                        materia=asignacion.materia,
                        periodo=periodo,
                        tipo_nota='NIVELACION',
                        defaults={
                            'valor_nota': nota_nivelacion,
                            'docente': docente_que_reporta or docente_asignado
                        }
                    )
                    
                    calificacion_original = Calificacion.objects.filter(
                        estudiante=estudiante, materia=asignacion.materia,
                        periodo=periodo, tipo_nota='PROM_PERIODO'
                    ).first()

                    if calificacion_original:
                        calificacion_original.es_recuperada = (nota_nivelacion >= Decimal('3.0'))
                        calificacion_original.save()
                    
                    resultado = "aprobó" if nota_nivelacion >= Decimal('3.0') else "no aprobó"
                    descripcion_obs = (
                        f"En el plan de mejoramiento para la materia de {asignacion.materia.nombre} "
                        f"correspondiente al {periodo}, el estudiante {resultado} "
                        f"con una nota final de {nota_nivelacion}."
                    )
                    Observacion.objects.update_or_create(
                        estudiante=estudiante, periodo=periodo, tipo_observacion='ACADEMICA',
                        asignacion=asignacion,
                        defaults={'descripcion': descripcion_obs, 'docente_reporta': docente_que_reporta or docente_asignado}
                    )
                else:
                    # Si el campo de nota está vacío, se eliminan los registros existentes.
                    PlanDeMejoramiento.objects.filter(estudiante_id=est_id, asignacion_id=asignacion_id, periodo_recuperado_id=periodo_id).delete()
                    Calificacion.objects.filter(estudiante_id=est_id, materia_id=asignacion.materia.id, periodo_id=periodo_id, tipo_nota='NIVELACION').delete()
                    
                    calificacion_original = Calificacion.objects.filter(
                        estudiante_id=est_id, materia_id=asignacion.materia.id,
                        periodo_id=periodo_id, tipo_nota='PROM_PERIODO'
                    ).first()
                    if calificacion_original:
                        calificacion_original.es_recuperada = False
                        calificacion_original.save()
            
            messages.success(request, "Nivelaciones guardadas y registros actualizados exitosamente.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al guardar: {e}")
        
        # CORRECCIÓN CLAVE: Redirigir a la URL actual para forzar una recarga limpia
        return redirect(request.get_full_path())

    # Lógica para mostrar los datos (GET)
    if asignacion_seleccionada_id_str and periodo_seleccionado_id_str:
        try:
            asignacion_actual = get_object_or_404(AsignacionDocente, id=asignacion_seleccionada_id_str)
            periodo_obj = get_object_or_404(PeriodoAcademico, id=periodo_seleccionado_id_str)
            
            context['plazo_nivelaciones_cerrado'] = not periodo_obj.nivelaciones_activas

            calificaciones_bajas = Calificacion.objects.filter(
                materia=asignacion_actual.materia, periodo=periodo_obj,
                tipo_nota='PROM_PERIODO', valor_nota__lt=3.0,
                estudiante__curso=asignacion_actual.curso,
                estudiante__is_active=True
            ).select_related('estudiante__user').order_by('estudiante__user__last_name', 'estudiante__user__first_name')
            
            for cal in calificaciones_bajas:
                estudiante = cal.estudiante
                plan_existente = PlanDeMejoramiento.objects.filter(
                    estudiante=estudiante, asignacion=asignacion_actual, periodo_recuperado=periodo_obj
                ).first()
                context['estudiantes_para_nivelar_data'].append({
                    'estudiante': estudiante,
                    'promedio_original': cal.valor_nota,
                    'plan': plan_existente
                })
        except Exception as e:
            messages.warning(request, f"No se pudieron cargar los datos: {e}")

    return render(request, 'notas/docente/plan_mejoramiento.html', context)
