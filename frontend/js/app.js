document.addEventListener('DOMContentLoaded', () => {
    // ============================================
    // CONFIGURACIÓN Y ELEMENTOS DEL DOM
    // ============================================

    // URL del backend (configurable)
    const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://127.0.0.1:8000'
        : ''; // En producción usa la misma URL

    // Elementos del DOM
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    const selectButton = document.getElementById('selectButton');
    const convertButton = document.getElementById('convertButton');
    const widthSlider = document.getElementById('widthSlider');
    const widthValue = document.getElementById('widthValue');
    const profileInfo = document.getElementById('profileInfo');
    const imagePreview = document.getElementById('imagePreview');
    const resultSection = document.getElementById('resultSection');
    const asciiResult = document.getElementById('asciiResult');
    const copyButton = document.getElementById('copyButton');
    const downloadButton = document.getElementById('downloadButton');
    const metadataToggle = document.getElementById('metadataToggle');
    const metadataSection = document.getElementById('metadataSection');
    const metadataContent = document.getElementById('metadataContent');

    // Estado de la aplicación
    let selectedFile = null;
    let currentMetadata = null;

    // ============================================
    // EVENT LISTENERS
    // ============================================

    // Botón para seleccionar imagen
    selectButton.addEventListener('click', () => imageInput.click());

    // Cuando se selecciona una imagen
    imageInput.addEventListener('change', handleImageSelect);

    // Slider de ancho
    widthSlider.addEventListener('input', () => {
        const width = parseInt(widthSlider.value);
        widthValue.textContent = width;
        updateProfileInfo(width);
    });

    // Botones de acción
    convertButton.addEventListener('click', convertToAscii);
    copyButton.addEventListener('click', copyToClipboard);
    downloadButton.addEventListener('click', downloadAsText);

    // Toggle de metadata
    if (metadataToggle) {
        metadataToggle.addEventListener('change', (e) => {
            if (e.target.checked && currentMetadata) {
                displayMetadata(currentMetadata);
            } else if (metadataSection) {
                metadataSection.hidden = true;
            }
        });
    }

    // Drag and drop eventos
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {
            imageInput.files = e.dataTransfer.files;
            handleImageSelect();
        }
    });

    // Inicializar info del perfil al cargar
    updateProfileInfo(parseInt(widthSlider.value));

    // ============================================
    // FUNCIONES PRINCIPALES
    // ============================================

    /**
     * Actualiza la información del perfil según el ancho seleccionado
     * Muestra el modo (FORMA/HÍBRIDO/DETALLE) y descripción
     */
    function updateProfileInfo(width) {
        if (!profileInfo) return;

        let profile, description, color, mode;

        if (width < 40) {
            profile = "PEQUEÑO (FORMA)";
            description = "Sin dithering • Silueta clara • 5 niveles";
            color = "#e74c3c"; // Rojo
            mode = "FORMA";
        } else if (width < 90) {
            profile = "MEDIO (HÍBRIDO)";
            description = "Dithering 30% • Balance forma-detalle • 7 niveles";
            color = "#f39c12"; // Naranja
            mode = "HÍBRIDO";
        } else {
            profile = "GRANDE (DETALLE)";
            description = "Dithering 100% • Máximo detalle • 12 niveles";
            color = "#27ae60"; // Verde
            mode = "DETALLE";
        }

        profileInfo.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: ${color}; font-size: 1.1em;">▓ ${profile}</strong><br>
                    <span style="color: #fff; font-size: 0.9em; margin-top: 5px; display: inline-block;">
                        ${description}
                    </span>
                </div>
                <div style="text-align: right; color: ${color}; font-size: 2em; font-weight: bold; opacity: 0.3;">
                    ${mode === 'FORMA' ? '◢' : mode === 'HÍBRIDO' ? '◆' : '█'}
                </div>
            </div>
        `;
    }

    /**
     * Maneja la selección de imagen (por click o drag&drop)
     */
    function handleImageSelect() {
        if (imageInput.files.length > 0) {
            selectedFile = imageInput.files[0];

            // Validar tipo de archivo
            if (!selectedFile.type.startsWith('image/')) {
                showNotification('⚠️ Por favor selecciona un archivo de imagen válido', 'error');
                selectedFile = null;
                return;
            }

            // Validar tamaño (10MB máximo)
            if (selectedFile.size > 10 * 1024 * 1024) {
                showNotification('⚠️ La imagen es muy grande. Máximo 10MB', 'error');
                selectedFile = null;
                return;
            }

            // Mostrar vista previa
            const reader = new FileReader();
            reader.onload = (e) => {
                // Crear elemento img si no existe
                let img = document.querySelector('#imagePreview img');
                if (!img) {
                    img = document.createElement('img');
                    img.style.maxWidth = '100%';
                    img.style.maxHeight = '300px';
                    img.style.borderRadius = '4px';
                    imagePreview.appendChild(img);
                }
                img.src = e.target.result;
                imagePreview.style.display = 'block';
                convertButton.disabled = false;

                // Mostrar nombre del archivo
                const fileName = document.getElementById('fileName');
                if (fileName) {
                    fileName.textContent = `📁 ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(2)} KB)`;
                    fileName.style.display = 'block';
                }

                // Ocultar resultado anterior si existe
                if (resultSection) {
                    resultSection.hidden = true;
                }
                if (metadataSection) {
                    metadataSection.hidden = true;
                }
            };
            reader.readAsDataURL(selectedFile);
        }
    }

    /**
     * Convierte la imagen a ASCII usando la API
     */
    async function convertToAscii() {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append('image', selectedFile);
        formData.append('max_width', widthSlider.value);

        // Incluir metadata si el toggle está activado
        const includeMetadata = metadataToggle ? metadataToggle.checked : false;
        formData.append('include_metadata', includeMetadata);

        try {
            // Mostrar indicador de carga
            const originalText = convertButton.innerHTML;
            convertButton.innerHTML = '<span class="loading-spinner"></span> PROCESANDO...';
            convertButton.disabled = true;

            const startTime = performance.now();

            const response = await fetch(`${API_URL}/api/convert`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Error al procesar la imagen');
            }

            const data = await response.json();
            const endTime = performance.now();
            const processingTime = ((endTime - startTime) / 1000).toFixed(2);

            // Mostrar resultado ASCII
            asciiResult.textContent = data.ascii_art;
            resultSection.hidden = false;

            // Guardar metadata si está disponible
            if (data.metadata) {
                currentMetadata = data.metadata;
                currentMetadata.processing_time = processingTime;

                if (includeMetadata) {
                    displayMetadata(currentMetadata);
                }
            }

            // Scroll al resultado con delay para animación
            setTimeout(() => {
                resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);

            showNotification(`✅ ¡Conversión exitosa! (${processingTime}s)`, 'success');

        } catch (error) {
            console.error('Error:', error);
            showNotification(`❌ ${error.message}`, 'error');
        } finally {
            convertButton.innerHTML = '<span class="button-brackets">►</span> CONVERTIR A ASCII <span class="button-brackets">◄</span>';
            convertButton.disabled = false;
        }
    }

    /**
     * Muestra la metadata del proceso de conversión
     * VERSIÓN ACTUALIZADA con información del modo FORMA/DETALLE
     */
    function displayMetadata(metadata) {
        if (!metadataSection || !metadataContent) return;

        const {
            width,
            height,
            profile,
            mode,
            dithering_strength,
            ramp_info,
            parameters,
            original_size,
            processing_time
        } = metadata;

        // Determinar color según modo
        let modeColor = '#27ae60';
        let modeIcon = '█';
        if (mode === 'FORMA') {
            modeColor = '#e74c3c';
            modeIcon = '◢';
        } else if (mode === 'HIBRIDO') {
            modeColor = '#f39c12';
            modeIcon = '◆';
        }

        // Descripción del modo
        let modeDescription = '';
        if (mode === 'FORMA') {
            modeDescription = 'Sin dithering, posterización activa. Prioriza silueta clara sobre gradientes.';
        } else if (mode === 'HIBRIDO') {
            modeDescription = 'Dithering reducido (30%). Balance entre forma y detalle.';
        } else {
            modeDescription = 'Dithering completo. Máximo detalle y gradientes suaves.';
        }

        const html = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div>
                    <h4 style="margin: 0 0 8px 0; color: #00ff00; font-size: 0.95em;">
                        ▓ DIMENSIONES
                    </h4>
                    <p style="margin: 0; font-size: 0.9em; color: #fff; line-height: 1.6;">
                        Original: <strong>${original_size[0]} × ${original_size[1]}px</strong><br>
                        ASCII: <strong>${width} × ${height} chars</strong>
                    </p>
                </div>
                
                <div>
                    <h4 style="margin: 0 0 8px 0; color: #00ff00; font-size: 0.95em;">
                        ▓ PERFIL Y MODO
                    </h4>
                    <p style="margin: 0; font-size: 0.9em; color: #fff; line-height: 1.6;">
                        Perfil: <strong>${profile}</strong><br>
                        Modo: <strong style="color: ${modeColor};">${modeIcon} ${mode}</strong><br>
                        Dithering: <strong>${(dithering_strength * 100).toFixed(0)}%</strong>
                    </p>
                </div>
                
                <div>
                    <h4 style="margin: 0 0 8px 0; color: #00ff00; font-size: 0.95em;">
                        ▓ PARÁMETROS
                    </h4>
                    <p style="margin: 0; font-size: 0.9em; color: #fff; line-height: 1.6;">
                        Gamma: <strong>${parameters.gamma}</strong><br>
                        Contraste: <strong>${(parameters.contrast_boost * 100).toFixed(0)}%</strong><br>
                        Edge Enhance: <strong>${parameters.edge_enhance ? '✓ Sí' : '✗ No'}</strong>
                    </p>
                </div>
                
                <div>
                    <h4 style="margin: 0 0 8px 0; color: #00ff00; font-size: 0.95em;">
                        ▓ PROCESAMIENTO
                    </h4>
                    <p style="margin: 0; font-size: 0.9em; color: #fff; line-height: 1.6;">
                        Niveles: <strong>${ramp_info.ramp_length} caracteres</strong><br>
                        Posterización: <strong>${parameters.posterize_levels} niveles</strong><br>
                        Tiempo: <strong>${processing_time || 'N/A'}s</strong>
                    </p>
                </div>
            </div>
            
            <!-- Rampa de caracteres -->
            <div style="margin-bottom: 15px; padding: 12px; background: rgba(0, 255, 0, 0.1); border-radius: 4px; border: 1px solid #00ff00;">
                <h4 style="margin: 0 0 8px 0; color: #00ff00; font-size: 0.95em;">
                    ▓ RAMPA DE CARACTERES (${ramp_info.profile})
                </h4>
                <pre style="margin: 0; font-size: 24px; letter-spacing: 6px; line-height: 1.5; color: #fff; text-align: center;">${ramp_info.characters.join(' ')}</pre>
                <p style="margin: 8px 0 0 0; font-size: 0.85em; color: #00ff00; text-align: center;">
                    ${ramp_info.description}
                </p>
            </div>

            <!-- Explicación del modo -->
            <div style="padding: 12px; background: rgba(255, 255, 0, 0.1); border-left: 3px solid #ffff00; border-radius: 0 4px 4px 0;">
                <h4 style="margin: 0 0 8px 0; color: #ffff00; font-size: 0.9em;">
                    💡 EXPLICACIÓN DEL MODO ${mode}:
                </h4>
                <p style="margin: 0; font-size: 0.85em; color: #fff; line-height: 1.5;">
                    ${modeDescription}
                </p>
            </div>

            <!-- Comparación de parámetros -->
            <div style="margin-top: 15px; padding: 12px; background: rgba(0, 0, 0, 0.3); border-radius: 4px; border: 1px solid #333;">
                <h4 style="margin: 0 0 10px 0; color: #00ff00; font-size: 0.9em;">
                    ▓ COMPARACIÓN DE MODOS:
                </h4>
                <table style="width: 100%; font-size: 0.8em; color: #fff; border-collapse: collapse;">
                    <thead>
                        <tr style="border-bottom: 1px solid #00ff00;">
                            <th style="text-align: left; padding: 5px; color: #00ff00;">Característica</th>
                            <th style="text-align: center; padding: 5px; color: #e74c3c;">FORMA</th>
                            <th style="text-align: center; padding: 5px; color: #f39c12;">HÍBRIDO</th>
                            <th style="text-align: center; padding: 5px; color: #27ae60;">DETALLE</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 5px; border-bottom: 1px solid #333;">Dithering</td>
                            <td style="text-align: center; padding: 5px; border-bottom: 1px solid #333; color: ${mode === 'FORMA' ? '#00ff00' : '#666'};">0%</td>
                            <td style="text-align: center; padding: 5px; border-bottom: 1px solid #333; color: ${mode === 'HIBRIDO' ? '#00ff00' : '#666'};">30%</td>
                            <td style="text-align: center; padding: 5px; border-bottom: 1px solid #333; color: ${mode === 'DETALLE' ? '#00ff00' : '#666'};">100%</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px; border-bottom: 1px solid #333;">Niveles</td>
                            <td style="text-align: center; padding: 5px; border-bottom: 1px solid #333; color: ${mode === 'FORMA' ? '#00ff00' : '#666'};">5</td>
                            <td style="text-align: center; padding: 5px; border-bottom: 1px solid #333; color: ${mode === 'HIBRIDO' ? '#00ff00' : '#666'};">7</td>
                            <td style="text-align: center; padding: 5px; border-bottom: 1px solid #333; color: ${mode === 'DETALLE' ? '#00ff00' : '#666'};">12</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px;">Posterización</td>
                            <td style="text-align: center; padding: 5px; color: ${mode === 'FORMA' ? '#00ff00' : '#666'};">5 niveles</td>
                            <td style="text-align: center; padding: 5px; color: ${mode === 'HIBRIDO' ? '#00ff00' : '#666'};">7 niveles</td>
                            <td style="text-align: center; padding: 5px; color: ${mode === 'DETALLE' ? '#00ff00' : '#666'};">12 niveles</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;

        metadataContent.innerHTML = html;
        metadataSection.hidden = false;

        // Scroll suave a la metadata
        setTimeout(() => {
            metadataSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }

    /**
     * Copia el resultado al portapapeles
     */
    function copyToClipboard() {
        const text = asciiResult.textContent;

        navigator.clipboard.writeText(text)
            .then(() => {
                showNotification('✅ Copiado al portapapeles', 'success');

                // Feedback visual en el botón
                const originalHTML = copyButton.innerHTML;
                copyButton.innerHTML = '<span class="button-icon">✓</span> COPIADO';
                copyButton.style.background = 'linear-gradient(145deg, #1e7e34, #28a745)';

                setTimeout(() => {
                    copyButton.innerHTML = originalHTML;
                    copyButton.style.background = '';
                }, 2000);
            })
            .catch((err) => {
                console.error('Error al copiar:', err);
                showNotification('❌ Error al copiar al portapapeles', 'error');
            });
    }

    /**
     * Descarga el resultado como archivo de texto
     */
    function downloadAsText() {
        const text = asciiResult.textContent;

        // Agregar header informativo al archivo
        const width = widthSlider.value;
        const timestamp = new Date().toLocaleString('es-ES');
        const header = `ASCII ART GENERATOR v2.0
