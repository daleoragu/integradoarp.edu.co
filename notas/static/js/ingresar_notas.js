/**
 * Script para manejar la página de ingreso de notas.
 * Gestiona la creación dinámica de campos de nota, cálculos en tiempo real,
 * el manejo de inasistencias y el envío de datos al servidor.
 */
document.addEventListener('DOMContentLoaded', function () {
    const container = document.querySelector('.container-notas');
    if (!container) return;

    const tablaCalificaciones = document.getElementById('tabla-calificaciones');
    const tbody = tablaCalificaciones?.querySelector('tbody');
    const guardarTodoBtn = document.getElementById('guardarTodoBtn');
    const statusIndicator = document.getElementById('status-indicator');
    
    const asignacionData = {
        id: container.dataset.asignacionId,
        materiaId: container.dataset.materiaId,
        periodoId: container.dataset.periodoId,
        csrfToken: container.dataset.csrfToken,
        guardarUrl: container.dataset.guardarUrl,
    };

    const estudiantesDataEl = document.getElementById('estudiantes-data-json');
    if (!estudiantesDataEl || !tbody) {
        console.error("Elementos clave de la tabla (tbody o JSON data) no encontrados.");
        return;
    }
    
    const estudiantesData = JSON.parse(estudiantesDataEl.textContent || '[]');
    let hayCambiosSinGuardar = false;

    function actualizarStatus(estado) {
        if (!statusIndicator) return;
        statusIndicator.className = 'status-indicator';
        switch (estado) {
            case 'pending':
                statusIndicator.classList.add('status-pending');
                statusIndicator.title = 'Cambios sin guardar';
                hayCambiosSinGuardar = true;
                if(guardarTodoBtn) guardarTodoBtn.disabled = false;
                break;
            case 'saved':
                statusIndicator.classList.add('status-saved');
                statusIndicator.title = 'Todos los cambios guardados';
                hayCambiosSinGuardar = false;
                if(guardarTodoBtn) guardarTodoBtn.disabled = true;
                break;
            case 'error':
                statusIndicator.classList.add('status-error');
                statusIndicator.title = 'Error al guardar';
                hayCambiosSinGuardar = true;
                if(guardarTodoBtn) guardarTodoBtn.disabled = false;
                break;
        }
    }

    function crearElementoNota(nota = { desc: '', valor: '' }) {
        const div = document.createElement('div');
        div.className = 'nota-detallada-item';
        div.innerHTML = `
            <input type="text" class="form-control form-control-sm input-desc" placeholder='Descripción' value="${nota.desc || ''}">
            <input type="text" class="form-control form-control-sm input-valor" inputmode="decimal" placeholder='Nota' value="${nota.valor || ''}">
            <button type="button" class="btn btn-danger btn-sm btn-remove-nota" title="Eliminar nota">&times;</button>
        `;
        return div;
    }

    function crearFilaEstudiante(estudiante, index) {
        const fila = document.createElement('tr');
        fila.dataset.estudianteId = estudiante.info.id;
        fila.innerHTML = `
            <td class="text-center">${index + 1}</td>
            <td><span class="nombre-estudiante">${estudiante.info.full_name}</span></td>
            <td class="notas-container" data-tipo="ser"><div class="promedio-display">Prom: <span>N/A</span></div></td>
            <td class="notas-container" data-tipo="saber"><div class="promedio-display">Prom: <span>N/A</span></div></td>
            <td class="notas-container" data-tipo="hacer"><div class="promedio-display">Prom: <span>N/A</span></div></td>
            <td class="text-center fw-bold celda-definitiva"><span>N/A</span></td>
            <!-- Celda de Inasistencias reintegrada -->
            <td class="celda-inasistencias">
                <input type="number" class="form-control form-control-sm input-inasistencia" min="0" value="${estudiante.inasistencias || ''}">
            </td>
        `;
        return fila;
    }

    function renderizarTablaCompleta() {
        tbody.innerHTML = '';
        if (estudiantesData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No hay estudiantes en este curso.</td></tr>';
            return;
        }

        estudiantesData.forEach((estudiante, index) => {
            const fila = crearFilaEstudiante(estudiante, index);
            tbody.appendChild(fila);

            ['SER', 'SABER', 'HACER'].forEach(tipo => {
                const contenedor = fila.querySelector(`.notas-container[data-tipo="${tipo.toLowerCase()}"]`);
                const notas = estudiante.calificaciones[tipo]?.detalladas || [];
                
                if (notas.length > 0) {
                    notas.forEach(nota => contenedor.prepend(crearElementoNota(nota)));
                } else {
                    contenedor.prepend(crearElementoNota());
                }
                actualizarPromedio(contenedor);
            });
            actualizarDefinitiva(fila);
        });
        actualizarStatus('saved');
    }

    function actualizarPromedio(contenedor) {
        const notasInputs = contenedor.querySelectorAll('.input-valor');
        const displaySpan = contenedor.querySelector('.promedio-display span');
        let suma = 0;
        let count = 0;

        notasInputs.forEach(input => {
            const valor = parseFloat(input.value.replace(',', '.'));
            if (!isNaN(valor) && valor >= 1.0 && valor <= 5.0) {
                suma += valor;
                count++;
            }
        });

        const promedio = count > 0 ? (suma / count).toFixed(2) : 'N/A';
        displaySpan.textContent = promedio;
        
        const fila = contenedor.closest('tr');
        if(fila) actualizarDefinitiva(fila);
    }

    function actualizarDefinitiva(fila) {
        const pSerText = document.querySelector('.comp-ser')?.textContent || '33.33';
        const pSaberText = document.querySelector('.comp-saber')?.textContent || '33.33';
        const pHacerText = document.querySelector('.comp-hacer')?.textContent || '33.34';

        const pSer = parseFloat(pSerText.match(/(\d+(\.\d+)?)/)?.[0] || 33.33) / 100;
        const pSaber = parseFloat(pSaberText.match(/(\d+(\.\d+)?)/)?.[0] || 33.33) / 100;
        const pHacer = parseFloat(pHacerText.match(/(\d+(\.\d+)?)/)?.[0] || 33.34) / 100;

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

    if (tablaCalificaciones) {
        tablaCalificaciones.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-remove-nota')) {
                const item = e.target.closest('.nota-detallada-item');
                const contenedor = item.parentElement;
                item.remove();
                actualizarPromedio(contenedor);
                actualizarStatus('pending');
            }
        });

        tablaCalificaciones.addEventListener('input', (e) => {
            if (e.target.classList.contains('input-valor') || e.target.classList.contains('input-desc')) {
                const contenedor = e.target.closest('.notas-container');
                if (contenedor) actualizarPromedio(contenedor);
                actualizarStatus('pending');
            }
            // Escuchar cambios en inasistencias
            if (e.target.classList.contains('input-inasistencia')) {
                actualizarStatus('pending');
            }
        });
    }

    document.querySelectorAll('.btn-add-all').forEach(btn => {
        btn.addEventListener('click', function() {
            const tipo = this.dataset.tipo;
            tablaCalificaciones.querySelectorAll(`.notas-container[data-tipo="${tipo}"]`).forEach(contenedor => {
                contenedor.prepend(crearElementoNota());
            });
            actualizarStatus('pending');
        });
    });

    guardarTodoBtn?.addEventListener('click', async function() {
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

        const payload = {
            periodo_id: asignacionData.periodoId,
            materia_id: asignacionData.materiaId,
            asignacion_id: asignacionData.id,
            estudiantes: []
        };

        tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(fila => {
            const estudianteId = fila.dataset.estudianteId;
            const datosEstudiante = {
                estudiante_id: estudianteId,
                ser: [], saber: [], hacer: [],
                // Se añade el campo de inasistencias al payload
                inasistencias: fila.querySelector('.input-inasistencia').value.trim()
            };

            ['ser', 'saber', 'hacer'].forEach(tipo => {
                fila.querySelectorAll(`.notas-container[data-tipo="${tipo}"] .nota-detallada-item`).forEach(item => {
                    const desc = item.querySelector('.input-desc').value.trim();
                    const valor = item.querySelector('.input-valor').value.trim();
                    if (valor) {
                        datosEstudiante[tipo].push({ desc, valor });
                    }
                });
            });
            payload.estudiantes.push(datosEstudiante);
        });

        try {
            const response = await fetch(asignacionData.guardarUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': asignacionData.csrfToken },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            
            if (response.ok && result.status === 'success') {
                alert('¡Éxito! ' + result.message);
                actualizarStatus('saved');
            } else {
                throw new Error(result.message || 'Error desconocido.');
            }
        } catch (error) {
            alert('Error: ' + error.message);
            actualizarStatus('error');
        } finally {
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-save me-2"></i>Guardar Todos los Cambios';
        }
    });
    
    window.addEventListener('beforeunload', (e) => {
        if (hayCambiosSinGuardar) {
            e.preventDefault();
            e.returnValue = 'Tienes cambios sin guardar. ¿Estás seguro de que quieres salir?';
        }
    });

    renderizarTablaCompleta();
});
