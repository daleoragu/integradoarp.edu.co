/**
 * Script for handling the grade entry page with a spreadsheet style.
 * @version 8.0 - Added paste from Excel and indicator validation.
 */
document.addEventListener('DOMContentLoaded', function () {
    // --- DOM ELEMENTS AND INITIAL DATA ---
    const container = document.querySelector('.container-notas');
    if (!container) return;

    const tablaCalificaciones = document.getElementById('tabla-calificaciones');
    const guardarTodoBtn = document.getElementById('guardarTodoBtn');
    const statusIndicator = document.getElementById('status-indicator');
    const estudiantesDataEl = document.getElementById('estudiantes-data-json');
    const asignacionDetailsEl = document.getElementById('asignacion-details');
    const urlInasistenciasEl = document.getElementById('url-get-inasistencias');
    const mensajeIndicadoresEl = document.getElementById('mensaje-indicadores');

    if (!tablaCalificaciones || !estudiantesDataEl || !asignacionDetailsEl || !urlInasistenciasEl) {
        console.error("Faltan elementos HTML esenciales para la inicialización del script.");
        return;
    }

    const asignacionData = {
        id: container.dataset.asignacionId,
        periodoId: container.dataset.periodoId,
        csrfToken: container.dataset.csrfToken,
        guardarUrl: container.dataset.guardarUrl,
        inasistenciasUrl: urlInasistenciasEl.dataset.url,
        esPonderacionEquitativa: asignacionDetailsEl.dataset.usarPonderacionEquitativa === 'true',
        pSer: parseFloat(asignacionDetailsEl.dataset.pSer),
        pSaber: parseFloat(asignacionDetailsEl.dataset.pSaber),
        pHacer: parseFloat(asignacionDetailsEl.dataset.pHacer)
    };

    let estudiantesData = [];
    try {
        estudiantesData = JSON.parse(estudiantesDataEl.textContent.trim() || '[]');
    } catch (e) {
        console.error("Error parsing student JSON:", e);
        tablaCalificaciones.innerHTML = '<p class="text-danger">Error al cargar datos de estudiantes.</p>';
        return;
    }

    let hayCambiosSinGuardar = false;
    let descripcionesColumnas = { ser: {}, saber: {}, hacer: {} };

    // --- MEJORA 1: VALIDACIÓN DE INDICADORES (FRONTEND) ---
    function gestionarEstadoInputsPorIndicadores() {
        const hayIndicadores = tablaCalificaciones.dataset.hayIndicadores === 'true';
        if (hayIndicadores) {
            mensajeIndicadoresEl.style.display = 'none';
            return; // Si hay indicadores, no hacemos nada.
        }

        // Si no hay indicadores, bloqueamos todo.
        mensajeIndicadoresEl.innerHTML = `
            <div class="alert alert-warning" role="alert">
                <h4 class="alert-heading"><i class="fas fa-exclamation-triangle"></i> Atención</h4>
                <p>No se pueden ingresar calificaciones porque <strong>no ha definido ningún indicador de logro</strong> para esta asignación en este periodo.</p>
                <hr>
                <p class="mb-0">Por favor, agregue al menos un indicador en la sección de arriba para poder continuar.</p>
            </div>
        `;
        mensajeIndicadoresEl.style.display = 'block';

        // Deshabilitamos los botones de añadir/quitar columnas y el de guardar.
        container.querySelectorAll('.btn-add-col, .btn-remove-col').forEach(btn => btn.disabled = true);
        if (guardarTodoBtn) guardarTodoBtn.disabled = true;
        
        // La tabla se renderizará sin inputs habilitados.
    }

    // --- RENDERING AND UI FUNCTIONS ---
    function renderizarTabla() {
        const hayIndicadores = tablaCalificaciones.dataset.hayIndicadores === 'true';
        const maxNotas = { ser: 0, saber: 0, hacer: 0 };
        estudiantesData.forEach(est => {
            for (const tipo in maxNotas) {
                const notasCount = est.notas[tipo]?.length || 0;
                if (notasCount > maxNotas[tipo]) maxNotas[tipo] = notasCount;
                est.notas[tipo]?.forEach((nota, i) => {
                    if (nota.descripcion && !descripcionesColumnas[tipo][i]) {
                        descripcionesColumnas[tipo][i] = nota.descripcion;
                    }
                });
            }
        });

        for (const tipo in maxNotas) {
            if (maxNotas[tipo] === 0) maxNotas[tipo] = 1;
        }

        let headerHtml = `<thead class="table-light"><tr><th rowspan="2" class="text-center align-middle">#</th><th rowspan="2" class="align-middle">Estudiante</th>`;
        const porcentajes = { ser: asignacionData.pSer, saber: asignacionData.pSaber, hacer: asignacionData.pHacer };
        for (const tipo of ['ser', 'saber', 'hacer']) {
            const porcentajeStr = asignacionData.esPonderacionEquitativa ? '' : ` (${porcentajes[tipo]}%)`;
            headerHtml += `<th colspan="${maxNotas[tipo] + 1}" class="text-center comp-${tipo}">${tipo.toUpperCase()}${porcentajeStr} <button class="btn btn-outline-success btn-sm btn-add-col" data-tipo="${tipo}" title="Añadir columna de nota" ${!hayIndicadores ? 'disabled' : ''}>+</button><button class="btn btn-outline-danger btn-sm btn-remove-col" data-tipo="${tipo}" title="Quitar última columna" ${!hayIndicadores ? 'disabled' : ''}>-</button></th>`;
        }
        headerHtml += `<th rowspan="2" class="text-center align-middle">Definitiva</th><th rowspan="2" class="text-center align-middle">Inasistencias</th></tr><tr>`;

        for (const tipo of ['ser', 'saber', 'hacer']) {
            for (let i = 0; i < maxNotas[tipo]; i++) {
                const desc = descripcionesColumnas[tipo][i] || '';
                headerHtml += `<th class="text-center th-nota" data-tipo="${tipo}" data-col-index="${i}" title="Clic para describir esta columna">
                                 <span class="col-title">n${i + 1}</span>
                                 <span class="col-desc">${desc}</span>
                               </th>`;
            }
            headerHtml += `<th class="text-center align-middle prom-header">Prom.</th>`;
        }
        headerHtml += `</tr></thead>`;

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
                        // MEJORA: El input se deshabilita si no hay indicadores
                        bodyHtml += `<td><input type="text" class="form-control form-control-sm input-nota" data-tipo="${tipo}" value="${nota}" inputmode="decimal" ${!hayIndicadores ? 'disabled' : ''}></td>`;
                    }
                    bodyHtml += `<td class="text-center align-middle fw-bold prom-celda" data-tipo="${tipo}">0.0</td>`;
                }
                bodyHtml += `<td class="text-center align-middle fw-bolder def-celda">0.0</td>
                             <td class="align-middle">
                               <div class="input-group input-group-sm">
                                 <input type="number" class="form-control input-inasistencia" min="0" value="${estudiante.inasistencias || 0}" ${!hayIndicadores ? 'disabled' : ''}>
                                 <button class="btn btn-outline-secondary sync-inasistencias" type="button" title="Sincronizar faltas automáticas" ${!hayIndicadores ? 'disabled' : ''}>
                                   <i class="fas fa-sync-alt"></i>
                                 </button>
                               </div>
                             </td></tr>`;
            });
        }
        bodyHtml += `</tbody>`;
        tablaCalificaciones.innerHTML = headerHtml + bodyHtml;
        tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(actualizarTodosLosPromedios);
    }

    // --- CALCULATION FUNCTIONS (Sin cambios) ---
    function actualizarTodosLosPromedios(fila) { /* ... */ }
    function actualizarDefinitiva(fila) { /* ... */ }
    // (Se pegan las funciones originales aquí para brevedad)
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
            promCelda.textContent = count > 0 ? (suma / count).toFixed(1) : '0.0';
        });
        actualizarDefinitiva(fila);
    }
    function actualizarDefinitiva(fila) {
        const defCelda = fila.querySelector('.def-celda');
        let definitiva = 0;
        const porcentajes = { ser: asignacionData.pSer / 100, saber: asignacionData.pSaber / 100, hacer: asignacionData.pHacer / 100 };
        ['ser', 'saber', 'hacer'].forEach(tipo => {
            const prom = parseFloat(fila.querySelector(`.prom-celda[data-tipo="${tipo}"]`).textContent);
            if (!isNaN(prom)) definitiva += prom * porcentajes[tipo];
        });
        defCelda.textContent = definitiva.toFixed(1);
        defCelda.classList.remove('nota-roja', 'nota-amarilla', 'nota-verde', 'nota-azul');
        const notaFinal = parseFloat(defCelda.textContent);
        if (notaFinal < 3.0) defCelda.classList.add('nota-roja');
        else if (notaFinal < 4.0) defCelda.classList.add('nota-amarilla');
        else if (notaFinal < 4.6) defCelda.classList.add('nota-verde');
        else defCelda.classList.add('nota-azul');
    }
    function actualizarStatus(estado) {
        if (!statusIndicator) return;
        statusIndicator.className = 'status-indicator';
        const periodoCerrado = document.querySelector('.card-footer .text-warning');
        switch (estado) {
            case 'pending':
                statusIndicator.classList.add('status-pending');
                statusIndicator.title = 'Cambios sin guardar';
                hayCambiosSinGuardar = true;
                if (guardarTodoBtn && !periodoCerrado && tablaCalificaciones.dataset.hayIndicadores === 'true') guardarTodoBtn.disabled = false;
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

    // --- EVENT HANDLERS ---
    tablaCalificaciones.addEventListener('input', e => { /* ... sin cambios ... */ });
    tablaCalificaciones.addEventListener('click', async (e) => { /* ... sin cambios ... */ });
    guardarTodoBtn?.addEventListener('click', async function() { /* ... sin cambios ... */ });
    // (Se pegan los manejadores originales para brevedad)
    tablaCalificaciones.addEventListener('input', e => {
        if (e.target.classList.contains('input-nota')) {
            actualizarTodosLosPromedios(e.target.closest('tr'));
        }
        if (e.target.classList.contains('input-nota') || e.target.classList.contains('input-inasistencia')) {
            actualizarStatus('pending');
        }
    });
    tablaCalificaciones.addEventListener('click', async (e) => {
        const target = e.target;
        const btnAdd = target.closest('.btn-add-col');
        const btnRemove = target.closest('.btn-remove-col');
        const thNota = target.closest('.th-nota');
        const btnSync = target.closest('.sync-inasistencias');

        if (btnAdd) {
            const tipo = btnAdd.dataset.tipo;
            if (estudiantesData.length > 0) {
                estudiantesData.forEach(est => {
                    if (!est.notas[tipo]) est.notas[tipo] = [];
                    est.notas[tipo].push({ valor: '', descripcion: '' });
                });
            }
            renderizarTabla();
            actualizarStatus('pending');
        }
        if (btnRemove) {
            const tipo = btnRemove.dataset.tipo;
            estudiantesData.forEach(est => {
                if (est.notas[tipo]?.length > 0) est.notas[tipo].pop();
            });
            const lastIndex = Object.keys(descripcionesColumnas[tipo]).length - 1;
            if (lastIndex >= 0) delete descripcionesColumnas[tipo][lastIndex];
            renderizarTabla();
            actualizarStatus('pending');
        }
        if (thNota) {
            const tipo = thNota.dataset.tipo;
            const colIndex = thNota.dataset.colIndex;
            const descSpan = thNota.querySelector('.col-desc');
            const descActual = descripcionesColumnas[tipo][colIndex] || '';
            const nuevaDesc = prompt(`Descripción para la columna ${thNota.querySelector('.col-title').textContent}:`, descActual);
            if (nuevaDesc !== null) {
                descripcionesColumnas[tipo][colIndex] = nuevaDesc.trim();
                descSpan.textContent = nuevaDesc.trim();
                actualizarStatus('pending');
            }
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
                const data = await response.json();
                if (data.status === 'success') {
                    inputInasistencia.value = data.inasistencias_auto;
                    actualizarStatus('pending');
                } else { throw new Error(data.message); }
            } catch (error) {
                alert('Error al sincronizar inasistencias: ' + error.message);
            } finally {
                btnSync.disabled = false;
                btnSync.querySelector('i').classList.remove('fa-spin');
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

    // --- MEJORA 2: FUNCIONALIDAD DE PEGAR DESDE EXCEL ---
    tablaCalificaciones.addEventListener('paste', (e) => {
        // Solo actuar si el pegado ocurre en un input de nota
        if (!e.target.classList.contains('input-nota')) return;

        e.preventDefault(); // Detener el comportamiento de pegado por defecto

        const pastedData = (e.clipboardData || window.clipboardData).getData('text');
        const rows = pastedData.split(/\r\n|\n|\r/); // Dividir por saltos de línea
        
        const startInput = e.target;
        const startCell = startInput.parentElement; // El <td>
        const startRow = startCell.parentElement; // El <tr>
        const allRows = Array.from(tablaCalificaciones.querySelectorAll('tbody tr'));
        const startRowIndex = allRows.indexOf(startRow);
        
        const allCellsInRow = Array.from(startRow.children);
        const startCellIndex = allCellsInRow.indexOf(startCell);

        rows.forEach((rowData, rowIndex) => {
            const currentRowIndex = startRowIndex + rowIndex;
            if (currentRowIndex >= allRows.length) return; // No pegar más allá de las filas de la tabla

            const currentRow = allRows[currentRowIndex];
            const cellsData = rowData.split('\t'); // Dividir por tabulaciones (formato Excel)

            cellsData.forEach((cellData, colIndex) => {
                const currentCellIndex = startCellIndex + colIndex;
                if (currentCellIndex >= currentRow.children.length) return; // No pegar más allá de las columnas

                const targetCell = currentRow.children[currentCellIndex];
                const targetInput = targetCell.querySelector('.input-nota');

                if (targetInput) {
                    targetInput.value = cellData.trim().replace(',', '.');
                }
            });
        });

        // Actualizar todos los promedios y definitivas de las filas afectadas
        for (let i = 0; i < rows.length; i++) {
            const affectedRowIndex = startRowIndex + i;
            if (affectedRowIndex < allRows.length) {
                actualizarTodosLosPromedios(allRows[affectedRowIndex]);
            }
        }
        
        actualizarStatus('pending'); // Marcar que hay cambios sin guardar
    });


    // --- INITIALIZATION ---
    renderizarTabla();
    gestionarEstadoInputsPorIndicadores(); // Llamar a la nueva función de validación
    actualizarStatus('saved');
});
