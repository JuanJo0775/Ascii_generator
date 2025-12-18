"""
Rutas de la API mejoradas con validación y metadata opcional.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Optional
from ..utils.image_processor import process_image, get_image_info, validate_image
from ..core.config import settings

router = APIRouter()


@router.post("/convert")
async def convert_to_ascii(
        image: UploadFile = File(...),
        max_width: int = Form(100),
        include_metadata: bool = Form(False)
):
    """
    Convierte una imagen a arte ASCII adaptativo.

    Args:
        image: Archivo de imagen
        max_width: Ancho en caracteres (15-200)
        include_metadata: Incluir información del proceso

    Returns:
        JSON con ascii_art (y opcionalmente metadata)
    """
    # Validar tipo de archivo
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )

    # Validar ancho
    if not (settings.min_max_width <= max_width <= settings.max_max_width):
        raise HTTPException(
            status_code=400,
            detail=f"El ancho debe estar entre {settings.min_max_width} y {settings.max_max_width}"
        )

    try:
        # Leer bytes de la imagen
        image_bytes = await image.read()

        # Validar tamaño
        if len(image_bytes) > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo muy grande. Máximo {settings.max_file_size / (1024 * 1024):.0f}MB"
            )

        # Validar imagen
        is_valid, error_msg = validate_image(image_bytes)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Procesar imagen
        result = process_image(
            image_bytes,
            max_width=max_width,
            return_metadata=include_metadata or settings.enable_metadata
        )

        # Preparar respuesta
        if include_metadata or settings.enable_metadata:
            ascii_art, metadata = result
            return {
                "ascii_art": ascii_art,
                "metadata": metadata
            }
        else:
            return {"ascii_art": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando imagen: {str(e)}"
        )


@router.post("/info")
async def get_image_information(image: UploadFile = File(...)):
    """
    Obtiene información de una imagen sin procesarla.
    """
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    try:
        image_bytes = await image.read()
        info = get_image_info(image_bytes)
        return info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles")
async def get_available_profiles():
    """
    Devuelve información sobre los perfiles adaptativos disponibles.
    """
    from ..core.character_ramps import CharacterRamps

    return {
        "profiles": [
            {
                "name": "SMALL",
                "width_range": "15-39 caracteres",
                "ramp": CharacterRamps.get_ramp_info(30),
                "description": "Alto contraste, enfoque en silueta"
            },
            {
                "name": "MEDIUM",
                "width_range": "40-89 caracteres",
                "ramp": CharacterRamps.get_ramp_info(60),
                "description": "Balance entre forma y detalle"
            },
            {
                "name": "LARGE",
                "width_range": "90+ caracteres",
                "ramp": CharacterRamps.get_ramp_info(120),
                "description": "Máximo detalle con gradientes suaves"
            }
        ]
    }