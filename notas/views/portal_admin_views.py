# notas/views/portal_admin_views.py
import os
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
# Se añade HttpResponseNotFound para manejar el caso de un colegio no identificado
from django.http import HttpResponseNotFound

from ..models import DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel
from ..forms import DocumentoPublicoForm, FotoGaleriaForm, NoticiaForm, ImagenCarruselForm

def es_admin_o_docente(user):
    # Este decorador se mantiene, pero la lógica fina se hace en cada vista.
    return user.is_superuser or user.groups.filter(name='Docentes').exists()

@user_passes_test(es_admin_o_docente)
def configuracion_portal_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    # Pasamos el colegio a la plantilla para que los enlaces funcionen correctamente.
    return render(request, 'notas/admin_portal/configuracion_portal.html', {'colegio': request.colegio})

# --- Vistas para Documentos ---
@user_passes_test(es_admin_o_docente)
def gestion_documentos_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        form = DocumentoPublicoForm(request.POST, request.FILES)
        if form.is_valid():
            # CORRECCIÓN: Asociar el nuevo documento al colegio actual.
            documento = form.save(commit=False)
            documento.colegio = request.colegio
            documento.save()
            messages.success(request, 'Documento guardado exitosamente.')
            return redirect('gestion_documentos')
    else:
        form = DocumentoPublicoForm()
    
    # CORRECCIÓN: Mostrar solo los documentos del colegio actual.
    documentos = DocumentoPublico.objects.filter(colegio=request.colegio)
    context = {'form': form, 'documentos': documentos, 'page_title': 'Gestionar Documentos', 'colegio': request.colegio}
    return render(request, 'notas/admin_portal/gestion_documentos.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_documento_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    # CORRECCIÓN: Asegurar que solo se puede eliminar un documento del colegio actual.
    documento = get_object_or_404(DocumentoPublico, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        documento.delete()
        messages.success(request, 'Documento eliminado exitosamente.')
    return redirect('gestion_documentos')

# --- Vistas para la Galería ---
@user_passes_test(es_admin_o_docente)
def gestion_galeria_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    if request.method == 'POST':
        form = FotoGaleriaForm(request.POST, request.FILES)
        if form.is_valid():
            # CORRECCIÓN: Asociar la nueva foto al colegio actual.
            foto = form.save(commit=False)
            foto.colegio = request.colegio
            foto.save()
            messages.success(request, 'Foto añadida a la galería.')
            return redirect('gestion_galeria')
    else:
        form = FotoGaleriaForm()

    # CORRECCIÓN: Mostrar solo las fotos del colegio actual.
    fotos = FotoGaleria.objects.filter(colegio=request.colegio)
    context = {'form': form, 'fotos': fotos, 'page_title': 'Gestionar Galería', 'colegio': request.colegio}
    return render(request, 'notas/admin_portal/gestion_galeria.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_foto_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    # CORRECCIÓN: Asegurar que solo se puede eliminar una foto del colegio actual.
    foto = get_object_or_404(FotoGaleria, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        foto.delete()
        messages.success(request, 'Foto eliminada de la galería.')
    return redirect('gestion_galeria')

# --- Vistas para Noticias ---
@user_passes_test(es_admin_o_docente)
def gestion_noticias_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    # CORRECCIÓN: Mostrar solo las noticias del colegio actual.
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
            # CORRECCIÓN: Asociar la nueva noticia al colegio actual.
            noticia.colegio = request.colegio
            noticia.save()
            messages.success(request, 'Noticia creada como BORRADOR. Ahora puedes publicarla desde la lista.')
            return redirect('gestion_noticias')
    else:
        form = NoticiaForm()
    context = {'form': form, 'accion': 'Crear', 'page_title': 'Crear Noticia', 'colegio': request.colegio}
    return render(request, 'notas/admin_portal/formulario_noticia.html', context)

@user_passes_test(es_admin_o_docente)
def editar_noticia_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    # CORRECCIÓN: Asegurar que solo se puede editar una noticia del colegio actual.
    noticia = get_object_or_404(Noticia, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia actualizada exitosamente.')
            return redirect('gestion_noticias')
    else:
        form = NoticiaForm(instance=noticia)
    context = {'form': form, 'accion': 'Editar', 'page_title': f'Editando: {noticia.titulo}', 'colegio': request.colegio}
    return render(request, 'notas/admin_portal/formulario_noticia.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_noticia_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    # CORRECCIÓN: Asegurar que solo se puede eliminar una noticia del colegio actual.
    noticia = get_object_or_404(Noticia, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Noticia eliminada exitosamente.')
    return redirect('gestion_noticias')

@user_passes_test(es_admin_o_docente)
def publicar_noticia_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    # CORRECCIÓN: Asegurar que solo se puede publicar una noticia del colegio actual.
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

# --- VISTAS PARA GESTIONAR EL CARRUSEL ---
@user_passes_test(es_admin_o_docente)
def gestion_carrusel_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    if request.method == 'POST':
        form = ImagenCarruselForm(request.POST, request.FILES)
        if form.is_valid():
            # CORRECCIÓN: Asociar la nueva imagen al colegio actual.
            imagen = form.save(commit=False)
            imagen.colegio = request.colegio
            imagen.save()
            messages.success(request, 'Imagen añadida al carrusel.')
        else:
            messages.error(request, f"El formulario no es válido. Errores: {form.errors}")
        return redirect('gestion_carrusel')
    else:
        form = ImagenCarruselForm()
    
    # CORRECCIÓN: Mostrar solo las imágenes del colegio actual.
    imagenes = ImagenCarrusel.objects.filter(colegio=request.colegio).order_by('orden')
    context = { 
        'form': form, 
        'imagenes': imagenes, 
        'page_title': 'Gestionar Carrusel',
        'colegio': request.colegio
    }
    return render(request, 'notas/admin_portal/gestion_carrusel.html', context)

@user_passes_test(es_admin_o_docente)
def editar_imagen_carrusel_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    # CORRECCIÓN: Asegurar que solo se puede editar una imagen del colegio actual.
    imagen = get_object_or_404(ImagenCarrusel, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        form = ImagenCarruselForm(request.POST, request.FILES, instance=imagen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen del carrusel actualizada exitosamente.')
            return redirect('gestion_carrusel')
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
    # CORRECCIÓN: Asegurar que solo se puede eliminar una imagen del colegio actual.
    imagen = get_object_or_404(ImagenCarrusel, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        imagen.delete()
        messages.success(request, 'Imagen eliminada del carrusel.')
    return redirect('gestion_carrusel')
