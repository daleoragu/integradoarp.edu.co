document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container-notas');
    if (!container) return;

    const csrfToken = container.dataset.csrfToken;
    const asignacionId = container.dataset.asignacionId;
    const materiaId = container.dataset.materiaId;
    const periodoId = container.dataset.periodoId;
    const guardarUrl = container.dataset.guardarUrl;

    const tablaBody = document.getElementById('tabla-notas-body');
    if (!tablaBody) return;

    const guardarBtn = document.getElementById('guardar-todo-btn');
    const statusMsg = document.getElementById('guardar-status');

    tablaBody.querySelectorAll('tr').forEach(fila => {
        const inputs = fila.querySelectorAll('.nota-input');
        if (inputs.length === 3) {
            inputs[0].dataset.tipo = 'ser';
            inputs[1].dataset.tipo = 'saber';
            inputs[2].dataset.tipo = 'hacer';
        }
    });

    function calcularPromedio(fila) {
        // Al leer los valores, siempre se reemplaza la coma por el punto para poder calcular.
        const serValue = fila.querySelector('.nota-input[data-tipo="ser"]').value.replace(',', '.');
        const saberValue = fila.querySelector('.nota-input[data-tipo="saber"]').value.replace(',', '.');
        const hacerValue = fila.querySelector('.nota-input[data-tipo="hacer"]').value.replace(',', '.');
        
        const ser = parseFloat(serValue);
        const saber = parseFloat(saberValue);
        const hacer = parseFloat(hacerValue);

        const celdaPromedio = fila.querySelector('.promedio-cell');

        if (!isNaN(ser) && !isNaN(saber) && !isNaN(hacer)) {
            const promedio = (ser + saber + hacer) / 3;
            // CORREGIDO: Se muestra el promedio con coma para consistencia visual.
            celdaPromedio.textContent = promedio.toFixed(1).replace('.', ',');
        } else {
            celdaPromedio.textContent = '';
        }
    }
    
    function validarAlSalir(e) {
        const input = e.target;
        if (!input.classList.contains('nota-input')) return;

        if (input.value.trim() === '') {
            const fila = input.closest('tr');
            if(fila) calcularPromedio(fila);
            return;
        }

        let valor = input.value.replace(',', '.');
        let valorNumerico = parseFloat(valor);

        if (isNaN(valorNumerico)) {
            input.value = '';
        } else {
            if (valorNumerico > 5.0) valorNumerico = 5.0;
            if (valorNumerico < 1.0) valorNumerico = 1.0;
            
            // CORREGIDO: Se formatea el número a un solo decimal y se muestra con coma.
            input.value = valorNumerico.toFixed(1).replace('.', ',');
        }
        
        const fila = input.closest('tr');
        if (fila) {
            calcularPromedio(fila);
        }
    }

    tablaBody.addEventListener('input', function(e) {
        if (e.target.classList.contains('nota-input') || e.target.classList.contains('input-inasistencia')) {
            guardarBtn.disabled = false;
        }
    });

    tablaBody.addEventListener('blur', validarAlSalir, true);
    
    tablaBody.addEventListener('click', function(e) {
        const syncButton = e.target.closest('.sync-inasistencias');
        if (syncButton) {
            const inputInasistencia = syncButton.previousElementSibling;
            if (inputInasistencia) {
                inputInasistencia.value = ''; 
                inputInasistencia.dispatchEvent(new Event('input', { 'bubbles': true }));
                statusMsg.textContent = 'Actualizando...';
                statusMsg.className = 'text-primary';
                statusMsg.style.opacity = '1';
                guardarBtn.click();
            }
        }
    });

    guardarBtn.addEventListener('click', async function() {
        const estudiantesData = [];
        tablaBody.querySelectorAll('tr').forEach(fila => {
            // Se reemplaza la coma por el punto antes de enviar al backend.
            estudiantesData.push({
                estudiante_id: fila.querySelector('.nota-input').dataset.estudianteId,
                nota_ser: fila.querySelector('[data-tipo="ser"]').value.replace(',', '.'),
                nota_saber: fila.querySelector('[data-tipo="saber"]').value.replace(',', '.'),
                nota_hacer: fila.querySelector('[data-tipo="hacer"]').value.replace(',', '.'),
                inasistencias: fila.querySelector('.input-inasistencia').value,
            });
        });

        const payload = { 
            asignacion_id: asignacionId, materia_id: materiaId, 
            periodo_id: periodoId, estudiantes: estudiantesData 
        };

        statusMsg.textContent = 'Guardando...';
        statusMsg.className = 'text-primary';
        statusMsg.style.opacity = '1';
        this.disabled = true;

        try {
            const response = await fetch(guardarUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (result.status === 'success') {
                statusMsg.textContent = '¡Guardado con éxito!';
                statusMsg.className = 'text-success';
                setTimeout(() => window.location.reload(), 1200);
            } else if (result.status === 'success_with_errors') {
                let errorHtml = `<p class="mb-1"><strong>${result.message}</strong></p><ul class="mb-0 ps-4" style="font-size: 0.9em;">`;
                result.errors.forEach(err => { errorHtml += `<li>${err}</li>`; });
                errorHtml += '</ul>';
                statusMsg.innerHTML = errorHtml;
                statusMsg.className = 'alert alert-warning p-2';
                this.disabled = false;
            } else {
                statusMsg.textContent = `Error: ${result.message}`;
                statusMsg.className = 'alert alert-danger p-2';
                this.disabled = false;
            }
        } catch (error) {
            console.error('Error en la solicitud fetch:', error);
            statusMsg.textContent = 'Error de red. Verifique su conexión.';
            statusMsg.className = 'alert alert-danger p-2';
            this.disabled = false;
        } finally {
            statusMsg.style.opacity = '1';
        }
    });

    tablaBody.addEventListener('paste', function(e) {
        e.preventDefault();
        let pasteData = (e.clipboardData || window.clipboardData).getData('text');
        if (!pasteData) return;
        // Al pegar, no se cambia coma por punto, ya que la validación 'blur' lo hará.
        const rows = pasteData.split(/\r\n|\n|\r/);
        const activeElement = document.activeElement;
        if (activeElement.tagName !== 'INPUT' || (!activeElement.classList.contains('nota-input') && !activeElement.classList.contains('input-inasistencia'))) return;
        
        let startCell = activeElement.parentElement;
        let startRow = startCell.parentElement;
        let startCellIndex = Array.from(startRow.children).indexOf(startCell);
        let startRowIndex = Array.from(tablaBody.children).indexOf(startRow);
        
        rows.forEach((rowText, rowIndex) => {
            const cells = rowText.split('\t');
            const targetRow = tablaBody.children[startRowIndex + rowIndex];
            if (!targetRow) return;
            cells.forEach((cellText, cellIndex) => {
                const targetCell = targetRow.children[startCellIndex + cellIndex];
                if (!targetCell) return;
                const input = targetCell.querySelector('.nota-input, .input-inasistencia');
                if (input && !input.disabled) {
                    input.value = cellText.trim();
                    input.dispatchEvent(new Event('blur', { 'bubbles': true, cancelable: true }));
                    input.dispatchEvent(new Event('input', { 'bubbles': true, cancelable: true }));
                }
            });
        });
    });
    
    tablaBody.querySelectorAll('tr').forEach(calcularPromedio);
});
