"""
Configuración centralizada de la aplicación.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Información de la aplicación
    app_name: str = "ASCII Image Generator"
    app_version: str = "2.0.0"  # ← Actualizar versión
    debug: bool = False

    # Configuración del servidor
    host: str = "0.0.0.0"
    port: int = 8000

    # Configuración de CORS
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Configuración de subida de archivos
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    allowed_extensions: List[str] = ["jpg", "jpeg", "png", "webp", "gif", "bmp"]

    # Configuración de procesamiento de imágenes
    default_max_width: int = 100
    min_max_width: int = 15  # ← Reducir mínimo
    max_max_width: int = 200

    # Límites de dimensiones de imagen
    min_image_dimension: int = 10  # ← NUEVO
    max_image_dimension: int = 10000  # ← NUEVO

    # Sistema adaptativo (NUEVO)
    enable_adaptive_mode: bool = True
    enable_metadata: bool = False  # Por defecto no devolver metadata

    # Configuración de caché
    enable_cache: bool = False
    cache_ttl: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()