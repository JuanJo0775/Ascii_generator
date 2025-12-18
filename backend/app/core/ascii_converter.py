import numpy as np
from PIL import Image


class ASCIIConverter:
    """
    Conversor de imágenes a arte ASCII/Braille
    usando una rampa corta de alto contraste.
    """

    # Rampa de caracteres (claro → oscuro)
    UNICODE_CHARS = [
        '⠀',  # blanco
        '⠁',
        '⠃',
        '⠇',
        '⠏',
        '⠗',
        '⠟',
        '⠯',
        '⠿',
        '⡿',
        '⢿',
        '⣻',
        '⣽',
        '⣿'  # negro
    ]

    @staticmethod
    def floyd_steinberg_dithering(image: Image.Image) -> np.ndarray:
        """
        Aplica Floyd–Steinberg dithering sobre una imagen en escala de grises.
        Devuelve una matriz de índices de caracteres.
        """
        pixels = np.array(image, dtype=float)
        height, width = pixels.shape
        levels = len(ASCIIConverter.UNICODE_CHARS)

        for y in range(height):
            for x in range(width):
                old_pixel = pixels[y, x]

                # Cuantización correcta
                new_level = int((old_pixel / 255) ** 0.9 * (levels - 1))
                pixels[y, x] = new_level

                # Error de cuantización
                quant_error = old_pixel - (new_level / (levels - 1)) * 255

                # Difusión del error
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
    def image_to_ascii(image: Image.Image, max_width: int = 100) -> str:
        """
        Convierte una imagen a arte ASCII/Braille.
        """
        # Escala de grises
        gray = image.convert("L")

        # Mantener proporción (ajuste para caracteres)
        aspect_ratio = gray.height / gray.width
        new_height = int(max_width * aspect_ratio * 0.55)

        # Redimensionar
        resized = gray.resize(
            (max_width, new_height),
            Image.Resampling.LANCZOS
        )

        # Dithering
        indexed_pixels = ASCIIConverter.floyd_steinberg_dithering(resized)

        # Construir ASCII
        lines = [
            ''.join(ASCIIConverter.UNICODE_CHARS[p] for p in row)
            for row in indexed_pixels
        ]

        return '\n'.join(lines)
