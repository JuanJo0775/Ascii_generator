"""
Procesador de imágenes mejorado con validación y manejo robusto.
"""

from PIL import Image
import io
import numpy as np
from typing import Tuple, Optional


def validate_image(image_bytes: bytes) -> Tuple[bool, Optional[str]]:
    """
    Valida que los bytes correspondan a una imagen válida.

    Returns:
        Tuple (es_válida, mensaje_error)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Verifica integridad

        # Reabrir después de verify
        image = Image.open(io.BytesIO(image_bytes))

        # Validar dimensiones mínimas
        if image.width < 10 or image.height < 10:
            return False, "Imagen demasiado pequeña (mínimo 10x10 px)"

        # Validar dimensiones máximas
        if image.width > 10000 or image.height > 10000:
            return False, "Imagen demasiado grande (máximo 10000x10000 px)"

        return True, None

    except Exception as e:
        return False, f"Imagen inválida o corrupta: {str(e)}"


def process_image(
        image_bytes: bytes,
        max_width: int = 100,
        return_metadata: bool = False
) -> str | Tuple[str, dict]:
    """
    Procesa la imagen subida y la convierte a arte ASCII.

    Args:
        image_bytes: Bytes de la imagen
        max_width: Ancho máximo en caracteres
        return_metadata: Si True, incluye información del proceso

    Returns:
        Arte ASCII (y opcionalmente metadata)

    Raises:
        ValueError: Si la imagen es inválida o hay error en procesamiento
    """
    # Validar imagen
    is_valid, error_msg = validate_image(image_bytes)
    if not is_valid:
        raise ValueError(error_msg)

    try:
        # Abrir imagen desde bytes
        image = Image.open(io.BytesIO(image_bytes))

        # Convertir a RGB si es necesario (para manejar PNG con alpha, etc.)
        if image.mode not in ('RGB', 'L'):
            if image.mode == 'RGBA':
                # Crear fondo blanco para transparencias
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            else:
                image = image.convert('RGB')

        # Convertir a ASCII usando el sistema adaptativo
        from ..core.ascii_converter import ASCIIConverter

        result = ASCIIConverter.image_to_ascii(
            image,
            max_width=max_width,
            return_metadata=return_metadata
        )

        return result

    except Exception as e:
        raise ValueError(f"Error procesando imagen: {str(e)}")


def get_image_info(image_bytes: bytes) -> dict:
    """
    Obtiene información básica de una imagen sin procesarla.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        return {
            "format": image.format,
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
            "size_kb": len(image_bytes) / 1024
        }
    except Exception as e:
        raise ValueError(f"Error leyendo información de imagen: {str(e)}")