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
        """
        if width < 40:
            return {
                "gamma": 1.5,
                "contrast_boost": 1.3,
                "aspect_ratio": 0.65,
                "quantization_power": 1.5,
                "profile_name": "SMALL",
                "mode": "FORMA",
                "dithering_strength": 0.0,
                "edge_enhance": True,
                "posterize_levels": 5
            }

        elif width < 90:
            return {
                "gamma": 1.2,
                "contrast_boost": 1.1,
                "aspect_ratio": 0.58,
                "quantization_power": 1.1,
                "profile_name": "MEDIUM",
                "mode": "HIBRIDO",
                "dithering_strength": 0.3,
                "edge_enhance": True,
                "posterize_levels": 7
            }

        else:
            return {
                "gamma": 1.0,
                "contrast_boost": 1.0,
                "aspect_ratio": 0.52,
                "quantization_power": 0.9,
                "profile_name": "LARGE",
                "mode": "DETALLE",
                "dithering_strength": 1.0,
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
        Contraste adaptativo con realce opcional de bordes.
        """
        if edge_enhance:
            image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)

        pixels = np.array(image, dtype=np.float32)

        min_val = np.percentile(pixels, 2)
        max_val = np.percentile(pixels, 98)

        if max_val > min_val:
            pixels = (pixels - min_val) / (max_val - min_val) * 255.0
            pixels = np.clip(pixels, 0, 255)

            pixels *= contrast_boost
            pixels = np.clip(pixels, 0, 255)

            # Gamma seguro
            normalized = pixels / 255.0
            normalized = np.clip(normalized, 0.0, 1.0)
            pixels = np.power(normalized, gamma) * 255.0

        return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))

    @staticmethod
    def posterize_image(image: Image.Image, levels: int) -> Image.Image:
        """
        Posterización para crear bloques sólidos (modo FORMA).
        """
        pixels = np.array(image, dtype=np.float32)
        pixels = np.clip(pixels, 0, 255)

        pixels = (
            np.floor(pixels / 255.0 * (levels - 1))
            / (levels - 1)
            * 255.0
        )

        return Image.fromarray(pixels.astype(np.uint8))

    @staticmethod
    def floyd_steinberg_dithering(
            image: Image.Image,
            char_ramp: list,
            quantization_power: float = 1.0,
            strength: float = 1.0
    ) -> np.ndarray:
        """
        Floyd-Steinberg con control de intensidad y estabilidad numérica.
        """
        pixels = np.array(image, dtype=np.float32)
        height, width = pixels.shape
        levels = len(char_ramp)

        # --- SIN DITHERING ---
        if strength == 0.0:
            normalized = pixels / 255.0
            normalized = np.clip(normalized, 0.0, 1.0)

            indices = np.power(normalized, quantization_power) * (levels - 1)
            indices = np.nan_to_num(indices, nan=0.0, posinf=levels - 1, neginf=0.0)

            return np.clip(indices, 0, levels - 1).astype(int)

        # --- DITHERING COMPLETO ---
        for y in range(height):
            for x in range(width):
                old_pixel = pixels[y, x]

                # Normalización segura
                normalized = old_pixel / 255.0
                normalized = np.clip(normalized, 0.0, 1.0)

                new_level = int(
                    np.power(normalized, quantization_power) * (levels - 1)
                )
                new_level = np.clip(new_level, 0, levels - 1)

                pixels[y, x] = new_level

                quantized_value = (new_level / (levels - 1)) * 255.0
                quant_error = (old_pixel - quantized_value) * strength

                if x + 1 < width:
                    pixels[y, x + 1] += quant_error * 7 / 16

                if y + 1 < height:
                    if x > 0:
                        pixels[y + 1, x - 1] += quant_error * 3 / 16
                    pixels[y + 1, x] += quant_error * 5 / 16
                    if x + 1 < width:
                        pixels[y + 1, x + 1] += quant_error * 1 / 16

        # Limpieza final CRÍTICA
        pixels = np.nan_to_num(
            pixels,
            nan=0.0,
            posinf=levels - 1,
            neginf=0.0
        )

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
        params = ASCIIConverter.get_adaptive_params(max_width)
        char_ramp = CharacterRamps.get_ramp_for_width(max_width)

        gray = image.convert("L")

        gray = ASCIIConverter.apply_adaptive_contrast(
            gray,
            gamma=params["gamma"],
            contrast_boost=params["contrast_boost"],
            edge_enhance=params.get("edge_enhance", False)
        )

        if params["mode"] == "FORMA":
            gray = ASCIIConverter.posterize_image(
                gray,
                params["posterize_levels"]
            )

        aspect_ratio = gray.height / gray.width
        new_height = int(max_width * aspect_ratio * params["aspect_ratio"])

        resized = gray.resize(
            (max_width, new_height),
            Image.Resampling.LANCZOS
        )

        # Sanitización previa al dithering
        resized_array = np.array(resized, dtype=np.float32)
        resized_array = np.clip(resized_array, 0, 255)
        resized = Image.fromarray(resized_array.astype(np.uint8))

        indexed_pixels = ASCIIConverter.floyd_steinberg_dithering(
            resized,
            char_ramp,
            quantization_power=params["quantization_power"],
            strength=params["dithering_strength"]
        )

        lines = [
            ''.join(char_ramp[pixel] for pixel in row)
            for row in indexed_pixels
        ]

        ascii_art = '\n'.join(lines)

        if return_metadata:
            metadata = {
                "width": max_width,
                "height": new_height,
                "profile": params["profile_name"],
                "mode": params["mode"],
                "dithering_strength": params["dithering_strength"],
                "ramp_info": CharacterRamps.get_ramp_info(max_width),
                "parameters": params,
                "original_size": (image.width, image.height)
            }
            return ascii_art, metadata

        return ascii_art
