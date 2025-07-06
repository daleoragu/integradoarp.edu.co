# notas/views/estudiante_observador_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone

# --- INICIO DE LA CORRECCIÓN ---
# Importamos los modelos necesarios
from ..models import Estudiante, FichaEstudiante, RegistroObservador
# Y nuestra función de utilidad para crear notificaciones
from ..utils import crear_notificacion
# ¡Importamos el nuevo formulario que creamos!
from ..forms import EstudianteCompromisoForm
# --- FIN DE LA CORRECCIÓN ---


def es_estudiante(user):
    """Verifica si el usuario pertenece al grupo de Estudiantes."""
    return user.groups.filter(name='Estudiantes').exists()

@login_required
@user_passes_test(es_estudiante, login_url='login')
def mi_observador_vista(request):
    """
    Muestra el observador personal del estudiante logueado y maneja
    el envío de su descargo y la edición de su compromiso.
    """
    try:
        estudiante = Estudiante.objects.get(user=request.user)
    except Estudiante.DoesNotExist:
        messages.error(request, "Acceso denegado. Su usuario no está asociado a un perfil de estudiante.")
        return redirect('login')

    # Obtenemos la ficha del estudiante o la creamos si no existe.
    ficha, created = FichaEstudiante.objects.get_or_create(estudiante=estudiante)

    if request.method == 'POST':
        # --- LÓGICA PARA DIFERENCIAR QUÉ FORMULARIO SE ENVÍA ---
        # Usamos el nombre del botón de 'submit' para saber qué acción procesar.
        
        # 1. Si se está guardando un DESCARGO de una observación específica.
        if 'guardar_descargo' in request.POST:
            registro_id = request.POST.get('registro_id')
            descargo_texto = request.POST.get('descargo')
            
            if registro_id and descargo_texto:
                registro = get_object_or_404(RegistroObservador, id=registro_id, estudiante=estudiante)
                registro.descargo_estudiante = descargo_texto
                registro.fecha_descargo = timezone.now()
                registro.save()
                
                if registro.docente_reporta:
                    nombre_estudiante = estudiante.user.get_full_name()
                    crear_notificacion(
                        destinatario=registro.docente_reporta.user,
                        mensaje=f"El estudiante {nombre_estudiante} ha añadido un descargo a tu observación.",
                        tipo='OBSERVADOR',
                        url_name='vista_detalle_observador',
                        estudiante_id=estudiante.id
                    )
                messages.success(request, "Tu descargo ha sido guardado correctamente.")
            else:
                messages.error(request, "No se pudo guardar el descargo. Faltaron datos.")

        # 2. Si se está guardando el COMPROMISO de la ficha general.
        elif 'guardar_compromiso' in request.POST:
            compromiso_form = EstudianteCompromisoForm(request.POST, instance=ficha)
            if compromiso_form.is_valid():
                compromiso_form.save()
                messages.success(request, "Tu compromiso ha sido actualizado correctamente.")
            else:
                messages.error(request, "Hubo un error al guardar tu compromiso. Por favor, inténtalo de nuevo.")
            
        return redirect('mi_observador')

    # Para peticiones GET (cuando se carga la página), preparamos el formulario.
    compromiso_form = EstudianteCompromisoForm(instance=ficha)
    registros = RegistroObservador.objects.filter(estudiante=estudiante).order_by('-fecha_suceso')

    context = {
        'estudiante': estudiante,
        'ficha': ficha,
        'registros': registros,
        'compromiso_form': compromiso_form, # Pasamos el formulario de compromiso al contexto
        'page_title': 'Mi Observador Estudiantil'
    }
    
    return render(request, 'notas/estudiante/mi_observador.html', context)
