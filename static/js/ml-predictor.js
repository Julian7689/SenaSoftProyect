/**
 * MÓDULO DE PREDICCIÓN ML - ml-predictor.js
 * Funcionalidad para hacer predicciones con el modelo de Machine Learning
 * Integración con endpoint /api/predict del backend Flask
 */

(function() {
    'use strict';

    // ==================== CONSTANTES ====================
    const API_ENDPOINT = '/api/predict';
    const BATCH_ENDPOINT = '/api/predict-batch';

    // Features que el modelo espera (en el orden correcto)
    const MODEL_FEATURES = [
        'poblacion_total',
        'porcentaje_rural',
        'estrato_promedio',
        'tasa_pobreza',
        'num_instituciones',
        'computadores_por_estudiante',
        'salones_por_institucion',
        'docentes_por_institucion',
        'cobertura_electrica',
        'cobertura_4g',
        'dispositivos_promedio_hogar',
        'tasa_aprobacion',
        'tasa_desercion',
        'puntaje_pruebas'
    ];

    // Definición de campos y validación
    const FIELD_CONFIG = {
        poblacion_total: {
            label: 'Población Total',
            type: 'number',
            min: 0,
            placeholder: 'Ej: 16295',
            tooltip: 'Número total de habitantes'
        },
        porcentaje_rural: {
            label: 'Porcentaje Rural (%)',
            type: 'number',
            min: 0,
            max: 100,
            placeholder: 'Ej: 8.66',
            tooltip: 'Porcentaje de población rural (0-100)'
        },
        estrato_promedio: {
            label: 'Estrato Promedio',
            type: 'number',
            min: 1,
            max: 6,
            placeholder: 'Ej: 2.54',
            tooltip: 'Estrato socioeconómico (1-6)'
        },
        tasa_pobreza: {
            label: 'Tasa de Pobreza (%)',
            type: 'number',
            min: 0,
            max: 100,
            placeholder: 'Ej: 54.49',
            tooltip: 'Porcentaje de población en pobreza (0-100)'
        },
        num_instituciones: {
            label: 'Número de Instituciones',
            type: 'number',
            min: 0,
            placeholder: 'Ej: 59',
            tooltip: 'Cantidad de instituciones educativas'
        },
        computadores_por_estudiante: {
            label: 'Computadores por Estudiante',
            type: 'number',
            min: 0,
            placeholder: 'Ej: 1.34',
            tooltip: 'Ratio de computadores disponibles'
        },
        salones_por_institucion: {
            label: 'Salones por Institución',
            type: 'number',
            min: 0,
            placeholder: 'Ej: 24',
            tooltip: 'Promedio de salones por institución'
        },
        docentes_por_institucion: {
            label: 'Docentes por Institución',
            type: 'number',
            min: 0,
            placeholder: 'Ej: 78',
            tooltip: 'Promedio de docentes por institución'
        },
        cobertura_electrica: {
            label: 'Cobertura Eléctrica (%)',
            type: 'number',
            min: 0,
            max: 100,
            placeholder: 'Ej: 89.94',
            tooltip: 'Porcentaje de cobertura eléctrica (0-100)'
        },
        cobertura_4g: {
            label: 'Cobertura 4G (%)',
            type: 'number',
            min: 0,
            max: 100,
            placeholder: 'Ej: 42.64',
            tooltip: 'Porcentaje de cobertura 4G (0-100)'
        },
        dispositivos_promedio_hogar: {
            label: 'Dispositivos por Hogar (Promedio)',
            type: 'number',
            min: 0,
            placeholder: 'Ej: 1.96',
            tooltip: 'Promedio de dispositivos electrónicos por hogar'
        },
        tasa_aprobacion: {
            label: 'Tasa de Aprobación (%)',
            type: 'number',
            min: 0,
            max: 100,
            placeholder: 'Ej: 62.50',
            tooltip: 'Porcentaje de estudiantes que aprueban (0-100)'
        },
        tasa_desercion: {
            label: 'Tasa de Deserción (%)',
            type: 'number',
            min: 0,
            max: 100,
            placeholder: 'Ej: 36.06',
            tooltip: 'Porcentaje de estudiantes que desertan (0-100)'
        },
        puntaje_pruebas: {
            label: 'Puntaje de Pruebas',
            type: 'number',
            min: 0,
            max: 500,
            placeholder: 'Ej: 354.19',
            tooltip: 'Puntaje promedio en pruebas estandarizadas (0-500)'
        }
    };

    // ==================== FUNCIONES PRINCIPALES ====================

    /**
     * Obtener valores del formulario de predicción
     */
    function getFormValues() {
        const values = {};
        let isValid = true;

        for (const feature of MODEL_FEATURES) {
            const inputElement = document.getElementById(`input-${feature}`);
            
            if (!inputElement) {
                console.warn(`⚠ Campo no encontrado: input-${feature}`);
                continue;
            }

            const value = inputElement.value.trim();

            if (!value) {
                showFieldError(inputElement, `${FIELD_CONFIG[feature].label} es requerido`);
                isValid = false;
                continue;
            }

            const numValue = parseFloat(value);

            if (isNaN(numValue)) {
                showFieldError(inputElement, `Debe ser un número válido`);
                isValid = false;
                continue;
            }

            const config = FIELD_CONFIG[feature];
            if (config.min !== undefined && numValue < config.min) {
                showFieldError(inputElement, `Mínimo: ${config.min}`);
                isValid = false;
                continue;
            }

            if (config.max !== undefined && numValue > config.max) {
                showFieldError(inputElement, `Máximo: ${config.max}`);
                isValid = false;
                continue;
            }

            clearFieldError(inputElement);
            values[feature] = numValue;
        }

        return { values, isValid };
    }

    /**
     * Mostrar error en un campo
     */
    function showFieldError(element, message) {
        element.classList.add('input-error');
        
        let errorElement = element.parentElement.querySelector('.field-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error';
            element.parentElement.appendChild(errorElement);
        }
        errorElement.textContent = message;
    }

    /**
     * Limpiar error de un campo
     */
    function clearFieldError(element) {
        element.classList.remove('input-error');
        const errorElement = element.parentElement.querySelector('.field-error');
        if (errorElement) {
            errorElement.textContent = '';
        }
    }

    /**
     * Función principal: Hacer predicción
     */
    async function makePrediction() {
        const { values, isValid } = getFormValues();

        if (!isValid) {
            showAlert('⚠ Por favor completa todos los campos correctamente', 'warning');
            return;
        }

        // Mostrar loading
        const predictBtn = document.getElementById('predict-btn');
        const originalText = predictBtn.innerHTML;
        predictBtn.disabled = true;
        predictBtn.innerHTML = '<span class="spinner"></span> Procesando...';

        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(values)
            });

            const result = await response.json();

            if (result.success) {
                displayPredictionResult(result);
                logPrediction(values, result);
            } else {
                showAlert(`❌ Error: ${result.error}`, 'error');
                console.error('Predicción fallida:', result);
            }
        } catch (error) {
            console.error('Error conectando con servidor:', error);
            showAlert('❌ Error al conectar con el servidor', 'error');
        } finally {
            predictBtn.disabled = false;
            predictBtn.innerHTML = originalText;
        }
    }

    /**
     * Mostrar resultado de la predicción
     */
    function displayPredictionResult(result) {
        const resultDiv = document.getElementById('prediction-result');
        
        if (!resultDiv) {
            console.error('Elemento resultado no encontrado');
            return;
        }

        // Estilos según predicción
        const predictionClass = result.prediction === 0 ? 'prediction-no-access' : 'prediction-access';
        const predictionValue = result.prediction === 0 ? 'SIN ACCESO' : 'CON ACCESO';

        let probabilityHTML = '';
        if (result.prediction_proba && result.prediction_proba[0] !== null) {
            const prob0 = (result.prediction_proba[0] * 100).toFixed(2);
            const prob1 = (result.prediction_proba[1] * 100).toFixed(2);
            probabilityHTML = `
                <div class="probability-bars">
                    <div class="prob-bar">
                        <span>Sin acceso: ${prob0}%</span>
                        <div class="bar">
                            <div class="fill" style="width: ${prob0}%"></div>
                        </div>
                    </div>
                    <div class="prob-bar">
                        <span>Con acceso: ${prob1}%</span>
                        <div class="bar">
                            <div class="fill" style="width: ${prob1}%"></div>
                        </div>
                    </div>
                </div>
            `;
        }

        resultDiv.innerHTML = `
            <div class="result-container ${predictionClass}">
                <div class="result-header">
                    <h3>📊 Resultado de la Predicción</h3>
                    <span class="result-time">${new Date().toLocaleTimeString('es-CO')}</span>
                </div>
                
                <div class="result-main">
                    <div class="prediction-value">
                        <span class="label">Predicción:</span>
                        <span class="value">${predictionValue}</span>
                    </div>
                    <div class="result-interpretation">
                        <p>${result.interpretation}</p>
                    </div>
                </div>

                ${probabilityHTML}

                <div class="result-actions">
                    <button type="button" onclick="window.mlPredictor.clearForm()" class="btn-secondary">
                        🔄 Limpiar Formulario
                    </button>
                    <button type="button" onclick="window.mlPredictor.exportResult()" class="btn-secondary">
                        📥 Descargar Resultado
                    </button>
                </div>
            </div>
        `;

        // Scroll al resultado
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Limpiar el formulario
     */
    function clearForm() {
        for (const feature of MODEL_FEATURES) {
            const input = document.getElementById(`input-${feature}`);
            if (input) {
                input.value = '';
                clearFieldError(input);
            }
        }
        
        const resultDiv = document.getElementById('prediction-result');
        if (resultDiv) {
            resultDiv.innerHTML = '';
        }

        // Focus en el primer campo
        const firstInput = document.getElementById(`input-${MODEL_FEATURES[0]}`);
        if (firstInput) {
            firstInput.focus();
        }
    }

    /**
     * Exportar resultado como JSON
     */
    function exportResult() {
        const resultDiv = document.getElementById('prediction-result');
        if (!resultDiv || !resultDiv.innerHTML) {
            showAlert('No hay resultado para exportar', 'warning');
            return;
        }

        // Obtener datos
        const { values } = getFormValues();
        const exportData = {
            timestamp: new Date().toISOString(),
            input_data: values,
            result: resultDiv.innerHTML
        };

        // Crear JSON y descargarlo
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `prediccion_${new Date().getTime()}.json`;
        link.click();
        URL.revokeObjectURL(url);

        showAlert('✓ Resultado descargado correctamente', 'success');
    }

    /**
     * Registrar predicción en log (enviar al servidor)
     */
    async function logPrediction(inputs, result) {
        try {
            await fetch('/api/log-prediction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    inputs,
                    prediction: result.prediction,
                    timestamp: new Date().toISOString()
                })
            }).catch(() => {
                // El endpoint puede no existir aún, no es crítico
            });
        } catch (e) {
            console.warn('No se pudo registrar la predicción');
        }
    }

    /**
     * Mostrar alerta al usuario
     */
    function showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.innerHTML = `
            <div class="alert-content">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="btn-close">✕</button>
            </div>
        `;

        const container = document.getElementById('alerts-container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    /**
     * Cargar valores de ejemplo
     */
    function loadExampleData() {
        const exampleData = {
            poblacion_total: 16295,
            porcentaje_rural: 8.66,
            estrato_promedio: 2.54,
            tasa_pobreza: 54.49,
            num_instituciones: 59,
            computadores_por_estudiante: 1.34,
            salones_por_institucion: 24,
            docentes_por_institucion: 78,
            cobertura_electrica: 89.94,
            cobertura_4g: 42.64,
            dispositivos_promedio_hogar: 1.96,
            tasa_aprobacion: 62.50,
            tasa_desercion: 36.06,
            puntaje_pruebas: 354.19
        };

        for (const [feature, value] of Object.entries(exampleData)) {
            const input = document.getElementById(`input-${feature}`);
            if (input) {
                input.value = value;
                clearFieldError(input);
            }
        }

        showAlert('✓ Datos de ejemplo cargados', 'success');
    }

    // ==================== INICIALIZACIÓN ====================

    function initialize() {
        console.log('🚀 Inicializando módulo ML Predictor');

        // Vincular botón de predicción
        const predictBtn = document.getElementById('predict-btn');
        if (predictBtn) {
            predictBtn.addEventListener('click', makePrediction);
        } else {
            console.warn('⚠ Botón de predicción no encontrado');
        }

        // Vincular botón de ejemplo
        const exampleBtn = document.getElementById('example-btn');
        if (exampleBtn) {
            exampleBtn.addEventListener('click', loadExampleData);
        }

        // Permitir Enter para enviar
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && document.activeElement.classList.contains('ml-input')) {
                makePrediction();
            }
        });

        console.log('✓ Módulo ML Predictor listo');
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

    // ==================== EXPORTAR API PÚBLICA ====================
    
    // Exponer funciones globales para uso desde HTML
    window.mlPredictor = {
        makePrediction,
        clearForm,
        exportResult,
        loadExampleData,
        getFormValues,
        showAlert,
        MODEL_FEATURES,
        FIELD_CONFIG
    };

})();
