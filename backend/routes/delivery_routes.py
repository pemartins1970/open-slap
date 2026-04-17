"""
📦 Delivery Routes - Endpoints para entrega local de arquivos
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os

from ..deps import delivery_registry

delivery_router = APIRouter(prefix="/local", tags=["delivery"])

@delivery_router.get("/{delivery_id}")
@delivery_router.get("/{delivery_id}/")
async def local_delivery_index(delivery_id: str):
    """Serve página index de entrega local."""
    info = delivery_registry.get(delivery_id)
    if not info:
        raise HTTPException(status_code=404, detail="Delivery não encontrado")
    
    abs_path = Path(info["base_dir"]) / "index.html"
    if not abs_path.is_file():
        raise HTTPException(status_code=404, detail="index.html não encontrado")
    
    media_type = "text/html"
    return FileResponse(abs_path, media_type=media_type)

@delivery_router.get("/{delivery_id}/{file_path:path}")
async def local_delivery_file(delivery_id: str, file_path: str):
    """Serve arquivos estáticos de entrega local."""
    info = delivery_registry.get(delivery_id)
    if not info:
        raise HTTPException(status_code=404, detail="Delivery não encontrado")
    
    abs_path = Path(info["base_dir"]) / file_path
    if not abs_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    # Detectar media type pelo arquivo
    media_type = "application/octet-stream"
    if abs_path.suffix == ".html":
        media_type = "text/html"
    elif abs_path.suffix == ".css":
        media_type = "text/css"
    elif abs_path.suffix == ".js":
        media_type = "application/javascript"
    elif abs_path.suffix in [".png", ".jpg", ".jpeg", ".gif", ".svg"]:
        media_type = f"image/{abs_path.suffix[1:]}"
    
    return FileResponse(abs_path, media_type=media_type)