════════════════════════════════════════
Generado: ${timestamp}
Ancho: ${width} caracteres
${currentMetadata ? `Modo: ${currentMetadata.mode}` : ''}
${currentMetadata ? `Perfil: ${currentMetadata.profile}` : ''}
════════════════════════════════════════

`;

        const fullText = header + text;
        const blob = new Blob([fullText], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const timestampFile = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const fileName = `ascii-art-${width}chars-${timestampFile}.txt`;

        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showNotification(`💾 Archivo descargado: ${fileName}`, 'success');
    }

    /**
     * Muestra una notificación temporal
     */
    function showNotification(message, type = 'success') {
        // Eliminar notificaciones anteriores
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notif => {
            if (notif.parentNode) {
                document.body.removeChild(notif);
            }
        });

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        // Estilos adicionales para mejor visualización
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '15px 25px';
        notification.style.borderRadius = '4px';
        notification.style.color = 'white';
        notification.style.fontWeight = 'bold';
        notification.style.zIndex = '10000';
        notification.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
        notification.style.border = '2px solid';
        notification.style.minWidth = '300px';
        notification.style.transition = 'all 0.3s ease';

        if (type === 'success') {
            notification.style.background = 'linear-gradient(145deg, #1e7e34, #28a745)';
            notification.style.borderColor = '#6c757d';
        } else {
            notification.style.background = 'linear-gradient(145deg, #c0392b, #e74c3c)';
            notification.style.borderColor = '#000000';
        }

        document.body.appendChild(notification);

        // Animación de entrada
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        });

        // Auto-ocultar después de 3 segundos
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            notification.style.opacity = '0';

            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Carga y muestra los perfiles disponibles (opcional)
     * Útil para debugging o información adicional
     */
    async function loadProfiles() {
        try {
            const response = await fetch(`${API_URL}/api/profiles`);
            if (response.ok) {
                const data = await response.json();
                console.log('📊 Perfiles disponibles:', data.profiles);
            }
        } catch (error) {
            console.warn('⚠️ No se pudieron cargar los perfiles:', error);
        }
    }

    // Cargar perfiles al inicio (opcional, solo para debug)
    // loadProfiles();

    // ============================================
    // LOG DE INICIALIZACIÓN
    // ============================================
    console.log('%c████ ASCII ART GENERATOR v2.0 ████', 'color: #00ff00; font-size: 16px; font-weight: bold;');
    console.log('%cModo adaptativo activado:', 'color: #00ff00; font-weight: bold;');
    console.log('  • FORMA (< 40 chars): Sin dithering, 5 niveles');
    console.log('  • HÍBRIDO (40-89 chars): Dithering 30%, 7 niveles');
    console.log('  • DETALLE (≥ 90 chars): Dithering 100%, 12 niveles');
    console.log('%c════════════════════════════════════', 'color: #00ff00;');
});