# notas/views/portal_admin_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import HttpResponseNotFound

# Se importan los modelos y formularios necesarios
from ..models import DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel
from ..forms import (
    DocumentoPublicoForm, FotoGaleriaForm, NoticiaForm, ImagenCarruselForm,
    ColegioPersonalizacionForm
)

def es_admin_o_docente(user):
    return user.is_superuser or user.groups.filter(name='Docentes').exists()

@user_passes_test(es_admin_o_docente)
def personalizacion_portal_vista(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        form = ColegioPersonalizacionForm(request.POST, request.FILES, instance=colegio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡La personalización del portal se ha guardado correctamente!')
            return redirect('personalizacion_portal')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = ColegioPersonalizacionForm(instance=colegio)

    context = {
        'form': form,
        'page_title': 'Personalizar Apariencia y Contenido del Portal',
        'colegio': colegio
    }
    return render(request, 'notas/admin_portal/personalizacion_portal.html', context)

@user_passes_test(es_admin_o_docente)
def configuracion_portal_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    return render(request, 'notas/admin_portal/configuracion_portal.html', {'colegio': request.colegio})

# --- Vistas para Documentos (CORREGIDA) ---
@user_passes_test(es_admin_o_docente)
def gestion_documentos_vista(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        form = DocumentoPublicoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.colegio = colegio
            documento.save()
            messages.success(request, 'Documento guardado exitosamente.')
            return redirect('gestion_documentos')
        else:
            # Si el formulario no es válido, se añade un mensaje de error.
            messages.error(request, 'No se pudo guardar el documento. Por favor, corrija los errores.')
    else:
        form = DocumentoPublicoForm()
    
    documentos = DocumentoPublico.objects.filter(colegio=colegio)
    # La vista ahora re-renderiza la página con el formulario inválido para mostrar los errores.
    context = {'form': form, 'documentos': documentos, 'page_title': 'Gestionar Documentos', 'colegio': colegio}
    return render(request, 'notas/admin_portal/gestion_documentos.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_documento_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    documento = get_object_or_404(DocumentoPublico, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        documento.delete()
        messages.success(request, 'Documento eliminado exitosamente.')
    return redirect('gestion_documentos')

# --- Vistas para la Galería (CORREGIDA) ---
@user_passes_test(es_admin_o_docente)
def gestion_galeria_vista(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    if request.method == 'POST':
        form = FotoGaleriaForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.colegio = colegio
            foto.save()
            messages.success(request, 'Foto añadida a la galería.')
            return redirect('gestion_galeria')
        else:
            messages.error(request, 'No se pudo añadir la foto. Por favor, corrija los errores.')
    else:
        form = FotoGaleriaForm()

    fotos = FotoGaleria.objects.filter(colegio=colegio)
    context = {'form': form, 'fotos': fotos, 'page_title': 'Gestionar Galería', 'colegio': colegio}
    return render(request, 'notas/admin_portal/gestion_galeria.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_foto_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    foto = get_object_or_404(FotoGaleria, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        foto.delete()
        messages.success(request, 'Foto eliminada de la galería.')
    return redirect('gestion_galeria')

# --- Vistas para Noticias (MEJORADA) ---
@user_passes_test(es_admin_o_docente)
def gestion_noticias_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    noticias = Noticia.objects.filter(colegio=request.colegio)
    context = {'noticias': noticias, 'page_title': 'Gestionar Noticias', 'colegio': request.colegio}
    return render(request, 'notas/admin_portal/gestion_noticias.html', context)

@user_passes_test(es_admin_o_docente)
def crear_noticia_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save(commit=False)
            noticia.autor = request.user
            noticia.colegio = request.colegio
            noticia.save()
            messages.success(request, 'Noticia creada como BORRADOR. Ahora puedes publicarla desde la lista.')
            return redirect('gestion_noticias')
        else:
            # Se añade un mensaje de error explícito para diagnóstico.
            messages.error(request, 'El formulario contiene errores. Por favor, revise los campos.')
    else:
        form = NoticiaForm()
    context = {'form': form, 'accion': 'Crear', 'page_title': 'Crear Noticia', 'colegio': request.colegio}
    return render(request, 'notas/admin_portal/formulario_noticia.html', context)

@user_passes_test(es_admin_o_docente)
def editar_noticia_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    noticia = get_object_or_404(Noticia, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia actualizada exitosamente.')
            return redirect('gestion_noticias')
        else:
            # Se añade un mensaje de error explícito para diagnóstico.
            messages.error(request, 'El formulario contiene errores. Por favor, revise los campos.')
    else:
        form = NoticiaForm(instance=noticia)
    context = {'form': form, 'accion': 'Editar', 'page_title': f'Editando: {noticia.titulo}', 'colegio': request.colegio}
    return render(request, 'notas/admin_portal/formulario_noticia.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_noticia_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    noticia = get_object_or_404(Noticia, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Noticia eliminada exitosamente.')
    return redirect('gestion_noticias')

@user_passes_test(es_admin_o_docente)
def publicar_noticia_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    noticia = get_object_or_404(Noticia, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        if noticia.estado == 'BORRADOR':
            noticia.estado = 'PUBLICADO'
            messages.success(request, f"La noticia '{noticia.titulo}' ha sido publicada.")
        else:
            noticia.estado = 'BORRADOR'
            messages.info(request, f"La noticia '{noticia.titulo}' ha sido movida a borradores.")
        noticia.save()
    return redirect('gestion_noticias')

# --- Vistas para gestionar el Carrusel (CORREGIDA) ---
@user_passes_test(es_admin_o_docente)
def gestion_carrusel_vista(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    if request.method == 'POST':
        form = ImagenCarruselForm(request.POST, request.FILES)
        if form.is_valid():
            imagen = form.save(commit=False)
            imagen.colegio = colegio
            imagen.save()
            messages.success(request, 'Imagen añadida al carrusel.')
            return redirect('gestion_carrusel')
        else:
            messages.error(request, 'No se pudo añadir la imagen. Por favor, corrija los errores.')
    else:
        form = ImagenCarruselForm()
    
    imagenes = ImagenCarrusel.objects.filter(colegio=colegio).order_by('orden')
    context = { 
        'form': form, 
        'imagenes': imagenes, 
        'page_title': 'Gestionar Carrusel',
        'colegio': colegio
    }
    return render(request, 'notas/admin_portal/gestion_carrusel.html', context)

@user_passes_test(es_admin_o_docente)
def editar_imagen_carrusel_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    imagen = get_object_or_404(ImagenCarrusel, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        form = ImagenCarruselForm(request.POST, request.FILES, instance=imagen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen del carrusel actualizada exitosamente.')
            return redirect('gestion_carrusel')
        else:
            messages.error(request, 'El formulario contiene errores. Por favor, revise los campos.')
    else:
        form = ImagenCarruselForm(instance=imagen)
    
    context = {
        'form': form,
        'page_title': f'Editando Imagen: {imagen.titulo}',
        'colegio': request.colegio
    }
    return render(request, 'notas/admin_portal/editar_imagen_carrusel.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_imagen_carrusel_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    imagen = get_object_or_404(ImagenCarrusel, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        imagen.delete()
        messages.success(request, 'Imagen eliminada del carrusel.')
    return redirect('gestion_carrusel')
