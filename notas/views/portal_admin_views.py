# notas/views/portal_admin_views.py
import os
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

from ..models import DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel
from ..forms import DocumentoPublicoForm, FotoGaleriaForm, NoticiaForm, ImagenCarruselForm

def es_admin_o_docente(user):
    return user.is_superuser or user.groups.filter(name='Docentes').exists()

@user_passes_test(es_admin_o_docente)
def configuracion_portal_vista(request):
    return render(request, 'notas/admin_portal/configuracion_portal.html')

# --- Vistas para Documentos ---
@user_passes_test(es_admin_o_docente)
def gestion_documentos_vista(request):
    if request.method == 'POST':
        form = DocumentoPublicoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documento guardado exitosamente.')
            return redirect('gestion_documentos')
    else:
        form = DocumentoPublicoForm()
    documentos = DocumentoPublico.objects.all()
    context = {'form': form, 'documentos': documentos, 'page_title': 'Gestionar Documentos'}
    return render(request, 'notas/admin_portal/gestion_documentos.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_documento_vista(request, pk):
    documento = get_object_or_404(DocumentoPublico, pk=pk)
    if request.method == 'POST':
        documento.delete()
        messages.success(request, 'Documento eliminado exitosamente.')
    return redirect('gestion_documentos')

# --- Vistas para la Galería ---
@user_passes_test(es_admin_o_docente)
def gestion_galeria_vista(request):
    if request.method == 'POST':
        form = FotoGaleriaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Foto añadida a la galería.')
            return redirect('gestion_galeria')
    else:
        form = FotoGaleriaForm()
    fotos = FotoGaleria.objects.all()
    context = {'form': form, 'fotos': fotos, 'page_title': 'Gestionar Galería'}
    return render(request, 'notas/admin_portal/gestion_galeria.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_foto_vista(request, pk):
    foto = get_object_or_404(FotoGaleria, pk=pk)
    if request.method == 'POST':
        foto.delete()
        messages.success(request, 'Foto eliminada de la galería.')
    return redirect('gestion_galeria')

# --- Vistas para Noticias ---
@user_passes_test(es_admin_o_docente)
def gestion_noticias_vista(request):
    noticias = Noticia.objects.all()
    context = {'noticias': noticias, 'page_title': 'Gestionar Noticias'}
    return render(request, 'notas/admin_portal/gestion_noticias.html', context)

@user_passes_test(es_admin_o_docente)
def crear_noticia_vista(request):
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save(commit=False)
            noticia.autor = request.user
            noticia.save()
            messages.success(request, 'Noticia creada como BORRADOR. Ahora puedes publicarla desde la lista.')
            return redirect('gestion_noticias')
    else:
        form = NoticiaForm()
    context = {'form': form, 'accion': 'Crear', 'page_title': 'Crear Noticia'}
    return render(request, 'notas/admin_portal/formulario_noticia.html', context)

@user_passes_test(es_admin_o_docente)
def editar_noticia_vista(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia actualizada exitosamente.')
            return redirect('gestion_noticias')
    else:
        form = NoticiaForm(instance=noticia)
    context = {'form': form, 'accion': 'Editar', 'page_title': f'Editando: {noticia.titulo}'}
    return render(request, 'notas/admin_portal/formulario_noticia.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_noticia_vista(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Noticia eliminada exitosamente.')
    return redirect('gestion_noticias')

@user_passes_test(es_admin_o_docente)
def publicar_noticia_vista(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
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
# --- VISTAS PARA GESTIONAR EL CARRUSEL ---
@user_passes_test(es_admin_o_docente)
def gestion_carrusel_vista(request):
    if request.method == 'POST':
        form = ImagenCarruselForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen añadida al carrusel.')
            return redirect('gestion_carrusel')
        else:
            messages.error(request, f"El formulario no es válido. Errores: {form.errors}")
    else:
        form = ImagenCarruselForm()
    
    imagenes = ImagenCarrusel.objects.order_by('orden') # Ordenamos por el campo 'orden'
    context = { 
        'form': form, 
        'imagenes': imagenes, 
        'page_title': 'Gestionar Carrusel',
    }
    return render(request, 'notas/admin_portal/gestion_carrusel.html', context)

# --- VISTA NUEVA PARA EDITAR LA IMAGEN ---
@user_passes_test(es_admin_o_docente)
def editar_imagen_carrusel_vista(request, pk):
    imagen = get_object_or_404(ImagenCarrusel, pk=pk)
    if request.method == 'POST':
        # Pasamos la instancia para que el formulario sepa que estamos editando
        form = ImagenCarruselForm(request.POST, request.FILES, instance=imagen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen del carrusel actualizada exitosamente.')
            return redirect('gestion_carrusel')
    else:
        # Llenamos el formulario con los datos de la imagen existente
        form = ImagenCarruselForm(instance=imagen)
    
    context = {
        'form': form,
        'page_title': f'Editando Imagen: {imagen.titulo}'
    }
    # Usaremos un nuevo template para la página de edición
    return render(request, 'notas/admin_portal/editar_imagen_carrusel.html', context)


@user_passes_test(es_admin_o_docente)
def eliminar_imagen_carrusel_vista(request, pk):
    imagen = get_object_or_404(ImagenCarrusel, pk=pk)
    if request.method == 'POST':
        imagen.delete()
        messages.success(request, 'Imagen eliminada del carrusel.')
    return redirect('gestion_carrusel')
