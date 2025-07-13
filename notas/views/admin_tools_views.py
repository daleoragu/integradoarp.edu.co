# notas/views/admin_tools_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User, Group
# Se añade HttpResponseNotFound para manejar el caso de un colegio no identificado
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth import get_user_model
from django import forms
from django.forms import modelformset_factory

from ..models import (
    Curso, Materia, Estudiante, Docente, AsignacionDocente, PeriodoAcademico,
    ReporteParcial, Observacion, ConfiguracionSistema, Notificacion
)
from ..models.academicos import ConfiguracionCalificaciones


def enviar_notificacion_consolidada(request, estudiante, periodo, forzar_envio=False):
    """
    Verifica si un estudiante tiene todos los reportes de un periodo (o si se fuerza el envío),
    y de ser así, genera una observación consolidada y envía un único correo resumen.
    Devuelve True si se envió, False si no.
    """
    # Se asume que los objetos 'estudiante' y 'periodo' ya pertenecen al colegio correcto.
    colegio = request.colegio
    if not colegio:
        return False

    # Las consultas internas ya se basan en el estudiante, lo cual es seguro.
    if Observacion.objects.filter(estudiante=estudiante, tipo_observacion='AUTOMATICA', periodo=periodo).exists():
        print(f"DEBUG: Notificación para {estudiante} en {periodo} ya fue procesada previamente.")
        return False

    reportes_realizados = ReporteParcial.objects.filter(estudiante=estudiante, periodo=periodo)
    
    # CORRECCIÓN: Filtrar las asignaciones por el colegio para un conteo preciso.
    total_asignaciones_curso = AsignacionDocente.objects.filter(
        curso=estudiante.curso, colegio=colegio
    ).count()

    if not forzar_envio and (reportes_realizados.count() < total_asignaciones_curso or total_asignaciones_curso == 0):
        return False
        
    if not reportes_realizados.exists():
        return False

    acudiente_email = getattr(estudiante, 'correo_electronico_contacto', None)
    if not acudiente_email:
        print(f"DEBUG: No se envió correo para {estudiante} (no hay email de contacto).")
        return False

    materias_con_dificultades = reportes_realizados.filter(presenta_dificultades=True)
    
    if materias_con_dificultades.exists():
        texto_materias = ", ".join([r.asignacion.materia.nombre for r in materias_con_dificultades])
        descripcion_observacion = f"Informe parcial consolidado del {periodo}: Se identificaron dificultades académicas en: {texto_materias}."
    else:
        descripcion_observacion = f"Informe parcial consolidado del {periodo}: ¡Felicitaciones! Desempeño adecuado en todas las materias reportadas."
    
    # CORRECCIÓN: Asegurar que la observación se asocie al colegio.
    Observacion.objects.update_or_create(
        estudiante=estudiante, 
        tipo_observacion='AUTOMATICA',
        periodo=periodo,
        colegio=colegio, # Se añade el colegio
        defaults={
            'descripcion': descripcion_observacion, 
            'docente_reporta': estudiante.curso.director_grado if estudiante.curso and estudiante.curso.director_grado else None
        }
    )
    
    context_email = {'estudiante': estudiante, 'periodo': periodo, 'materias_con_dificultades': materias_con_dificultades, 'colegio': colegio}
    html_message = render_to_string('notas/emails/email_reporte_parcial.html', context_email)
    plain_message = render_to_string('notas/emails/email_reporte_parcial.txt', context_email)
    asunto = f"Informe Parcial Consolidado - {estudiante.user.get_full_name()} - {periodo}"
    
    try:
        send_mail(asunto, plain_message, settings.DEFAULT_FROM_EMAIL, [acudiente_email], html_message=html_message)
        return True
    except Exception as e:
        print(f"ERROR al enviar correo para {estudiante}: {e}")
        return False


def es_superusuario(user):
    return user.is_superuser

