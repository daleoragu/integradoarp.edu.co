/**
 * Script para manejar la página de ingreso de notas.
 * Gestiona la creación dinámica de campos de nota, cálculos en tiempo real,
 * el manejo de inasistencias y el envío de datos al servidor.
 * @version 4.0 - Corregida y Sincronizada con Django
 */
document.addEventListener('DOMContentLoaded', function () {
    // --- ELEMENTOS DEL DOM Y DATOS INICIALES ---
    const container = document.querySelector('.container-notas');
    if (!container) return;

    const tablaCalificaciones = document.getElementById('tabla-calificaciones');
    const tbody = tablaCalificaciones?.querySelector('tbody');
    const guardarTodoBtn = document.getElementById('guardarTodoBtn');
    const statusIndicator = document.getElementById('status-indicator');
    const urlInasistenciasEl = document.getElementById('url-get-inasistencias');
    const estudiantesDataEl = document.getElementById('estudiantes-data-json');

    // Valida que los elementos esenciales existan antes de continuar.
    if (!tablaCalificaciones || !tbody || !estudiantesDataEl) {
        console.error("Error crítico: No se encontraron elementos HTML esenciales (tabla, tbody o contenedor de datos JSON).");
        return;
    }

    // Lee los datos inyectados desde los atributos data-* de Django.
    const asignacionData = {
        id: container.dataset.asignacionId,
        periodoId: container.dataset.periodoId,
        csrfToken: container.dataset.csrfToken,
        guardarUrl: container.dataset.guardarUrl,
        inasistenciasUrl: urlInasistenciasEl?.dataset.url
    };

    let estudiantesData = [];
    try {
        const jsonData = estudiantesDataEl.textContent.trim();
        // Solo intenta parsear si el JSON no está vacío.
        if (jsonData) {
            estudiantesData = JSON.parse(jsonData);
        }
    } catch (e) {
        console.error("Error al parsear los datos de los estudiantes desde JSON:", e);
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger py-4">Error al cargar los datos. Revise la consola (F12).</td></tr>';
        return;
    }

    let hayCambiosSinGuardar = false;

    // --- FUNCIONES DE RENDERIZADO Y UI ---

    /**
     * Actualiza el indicador visual de estado (guardado, pendiente, error).
     * @param {'saved' | 'pending' | 'error'} estado El estado a mostrar.
     */
    function actualizarStatus(estado) {
        if (!statusIndicator) return;
        statusIndicator.className = 'status-indicator'; // Resetea clases
        switch (estado) {
            case 'pending':
                statusIndicator.classList.add('status-pending');
                statusIndicator.title = 'Cambios sin guardar';
                hayCambiosSinGuardar = true;
                if (guardarTodoBtn) guardarTodoBtn.disabled = false;
                break;
            case 'saved':
                statusIndicator.classList.add('status-saved');
                statusIndicator.title = 'Todos los cambios guardados';
                hayCambiosSinGuardar = false;
                if (guardarTodoBtn) guardarTodoBtn.disabled = true;
                break;
            case 'error':
                statusIndicator.classList.add('status-error');
                statusIndicator.title = 'Error al guardar. Intente de nuevo.';
                hayCambiosSinGuardar = true;
                if (guardarTodoBtn) guardarTodoBtn.disabled = false;
                break;
        }
    }

    /**
     * Crea un elemento HTML para una nota detallada (descripción y valor).
     * @param {object} nota - Objeto con {descripcion, valor}.
     * @returns {HTMLDivElement} El elemento div del item de nota.
     */
    function crearElementoNota(nota = { descripcion: '', valor: '' }) {
        const div = document.createElement('div');
        div.className = 'nota-detallada-item d-flex align-items-center mb-1';
        div.innerHTML = `
            <input type="text" class="form-control form-control-sm input-desc me-1" placeholder="Descripción" value="${nota.descripcion || ''}">
            <input type="text" class="form-control form-control-sm input-valor" inputmode="decimal" placeholder="Nota" value="${nota.valor || ''}">
            <button type="button" class="btn btn-danger btn-sm btn-remove-nota ms-1" title="Eliminar nota">&times;</button>
        `;
        return div;
    }
    
    /**
     * Crea una fila (TR) completa para un estudiante.
     * @param {object} estudiante - El objeto del estudiante con sus datos.
     * @param {number} index - El índice del estudiante para el contador #.
     * @returns {HTMLTableRowElement} La fila de la tabla.
     */
    function crearFilaEstudiante(estudiante, index) {
        const fila = document.createElement('tr');
        fila.dataset.estudianteId = estudiante.id;
        fila.innerHTML = `
            <td class="text-center align-middle">${index + 1}</td>
            <td class="align-middle"><span class="nombre-estudiante">${estudiante.nombre_completo}</span></td>
            <td class="notas-container" data-tipo="ser"><div class="promedio-display text-center small text-muted">Prom: <span>N/A</span></div></td>
            <td class="notas-container" data-tipo="saber"><div class="promedio-display text-center small text-muted">Prom: <span>N/A</span></div></td>
            <td class="notas-container" data-tipo="hacer"><div class="promedio-display text-center small text-muted">Prom: <span>N/A</span></div></td>
            <td class="text-center fw-bold align-middle celda-definitiva"><span>N/A</span></td>
            <td class="celda-inasistencias align-middle">
                <div class="input-group">
                    <input type="number" class="form-control form-control-sm input-inasistencia" min="0" value="${estudiante.inasistencias || 0}">
                    <button class="btn btn-outline-secondary btn-sm sync-inasistencias" type="button" title="Calcular inasistencias automáticas del sistema de asistencia diario.">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
            </td>
        `;
        return fila;
    }

    /**
     * Renderiza la tabla completa a partir de los datos de los estudiantes.
     */
    function renderizarTablaCompleta() {
        tbody.innerHTML = '';
        if (estudiantesData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No hay estudiantes matriculados en este curso.</td></tr>';
            return;
        }

        estudiantesData.forEach((estudiante, index) => {
            const fila = crearFilaEstudiante(estudiante, index);
            tbody.appendChild(fila);

            // Itera sobre las competencias para agregar las notas detalladas
            ['ser', 'saber', 'hacer'].forEach(tipo => {
                const contenedor = fila.querySelector(`.notas-container[data-tipo="${tipo}"]`);
                const notas = estudiante.notas[tipo] || [];
                
                if (notas.length > 0) {
                    notas.forEach(nota => contenedor.prepend(crearElementoNota(nota)));
                } else {
                    // Si no hay notas, agrega un campo vacío para empezar a calificar
                    contenedor.prepend(crearElementoNota());
                }
                actualizarPromedio(contenedor);
            });
            actualizarDefinitiva(fila);
        });
        actualizarStatus('saved'); // Estado inicial: sin cambios
    }
    
    // --- FUNCIONES DE CÁLCULO ---

    /**
     * Calcula y actualiza el promedio de una competencia (SER, SABER, HACER).
     * @param {HTMLElement} contenedor - El TD que contiene las notas de una competencia.
     */
    function actualizarPromedio(contenedor) {
        const notasInputs = contenedor.querySelectorAll('.input-valor');
        const displaySpan = contenedor.querySelector('.promedio-display span');
        let suma = 0, count = 0;
        
        notasInputs.forEach(input => {
            // Reemplaza la coma por punto para asegurar el parseo correcto
            const valor = parseFloat(input.value.replace(',', '.'));
            if (!isNaN(valor) && valor >= 1.0 && valor <= 5.0) {
                suma += valor;
                count++;
            }
        });

        const promedio = count > 0 ? (suma / count).toFixed(2) : 'N/A';
        displaySpan.textContent = promedio;
        
        const fila = contenedor.closest('tr');
        if (fila) actualizarDefinitiva(fila);
    }

    /**
     * Calcula y actualiza la nota definitiva del periodo para un estudiante.
     * @param {HTMLTableRowElement} fila - La fila del estudiante.
     */
    function actualizarDefinitiva(fila) {
        // Extrae los porcentajes desde el encabezado de la tabla
        const pSerText = document.querySelector('.comp-ser')?.textContent || '0';
        const pSaberText = document.querySelector('.comp-saber')?.textContent || '0';
        const pHacerText = document.querySelector('.comp-hacer')?.textContent || '0';

        const pSer = parseFloat(pSerText.match(/(\d+(\.\d+)?)/)?.[0] || 0) / 100;
        const pSaber = parseFloat(pSaberText.match(/(\d+(\.\d+)?)/)?.[0] || 0) / 100;
        const pHacer = parseFloat(pHacerText.match(/(\d+(\.\d+)?)/)?.[0] || 0) / 100;

        const promSer = parseFloat(fila.querySelector('.notas-container[data-tipo="ser"] .promedio-display span').textContent);
        const promSaber = parseFloat(fila.querySelector('.notas-container[data-tipo="saber"] .promedio-display span').textContent);
        const promHacer = parseFloat(fila.querySelector('.notas-container[data-tipo="hacer"] .promedio-display span').textContent);
        const celdaDefinitiva = fila.querySelector('.celda-definitiva span');

        if (!isNaN(promSer) && !isNaN(promSaber) && !isNaN(promHacer)) {
            const definitiva = (promSer * pSer) + (promSaber * pSaber) + (promHacer * pHacer);
            celdaDefinitiva.textContent = definitiva.toFixed(2);
        } else {
            celdaDefinitiva.textContent = 'N/A';
        }
    }

    // --- MANEJADORES DE EVENTOS ---

    if (tablaCalificaciones) {
        // Delegación de eventos en la tabla para manejar clics y cambios
        tablaCalificaciones.addEventListener('click', async (e) => {
            const btnEliminar = e.target.closest('.btn-remove-nota');
            const btnSync = e.target.closest('.sync-inasistencias');

            if (btnEliminar) {
                const item = btnEliminar.closest('.nota-detallada-item');
                const contenedor = item.parentElement;
                item.remove();
                actualizarPromedio(contenedor);
                actualizarStatus('pending');
            }
            
            if (btnSync) {
                const fila = btnSync.closest('tr');
                const estudianteId = fila.dataset.estudianteId;
                const inputInasistencia = fila.querySelector('.input-inasistencia');
                
                btnSync.disabled = true;
                btnSync.querySelector('i').classList.add('fa-spin');
                
                try {
                    const url = `${asignacionData.inasistenciasUrl}?estudiante_id=${estudianteId}&asignacion_id=${asignacionData.id}&periodo_id=${asignacionData.periodoId}`;
                    const response = await fetch(url);
                    if (!response.ok) throw new Error(`Error del servidor: ${response.statusText}`);
                    
                    const data = await response.json();
                    if (data.status === 'success') {
                        inputInasistencia.value = data.inasistencias_auto;
                        actualizarStatus('pending');
                    } else {
                        throw new Error(data.message || 'Respuesta no exitosa del servidor.');
                    }
                } catch (error) {
                    console.error('Error al sincronizar inasistencias:', error);
                    alert('Error al calcular inasistencias: ' + error.message);
                } finally {
                    btnSync.disabled = false;
                    btnSync.querySelector('i').classList.remove('fa-spin');
                }
            }
        });

        tablaCalificaciones.addEventListener('input', (e) => {
            const target = e.target;
            // Si se modifica cualquier campo de nota o inasistencia, marca como pendiente.
            if (target.classList.contains('input-valor') || target.classList.contains('input-desc') || target.classList.contains('input-inasistencia')) {
                if (target.classList.contains('input-valor')) {
                    const contenedor = target.closest('.notas-container');
                    if (contenedor) actualizarPromedio(contenedor);
                }
                actualizarStatus('pending');
            }
        });
    }

    // Evento para los botones "+" que añaden campos de nota a todos los estudiantes.
    document.querySelectorAll('.btn-add-all').forEach(btn => {
        btn.addEventListener('click', function() {
            const tipo = this.dataset.tipo;
            tablaCalificaciones.querySelectorAll(`.notas-container[data-tipo="${tipo}"]`).forEach(contenedor => {
                contenedor.prepend(crearElementoNota());
            });
            actualizarStatus('pending');
        });
    });

    // Evento para el botón principal de "Guardar Todos los Cambios".
    guardarTodoBtn?.addEventListener('click', async function() {
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';

        // Construye el objeto de datos (payload) para enviar al servidor
        const payload = {
            asignacion_id: asignacionData.id,
            periodo_id: asignacionData.periodoId,
            estudiantes: []
        };

        tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(fila => {
            const estudianteId = fila.dataset.estudianteId;
            const datosEstudiante = {
                id: estudianteId,
                notas: { ser: [], saber: [], hacer: [] },
                inasistencias: fila.querySelector('.input-inasistencia').value.trim() || '0'
            };

            ['ser', 'saber', 'hacer'].forEach(tipo => {
                fila.querySelectorAll(`.notas-container[data-tipo="${tipo}"] .nota-detallada-item`).forEach(item => {
                    const descripcion = item.querySelector('.input-desc').value.trim();
                    const valor = item.querySelector('.input-valor').value.trim().replace(',', '.');
                    // Solo añade la nota si tiene un valor
                    if (valor) {
                        datosEstudiante.notas[tipo].push({ descripcion, valor });
                    }
                });
            });
            payload.estudiantes.push(datosEstudiante);
        });

        try {
            const response = await fetch(asignacionData.guardarUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': asignacionData.csrfToken
                },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            
            if (response.ok && result.status === 'success') {
                alert('¡Éxito! ' + result.message);
                actualizarStatus('saved');
            } else {
                throw new Error(result.message || 'Error desconocido al guardar.');
            }
        } catch (error) {
            console.error('Error al guardar todo:', error);
            alert('Error: ' + error.message);
            actualizarStatus('error');
        } finally {
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-save me-2"></i>Guardar Todos los Cambios';
        }
    });
    
    // Advierte al usuario si intenta salir con cambios sin guardar.
    window.addEventListener('beforeunload', (e) => {
        if (hayCambiosSinGuardar) {
            e.preventDefault();
            e.returnValue = 'Tienes cambios sin guardar. ¿Estás seguro de que quieres salir?';
        }
    });

    // --- INICIALIZACIÓN ---
    // Llama a la función principal para construir la tabla al cargar la página.
    renderizarTablaCompleta();
});
