/**
 * portal_scripts.js
 * * Este script maneja la navegación dinámica del portal público, cargando
 * contenido de manera asíncrona desde el backend de Django.
 */
document.addEventListener('DOMContentLoaded', function() {
    
    // --- SELECTORES DE ELEMENTOS DEL DOM ---
    const defaultContentContainer = document.getElementById('defaultMainContent');
    const dynamicContentContainer = document.getElementById('dynamicMainContent');
    const dynamicContentBody = dynamicContentContainer.querySelector('.card-body');

    // --- PLANTILLAS HTML PARA CONTENIDO DINÁMICO ---
    const loadingSpinner = `
        <div class="text-center w-100 py-5">
            <div class="spinner-border" style="width: 3rem; height: 3rem; color: var(--color-vinotinto);" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-3 fw-bold">Cargando contenido...</p>
        </div>`;
    const errorAlert = (message) => `<div class="alert alert-danger text-center">${message}</div>`;
    
    // --- FUNCIONES DE MANEJO DE VISTAS ---

    /**
     * Oculta el contenedor de contenido dinámico y muestra el contenedor por defecto (el del carrusel).
     */
    function showDefaultView() {
        defaultContentContainer.classList.remove('d-none');
        dynamicContentContainer.classList.add('d-none');
        dynamicContentBody.innerHTML = '';
    }

    /**
     * Muestra el contenedor de contenido dinámico y oculta el contenedor por defecto.
     * @param {string} content - El contenido HTML que se insertará en el cuerpo del contenedor dinámico.
     */
    function showDynamicView(content) {
        defaultContentContainer.classList.add('d-none');
        dynamicContentContainer.classList.remove('d-none');
        dynamicContentBody.innerHTML = content;
    }

    // --- FUNCIONES ASÍNCRONAS PARA CARGAR DATOS (FETCH) ---

    /**
     * Carga y muestra el carrusel principal en la vista por defecto.
     */
    async function cargarInicio() {
        showDefaultView();
        defaultContentContainer.innerHTML = loadingSpinner;
        try {
            const response = await fetch(DJANGO_URLS.carrusel);
            if (!response.ok) throw new Error('Error de red al cargar el carrusel.');
            const imagenes = await response.json();

            if (imagenes.length === 0) {
                defaultContentContainer.innerHTML = errorAlert('No hay imágenes configuradas para el carrusel.');
                return;
            }

            const indicatorsHTML = imagenes.map((img, index) => {
                const activeClass = index === 0 ? 'active' : '';
                return `<button type="button" data-bs-target="#portalCarousel" data-bs-slide-to="${index}" class="${activeClass}" aria-current="true"></button>`;
            }).join('');

            const itemsHTML = imagenes.map((img, index) => {
                const activeClass = index === 0 ? 'active' : '';
                return `
                    <div class="carousel-item ${activeClass}">
                        <img src="${img.url_imagen}" class="d-block w-100" alt="${img.titulo}" style="max-height: 550px; object-fit: cover;">
                        <div class="carousel-caption d-none d-md-block bg-dark bg-opacity-50 p-3 rounded">
                            <h5>${img.titulo}</h5>
                            <p>${img.subtitulo}</p>
                        </div>
                    </div>`;
            }).join('');

            const carruselHTML = `
                <div id="portalCarousel" class="carousel slide mb-5" data-bs-ride="carousel">
                    <div class="carousel-indicators">${indicatorsHTML}</div>
                    <div class="carousel-inner rounded shadow-lg">${itemsHTML}</div>
                    <button class="carousel-control-prev" type="button" data-bs-target="#portalCarousel" data-bs-slide="prev"><span class="carousel-control-prev-icon" aria-hidden="true"></span></button>
                    <button class="carousel-control-next" type="button" data-bs-target="#portalCarousel" data-bs-slide="next"><span class="carousel-control-next-icon" aria-hidden="true"></span></button>
                </div>`;
            
            defaultContentContainer.innerHTML = carruselHTML;
        } catch (error) {
            defaultContentContainer.innerHTML = errorAlert('No se pudo cargar el carrusel de imágenes.');
            console.error("Error en cargarInicio:", error);
        }
    }
    
    /**
     * Función genérica para obtener contenido HTML desde una URL de Django y mostrarlo.
     * @param {string} url - La URL del endpoint de Django que devuelve HTML.
     */
    async function fetchAndShow(url) {
        showDynamicView(loadingSpinner);
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Error de red.');
            const htmlContent = await response.text();
            showDynamicView(htmlContent);
        } catch (error) {
            showDynamicView(errorAlert('No se pudo cargar el contenido solicitado.'));
            console.error(`Error al hacer fetch a ${url}:`, error);
        }
    }
    
    /**
     * Carga y muestra el listado de noticias.
     */
    async function cargarNoticias() {
        showDynamicView(loadingSpinner);
        try {
            const response = await fetch(DJANGO_URLS.noticias);
            if (!response.ok) throw new Error('Error de red.');
            const noticias = await response.json();
            
            let noticiasHTML = '';
            if (noticias.length === 0) {
                noticiasHTML = '<div class="card"><div class="card-body text-center text-muted">No hay noticias publicadas en este momento.</div></div>';
            } else {
                noticiasHTML = noticias.map(noticia => {
                    const imagenHTML = noticia.url_imagen ? `<img src="${noticia.url_imagen}" class="card-img-top" alt="${noticia.titulo}" style="max-height: 250px; object-fit: cover;">` : '';
                    return `
                        <div class="card mb-4 shadow-sm">
                            ${imagenHTML}
                            <div class="card-body">
                                <h4 class="card-title">${noticia.titulo}</h4>
                                <p class="card-text"><small class="text-muted">Publicado por ${noticia.autor} el ${noticia.fecha}</small></p>
                                <p class="card-text">${noticia.resumen}</p>
                                <a href="${noticia.url_detalle}" class="btn text-white" style="background-color: var(--color-vinotinto);">Leer más...</a>
                            </div>
                        </div>`;
                }).join('');
            }
            const finalHTML = `<h2 class="card-title mb-4 border-bottom pb-3">Últimas Noticias</h2> ${noticiasHTML}`;
            showDynamicView(finalHTML);
        } catch (error) {
            showDynamicView(errorAlert('No se pudieron cargar las noticias.'));
        }
    }


    // --- ASIGNACIÓN DE EVENTOS A LOS BOTONES DEL MENÚ ---
    
    // Mapeo de IDs de botones a las funciones que deben ejecutar.
    const menuActions = {
        'logoBtn': cargarInicio,
        'inicioBtn': cargarInicio,
        'noticiasBtn': cargarNoticias,
        'historiaBtn': () => fetchAndShow(DJANGO_URLS.historia),
        'misionBtn': () => fetchAndShow(DJANGO_URLS.mision),
        'modeloBtn': () => fetchAndShow(DJANGO_URLS.modelo),
        'directorioBtn': () => fetchAndShow(DJANGO_URLS.directorio),
        'galeriaBtn': () => fetchAndShow(DJANGO_URLS.galeria),
        'documentosBtn': () => fetchAndShow(DJANGO_URLS.documentos),
        'recursosBtn': () => fetchAndShow(DJANGO_URLS.recursos),
        'redesBtn': () => fetchAndShow(DJANGO_URLS.redes),
    };

    // Asigna el evento 'click' a cada botón del menú.
    for (const btnId in menuActions) {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.preventDefault(); // Previene la navegación por defecto del enlace.
                
                // Cierra el menú de hamburguesa en móviles si está abierto.
                const navbarCollapse = document.getElementById('main-navbar');
                if (navbarCollapse.classList.contains('show')) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                        toggle: false
                    });
                    bsCollapse.hide();
                }

                menuActions[btnId](); // Ejecuta la acción correspondiente.
            });
        }
    }

    // --- CARGA INICIAL ---
    // Carga el carrusel tan pronto como la página esté lista.
    cargarInicio();
});
