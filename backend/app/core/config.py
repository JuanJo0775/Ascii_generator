from pydantic import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Configuración básica de la aplicación
    app_name: str = "ASCII Image Generator"
    app_version: str = "1.0.0"
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
    min_max_width: int = 50
    max_max_width: int = 200
    default_char_height_ratio: float = 0.55  # Corrección de proporción de caracteres

    # Configuración de caché (opcional)
    enable_cache: bool = False
    cache_ttl: int = 3600  # segundos

    class Config:
        env_file = ".env"
        case_sensitive = False


# Crear una instancia de configuración para usar en toda la aplicación
settings = Settings()