# notas/views/portal_views.py

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Prefetch
from django.urls import reverse

# Se importan todos los modelos necesarios para las vistas del portal
from ..models import (
    Docente, Curso, AsignacionDocente, 
    DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel, 
)

# Se renombra AsignacionDocente para facilitar su uso en la vista
Asignacion = AsignacionDocente

def portal_vista(request):
    """
    Maneja la página principal del portal público. No redirige a los
    usuarios que ya han iniciado sesión.
    """
    if request.method == 'POST':
        if request.POST.get('form_type') == 'login_form':
            usuario = request.POST.get('username')
            contrasena = request.POST.get('password')
            user = authenticate(request, username=usuario, password=contrasena)
            
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'notas/portal.html')


def directorio_docentes_json(request):
    """
    Crea una lista en formato JSON con la información de cada docente,
    ordenada numéricamente por dirección de grupo.
    """
    try:
        cursos_con_director = Curso.objects.filter(director_grado__isnull=False).select_related('director_grado')
        directores_map = {c.director_grado.id: c.nombre for c in cursos_con_director}

        docentes = Docente.objects.filter(user__is_active=True).prefetch_related(
            Prefetch(
                'asignaciondocente_set',
                queryset=Asignacion.objects.select_related('curso', 'materia').order_by('curso__nombre', 'materia__nombre'),
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

        sorted_data = sorted(
            data_docentes,
            key=lambda d: (
                d['direccion_grupo'] == 'No aplica',
                int(d['direccion_grupo']) if d['direccion_grupo'] != 'No aplica' else 0,
                d['nombre_completo']
            )
        )
        return JsonResponse(sorted_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def documentos_publicos_json(request):
    """
    Obtiene todos los documentos públicos y los devuelve en formato JSON.
    """
    try:
        documentos = DocumentoPublico.objects.all().order_by('-fecha_publicacion')
        data_documentos = [
            {
                'titulo': doc.titulo,
                'descripcion': doc.descripcion,
                'url_archivo': doc.archivo.url,
                'fecha': doc.fecha_publicacion.strftime('%d de %B de %Y')
            }
            for doc in documentos
        ]
        return JsonResponse(data_documentos, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def galeria_fotos_json(request):
    """
    Obtiene todas las fotos de la galería y las devuelve en formato JSON.
    """
    try:
        fotos = FotoGaleria.objects.all().order_by('-fecha_subida')
        data_fotos = [
            {
                'titulo': foto.titulo,
                'url_imagen': foto.imagen.url,
            }
            for foto in fotos
        ]
        return JsonResponse(data_fotos, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def noticias_json(request):
    """
    Obtiene las 5 noticias más recientes que estén publicadas y las 
    devuelve en formato JSON.
    """
    try:
        noticias = Noticia.objects.filter(estado='PUBLICADO').order_by('-fecha_publicacion')[:5]
        data_noticias = [
            {
                'pk': noticia.pk,
                'titulo': noticia.titulo,
                'resumen': noticia.resumen,
                'url_imagen': noticia.imagen_portada.url if noticia.imagen_portada else '',
                'fecha': noticia.fecha_publicacion.strftime('%d de %B de %Y'),
                'autor': noticia.autor.get_full_name() if noticia.autor else 'Administración',
                'url_detalle': reverse('noticia_detalle', args=[noticia.pk])
            }
            for noticia in noticias
        ]
        return JsonResponse(data_noticias, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def noticia_detalle_vista(request, pk):
    """
    Muestra una noticia individual y completa en una página dedicada.
    """
    noticia = get_object_or_404(Noticia, pk=pk, estado='PUBLICADO')
    context = {
        'noticia': noticia
    }
    return render(request, 'notas/portal_components/noticia_detalle.html', context)

def carrusel_imagenes_json(request):
    """
    Devuelve las imágenes del carrusel principal en formato JSON.
    """
    try:
        imagenes = ImagenCarrusel.objects.filter(visible=True).order_by('orden')
        data = [{'url_imagen': img.imagen.url, 'titulo': img.titulo, 'subtitulo': img.subtitulo} for img in imagenes]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# --- Vistas para las secciones del Colegio ---

def ajax_historia(request):
    """
    Renderiza y devuelve el contenido parcial de la sección 'Historia'.
    """
    return render(request, 'notas/portal_components/_contenido_historia.html')

def ajax_mision_vision(request):
    """
    Renderiza y devuelve el contenido parcial de la sección 'Misión y Visión'.
    """
    return render(request, 'notas/portal_components/_contenido_mision_vision.html')

def ajax_modelo_pedagogico(request):
    """
    Renderiza y devuelve el contenido parcial de la sección 'Modelo Pedagógico'.
    """
    return render(request, 'notas/portal_components/_contenido_modelo.html')

# --- Vistas para secciones de Comunidad ---

def ajax_recursos_educativos(request):
    """
    Renderiza y devuelve el contenido parcial de la sección 'Recursos Educativos'.
    """
    return render(request, 'notas/portal_components/_contenido_recursos_educativos.html')

def ajax_redes_sociales(request):
    """
    Renderiza y devuelve el contenido parcial de la sección 'Redes Sociales'.
    """
    return render(request, 'notas/portal_components/_contenido_redes_sociales.html')
