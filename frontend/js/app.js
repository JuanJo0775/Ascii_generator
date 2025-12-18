document.addEventListener('DOMContentLoaded', () => {
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

    let selectedFile = null;
    let currentMetadata = null;

    // Event listeners
    selectButton.addEventListener('click', () => imageInput.click());
    imageInput.addEventListener('change', handleImageSelect);

    widthSlider.addEventListener('input', () => {
        const width = parseInt(widthSlider.value);
        widthValue.textContent = width;
        updateProfileInfo(width);
    });

    convertButton.addEventListener('click', convertToAscii);
    copyButton.addEventListener('click', copyToClipboard);
    downloadButton.addEventListener('click', downloadAsText);

    if (metadataToggle) {
        metadataToggle.addEventListener('change', (e) => {
            if (e.target.checked && currentMetadata) {
                displayMetadata(currentMetadata);
            } else if (metadataSection) {
                metadataSection.hidden = true;
            }
        });
    }

    // Drag and drop
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

    // Inicializar info del perfil
    updateProfileInfo(parseInt(widthSlider.value));

    // Funciones

    /**
     * Actualiza la información del perfil según el ancho seleccionado
     */
    function updateProfileInfo(width) {
        if (!profileInfo) return;

        let profile, description, color;

        if (width < 40) {
            profile = "PEQUEÑO";
            description = "Alto contraste, silueta clara";
            color = "#e74c3c"; // Rojo
        } else if (width < 90) {
            profile = "MEDIO";
            description = "Balance forma-detalle";
            color = "#f39c12"; // Naranja
        } else {
            profile = "GRANDE";
            description = "Máximo detalle y gradientes suaves";
            color = "#27ae60"; // Verde
        }

        profileInfo.innerHTML = `
            <strong style="color: ${color};">Perfil: ${profile}</strong> 
            <span style="color: #555;">- ${description}</span>
        `;
    }

    /**
     * Maneja la selección de imagen
     */
    function handleImageSelect() {
        if (imageInput.files.length > 0) {
            selectedFile = imageInput.files[0];

            // Validar tipo de archivo
            if (!selectedFile.type.startsWith('image/')) {
                showNotification('Por favor selecciona un archivo de imagen válido', 'error');
                selectedFile = null;
                return;
            }

            // Validar tamaño (10MB máximo)
            if (selectedFile.size > 10 * 1024 * 1024) {
                showNotification('La imagen es muy grande. Máximo 10MB', 'error');
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
                    img.style.borderRadius = '8px';
                    img.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                    imagePreview.appendChild(img);
                }
                img.src = e.target.result;
                imagePreview.style.display = 'block';
                convertButton.disabled = false;

                // Mostrar nombre del archivo
                const fileName = document.getElementById('fileName');
                if (fileName) {
                    fileName.textContent = `Archivo: ${selectedFile.name}`;
                    fileName.style.display = 'block';
                }
            };
            reader.readAsDataURL(selectedFile);
        }
    }

    /**
     * Convierte la imagen a ASCII
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
            const originalText = convertButton.textContent;
            convertButton.innerHTML = '<span class="loading-spinner"></span> Procesando...';
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

            // Scroll al resultado
            resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            showNotification(`¡Conversión exitosa! (${processingTime}s)`, 'success');

        } catch (error) {
            console.error('Error:', error);
            showNotification(error.message, 'error');
        } finally {
            convertButton.textContent = 'Convertir a ASCII';
            convertButton.disabled = false;
        }
    }

    /**
     * Muestra la metadata del proceso de conversión
     */
    function displayMetadata(metadata) {
        if (!metadataSection || !metadataContent) return;

        const { width, height, profile, ramp_info, parameters, original_size, processing_time } = metadata;

        const html = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div>
                    <h4 style="margin: 0 0 5px 0; color: var(--primary-color);">Dimensiones</h4>
                    <p style="margin: 0; font-size: 0.9em;">
                        Original: ${original_size[0]} × ${original_size[1]}px<br>
                        ASCII: ${width} × ${height} chars
                    </p>
                </div>
                
                <div>
                    <h4 style="margin: 0 0 5px 0; color: var(--primary-color);">Perfil</h4>
                    <p style="margin: 0; font-size: 0.9em;">
                        <strong>${profile}</strong><br>
                        ${ramp_info.description}
                    </p>
                </div>
                
                <div>
                    <h4 style="margin: 0 0 5px 0; color: var(--primary-color);">Parámetros</h4>
                    <p style="margin: 0; font-size: 0.9em;">
                        Gamma: ${parameters.gamma}<br>
                        Contraste: ${(parameters.contrast_boost * 100).toFixed(0)}%<br>
                        Aspect Ratio: ${parameters.aspect_ratio}
                    </p>
                </div>
                
                <div>
                    <h4 style="margin: 0 0 5px 0; color: var(--primary-color);">Rampa</h4>
                    <p style="margin: 0; font-size: 0.9em;">
                        Caracteres: ${ramp_info.ramp_length}<br>
                        Tiempo: ${processing_time || 'N/A'}s
                    </p>
                </div>
            </div>
            
            <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                <h4 style="margin: 0 0 5px 0; color: var(--primary-color); font-size: 0.95em;">
                    Vista previa de rampa:
                </h4>
                <pre style="margin: 0; font-size: 16px; letter-spacing: 2px; line-height: 1.5;">${ramp_info.characters.join(' ')}</pre>
            </div>
        `;

        metadataContent.innerHTML = html;
        metadataSection.hidden = false;
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
                const originalText = copyButton.textContent;
                copyButton.textContent = '✓ Copiado';
                copyButton.style.background = 'var(--success-color)';

                setTimeout(() => {
                    copyButton.textContent = originalText;
                    copyButton.style.background = '';
                }, 2000);
            })
            .catch((err) => {
                console.error('Error al copiar:', err);
                showNotification('❌ Error al copiar', 'error');
            });
    }

    /**
     * Descarga el resultado como archivo de texto
     */
    function downloadAsText() {
        const text = asciiResult.textContent;
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const width = widthSlider.value;
        const fileName = `ascii-art-${width}chars-${timestamp}.txt`;

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
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        // Forzar reflow para animación
        setTimeout(() => notification.classList.add('show'), 10);

        // Auto-ocultar después de 3 segundos
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Carga y muestra los perfiles disponibles (opcional)
     */
    async function loadProfiles() {
        try {
            const response = await fetch(`${API_URL}/api/profiles`);
            if (response.ok) {
                const data = await response.json();
                console.log('Perfiles disponibles:', data.profiles);
            }
        } catch (error) {
            console.warn('No se pudieron cargar los perfiles:', error);
        }
    }

    // Cargar perfiles al inicio (opcional)
    // loadProfiles();
});