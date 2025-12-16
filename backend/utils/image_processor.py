from PIL import Image
import io


def process_image(image_bytes, max_width=100):
    """Procesa la imagen subida y la convierte a arte ASCII."""
    try:
        # Abrir imagen desde bytes
        image = Image.open(io.BytesIO(image_bytes))

        # Convertir a ASCII
        from app.core.ascii_converter import ASCIIConverter
        ascii_art = ASCIIConverter.image_to_ascii(image, max_width)

        return ascii_art
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")