@login_required
@user_passes_test(es_superusuario)
def panel_control_periodos_vista(request):
    """
    Panel de control para que el administrador gestione los plazos de cada periodo
    del colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        try:
            action = request.POST.get('action')
            periodo_id = request.POST.get('periodo_id')
            
            # CORRECCIÓN: Obtener el periodo asegurando que pertenece al colegio actual.
            periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
            
            mensaje_notificacion = ""
            url_notificacion = "#"

            if action == 'toggle_ingreso_notas':
                periodo.esta_activo = not periodo.esta_activo
                estado = "abierto" if periodo.esta_activo else "cerrado"
                messages.success(request, f"El Ingreso de Notas para '{periodo}' ha sido {estado}.")
                mensaje_notificacion = f"El plazo para Ingresar Notas del {periodo} ha sido {estado}."
                url_notificacion = reverse('ingresar_notas_periodo')
            
            elif action == 'toggle_reporte_parcial':
                periodo.reporte_parcial_activo = not periodo.reporte_parcial_activo
                estado = "abierto" if periodo.reporte_parcial_activo else "cerrado"
                messages.success(request, f"El plazo para el Reporte Parcial de '{periodo}' ha sido {estado}.")
                mensaje_notificacion = f"El plazo para generar Reportes Parciales del {periodo} ha sido {estado}."
                url_notificacion = reverse('reporte_parcial')

            elif action == 'toggle_nivelaciones':
                periodo.nivelaciones_activas = not periodo.nivelaciones_activas
                estado = "abierto" if periodo.nivelaciones_activas else "cerrado"
                messages.success(request, f"El plazo para las Nivelaciones de '{periodo}' ha sido {estado}.")
                mensaje_notificacion = f"El plazo para registrar Nivelaciones del {periodo} ha sido {estado}."
                url_notificacion = reverse('plan_mejoramiento')
            
            else:
                messages.error(request, "Acción no reconocida.")

            periodo.save()
            
            if mensaje_notificacion:
                # CORRECCIÓN: Notificar solo a los docentes del colegio actual.
                docentes = User.objects.filter(docente__colegio=request.colegio)
                for docente_user in docentes:
                    Notificacion.objects.create(
                        destinatario=docente_user,
                        mensaje=mensaje_notificacion,
                        tipo='PERIODO',
                        url=url_notificacion,
                        colegio=request.colegio # Asociar la notificación al colegio
                    )

        except PeriodoAcademico.DoesNotExist:
            messages.error(request, "El periodo que intentó modificar no existe o no pertenece a este colegio.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error inesperado: {e}")
        
        return redirect('panel_control_periodos')

    # CORRECCIÓN: Mostrar solo los periodos del colegio actual.
    periodos = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', '-fecha_inicio')
    context = {
        'periodos': periodos,
        'colegio': request.colegio,
    }
    
    return render(request, 'notas/admin_tools/panel_control_periodos.html', context)

@login_required
@user_passes_test(es_superusuario)
def panel_control_promocion_vista(request):
    """
    Permite al administrador ver y modificar la regla de promoción del colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    # --- CAMBIO ARQUITECTÓNICO IMPORTANTE ---
    # La configuración del sistema ya no puede ser global (pk=1).
    # Debe estar asociada a cada colegio.
    #
    # ACCIÓN REQUERIDA:
    # 1. Añade una ForeignKey al modelo Colegio en tu modelo `ConfiguracionSistema`:
    #    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name='configuracion')
    # 2. Elimina `primary_key=True` si lo tenías en algún campo.
    # 3. Haz makemigrations y migrate.

    # CORRECCIÓN: Obtener o crear la configuración para el colegio específico.
    config, created = ConfiguracionSistema.objects.get_or_create(colegio=request.colegio)

    if request.method == 'POST':
        nuevo_valor_str = request.POST.get('max_materias_reprobadas')
        try:
            nuevo_valor = int(nuevo_valor_str)
            if nuevo_valor >= 0:
                config.max_materias_reprobadas = nuevo_valor
                config.save()
                messages.success(request, "La regla de promoción ha sido actualizada correctamente.")
            else:
                messages.error(request, "El valor debe ser un número entero positivo.")
        except (ValueError, TypeError):
            messages.error(request, "Por favor, ingrese un número válido.")
        
        return redirect('panel_control_promocion')

    context = {
        'config': config,
        'colegio': request.colegio,
    }
    return render(request, 'notas/admin_tools/panel_control_promocion.html', context)


class MateriaPorcentajeForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['porcentaje_ser', 'porcentaje_saber', 'porcentaje_hacer', 'usar_ponderacion_equitativa']
        widgets = {
            'porcentaje_ser': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'porcentaje_saber': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'porcentaje_hacer': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'usar_ponderacion_equitativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ConfiguracionGlobalForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionCalificaciones
        fields = ['docente_puede_modificar']

@user_passes_test(lambda u: u.is_superuser)
def configuracion_calificaciones_vista(request):
    """
    Vista para que el admin gestione los porcentajes por defecto de las materias
    y el permiso global para el COLEGIO ACTUAL.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    # CORRECCIÓN: El queryset del formset debe ser filtrado por colegio.
    materias_colegio = Materia.objects.filter(colegio=request.colegio)
    MateriaFormSet = modelformset_factory(Materia, form=MateriaPorcentajeForm, extra=0)
    
    # --- CAMBIO ARQUITECTÓNICO IMPORTANTE ---
    # La configuración de calificaciones también debe ser por colegio.
    # ACCIÓN REQUERIDA:
    # 1. Añade una ForeignKey al modelo Colegio en tu modelo `ConfiguracionCalificaciones`:
    #    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name='config_calificaciones')
    # 2. Haz makemigrations y migrate.

    # CORRECCIÓN: Obtener la configuración global para el colegio actual.
    config_global, _ = ConfiguracionCalificaciones.objects.get_or_create(colegio=request.colegio)

    if request.method == 'POST':
        # CORRECCIÓN: Usar el queryset filtrado al procesar el formset.
        formset = MateriaFormSet(request.POST, queryset=materias_colegio)
        form_global = ConfiguracionGlobalForm(request.POST, instance=config_global)

        if formset.is_valid() and form_global.is_valid():
            formset.save()
            form_global.save()
            messages.success(request, 'La configuración de calificaciones ha sido actualizada correctamente.')
            return redirect('configuracion_calificaciones')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')

    else:
        # CORRECCIÓN: Usar el queryset filtrado al inicializar el formset.
        formset = MateriaFormSet(queryset=materias_colegio.order_by('nombre'))
        form_global = ConfiguracionGlobalForm(instance=config_global)

    context = {
        'formset': formset,
        'form_global': form_global,
        'page_title': 'Configuración de Calificaciones por Materia',
        'colegio': request.colegio,
    }
    return render(request, 'notas/admin_tools/configuracion_calificaciones.html', context)
