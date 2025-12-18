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
    const imagePreview = document.getElementById('imagePreview');
    const resultSection = document.getElementById('resultSection');
    const asciiResult = document.getElementById('asciiResult');
    const copyButton = document.getElementById('copyButton');
    const downloadButton = document.getElementById('downloadButton');

    let selectedFile = null;

    // Event listeners
    selectButton.addEventListener('click', () => imageInput.click());
    imageInput.addEventListener('change', handleImageSelect);
    widthSlider.addEventListener('input', () => {
        widthValue.textContent = widthSlider.value;
    });
    convertButton.addEventListener('click', convertToAscii);
    copyButton.addEventListener('click', copyToClipboard);
    downloadButton.addEventListener('click', downloadAsText);

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

    // Funciones
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
                    imagePreview.appendChild(img);
                }
                img.src = e.target.result;
                imagePreview.style.display = 'block';
                convertButton.disabled = false;
            };
            reader.readAsDataURL(selectedFile);
        }
    }

    async function convertToAscii() {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append('image', selectedFile);
        formData.append('max_width', widthSlider.value);

        try {
            // Mostrar indicador de carga
            convertButton.textContent = 'Procesando...';
            convertButton.disabled = true;

            const response = await fetch(`${API_URL}/api/convert`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Error al procesar la imagen');
            }

            const data = await response.json();
            asciiResult.textContent = data.ascii_art;
            resultSection.hidden = false;

            // Scroll al resultado
            resultSection.scrollIntoView({ behavior: 'smooth' });
            showNotification('¡Conversión exitosa!', 'success');
        } catch (error) {
            console.error('Error:', error);
            showNotification(error.message, 'error');
        } finally {
            convertButton.textContent = 'Convertir a ASCII';
            convertButton.disabled = false;
        }
    }

    function copyToClipboard() {
        const text = asciiResult.textContent;
        navigator.clipboard.writeText(text)
            .then(() => showNotification('Copiado al portapapeles', 'success'))
            .catch(() => showNotification('Error al copiar', 'error'));
    }

    function downloadAsText() {
        const text = asciiResult.textContent;
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `ascii-art-${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showNotification('Archivo descargado', 'success');
    }

    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => notification.classList.add('show'), 10);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }
});