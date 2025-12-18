"""
Conversor adaptativo de imágenes a ASCII art.
Sistema inteligente que ajusta parámetros según el tamaño objetivo.
"""

import numpy as np
from PIL import Image
from typing import Tuple
from .character_ramps import CharacterRamps


class ASCIIConverter:
    """
    Conversor adaptativo de imágenes a arte ASCII/Braille.
    Ajusta automáticamente contraste, cuantización y proporción según el tamaño.
    """

    @staticmethod
    def get_adaptive_params(width: int) -> dict:
        """
        Calcula parámetros adaptativos según el ancho objetivo.

        Args:
            width: Ancho en caracteres

        Returns:
            Diccionario con parámetros optimizados
        """
        # Perfil PEQUEÑO (15-40 caracteres)
        if width < 40:
            return {
                "gamma": 1.3,  # Suaviza sombras
                "contrast_boost": 0.85,  # Contraste moderado
                "aspect_ratio": 0.65,  # Más altura para compensar
                "quantization_power": 1.2,  # Favorece tonos claros
                "profile_name": "SMALL"
            }

        # Perfil MEDIO (40-90 caracteres)
        elif width < 90:
            return {
                "gamma": 1.1,
                "contrast_boost": 0.95,
                "aspect_ratio": 0.58,
                "quantization_power": 1.0,
                "profile_name": "MEDIUM"
            }

        # Perfil GRANDE (90+ caracteres)
        else:
            return {
                "gamma": 0.95,  # Permite negros profundos
                "contrast_boost": 1.0,  # Contraste completo
                "aspect_ratio": 0.52,  # Proporción más compacta
                "quantization_power": 0.85,  # Aprovecha tonos oscuros
                "profile_name": "LARGE"
            }

    @staticmethod
    def apply_adaptive_contrast(
            image: Image.Image,
            gamma: float,
            contrast_boost: float
    ) -> Image.Image:
        """
        Aplica normalización de contraste adaptativa.

        Args:
            image: Imagen en escala de grises
            gamma: Factor de corrección gamma (< 1 oscurece, > 1 aclara)
            contrast_boost: Factor de expansión del contraste (0-1)

        Returns:
            Imagen procesada
        """
        pixels = np.array(image, dtype=np.float32)

        # Normalización conservadora
        min_val = pixels.min()
        max_val = pixels.max()

        if max_val > min_val:
            # Contraste adaptativo (no siempre 0-255)
            range_target = 255 * contrast_boost
            pixels = (pixels - min_val) / (max_val - min_val) * range_target

            # Aplicar gamma para ajustar distribución tonal
            pixels = np.power(pixels / 255.0, gamma) * 255.0

        return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))

    @staticmethod
    def floyd_steinberg_dithering(
            image: Image.Image,
            char_ramp: list,
            quantization_power: float = 1.0
    ) -> np.ndarray:
        """
        Aplica Floyd-Steinberg dithering con cuantización adaptativa.

        Args:
            image: Imagen en escala de grises
            char_ramp: Lista de caracteres a usar
            quantization_power: Potencia para la curva de cuantización

        Returns:
            Matriz de índices de caracteres
        """
        pixels = np.array(image, dtype=float)
        height, width = pixels.shape
        levels = len(char_ramp)

        for y in range(height):
            for x in range(width):
                old_pixel = pixels[y, x]

                # Cuantización adaptativa
                normalized = old_pixel / 255.0
                new_level = int(
                    np.power(normalized, quantization_power) * (levels - 1)
                )
                new_level = np.clip(new_level, 0, levels - 1)

                pixels[y, x] = new_level

                # Calcular error de cuantización
                quantized_value = (new_level / (levels - 1)) * 255
                quant_error = old_pixel - quantized_value

                # Difundir error (Floyd-Steinberg)
                if x + 1 < width:
                    pixels[y, x + 1] += quant_error * 7 / 16

                if y + 1 < height:
                    if x > 0:
                        pixels[y + 1, x - 1] += quant_error * 3 / 16
                    pixels[y + 1, x] += quant_error * 5 / 16
                    if x + 1 < width:
                        pixels[y + 1, x + 1] += quant_error * 1 / 16

        return np.clip(pixels, 0, levels - 1).astype(int)

    @staticmethod
    def image_to_ascii(
            image: Image.Image,
            max_width: int = 100,
            return_metadata: bool = False
    ) -> str | Tuple[str, dict]:
        """
        Convierte una imagen a arte ASCII con parámetros adaptativos.

        Args:
            image: Imagen PIL
            max_width: Ancho máximo en caracteres
            return_metadata: Si True, devuelve también metadata del proceso

        Returns:
            String con arte ASCII (y opcionalmente dict con metadata)
        """
        # 1. Obtener parámetros adaptativos
        params = ASCIIConverter.get_adaptive_params(max_width)

        # 2. Obtener rampa de caracteres apropiada
        char_ramp = CharacterRamps.get_ramp_for_width(max_width)

        # 3. Convertir a escala de grises
        gray = image.convert("L")

        # 4. Aplicar contraste adaptativo
        gray = ASCIIConverter.apply_adaptive_contrast(
            gray,
            gamma=params["gamma"],
            contrast_boost=params["contrast_boost"]
        )

        # 5. Calcular dimensiones con proporción adaptativa
        aspect_ratio = gray.height / gray.width
        new_height = int(max_width * aspect_ratio * params["aspect_ratio"])

        # 6. Redimensionar
        resized = gray.resize(
            (max_width, new_height),
            Image.Resampling.LANCZOS
        )

        # 7. Aplicar dithering con cuantización adaptativa
        indexed_pixels = ASCIIConverter.floyd_steinberg_dithering(
            resized,
            char_ramp,
            quantization_power=params["quantization_power"]
        )

        # 8. Construir ASCII art
        lines = [
            ''.join(char_ramp[pixel] for pixel in row)
            for row in indexed_pixels
        ]

        ascii_art = '\n'.join(lines)

        # 9. Preparar metadata si se solicita
        if return_metadata:
            metadata = {
                "width": max_width,
                "height": new_height,
                "profile": params["profile_name"],
                "ramp_info": CharacterRamps.get_ramp_info(max_width),
                "parameters": params,
                "original_size": (image.width, image.height)
            }
            return ascii_art, metadata

        return ascii_art