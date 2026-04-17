from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..auth import get_current_user
from ..deps import security
from ..db import delete_user_command_autoapprove, list_user_command_autoapprove

router = APIRouter()


@router.get("/api/commands/autoapprove")
async def commands_list_autoapprove(
    limit: int = Query(200, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    items = list_user_command_autoapprove(int(current_user["id"]), limit=int(limit))
    return {"items": items}


class CommandAutoapproveDeletePayload(BaseModel):
    command_norm: str = ""


@router.delete("/api/commands/autoapprove")
async def commands_delete_autoapprove(
    payload: CommandAutoapproveDeletePayload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    cmd = str(payload.command_norm or "").strip().lower()
    if not cmd:
        raise HTTPException(status_code=400, detail="command_norm é obrigatório")
    ok = delete_user_command_autoapprove(int(current_user["id"]), cmd)
    return {"ok": True, "deleted": bool(ok), "command_norm": cmd}

