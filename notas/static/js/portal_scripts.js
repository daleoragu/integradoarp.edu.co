/**
 * portal_scripts.js
 * This script handles the dynamic navigation of the public portal,
 * loading content asynchronously from the Django backend.
 */
document.addEventListener('DOMContentLoaded', function() {
    
    // --- DOM ELEMENT SELECTORS ---
    const defaultContentContainer = document.getElementById('defaultMainContent');
    const dynamicContentContainer = document.getElementById('dynamicMainContent');
    const dynamicContentBody = dynamicContentContainer.querySelector('.card-body');

    // --- HTML TEMPLATES FOR DYNAMIC CONTENT ---
    const loadingSpinner = `
        <div class="text-center w-100 py-5">
            <div class="spinner-border" style="width: 3rem; height: 3rem; color: var(--color-vinotinto);" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-3 fw-bold">Cargando contenido...</p>
        </div>`;
    const errorAlert = (message) => `<div class="alert alert-danger text-center">${message}</div>`;
    
    // --- VIEW MANAGEMENT FUNCTIONS ---

    /**
     * Hides the dynamic content container and shows the default one (for the carousel).
     */
    function showDefaultView() {
        defaultContentContainer.classList.remove('d-none');
        dynamicContentContainer.classList.add('d-none');
        dynamicContentBody.innerHTML = '';
    }

    /**
     * Shows the dynamic content container and hides the default one.
     * @param {string} content - The HTML content to be inserted into the dynamic container's body.
     */
    function showDynamicView(content) {
        defaultContentContainer.classList.add('d-none');
        dynamicContentContainer.classList.remove('d-none');
        dynamicContentBody.innerHTML = content;
    }

    // --- ASYNCHRONOUS DATA LOADING FUNCTIONS (FETCH) ---

    /**
     * Loads and displays the main carousel in the default view.
     */
    async function cargarInicio() {
        showDefaultView();
        defaultContentContainer.innerHTML = loadingSpinner;
        try {
            const response = await fetch(DJANGO_URLS.carrusel);
            if (!response.ok) throw new Error('Network error while loading the carousel.');
            const imagenes = await response.json();

            if (imagenes.length === 0) {
                defaultContentContainer.innerHTML = errorAlert('No images configured for the carousel.');
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
            defaultContentContainer.innerHTML = errorAlert('Could not load the image carousel.');
            console.error("Error in cargarInicio:", error);
        }
    }
    
    /**
     * Generic function to fetch HTML content from a Django URL and display it.
     * This is the corrected function that loads content from partial HTML files.
     * @param {string} url - The URL of the Django endpoint that returns HTML.
     */
    async function fetchAndShow(url) {
        showDynamicView(loadingSpinner);
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network error.');
            const htmlContent = await response.text();
            showDynamicView(htmlContent);
        } catch (error) {
            showDynamicView(errorAlert('Could not load the requested content.'));
            console.error(`Error fetching from ${url}:`, error);
        }
    }
    
    /**
     * Loads and displays the list of news articles.
     */
    async function cargarNoticias() {
        showDynamicView(loadingSpinner);
        try {
            const response = await fetch(DJANGO_URLS.noticias);
            if (!response.ok) throw new Error('Network error.');
            const noticias = await response.json();
            
            let noticiasHTML = '';
            if (noticias.length === 0) {
                noticiasHTML = '<div class="card"><div class="card-body text-center text-muted">There are no news articles published at the moment.</div></div>';
            } else {
                noticiasHTML = noticias.map(noticia => {
                    const imagenHTML = noticia.url_imagen ? `<img src="${noticia.url_imagen}" class="card-img-top" alt="${noticia.titulo}" style="max-height: 250px; object-fit: cover;">` : '';
                    return `
                        <div class="card mb-4 shadow-sm">
                            ${imagenHTML}
                            <div class="card-body">
                                <h4 class="card-title">${noticia.titulo}</h4>
                                <p class="card-text"><small class="text-muted">Published by ${noticia.autor} on ${noticia.fecha}</small></p>
                                <p class="card-text">${noticia.resumen}</p>
                                <a href="${noticia.url_detalle}" class="btn text-white" style="background-color: var(--color-vinotinto);">Read more...</a>
                            </div>
                        </div>`;
                }).join('');
            }
            const finalHTML = `<h2 class="card-title mb-4 border-bottom pb-3">Latest News</h2> ${noticiasHTML}`;
            showDynamicView(finalHTML);
        } catch (error) {
            showDynamicView(errorAlert('Could not load news articles.'));
        }
    }


    // --- EVENT LISTENERS FOR MENU BUTTONS ---
    
    // Map of button IDs to the functions they should execute.
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
        // The new floating button for documents also calls the same function.
        'documentosFloatBtn': () => fetchAndShow(DJANGO_URLS.documentos),
    };

    // Assigns the 'click' event to each button in the map.
    for (const btnId in menuActions) {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.preventDefault(); // Prevents the default link navigation.
                
                // Closes the mobile hamburger menu if it's open.
                const navbarCollapse = document.getElementById('main-navbar');
                if (navbarCollapse.classList.contains('show')) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                        toggle: false
                    });
                    bsCollapse.hide();
                }

                menuActions[btnId](); // Executes the corresponding action.
            });
        }
    }

    // --- INITIAL LOAD ---
    // Loads the carousel as soon as the page is ready.
    cargarInicio();
});
