"""
Conversor adaptativo de imágenes a ASCII art.
Implementa dos modos: FORMA (silueta clara) y DETALLE (gradientes).
"""

import numpy as np
from PIL import Image, ImageFilter
from typing import Tuple
from .character_ramps import CharacterRamps


class ASCIIConverter:
    """
    Conversor con doble modo:
    - FORMA: Para tamaños pequeños, prioriza silueta y contraste
    - DETALLE: Para tamaños grandes, usa dithering completo
    """

    @staticmethod
    def get_adaptive_params(width: int) -> dict:
        """
        Parámetros optimizados para legibilidad de forma.

        CAMBIOS CLAVE:
        - Modo FORMA elimina/reduce dithering
        - Contraste más agresivo en tamaños pequeños
        - Posterización en lugar de gradientes suaves
        """
        # Perfil PEQUEÑO (15-39 caracteres) - MODO FORMA PURO
        if width < 40:
            return {
                "gamma": 1.5,  # Aclara sombras agresivamente
                "contrast_boost": 1.3,  # Contraste muy alto
                "aspect_ratio": 0.65,
                "quantization_power": 1.5,  # Favorece extremos
                "profile_name": "SMALL",
                "mode": "FORMA",  # NUEVO
                "dithering_strength": 0.0,  # SIN dithering
                "edge_enhance": True,  # Realza bordes
                "posterize_levels": 5  # Posterización fuerte
            }

        # Perfil MEDIO (40-89 caracteres) - MODO HÍBRIDO
        elif width < 90:
            return {
                "gamma": 1.2,
                "contrast_boost": 1.1,
                "aspect_ratio": 0.58,
                "quantization_power": 1.1,
                "profile_name": "MEDIUM",
                "mode": "HIBRIDO",
                "dithering_strength": 0.3,  # Dithering reducido
                "edge_enhance": True,
                "posterize_levels": 7
            }

        # Perfil GRANDE (90+ caracteres) - MODO DETALLE
        else:
            return {
                "gamma": 1.0,
                "contrast_boost": 1.0,
                "aspect_ratio": 0.52,
                "quantization_power": 0.9,
                "profile_name": "LARGE",
                "mode": "DETALLE",
                "dithering_strength": 1.0,  # Dithering completo
                "edge_enhance": False,
                "posterize_levels": 12
            }

    @staticmethod
    def apply_adaptive_contrast(
            image: Image.Image,
            gamma: float,
            contrast_boost: float,
            edge_enhance: bool = False
    ) -> Image.Image:
        """
        Contraste adaptativo con opcional realce de bordes.
        """
        # Realzar bordes primero si es modo FORMA
        if edge_enhance:
            image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)

        pixels = np.array(image, dtype=np.float32)

        # Normalización agresiva
        min_val = np.percentile(pixels, 2)  # Ignorar outliers oscuros
        max_val = np.percentile(pixels, 98)  # Ignorar outliers claros

        if max_val > min_val:
            # Expansión del contraste
            pixels = (pixels - min_val) / (max_val - min_val) * 255
            pixels = np.clip(pixels, 0, 255)

            # Boost adicional
            pixels = pixels * contrast_boost
            pixels = np.clip(pixels, 0, 255)

            # Gamma
            pixels = np.power(pixels / 255.0, gamma) * 255.0

        return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))

    @staticmethod
    def posterize_image(image: Image.Image, levels: int) -> Image.Image:
        """
        NUEVA FUNCIÓN: Posterización para crear bloques sólidos.
        Esto es clave para el modo FORMA.
        """
        pixels = np.array(image, dtype=np.float32)

        # Cuantizar a N niveles discretos
        pixels = np.floor(pixels / 255.0 * (levels - 1)) / (levels - 1) * 255

        return Image.fromarray(pixels.astype(np.uint8))

    @staticmethod
    def detect_edges(image: Image.Image) -> np.ndarray:
        """
        NUEVA FUNCIÓN: Detecta bordes para tratarlos diferente.
        """
        # Usar Sobel para detección de bordes
        edges = image.filter(ImageFilter.FIND_EDGES)
        edge_array = np.array(edges)

        # Binarizar: True donde hay borde
        return edge_array > 30

    @staticmethod
    def floyd_steinberg_dithering(
            image: Image.Image,
            char_ramp: list,
            quantization_power: float = 1.0,
            strength: float = 1.0  # NUEVO: controla intensidad del dithering
    ) -> np.ndarray:
        """
        Floyd-Steinberg con intensidad controlable.
        strength=0.0 → sin dithering (cuantización directa)
        strength=1.0 → dithering completo
        """
        pixels = np.array(image, dtype=float)
        height, width = pixels.shape
        levels = len(char_ramp)

        # Si strength es 0, hacer cuantización directa sin difusión de error
        if strength == 0.0:
            normalized = pixels / 255.0
            indices = np.power(normalized, quantization_power) * (levels - 1)
            return np.clip(indices, 0, levels - 1).astype(int)

        # Floyd-Steinberg con intensidad controlada
        for y in range(height):
            for x in range(width):
                old_pixel = pixels[y, x]

                # Cuantización
                normalized = old_pixel / 255.0
                new_level = int(
                    np.power(normalized, quantization_power) * (levels - 1)
                )
                new_level = np.clip(new_level, 0, levels - 1)

                pixels[y, x] = new_level

                # Error de cuantización
                quantized_value = (new_level / (levels - 1)) * 255
                quant_error = (old_pixel - quantized_value) * strength  # Aplicar strength

                # Difundir error (coeficientes estándar Floyd-Steinberg)
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
        Pipeline completo con modo adaptativo FORMA/DETALLE.
        """
        # 1. Parámetros adaptativos
        params = ASCIIConverter.get_adaptive_params(max_width)
        char_ramp = CharacterRamps.get_ramp_for_width(max_width)

        # 2. Escala de grises
        gray = image.convert("L")

        # 3. Contraste adaptativo (con edge enhance si es modo FORMA)
        gray = ASCIIConverter.apply_adaptive_contrast(
            gray,
            gamma=params["gamma"],
            contrast_boost=params["contrast_boost"],
            edge_enhance=params.get("edge_enhance", False)
        )

        # 4. Posterización si es modo FORMA
        if params["mode"] == "FORMA":
            gray = ASCIIConverter.posterize_image(
                gray,
                params["posterize_levels"]
            )

        # 5. Redimensionar
        aspect_ratio = gray.height / gray.width
        new_height = int(max_width * aspect_ratio * params["aspect_ratio"])
        resized = gray.resize(
            (max_width, new_height),
            Image.Resampling.LANCZOS
        )

        # 6. Dithering con intensidad controlada
        indexed_pixels = ASCIIConverter.floyd_steinberg_dithering(
            resized,
            char_ramp,
            quantization_power=params["quantization_power"],
            strength=params["dithering_strength"]  # CLAVE: 0.0 para FORMA
        )

        # 7. Construir ASCII
        lines = [
            ''.join(char_ramp[pixel] for pixel in row)
            for row in indexed_pixels
        ]

        ascii_art = '\n'.join(lines)

        # 8. Metadata
        if return_metadata:
            metadata = {
                "width": max_width,
                "height": new_height,
                "profile": params["profile_name"],
                "mode": params["mode"],  # NUEVO
                "dithering_strength": params["dithering_strength"],  # NUEVO
                "ramp_info": CharacterRamps.get_ramp_info(max_width),
                "parameters": params,
                "original_size": (image.width, image.height)
            }
            return ascii_art, metadata

        return ascii_art