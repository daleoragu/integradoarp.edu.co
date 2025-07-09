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
    function showDefaultView() {
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
        showDynamicView(loadingSpinner);
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network error.');
            const htmlContent = await response.text();
            showDynamicView(htmlContent);
        } catch (error) {
            showDynamicView(errorAlert('No se pudo cargar el contenido solicitado.'));
            console.error(`Error fetching from ${url}:`, error);
        }
    }
    
    async function fetchAndShowJSON(url, renderFunction) {
        showDynamicView(loadingSpinner);
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network error.');
            const data = await response.json();
            renderFunction(data);
        } catch (error) {
            showDynamicView(errorAlert('No se pudo cargar el contenido solicitado.'));
            console.error(`Error fetching JSON from ${url}:`, error);
        }
    }

    // --- RENDER FUNCTIONS ---
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
        'logoBtn': () => fetchAndShow(DJANGO_URLS.carrusel), // Asumiendo que carrusel devuelve HTML
        'inicioBtn': () => fetchAndShow(DJANGO_URLS.carrusel),
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
            fetchAndShow(`/ajax/noticia/${pk}/`);
        } else if (volverBtn) {
            e.preventDefault();
            fetchAndShowJSON(DJANGO_URLS.noticias, renderNoticias);
        }
    });

    // --- INITIAL LOAD ---
    menuActions.inicioBtn();
});
