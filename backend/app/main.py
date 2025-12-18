from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from .api.routes import router as api_router

app = FastAPI(
    title="ASCII Image Generator",
    description="Convert images to ASCII art using Floyd-Steinberg Dithering",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de la API
app.include_router(api_router, prefix="/api")

# Servir archivos estáticos del frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/css", StaticFiles(directory=str(frontend_path / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(frontend_path / "js")), name="js")

@app.get("/")
async def root():
    """Servir el frontend"""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file)
    return {"message": "ASCII Image Generator API - Frontend not found"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "ASCII Image Generator API is running"}