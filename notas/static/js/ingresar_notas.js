/**
 * Script para manejar la página de ingreso de notas con estilo de hoja de cálculo.
 * @version 6.0 - Con coloreado de notas y gestión de porcentajes.
 */
document.addEventListener('DOMContentLoaded', function () {
    // --- ELEMENTOS DEL DOM Y DATOS INICIALES ---
    const container = document.querySelector('.container-notas');
    if (!container) return;

    const tablaCalificaciones = document.getElementById('tabla-calificaciones');
    const guardarTodoBtn = document.getElementById('guardarTodoBtn');
    const statusIndicator = document.getElementById('status-indicator');
    const estudiantesDataEl = document.getElementById('estudiantes-data-json');
    const asignacionDetailsEl = document.getElementById('asignacion-details');

    if (!tablaCalificaciones || !estudiantesDataEl || !asignacionDetailsEl) {
        console.error("Faltan elementos HTML esenciales: #tabla-calificaciones, #estudiantes-data-json o #asignacion-details.");
        return;
    }

    const asignacionData = {
        id: container.dataset.asignacionId,
        periodoId: container.dataset.periodoId,
        csrfToken: container.dataset.csrfToken,
        guardarUrl: container.dataset.guardarUrl,
        // Datos para la nueva lógica de visualización
        esPonderacionEquitativa: asignacionDetailsEl.dataset.usarPonderacionEquitativa === 'true',
        pSer: parseFloat(asignacionDetailsEl.dataset.pSer),
        pSaber: parseFloat(asignacionDetailsEl.dataset.pSaber),
        pHacer: parseFloat(asignacionDetailsEl.dataset.pHacer)
    };

    let estudiantesData = [];
    try {
        estudiantesData = JSON.parse(estudiantesDataEl.textContent.trim() || '[]');
    } catch (e) {
        console.error("Error al parsear JSON de estudiantes:", e);
        tablaCalificaciones.innerHTML = '<p class="text-danger">Error al cargar datos de estudiantes.</p>';
        return;
    }

    let hayCambiosSinGuardar = false;
    // Almacena las descripciones de las columnas de notas.
    let descripcionesColumnas = { ser: {}, saber: {}, hacer: {} };

    // --- FUNCIONES DE RENDERIZADO Y UI ---

    function actualizarStatus(estado) {
        if (!statusIndicator) return;
        statusIndicator.className = 'status-indicator';
        const periodoCerrado = document.querySelector('.card-footer .text-warning');
        switch (estado) {
            case 'pending':
                statusIndicator.classList.add('status-pending');
                statusIndicator.title = 'Cambios sin guardar';
                hayCambiosSinGuardar = true;
                if (guardarTodoBtn && !periodoCerrado) guardarTodoBtn.disabled = false;
                break;
            case 'saved':
                statusIndicator.classList.add('status-saved');
                statusIndicator.title = 'Cambios guardados';
                hayCambiosSinGuardar = false;
                if (guardarTodoBtn) guardarTodoBtn.disabled = true;
                break;
            case 'error':
                statusIndicator.classList.add('status-error');
                statusIndicator.title = 'Error al guardar';
                hayCambiosSinGuardar = true;
                if (guardarTodoBtn && !periodoCerrado) guardarTodoBtn.disabled = false;
                break;
        }
    }

    function renderizarTabla() {
        // 1. Determinar el número máximo de columnas necesarias para cada competencia
        const maxNotas = { ser: 0, saber: 0, hacer: 0 };
        estudiantesData.forEach(est => {
            for (const tipo in maxNotas) {
                const notasCount = est.notas[tipo]?.length || 0;
                if (notasCount > maxNotas[tipo]) {
                    maxNotas[tipo] = notasCount;
                }
                // Poblar las descripciones iniciales desde los datos
                est.notas[tipo]?.forEach((nota, i) => {
                    if (nota.descripcion && !descripcionesColumnas[tipo][i]) {
                        descripcionesColumnas[tipo][i] = nota.descripcion;
                    }
                });
            }
        });

        // Asegurar al menos una columna si no hay notas
        for (const tipo in maxNotas) {
            if (maxNotas[tipo] === 0) maxNotas[tipo] = 1;
        }

        // 2. Construir el HTML del encabezado (thead)
        let headerHtml = `<thead class="table-light"><tr><th rowspan="2" class="text-center align-middle">#</th><th rowspan="2" class="align-middle">Estudiante</th>`;
        
        // Lógica para mostrar u ocultar porcentajes
        const porcentajes = { ser: asignacionData.pSer, saber: asignacionData.pSaber, hacer: asignacionData.pHacer };
        for (const tipo of ['ser', 'saber', 'hacer']) {
            const porcentajeStr = asignacionData.esPonderacionEquitativa ? '' : ` (${porcentajes[tipo]}%)`;
            headerHtml += `<th colspan="${maxNotas[tipo] + 1}" class="text-center comp-${tipo}">${tipo.toUpperCase()}${porcentajeStr} 
                <button class="btn btn-outline-success btn-sm btn-add-col" data-tipo="${tipo}" title="Añadir columna de nota">+</button>
                <button class="btn btn-outline-danger btn-sm btn-remove-col" data-tipo="${tipo}" title="Quitar última columna">-</button>
            </th>`;
        }
        headerHtml += `<th rowspan="2" class="text-center align-middle">Definitiva</th><th rowspan="2" class="text-center align-middle">Inasistencias</th></tr><tr>`;

        for (const tipo of ['ser', 'saber', 'hacer']) {
            for (let i = 0; i < maxNotas[tipo]; i++) {
                const desc = descripcionesColumnas[tipo][i] || `N${i + 1}`;
                headerHtml += `<th class="text-center th-nota" data-tipo="${tipo}" data-col-index="${i}" title="Clic para describir esta nota">${desc}</th>`;
            }
            headerHtml += `<th class="text-center align-middle prom-header">Prom.</th>`;
        }
        headerHtml += `</tr></thead>`;

        // 3. Construir el HTML del cuerpo (tbody)
        let bodyHtml = `<tbody>`;
        if (estudiantesData.length === 0) {
            const colspan = 4 + maxNotas.ser + maxNotas.saber + maxNotas.hacer;
            bodyHtml += `<tr><td colspan="${colspan}" class="text-center text-muted py-4">No hay estudiantes en este curso.</td></tr>`;
        } else {
            estudiantesData.forEach((estudiante, index) => {
                bodyHtml += `<tr data-estudiante-id="${estudiante.id}"><td class="text-center align-middle">${index + 1}</td><td class="align-middle">${estudiante.nombre_completo}</td>`;
                for (const tipo of ['ser', 'saber', 'hacer']) {
                    for (let i = 0; i < maxNotas[tipo]; i++) {
                        const nota = estudiante.notas[tipo]?.[i]?.valor || '';
                        bodyHtml += `<td><input type="text" class="form-control form-control-sm input-nota" data-tipo="${tipo}" value="${nota}" inputmode="decimal"></td>`;
                    }
                    bodyHtml += `<td class="text-center align-middle fw-bold prom-celda" data-tipo="${tipo}">0.00</td>`;
                }
                bodyHtml += `<td class="text-center align-middle fw-bolder def-celda">0.00</td><td class="align-middle"><input type="number" class="form-control form-control-sm input-inasistencia" min="0" value="${estudiante.inasistencias || 0}"></td></tr>`;
            });
        }
        bodyHtml += `</tbody>`;
        tablaCalificaciones.innerHTML = headerHtml + bodyHtml;

        // 4. Calcular todos los promedios y definitivas iniciales
        tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(actualizarTodosLosPromedios);
    }

    // --- FUNCIONES DE CÁLCULO ---

    function actualizarTodosLosPromedios(fila) {
        ['ser', 'saber', 'hacer'].forEach(tipo => {
            const inputs = fila.querySelectorAll(`.input-nota[data-tipo="${tipo}"]`);
            const promCelda = fila.querySelector(`.prom-celda[data-tipo="${tipo}"]`);
            let suma = 0, count = 0;
            inputs.forEach(input => {
                const valor = parseFloat(input.value.replace(',', '.'));
                if (!isNaN(valor) && valor >= 1.0 && valor <= 5.0) {
                    suma += valor;
                    count++;
                }
            });
            promCelda.textContent = count > 0 ? (suma / count).toFixed(2) : '0.00';
        });
        actualizarDefinitiva(fila);
    }

    function actualizarDefinitiva(fila) {
        const defCelda = fila.querySelector('.def-celda');
        let definitiva = 0;
        const porcentajes = { ser: asignacionData.pSer / 100, saber: asignacionData.pSaber / 100, hacer: asignacionData.pHacer / 100 };
        
        ['ser', 'saber', 'hacer'].forEach(tipo => {
            const prom = parseFloat(fila.querySelector(`.prom-celda[data-tipo="${tipo}"]`).textContent);
            if (!isNaN(prom)) {
                definitiva += prom * porcentajes[tipo];
            }
        });
        
        defCelda.textContent = definitiva.toFixed(2);

        // Lógica de coloreado de la celda de definitiva
        defCelda.classList.remove('nota-roja', 'nota-amarilla', 'nota-verde', 'nota-azul');
        const notaFinal = parseFloat(defCelda.textContent);

        if (notaFinal < 3.0) {
            defCelda.classList.add('nota-roja');
        } else if (notaFinal < 4.0) {
            defCelda.classList.add('nota-amarilla');
        } else if (notaFinal < 4.6) {
            defCelda.classList.add('nota-verde');
        } else {
            defCelda.classList.add('nota-azul');
        }
    }

    // --- MANEJADORES DE EVENTOS ---

    tablaCalificaciones.addEventListener('input', e => {
        if (e.target.classList.contains('input-nota') || e.target.classList.contains('input-inasistencia')) {
            if (e.target.classList.contains('input-nota')) {
                const fila = e.target.closest('tr');
                actualizarTodosLosPromedios(fila);
            }
            actualizarStatus('pending');
        }
    });

    tablaCalificaciones.addEventListener('click', e => {
        const target = e.target;
        if (target.classList.contains('btn-add-col')) {
            const tipo = target.dataset.tipo;
            // Añade una nota vacía al primer estudiante para forzar una nueva columna
            if (estudiantesData.length > 0) {
                if (!estudiantesData[0].notas[tipo]) estudiantesData[0].notas[tipo] = [];
                estudiantesData[0].notas[tipo].push({ valor: '', descripcion: '' });
            }
            renderizarTabla();
            actualizarStatus('pending');
        }
        if (target.classList.contains('btn-remove-col')) {
            const tipo = target.dataset.tipo;
            // Elimina la última nota de todos los estudiantes para esa competencia
            estudiantesData.forEach(est => {
                if (est.notas[tipo]?.length > 0) {
                    est.notas[tipo].pop();
                }
            });
            // Limpia la descripción de la columna eliminada
            const lastIndex = Object.keys(descripcionesColumnas[tipo]).length - 1;
            if (lastIndex >= 0) {
                delete descripcionesColumnas[tipo][lastIndex];
            }
            renderizarTabla();
            actualizarStatus('pending');
        }
        if (target.classList.contains('th-nota')) {
            const th = target;
            const tipo = th.dataset.tipo;
            const colIndex = th.dataset.colIndex;
            const descActual = descripcionesColumnas[tipo][colIndex] || '';
            const nuevaDesc = prompt(`Descripción para la columna ${th.textContent.trim()}:`, descActual);
            if (nuevaDesc !== null) {
                descripcionesColumnas[tipo][colIndex] = nuevaDesc.trim();
                th.textContent = nuevaDesc.trim() || `N${parseInt(colIndex) + 1}`;
                actualizarStatus('pending');
            }
        }
    });
    
    guardarTodoBtn?.addEventListener('click', async function() {
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

        const payload = {
            asignacion_id: asignacionData.id,
            periodo_id: asignacionData.periodoId,
            estudiantes: []
        };

        tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(fila => {
            const estId = fila.dataset.estudianteId;
            const datosEst = { id: estId, notas: { ser: [], saber: [], hacer: [] }, inasistencias: fila.querySelector('.input-inasistencia').value };
            
            for (const tipo of ['ser', 'saber', 'hacer']) {
                fila.querySelectorAll(`.input-nota[data-tipo="${tipo}"]`).forEach((input, index) => {
                    const valor = input.value.replace(',', '.').trim();
                    if (valor) {
                        const descripcion = descripcionesColumnas[tipo][index] || `Nota ${index + 1}`;
                        datosEst.notas[tipo].push({ descripcion, valor });
                    }
                });
            }
            payload.estudiantes.push(datosEst);
        });

        try {
            const response = await fetch(asignacionData.guardarUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': asignacionData.csrfToken },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.message || 'Error del servidor');
            
            actualizarStatus('saved');
            alert('¡Guardado con éxito!');

        } catch (error) {
            console.error('Error al guardar:', error);
            alert('Error al guardar: ' + error.message);
            actualizarStatus('error');
        } finally {
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-save me-2"></i>Guardar Cambios';
        }
    });

    // --- INICIALIZACIÓN ---
    renderizarTabla();
    actualizarStatus('saved');
});
