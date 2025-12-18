from PIL import Image
import io
import numpy as np


def process_image(image_bytes, max_width=100):
    """Procesa la imagen subida y la convierte a arte ASCII."""
    try:
        # Abrir imagen desde bytes
        image = Image.open(io.BytesIO(image_bytes))

        # Convertir a escala de grises
        gray = image.convert("L")

        # --- NORMALIZACIÓN DE CONTRASTE (CLAVE) ---
        pixels = np.array(gray, dtype=np.float32)
        min_val = pixels.min()
        max_val = pixels.max()

        if max_val > min_val:
            pixels = (pixels - min_val) / (max_val - min_val) * 255

        gray = Image.fromarray(pixels.astype(np.uint8))
        # -----------------------------------------

        # Convertir a ASCII
        from ..core.ascii_converter import ASCIIConverter
        ascii_art = ASCIIConverter.image_to_ascii(gray, max_width)

        return ascii_art

    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")
