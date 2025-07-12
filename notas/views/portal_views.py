# notas/views/portal_views.py

from django.http import JsonResponse, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Prefetch
from django.urls import reverse

from ..models import (
    Docente, Estudiante, Curso, AsignacionDocente, 
    DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel, 
)

Asignacion = AsignacionDocente

def portal_vista(request):
    """
    Maneja la página principal.
    - Si se identifica un colegio (request.colegio existe), muestra el portal de ese colegio.
    - Si no, muestra la página de inicio principal (landing page) de la plataforma.
    """
    # El middleware ya ha intentado encontrar un colegio.
    if request.colegio:
        # --- LÓGICA DEL PORTAL DEL COLEGIO (YA EXISTENTE) ---
        if request.method == 'POST':
            if request.POST.get('form_type') == 'login_form':
                usuario = request.POST.get('username')
                contrasena = request.POST.get('password')
                user = authenticate(request, username=usuario, password=contrasena)

                if user is not None:
                    # Verificamos que el usuario pertenezca al colegio actual
                    es_docente = Docente.objects.filter(user=user, colegio=request.colegio).exists()
                    es_estudiante = hasattr(user, 'estudiante') and user.estudiante.colegio == request.colegio
                    
                    if user.is_superuser or es_docente or es_estudiante:
                        login(request, user)
                        return redirect('dashboard')
                    else:
                        messages.error(request, 'Este usuario no pertenece a este colegio.')
                else:
                    messages.error(request, 'Usuario o contraseña incorrectos.')
        
        context = {'colegio': request.colegio}
        return render(request, 'notas/portal.html', context)
    else:
        # --- LÓGICA NUEVA: MOSTRAR LANDING PAGE PRINCIPAL ---
        # No se encontró un colegio para este dominio, así que mostramos la página de inicio del servicio.
        return render(request, 'landing/index.html')


def directorio_docentes_json(request):
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no identificado'}, status=404)
    try:
        # 👇 FILTRADO: Obtener solo cursos del colegio actual
        cursos_con_director = Curso.objects.filter(colegio=request.colegio, director_grado__isnull=False).select_related('director_grado')
        directores_map = {c.director_grado.id: c.nombre for c in cursos_con_director}

        # 👇 FILTRADO: Obtener solo docentes del colegio actual
        docentes = Docente.objects.filter(colegio=request.colegio, user__is_active=True).prefetch_related(
            Prefetch(
                'asignaciondocente_set',
                queryset=Asignacion.objects.filter(colegio=request.colegio).select_related('curso', 'materia'),
                to_attr='asignaciones_optimizadas'
            )
        ).order_by('user__last_name', 'user__first_name')

        data_docentes = []
        for docente in docentes:
            materias_grados = {}
            if hasattr(docente, 'asignaciones_optimizadas'):
                for asignacion in docente.asignaciones_optimizadas:
                    materia_nombre = asignacion.materia.nombre
                    grado_nombre = asignacion.curso.nombre 
                    if materia_nombre not in materias_grados:
                        materias_grados[materia_nombre] = set()
                    materias_grados[materia_nombre].add(grado_nombre)
            
            asignaturas_str = "; ".join([f"{materia} ({', '.join(sorted(list(grados)))})" for materia, grados in materias_grados.items()])

            data_docentes.append({
                'nombre_completo': docente.user.get_full_name() or docente.user.username,
                'asignaturas': asignaturas_str if asignaturas_str else "Sin asignaturas",
                'direccion_grupo': directores_map.get(docente.id, "No aplica")
            })
        
        return JsonResponse(data_docentes, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def documentos_publicos_json(request):
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no identificado'}, status=404)
    try:
        # 👇 FILTRADO: Obtener solo documentos del colegio actual
        documentos = DocumentoPublico.objects.filter(colegio=request.colegio).order_by('-fecha_publicacion')
        data_documentos = [
            {'titulo': doc.titulo, 'descripcion': doc.descripcion, 'url_archivo': doc.archivo.url, 'fecha': doc.fecha_publicacion.strftime('%d de %B de %Y')}
            for doc in documentos
        ]
        return JsonResponse(data_documentos, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def galeria_fotos_json(request):
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no identificado'}, status=404)
    try:
        # 👇 FILTRADO: Obtener solo fotos del colegio actual
        fotos = FotoGaleria.objects.filter(colegio=request.colegio).order_by('-fecha_subida')
        data_fotos = [{'titulo': foto.titulo, 'url_imagen': foto.imagen.url} for foto in fotos]
        return JsonResponse(data_fotos, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def noticias_json(request):
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no identificado'}, status=404)
    try:
        # 👇 FILTRADO: Obtener solo noticias del colegio actual
        noticias = Noticia.objects.filter(colegio=request.colegio, estado='PUBLICADO').order_by('-fecha_publicacion')[:10]
        data_noticias = [
            {'pk': noticia.pk, 'titulo': noticia.titulo, 'resumen': noticia.resumen, 'url_imagen': noticia.imagen_portada.url if noticia.imagen_portada else '', 'fecha': noticia.fecha_publicacion.strftime('%d de %B de %Y'), 'autor': noticia.autor.get_full_name() if noticia.autor else 'Administración'}
            for noticia in noticias
        ]
        return JsonResponse(data_noticias, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def carrusel_imagenes_json(request):
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no identificado'}, status=404)
    try:
        # 👇 FILTRADO: Obtener solo imágenes del carrusel del colegio actual
        imagenes = ImagenCarrusel.objects.filter(colegio=request.colegio, visible=True).order_by('orden')
        data = [{'url_imagen': img.imagen.url, 'titulo': img.titulo, 'subtitulo': img.subtitulo} for img in imagenes]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def ajax_noticia_detalle(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    # 👇 FILTRADO: Asegurar que la noticia pertenece al colegio actual
    noticia = get_object_or_404(Noticia, pk=pk, estado='PUBLICADO', colegio=request.colegio)
    context = {'noticia': noticia, 'colegio': request.colegio}
    return render(request, 'notas/portal_components/_contenido_noticia_detalle.html', context)

# Las siguientes vistas de contenido estático podrían necesitar personalización por colegio en el futuro
def ajax_historia(request):
    return render(request, 'notas/portal_components/_contenido_historia.html', {'colegio': request.colegio})

def ajax_mision_vision(request):
    return render(request, 'notas/portal_components/_contenido_mision_vision.html', {'colegio': request.colegio})

def ajax_modelo_pedagogico(request):
    return render(request, 'notas/portal_components/_contenido_modelo.html', {'colegio': request.colegio})

def ajax_recursos_educativos(request):
    return render(request, 'notas/portal_components/_contenido_recursos_educativos.html', {'colegio': request.colegio})

def ajax_redes_sociales(request):
    return render(request, 'notas/portal_components/_contenido_redes_sociales.html', {'colegio': request.colegio})
