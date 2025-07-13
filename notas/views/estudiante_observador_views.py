# notas/views/estudiante_observador_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
# Se añade HttpResponseNotFound para manejar el caso de un colegio no identificado
from django.http import HttpResponseNotFound

# Importamos los modelos y formularios necesarios
from ..models import Estudiante, FichaEstudiante, RegistroObservador
from ..utils import crear_notificacion
from ..forms import EstudianteCompromisoForm


def es_estudiante(user):
    """Verifica si el usuario pertenece al grupo de Estudiantes."""
    return user.groups.filter(name='Estudiantes').exists()

@login_required
@user_passes_test(es_estudiante, login_url='login')
def mi_observador_vista(request):
    """
    Muestra el observador personal del estudiante logueado, asegurando
    que el estudiante pertenezca al colegio actual.
    """
    # CORRECCIÓN: Verificar que se ha identificado un colegio.
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    try:
        # CORRECCIÓN: Asegurar que se obtiene el estudiante del colegio actual.
        estudiante = Estudiante.objects.get(user=request.user, colegio=request.colegio)
    except Estudiante.DoesNotExist:
        messages.error(request, "Acceso denegado. Su usuario no está asociado a un perfil de estudiante en este colegio.")
        # Redirigir a logout para limpiar la sesión es más seguro.
        return redirect('logout')

    # La obtención de la ficha ya es segura porque depende de un 'estudiante' ya filtrado.
    ficha, created = FichaEstudiante.objects.get_or_create(estudiante=estudiante)

    if request.method == 'POST':
        # 1. Si se está guardando un DESCARGO de una observación específica.
        if 'guardar_descargo' in request.POST:
            registro_id = request.POST.get('registro_id')
            descargo_texto = request.POST.get('descargo')
            
            if registro_id and descargo_texto:
                # La consulta del registro ya es segura porque se filtra por el 'estudiante' del usuario logueado.
                registro = get_object_or_404(RegistroObservador, id=registro_id, estudiante=estudiante)
                registro.descargo_estudiante = descargo_texto
                registro.fecha_descargo = timezone.now()
                registro.save()
                
                # La notificación también es segura.
                if registro.docente_reporta:
                    nombre_estudiante = estudiante.user.get_full_name()
                    crear_notificacion(
                        destinatario=registro.docente_reporta.user,
                        mensaje=f"El estudiante {nombre_estudiante} ha añadido un descargo a tu observación.",
                        tipo='OBSERVADOR',
                        url_name='vista_detalle_observador',
                        estudiante_id=estudiante.id,
                        colegio=request.colegio # Asociar la notificación al colegio
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

    # Para peticiones GET, preparamos el formulario.
    compromiso_form = EstudianteCompromisoForm(instance=ficha)
    
    # CORRECCIÓN: Filtrar los registros por el colegio actual para mayor seguridad.
    registros = RegistroObservador.objects.filter(
        estudiante=estudiante, colegio=request.colegio
    ).order_by('-fecha_suceso')

    context = {
        'estudiante': estudiante,
        'ficha': ficha,
        'registros': registros,
        'compromiso_form': compromiso_form,
        'page_title': 'Mi Observador Estudiantil',
        'colegio': request.colegio
    }
    
    return render(request, 'notas/estudiante/mi_observador.html', context)
