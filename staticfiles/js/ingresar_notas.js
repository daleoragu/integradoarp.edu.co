/**
 * Script for handling the grade entry page with a spreadsheet style.
 * @version 10.0 - Corrected button enable/disable logic based on indicators.
 */
document.addEventListener('DOMContentLoaded', function () {
    // --- DOM ELEMENTS AND INITIAL DATA ---
    const container = document.querySelector('.container-notas');
    if (!container) return;

    const tablaCalificaciones = document.getElementById('tabla-calificaciones');
    const guardarTodoBtn = document.getElementById('guardarTodoBtn');
    const statusIndicator = document.getElementById('status-indicator');
    const estudiantesDataEl = document.getElementById('estudiantes-data-json');
    const mensajeIndicadoresEl = document.getElementById('mensaje-indicadores');
    
    const pSerInput = document.getElementById('p-ser');
    const pSaberInput = document.getElementById('p-saber');
    const pHacerInput = document.getElementById('p-hacer');

    if (!tablaCalificaciones || !estudiantesDataEl || !mensajeIndicadoresEl) {
        console.error("Faltan elementos HTML esenciales para la inicialización del script.");
        return;
    }

    const asignacionData = {
        id: container.dataset.asignacionId,
        periodoId: container.dataset.periodoId,
        csrfToken: container.dataset.csrfToken,
        guardarUrl: container.dataset.guardarUrl,
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

    // --- ============================================= ---
    // --- FUNCIÓN CORREGIDA PARA HABILITAR/DESHABILITAR ---
    // --- ============================================= ---
    function gestionarEstadoInputsPorIndicadores() {
        const hayIndicadores = tablaCalificaciones.dataset.hayIndicadores === 'true';
        
        if (hayIndicadores) {
            // Si hay indicadores, nos aseguramos de que todo esté habilitado.
            mensajeIndicadoresEl.style.display = 'none';
            container.querySelectorAll('.btn-add-col, .btn-remove-col').forEach(btn => btn.disabled = false);
            // El botón de guardar se gestionará por separado (si hay cambios o no).
        } else {
            // Si NO hay indicadores, mostramos el mensaje y deshabilitamos todo.
            mensajeIndicadoresEl.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <h4 class="alert-heading"><i class="fas fa-exclamation-triangle"></i> Atención</h4>
                    <p>No se pueden ingresar calificaciones porque <strong>no ha definido ningún indicador de logro</strong> para esta asignación en este periodo.</p>
                </div>
            `;
            mensajeIndicadoresEl.style.display = 'block';
            container.querySelectorAll('.btn-add-col, .btn-remove-col').forEach(btn => btn.disabled = true);
            if (guardarTodoBtn) guardarTodoBtn.disabled = true;
        }
    }

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
        for (const tipo of ['ser', 'saber', 'hacer']) {
            headerHtml += `<th colspan="${maxNotas[tipo] + 1}" class="text-center comp-${tipo}">${tipo.toUpperCase()} <button class="btn btn-outline-success btn-sm btn-add-col" data-tipo="${tipo}" title="Añadir columna de nota" ${!hayIndicadores ? 'disabled' : ''}>+</button><button class="btn btn-outline-danger btn-sm btn-remove-col" data-tipo="${tipo}" title="Quitar última columna" ${!hayIndicadores ? 'disabled' : ''}>-</button></th>`;
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
        
        const porcentajes = {
            ser: (parseFloat(pSerInput.value) || 0) / 100,
            saber: (parseFloat(pSaberInput.value) || 0) / 100,
            hacer: (parseFloat(pHacerInput.value) || 0) / 100,
        };

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
                if (guardarTodoBtn && !periodoCerrado && tablaCalificaciones.dataset.hayIndicadores === 'true') {
                    const suma = (parseInt(pSerInput.value, 10) || 0) + (parseInt(pSaberInput.value, 10) || 0) + (parseInt(pHacerInput.value, 10) || 0);
                    guardarTodoBtn.disabled = (suma !== 100);
                }
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
    tablaCalificaciones.addEventListener('input', e => {
        if (e.target.classList.contains('input-nota') || e.target.classList.contains('input-inasistencia')) {
            if (e.target.classList.contains('input-nota')) {
                actualizarTodosLosPromedios(e.target.closest('tr'));
            }
            actualizarStatus('pending');
        }
    });

    [pSerInput, pSaberInput, pHacerInput].forEach(input => {
        input?.addEventListener('input', () => {
            tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(fila => {
                actualizarDefinitiva(fila);
            });
            actualizarStatus('pending');
        });
    });

    tablaCalificaciones.addEventListener('click', e => {
        const btnAdd = e.target.closest('.btn-add-col');
        const btnRemove = e.target.closest('.btn-remove-col');
        const thNota = e.target.closest('.th-nota');

        if (btnAdd) {
            const tipo = btnAdd.dataset.tipo;
            if (estudiantesData.length > 0) {
                estudiantesData.forEach(est => {
                    if (!est.notas[tipo]) est.notas[tipo] = [];
                    est.notas[tipo].push({ valor: '', descripcion: '' });
                });
            }
            renderizarTabla();
            gestionarEstadoInputsPorIndicadores();
            actualizarStatus('pending');
        }
        if (btnRemove) {
            const tipo = btnRemove.dataset.tipo;
            estudiantesData.forEach(est => {
                if (est.notas[tipo]?.length > 1) est.notas[tipo].pop();
            });
            const lastIndex = Object.keys(descripcionesColumnas[tipo]).length - 1;
            if (lastIndex >= 0) delete descripcionesColumnas[tipo][lastIndex];
            renderizarTabla();
            gestionarEstadoInputsPorIndicadores();
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
    });

    guardarTodoBtn?.addEventListener('click', async function() {
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';
        
        const payload = {
            asignacion_id: asignacionData.id,
            periodo_id: asignacionData.periodoId,
            estudiantes: [],
            porcentajes: {
                ser: pSerInput.value,
                saber: pSaberInput.value,
                hacer: pHacerInput.value
            }
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

    // --- INITIALIZATION ---
    renderizarTabla();
    gestionarEstadoInputsPorIndicadores();
    actualizarStatus('saved');
});
