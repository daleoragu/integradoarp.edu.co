# notas/views/publicacion_views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
from itertools import groupby

from ..models import PeriodoAcademico, PublicacionBoletin, Notificacion, Estudiante, PublicacionBoletinFinal

def es_admin(user):
    return user.is_superuser

@user_passes_test(es_admin)
def panel_publicacion_vista(request):
    if request.method == 'POST':
        tipo_publicacion = request.POST.get('tipo_publicacion')
        accion = request.POST.get('accion')
        
        if tipo_publicacion == 'periodo':
            periodo_id = request.POST.get('periodo_id')
            try:
                periodo = PeriodoAcademico.objects.get(id=periodo_id)
                publicacion, _ = PublicacionBoletin.objects.get_or_create(periodo=periodo, defaults={'publicado_por': request.user})
                
                if accion == 'publicar':
                    publicacion.esta_visible = True
                    publicacion.publicado_por = request.user
                    publicacion.save()
                    messages.success(request, f"Los boletines del '{periodo}' han sido publicados.")
                elif accion == 'ocultar':
                    publicacion.esta_visible = False
                    publicacion.save()
                    messages.warning(request, f"Los boletines del '{periodo}' han sido ocultados.")

            except PeriodoAcademico.DoesNotExist:
                messages.error(request, "El periodo seleccionado no existe.")

        elif tipo_publicacion == 'final':
            ano_lectivo = request.POST.get('ano_lectivo')
            try:
                publicacion, _ = PublicacionBoletinFinal.objects.get_or_create(ano_lectivo=ano_lectivo, defaults={'publicado_por': request.user})

                if accion == 'publicar':
                    publicacion.esta_visible = True
                    publicacion.publicado_por = request.user
                    publicacion.save()
                    messages.success(request, f"El Informe Final del año {ano_lectivo} ha sido publicado y se ha notificado a los estudiantes.")
                    
                    estudiantes_a_notificar = Estudiante.objects.filter(calificacion__periodo__ano_lectivo=ano_lectivo).distinct().select_related('user')
                    try:
                        url_boletin = reverse('mi_boletin')
                    except NoReverseMatch:
                        url_boletin = '#'
                    for est in estudiantes_a_notificar:
                        Notificacion.objects.create(
                            destinatario=est.user,
                            mensaje=f"Ya está disponible tu Informe Final del año {ano_lectivo}.",
                            tipo='GENERAL',
                            url=url_boletin
                        )
                elif accion == 'ocultar':
                    publicacion.esta_visible = False
                    publicacion.save()
                    messages.warning(request, f"El Informe Final del año {ano_lectivo} ha sido ocultado.")
            except Exception as e:
                messages.error(request, f"Error al procesar el informe final: {e}")

        return redirect('panel_publicacion')

    periodos = PeriodoAcademico.objects.all().order_by('-ano_lectivo', 'fecha_inicio')
    periodos_agrupados = {k: list(v) for k, v in groupby(periodos, key=lambda p: p.ano_lectivo)}
    
    publicaciones_periodos = set(PublicacionBoletin.objects.filter(esta_visible=True).values_list('periodo_id', flat=True))
    publicaciones_finales = set(PublicacionBoletinFinal.objects.filter(esta_visible=True).values_list('ano_lectivo', flat=True))
    
    context = {
        'periodos_agrupados': periodos_agrupados,
        'publicaciones_periodos': publicaciones_periodos,
        'publicaciones_finales': publicaciones_finales
    }
    return render(request, 'notas/admin_tools/publicar_boletines.html', context)
