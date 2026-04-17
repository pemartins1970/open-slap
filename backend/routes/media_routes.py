"""
📁 Media Routes - Endpoints para servir arquivos estáticos e mídia
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os

from ..deps import MEDIA_DIR

media_router = APIRouter(prefix="", tags=["media"])

@media_router.get("/media/{file_path:path}", include_in_schema=False)
async def serve_media_direct(file_path: str):
    """Serve arquivos de mídia diretamente."""
    media_path = (MEDIA_DIR / file_path).resolve()
    try:
        if not media_path.is_file():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        if not str(media_path).startswith(str(MEDIA_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Acesso negado")
        return FileResponse(media_path)
    except Exception:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@media_router.get("/open_slap.png", include_in_schema=False)
async def serve_root_open_slap_png():
    """Serve o logo open_slap.png da raiz."""
    fname = "open_slap.png"
    p = (MEDIA_DIR / fname).resolve()
    try:
        if not p.is_file():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        return FileResponse(p, media_type="image/png")
    except Exception:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@media_router.get("/pemartins.jpg", include_in_schema=False)
async def serve_root_pemartins_jpg():
    """Serve a imagem pemartins.jpg da raiz."""
    fname = "pemartins.jpg"
    p = (MEDIA_DIR / fname).resolve()
    try:
        if not p.is_file():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        return FileResponse(p, media_type="image/jpeg")
    except Exception:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@media_router.get("/doacoes.txt", include_in_schema=False)
async def serve_root_doacoes_txt():
    """Serve o arquivo doacoes.txt da raiz."""
    fname = "doacoes.txt"
    p = (MEDIA_DIR / fname).resolve()
    try:
        if not p.is_file():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        return FileResponse(p, media_type="text/plain")
    except Exception:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@media_router.get("/btn_donateCC_LG.gif", include_in_schema=False)
async def serve_root_btn_donate():
    """Serve o botão de doação btn_donateCC_LG.gif da raiz."""
    fname = "btn_donateCC_LG.gif"
    p = (MEDIA_DIR / fname).resolve()
    try:
        if not p.is_file():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        return FileResponse(p, media_type="image/gif")
    except Exception:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
