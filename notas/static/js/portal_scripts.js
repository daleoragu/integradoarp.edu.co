document.addEventListener('DOMContentLoaded', function() {
    // Contenedores
    const defaultContentContainer = document.getElementById('defaultMainContent');
    const dynamicContentContainer = document.getElementById('dynamicMainContent');
    const dynamicContentBody = dynamicContentContainer.querySelector('.card-body');

    // Botones del nuevo menú
    const logoBtn = document.getElementById('logoBtn');
    const inicioBtn = document.getElementById('inicioBtn');
    const noticiasBtn = document.getElementById('noticiasBtn');
    const misionBtn = document.getElementById('misionBtn');
    const historiaBtn = document.getElementById('historiaBtn');
    const modeloBtn = document.getElementById('modeloBtn');
    const galeriaBtn = document.getElementById('galeriaBtn');
    const directorioBtn = document.getElementById('directorioBtn');
    const documentosBtn = document.getElementById('documentosBtn');
    const recursosBtn = document.getElementById('recursosBtn');
    const redesBtn = document.getElementById('redesBtn');

    // --- Contenidos HTML Estáticos ---
    const misionHTML = `<h2 class="h3 fw-bold text-center mb-4" style="color: var(--color-primario);">Misión y Visión</h2><p class="text-justify">La Institución Educativa Técnica Alfonso Palacio Rudas, fiel a su tradición democrática e integradora, inspirada en la tolerancia, autonomía, identidad, libertad y paz, tiene como misión relacionar el ser con el saber y el saber hacer; así como desarrollar la capacidad de sentir, pensar y actuar de quien aprende.</p><hr class="my-4"><p class="text-justify">La visión de futuro de la INSTITUCIÓN EDUCATIVA TÉCNICA ALFONSO PALACIO RUDAS se enmarca dentro del compromiso común de cada uno de los miembros de la Comunidad Educativa por formar hombres y mujeres íntegros(as) e integrales. Se pretende que demuestren liderazgo social, pronunciamiento y compromiso ante el mundo que les rodea, como agentes de cambio, íntegros, creativos y coherentes a través de lo que piensan, sienten dicen y hacen.</p>`;
    const historiaHTML = `<h2 class="h3 fw-bold text-center mb-4" style="color: var(--color-primario);">Nuestra Historia</h2><p>Contenido sobre la historia del colegio...</p>`;
    const modeloHTML = `<h2 class="h3 fw-bold text-center mb-4" style="color: var(--color-primario);">Modelo Pedagógico</h2><p>Contenido sobre el modelo pedagógico...</p>`;
    const recursosHTML = `<h2 class="h3 fw-bold text-center mb-4" style="color: var(--color-primario);">Recursos Educativos</h2><div class="list-group"><a href="https://www.duolingo.com" target="_blank" class="list-group-item list-group-item-action">Duolingo - Aprender idiomas</a><a href="https://es.khanacademy.org/" target="_blank" class="list-group-item list-group-item-action">Khan Academy - Matemáticas, ciencias y más</a></div>`;
    const redesHTML = `<h2 class="h3 fw-bold text-center mb-4" style="color: var(--color-primario);">Nuestras Redes Sociales</h2><div class="list-group"><a href="https://www.facebook.com/iet.alfonso.palacio.rudas.honda" target="_blank" class="list-group-item list-group-item-action fs-5"><i class="fab fa-facebook-square fa-fw me-3"></i>Facebook</a><a href="https://www.instagram.com/nombredeusuario" target="_blank" class="list-group-item list-group-item-action fs-5"><i class="fab fa-instagram-square fa-fw me-3"></i>Instagram</a></div>`;
    
    // --- Plantillas HTML base para contenido dinámico ---
    const cofradiaTitleHTML = `<div class="text-center mb-4 border-bottom pb-3"><p class="text-uppercase small text-muted mb-0" style="letter-spacing: 2px;">Últimas Noticias</p><h2 class="display-5 fw-bold" style="color: var(--color-primario);">El Diario La Cofradía Informa</h2></div>`;
    const galeriaBaseHTML = `<h2 class="h3 fw-bold text-center mb-4" style="color: var(--color-primario);">GALERÍA DE FOTOS</h2><div id="galeria-grid" class="row g-3"></div>`;
    const directorioBaseHTML = `<h2 class="h3 fw-bold text-center mb-4" style="color: var(--color-primario);">NUESTRO EQUIPO DOCENTE</h2><div class="table-responsive"><table class="table table-striped table-hover"><thead class="table-dark"><tr><th>Docente</th><th>Asignaturas y Grados</th><th>Director de Grupo</th></tr></thead><tbody id="directorio-tbody"></tbody></table></div>`;
    const documentosBaseHTML = `<h2 class="h3 fw-bold text-center mb-4" style="color: var(--color-primario);">DOCUMENTOS PÚBLICOS</h2><div id="documentos-lista" class="list-group"></div>`;

    
    // --- Funciones Asíncronas para Cargar Datos del Backend ---

    async function cargarInicio() {
        showDefaultView();
        defaultContentContainer.innerHTML = '<div class="text-center w-100"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Cargando...</p></div>';
        try {
            const response = await fetch(DJANGO_URLS.carrusel);
            if (!response.ok) throw new Error('Error de red');
            const imagenes = await response.json();

            if (imagenes.length === 0) {
                defaultContentContainer.innerHTML = '<div class="text-center p-5 bg-light rounded"><h3>Bienvenido al Portal</h3><p>Actualmente no hay imágenes en el carrusel.</p></div>';
                return;
            }

            let indicatorsHTML = '';
            let itemsHTML = '';
            imagenes.forEach((img, index) => {
                const activeClass = index === 0 ? 'active' : '';
                indicatorsHTML += `<button type="button" data-bs-target="#portalCarousel" data-bs-slide-to="${index}" class="${activeClass}" aria-current="true"></button>`;
                itemsHTML += `
                    <div class="carousel-item ${activeClass}">
                        <img src="${img.url_imagen}" class="d-block w-100" alt="${img.titulo}" style="max-height: 550px; object-fit: cover;">
                        <div class="carousel-caption d-none d-md-block bg-dark bg-opacity-50 p-3 rounded">
                            <h5>${img.titulo}</h5>
                            <p>${img.subtitulo}</p>
                        </div>
                    </div>
                `;
            });

            const carruselHTML = `
                <div id="portalCarousel" class="carousel slide mb-5" data-bs-ride="carousel">
                    <div class="carousel-indicators">${indicatorsHTML}</div>
                    <div class="carousel-inner rounded shadow-lg">${itemsHTML}</div>
                    <button class="carousel-control-prev" type="button" data-bs-target="#portalCarousel" data-bs-slide="prev"><span class="carousel-control-prev-icon" aria-hidden="true"></span><span class="visually-hidden">Previous</span></button>
                    <button class="carousel-control-next" type="button" data-bs-target="#portalCarousel" data-bs-slide="next"><span class="carousel-control-next-icon" aria-hidden="true"></span><span class="visually-hidden">Next</span></button>
                </div>`;
            
            defaultContentContainer.innerHTML = carruselHTML;
        } catch (error) {
            defaultContentContainer.innerHTML = '<p class="text-danger text-center">No se pudo cargar el carrusel de imágenes.</p>';
            console.error("Error en cargarInicio:", error);
        }
    }

    async function cargarNoticias() {
        showDynamicView(cofradiaTitleHTML + '<div id="noticias-container" class="mt-4"></div>');
        const noticiasContainer = document.getElementById('noticias-container');
        noticiasContainer.innerHTML = '<div class="text-center w-100"><div class="spinner-border text-primary" role="status"></div></div>';
        try {
            const response = await fetch(DJANGO_URLS.noticias);
            if (!response.ok) throw new Error('Error de red');
            const noticias = await response.json();
            
            let noticiasHTML = '';
            if (noticias.length === 0) {
                noticiasHTML = '<div class="card"><div class="card-body text-center text-muted">No hay noticias publicadas.</div></div>';
            } else {
                noticias.forEach(noticia => {
                    const imagenHTML = noticia.url_imagen ? `<img src="${noticia.url_imagen}" class="card-img-top" alt="${noticia.titulo}" style="max-height: 250px; object-fit: cover;">` : '';
                    noticiasHTML += `
                        <div class="card mb-4 shadow-sm">
                            ${imagenHTML}
                            <div class="card-body">
                                <h4 class="card-title">${noticia.titulo}</h4>
                                <p class="card-text"><small class="text-muted">Publicado por ${noticia.autor} el ${noticia.fecha}</small></p>
                                <p class="card-text">${noticia.resumen}</p>
                                <a href="${noticia.url_detalle}" class="btn btn-primary btn-sm">Leer más...</a>
                            </div>
                        </div>
                    `;
                });
            }
            noticiasContainer.innerHTML = noticiasHTML;
        } catch (error) {
            noticiasContainer.innerHTML = '<div class="card"><div class="card-body text-center text-danger">No se pudieron cargar las noticias.</div></div>';
        }
    }

    async function cargarGaleria() {
        showDynamicView(galeriaBaseHTML);
        const galeriaGrid = document.getElementById('galeria-grid');
        galeriaGrid.innerHTML = '<div class="text-center w-100"><div class="spinner-border text-primary"></div><p>Cargando...</p></div>';
        try {
            const response = await fetch(DJANGO_URLS.galeria); 
            if (!response.ok) throw new Error('Error de red.');
            const fotos = await response.json();
            galeriaGrid.innerHTML = '';
            if (fotos.length === 0) {
                galeriaGrid.innerHTML = '<p class="text-center text-muted w-100">No hay fotos en la galería.</p>';
            } else {
                fotos.forEach(foto => {
                    galeriaGrid.innerHTML += `<div class="col-6 col-md-4"><a href="${foto.url_imagen}" target="_blank" data-bs-toggle="tooltip" title="Ver imagen: ${foto.titulo}"><img src="${foto.url_imagen}" class="img-fluid rounded shadow-sm" alt="${foto.titulo}" style="height: 180px; width: 100%; object-fit: cover;"></a></div>`;
                });
                initializeTooltips(galeriaGrid);
            }
        } catch (error) {
            galeriaGrid.innerHTML = '<p class="text-center text-danger w-100">No se pudo cargar la galería.</p>';
        }
    }

    async function cargarDirectorio() {
        showDynamicView(directorioBaseHTML);
        const tbody = document.getElementById('directorio-tbody');
        tbody.innerHTML = '<tr><td colspan="3" class="text-center"><div class="spinner-border spinner-border-sm"></div> Cargando...</td></tr>';
        try {
            const response = await fetch(DJANGO_URLS.directorio);
            const docentes = await response.json();
            tbody.innerHTML = '';
            if (docentes.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No hay docentes para mostrar.</td></tr>';
            } else {
                docentes.forEach(docente => {
                    tbody.innerHTML += `<tr><td>${docente.nombre_completo}</td><td>${docente.asignaturas}</td><td>${docente.direccion_grupo}</td></tr>`;
                });
            }
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="3" class="text-center text-danger">No se pudo cargar el directorio.</td></tr>`;
        }
    }

    async function cargarDocumentos() {
        showDynamicView(documentosBaseHTML);
        const lista = document.getElementById('documentos-lista');
        lista.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm"></div> Cargando...</div>';
        try {
            const response = await fetch(DJANGO_URLS.documentos);
            const documentos = await response.json();
            lista.innerHTML = '';
            if (documentos.length === 0) {
                lista.innerHTML = '<p class="text-center text-muted">No hay documentos disponibles.</p>';
            } else {
                documentos.forEach(doc => {
                    lista.innerHTML += `<a href="${doc.url_archivo}" class="list-group-item list-group-item-action" download><div class="d-flex w-100 justify-content-between"><h5 class="mb-1"><i class="fas fa-file-download me-2"></i>${doc.titulo}</h5><small>${doc.fecha}</small></div><p class="mb-1 small">${doc.descripcion || 'Clic para descargar'}</p></a>`;
                });
            }
        } catch (error) {
            lista.innerHTML = '<p class="text-center text-danger">No se pudieron cargar los documentos.</p>';
        }
    }

    // --- Funciones de Manejo del DOM ---
    function showDynamicView(content) {
        defaultContentContainer.classList.add('d-none');
        dynamicContentContainer.classList.remove('d-none');
        dynamicContentBody.innerHTML = content;
    }
    
    function showDefaultView() {
        defaultContentContainer.classList.remove('d-none');
        dynamicContentContainer.classList.add('d-none');
        dynamicContentBody.innerHTML = '';
    }

    function initializeTooltips(container) {
        const tooltipTriggerList = [].slice.call(container.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // --- Asignación de Eventos ---
    const menuActions = {
        logoBtn: cargarInicio,
        inicioBtn: cargarInicio,
        noticiasBtn: cargarNoticias,
        misionBtn: () => showDynamicView(misionHTML),
        historiaBtn: () => showDynamicView(historiaHTML),
        modeloBtn: () => showDynamicView(modeloHTML),
        galeriaBtn: cargarGaleria,
        directorioBtn: cargarDirectorio,
        documentosBtn: cargarDocumentos,
        recursosBtn: () => showDynamicView(recursosHTML),
        redesBtn: () => showDynamicView(redesHTML)
    };

    for (const btnId in menuActions) {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                menuActions[btnId]();
            });
        }
    }

    // --- Carga Inicial ---
    cargarInicio();
});
