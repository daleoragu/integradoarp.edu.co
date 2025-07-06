# notas/views/asistencia_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import json
from datetime import datetime
from ..models import Docente, AsignacionDocente, Estudiante, Asistencia
from ..forms.auth_forms import CustomPasswordChangeForm
from django.contrib.auth import update_session_auth_hash




def _enviar_correo_inasistencia(estudiante, asignacion, fecha):
    """
    Prepara y envía un correo electrónico al acudiente cuando se registra una ausencia.
    """
    # Usamos getattr para evitar un error si el campo no existe en el modelo.
    acudiente_email = getattr(estudiante, 'correo_electronico_contacto', None)
    if not acudiente_email:
        print(f"DEBUG: No se envió correo para {estudiante} (sin email de contacto).")
        return

    contexto_email = {
        'estudiante': estudiante,
        'asignacion': asignacion,
        'fecha': fecha,
    }
    
    # --- LÍNEA CORREGIDA ---
    # Obtenemos el nombre completo desde el modelo User.
    asunto = f"Reporte de Inasistencia - {estudiante.user.get_full_name()}"
    
    html_mensaje = render_to_string('notas/emails/inasistencia_email.html', contexto_email)
    texto_plano = render_to_string('notas/emails/inasistencia_email.txt', contexto_email) # Corregido: contexto_email en lugar de texto_plano

    try:
        send_mail(
            asunto,
            texto_plano,
            settings.DEFAULT_FROM_EMAIL,
            [acudiente_email],
            html_message=html_mensaje
        )
    except Exception as e:
        print(f"ERROR al enviar correo de inasistencia para {estudiante}: {e}")


@login_required
def asistencia_vista(request):
    """
    Muestra la interfaz para el registro de asistencia diaria.
    """
    docente_actual = Docente.objects.filter(user=request.user).first()
    if not docente_actual and not request.user.is_superuser:
        messages.error(request, "Acceso denegado. Su usuario no está asociado a un perfil de docente.")
        return redirect('dashboard')

    if request.user.is_superuser:
        asignaciones_docente = AsignacionDocente.objects.all().select_related('curso', 'materia').order_by('curso__nombre', 'materia__nombre')
    else:
        asignaciones_docente = AsignacionDocente.objects.filter(docente=docente_actual).select_related('curso', 'materia').order_by('curso__nombre', 'materia__nombre')

    estudiantes_del_curso, asistencias_map, mostrar_lista = [], {}, False
    asignacion_id = request.GET.get('asignacion_id')
    fecha_str = request.GET.get('fecha', timezone.localdate().strftime('%Y-%m-%d'))
    
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_str = timezone.localdate().strftime('%Y-%m-%d')
        fecha_obj = timezone.localdate()
        messages.warning(request, "Fecha no válida, se ha usado la fecha de hoy.")

    if asignacion_id:
        try:
            asignacion_actual = AsignacionDocente.objects.get(id=asignacion_id)
            if not request.user.is_superuser and asignacion_actual.docente != docente_actual:
                raise AsignacionDocente.DoesNotExist
            
            mostrar_lista = True
            
            # --- TAREA DE AJUSTE 1: ORDEN ALFABÉTICO ---
            # La siguiente línea ordena la lista de estudiantes por apellido y luego por nombre.
            # Se accede a los campos del modelo User relacionado ('user__last_name', 'user__first_name').
            estudiantes_del_curso = Estudiante.objects.filter(
                curso=asignacion_actual.curso, is_active=True
            ).order_by('user__last_name', 'user__first_name')
            
            asistencias_hoy = Asistencia.objects.filter(asignacion=asignacion_actual, fecha=fecha_obj)
            asistencias_map = {a.estudiante_id: a.estado for a in asistencias_hoy}
        except AsignacionDocente.DoesNotExist:
            messages.warning(request, "La asignación seleccionada no es válida.")

    context = {
        'asignaciones': asignaciones_docente,
        'estudiantes': estudiantes_del_curso,
        'asistencias_map': asistencias_map,
        'asignacion_seleccionada_id': asignacion_id,
        'fecha_seleccionada': fecha_str,
        'mostrar_lista': mostrar_lista,
    }
    return render(request, 'notas/docente/asistencia.html', context)


@login_required
def guardar_inasistencia_ajax(request):
    """
    Gestiona el guardado asíncrono de los registros de asistencia (petición POST).
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        estudiante_id = data.get('estudiante_id')
        asignacion_id = data.get('asignacion_id')
        fecha_str = data.get('fecha')
        estado = data.get('estado')

        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
        estudiante = get_object_or_404(Estudiante, id=estudiante_id)
        
        docente_actual = Docente.objects.filter(user=request.user).first()
        if not request.user.is_superuser and asignacion.docente != docente_actual:
             return JsonResponse({'status': 'error', 'message': 'Permiso denegado'}, status=403)

        asistencia_obj, created = Asistencia.objects.update_or_create(
            estudiante=estudiante,
            asignacion=asignacion,
            fecha=fecha_str,
            defaults={'estado': estado}
        )

        if estado == 'A' and created:
            _enviar_correo_inasistencia(estudiante, asignacion, fecha_str)

        return JsonResponse({'status': 'success', 'message': 'Asistencia guardada.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    @login_required
    def cambiar_password_vista(request):
        if request.method == 'POST':
            form = CustomPasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # ¡Importante para mantener al usuario logueado!
                messages.success(request, '¡Tu contraseña ha sido actualizada exitosamente!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Por favor corrige los errores a continuación.')
        else:
            form = CustomPasswordChangeForm(request.user)
        return render(request, 'registration/cambiar_password.html', {
            'form': form
        })
