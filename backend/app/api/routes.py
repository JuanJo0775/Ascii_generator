from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.utils.image_processor import process_image

router = APIRouter()


@router.post("/convert")
async def convert_to_ascii(
        image: UploadFile = File(...),
        max_width: int = Form(100)
):
    """Convierte una imagen a arte ASCII."""
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        image_bytes = await image.read()
        ascii_art = process_image(image_bytes, max_width)
        return {"ascii_art": ascii_art}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))