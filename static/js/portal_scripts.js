/**
 * portal_scripts.js
 * This script handles all dynamic content loading for the public portal.
 */
document.addEventListener('DOMContentLoaded', function() {
    
    // --- DOM ELEMENT SELECTORS ---
    const defaultContentContainer = document.getElementById('defaultMainContent');
    const dynamicContentContainer = document.getElementById('dynamicMainContent');
    const dynamicContentBody = dynamicContentContainer.querySelector('.card-body');

    // --- HTML TEMPLATES ---
    const loadingSpinner = `<div class="text-center w-100 py-5"><div class="spinner-border" style="width: 3rem; height: 3rem; color: var(--color-vinotinto);" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-3 fw-bold">Cargando contenido...</p></div>`;
    const errorAlert = (message) => `<div class="alert alert-danger text-center">${message}</div>`;
    
    // --- VIEW MANAGEMENT FUNCTIONS ---
    function showDefaultView(content) {
        defaultContentContainer.innerHTML = content;
        defaultContentContainer.classList.remove('d-none');
        dynamicContentContainer.classList.add('d-none');
        dynamicContentBody.innerHTML = '';
    }

    function showDynamicView(content) {
        defaultContentContainer.classList.add('d-none');
        dynamicContentContainer.classList.remove('d-none');
        dynamicContentBody.innerHTML = content;
    }

    // --- ASYNCHRONOUS DATA LOADING FUNCTIONS ---
    async function fetchAndShow(url) {
        if (!url) {
            console.error("URL is undefined. Cannot fetch content.");
            showDynamicView(errorAlert('Error de configuración: No se pudo encontrar la ruta del contenido.'));
            return;
        }
        showDynamicView(loadingSpinner);
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Network error: ${response.statusText}`);
            const htmlContent = await response.text();
            showDynamicView(htmlContent);
        } catch (error) {
            showDynamicView(errorAlert('No se pudo cargar el contenido solicitado.'));
            console.error(`Error fetching from ${url}:`, error);
        }
    }
    
    async function fetchAndShowJSON(url, renderFunction) {
        if (!url) {
            console.error("URL is undefined. Cannot fetch JSON.");
            // Si la URL es para el carrusel, muestra la vista por defecto vacía en lugar de un error.
            if(renderFunction.name === 'renderCarrusel') {
                showDefaultView('');
            } else {
                showDynamicView(errorAlert('Error de configuración: No se pudo encontrar la ruta de los datos.'));
            }
            return;
        }
        // Para el carrusel, el spinner va en el contenedor por defecto.
        if (renderFunction.name === 'renderCarrusel') {
            showDefaultView(loadingSpinner);
        } else {
            showDynamicView(loadingSpinner);
        }
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Network error: ${response.statusText}`);
            const data = await response.json();
            renderFunction(data);
        } catch (error) {
            const errorMessage = 'No se pudo cargar el contenido solicitado.';
            if (renderFunction.name === 'renderCarrusel') {
                showDefaultView(errorAlert(errorMessage));
            } else {
                showDynamicView(errorAlert(errorMessage));
            }
            console.error(`Error fetching JSON from ${url}:`, error);
        }
    }

    // --- RENDER FUNCTIONS ---
    function renderCarrusel(imagenes) {
        if (imagenes.length === 0) {
            showDefaultView('<div class="text-center p-5 bg-light rounded"><h3>Bienvenido al Portal</h3><p>Aún no hay imágenes en el carrusel.</p></div>');
            return;
        }
        const indicatorsHTML = imagenes.map((img, index) => `<button type="button" data-bs-target="#portalCarousel" data-bs-slide-to="${index}" class="${index === 0 ? 'active' : ''}" aria-current="true"></button>`).join('');
        const itemsHTML = imagenes.map((img, index) => `
            <div class="carousel-item ${index === 0 ? 'active' : ''}">
                <img src="${img.url_imagen}" class="d-block w-100" alt="${img.titulo}" style="max-height: 550px; object-fit: cover;">
                <div class="carousel-caption d-none d-md-block bg-dark bg-opacity-50 p-3 rounded">
                    <h5>${img.titulo}</h5>
                    <p>${img.subtitulo}</p>
                </div>
            </div>`).join('');

        const carruselHTML = `
            <div id="portalCarousel" class="carousel slide mb-5" data-bs-ride="carousel">
                <div class="carousel-indicators">${indicatorsHTML}</div>
                <div class="carousel-inner rounded shadow-lg">${itemsHTML}</div>
                <button class="carousel-control-prev" type="button" data-bs-target="#portalCarousel" data-bs-slide="prev"><span class="carousel-control-prev-icon" aria-hidden="true"></span></button>
                <button class="carousel-control-next" type="button" data-bs-target="#portalCarousel" data-bs-slide="next"><span class="carousel-control-next-icon" aria-hidden="true"></span></button>
            </div>`;
        showDefaultView(carruselHTML);
    }

    function renderNoticias(noticias) {
        let noticiasHTML;
        if (noticias.length === 0) {
            noticiasHTML = '<div class="card"><div class="card-body text-center text-muted">No hay noticias publicadas.</div></div>';
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
                            <button class="btn text-white noticia-link" style="background-color: var(--color-vinotinto);" data-pk="${noticia.pk}">Leer más...</button>
                        </div>
                    </div>`;
            }).join('');
        }
        const finalHTML = `<h2 class="card-title mb-4 border-bottom pb-3">Últimas Noticias</h2> ${noticiasHTML}`;
        showDynamicView(finalHTML);
    }
    
    function renderDocumentos(documentos) {
        let documentosHTML;
        if (documentos.length === 0) {
            documentosHTML = '<p class="text-center text-muted">No hay documentos disponibles.</p>';
        } else {
            documentosHTML = '<div class="list-group">' + documentos.map(doc => 
                `<a href="${doc.url_archivo}" class="list-group-item list-group-item-action" target="_blank" rel="noopener noreferrer">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1"><i class="fas fa-file-download me-2"></i>${doc.titulo}</h5>
                        <small>${doc.fecha}</small>
                    </div>
                    <p class="mb-1 small">${doc.descripcion || 'Clic para descargar'}</p>
                </a>`
            ).join('') + '</div>';
        }
        const finalHTML = `<h2 class="card-title mb-4 border-bottom pb-3">Documentos Públicos</h2> ${documentosHTML}`;
        showDynamicView(finalHTML);
    }

    // --- EVENT LISTENERS ---
    const menuActions = {
        'inicioBtn': () => fetchAndShowJSON(DJANGO_URLS.carrusel, renderCarrusel),
        'noticiasBtn': () => fetchAndShowJSON(DJANGO_URLS.noticias, renderNoticias),
        'historiaBtn': () => fetchAndShow(DJANGO_URLS.historia),
        'misionBtn': () => fetchAndShow(DJANGO_URLS.mision),
        'modeloBtn': () => fetchAndShow(DJANGO_URLS.modelo),
        'directorioBtn': () => fetchAndShow(DJANGO_URLS.directorio),
        'galeriaBtn': () => fetchAndShow(DJANGO_URLS.galeria),
        'documentosBtn': () => fetchAndShowJSON(DJANGO_URLS.documentos, renderDocumentos),
        'recursosBtn': () => fetchAndShow(DJANGO_URLS.recursos),
        'redesBtn': () => fetchAndShow(DJANGO_URLS.redes),
        'documentosFloatBtn': () => fetchAndShowJSON(DJANGO_URLS.documentos, renderDocumentos),
    };
    menuActions['logoBtn'] = menuActions.inicioBtn;

    for (const btnId in menuActions) {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const navbarCollapse = document.getElementById('main-navbar');
                if (navbarCollapse && navbarCollapse.classList.contains('show')) {
                    new bootstrap.Collapse(navbarCollapse).hide();
                }
                menuActions[btnId]();
            });
        }
    }

    dynamicContentContainer.addEventListener('click', function(e) {
        const noticiaLink = e.target.closest('.noticia-link');
        const volverBtn = e.target.closest('.volver-noticias-btn');

        if (noticiaLink) {
            e.preventDefault();
            const pk = noticiaLink.dataset.pk;
            const url = DJANGO_URLS.noticia_detalle.replace('0', pk);
            fetchAndShow(url);
        } else if (volverBtn) {
            e.preventDefault();
            fetchAndShowJSON(DJANGO_URLS.noticias, renderNoticias);
        }
    });

    // --- INITIAL LOAD ---
    menuActions.inicioBtn();
});
