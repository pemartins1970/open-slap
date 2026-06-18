import logging
import os
from typing import Optional, Dict, Any, Literal
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..db import (
    get_user_projects,
    get_project,
    create_project,
    update_project_name,
    update_project_context,
    update_project_details,
    delete_project,
    update_project_status,
    update_project_repository,
    initialize_project_wiki,
    append_wiki_entry,
    get_wiki_section,
    get_wiki_full,
    upsert_user_connector_secret_ciphertext,
    get_user_connector_secret_ciphertext,
)
from ..auth import get_current_user
from ..deps import security, HTTPAuthorizationCredentials
from ..deps import _dpapi_protect_text, _dpapi_unprotect_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects"])

# --- Schemas ---

class ProjectCreateInput(BaseModel):
    name: str
    context_md: Optional[str] = ""
    tap_json: Optional[str] = "{}"
    expert_mode: Optional[int] = 0
    stakeholders_json: Optional[str] = "[]"
    risk_matrix_json: Optional[str] = "[]"
    release_plan_json: Optional[str] = "[]"
    team_charter_json: Optional[str] = "{}"
    status_report_json: Optional[str] = "{}"
    lessons_learned_json: Optional[str] = "{}"

class ProjectUpdateInput(BaseModel):
    name: Optional[str] = None
    context_md: Optional[str] = None
    tap_json: Optional[str] = None
    expert_mode: Optional[int] = None
    stakeholders_json: Optional[str] = None
    risk_matrix_json: Optional[str] = None
    release_plan_json: Optional[str] = None
    team_charter_json: Optional[str] = None
    status_report_json: Optional[str] = None
    lessons_learned_json: Optional[str] = None

class ProjectStatusInput(BaseModel):
    status: Literal['draft', 'ativo', 'suspenso', 'encerrado', 'cancelado']
    suspension_reason: Optional[str] = None

class ProjectRepositoryInput(BaseModel):
    type: str
    url: str
    credential: Optional[str] = None

# --- Routes ---

@router.get("")
async def list_projects(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Lista todos os projetos do usuário autenticado."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"projects": get_user_projects(user["id"])}

@router.post("")
async def create_project_endpoint(
    payload: ProjectCreateInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Cria um novo projeto."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nome do projeto é obrigatório")
    
    try:
        pid = create_project(user["id"], name, payload.context_md or "")
        
        details = {}
        if payload.tap_json is not None:
            details["tap_json"] = payload.tap_json
        if payload.expert_mode is not None:
            details["expert_mode"] = payload.expert_mode
        if payload.stakeholders_json is not None:
            details["stakeholders_json"] = payload.stakeholders_json
        if payload.risk_matrix_json is not None:
            details["risk_matrix_json"] = payload.risk_matrix_json
        if payload.release_plan_json is not None:
            details["release_plan_json"] = payload.release_plan_json
        if payload.team_charter_json is not None:
            details["team_charter_json"] = payload.team_charter_json
        if payload.status_report_json is not None:
            details["status_report_json"] = payload.status_report_json
        if payload.lessons_learned_json is not None:
            details["lessons_learned_json"] = payload.lessons_learned_json
            
        if details:
            update_project_details(pid, user["id"], details)

        initialize_project_wiki(pid, user["id"])
            
        return {"ok": True, "project_id": pid}
    except Exception as e:
        logger.exception("Falha ao criar projeto para o usuário %s", str(user.get("id")))
        
        debug = (os.getenv("OPENSLAP_DEBUG_ERRORS") or "").strip().lower() in {"1", "true", "yes", "on"}
        detail = str(e) if debug else "Erro interno ao processar a criação do projeto"
        raise HTTPException(status_code=500, detail=detail)

@router.put("/{project_id}")
async def update_project_endpoint(
    project_id: int,
    payload: ProjectUpdateInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Atualiza as informações de um projeto existente."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    details = {}
    if payload.name is not None:
        clean_name = payload.name.strip()
        if not clean_name:
            raise HTTPException(status_code=400, detail="Nome do projeto não pode ser vazio")
        details["name"] = clean_name
    if payload.context_md is not None:
        details["context_md"] = payload.context_md
    if payload.tap_json is not None:
        details["tap_json"] = payload.tap_json
    if payload.expert_mode is not None:
        details["expert_mode"] = payload.expert_mode
    if payload.stakeholders_json is not None:
        details["stakeholders_json"] = payload.stakeholders_json
    if payload.risk_matrix_json is not None:
        details["risk_matrix_json"] = payload.risk_matrix_json
    if payload.release_plan_json is not None:
        details["release_plan_json"] = payload.release_plan_json
    if payload.team_charter_json is not None:
        details["team_charter_json"] = payload.team_charter_json
    if payload.status_report_json is not None:
        details["status_report_json"] = payload.status_report_json
    if payload.lessons_learned_json is not None:
        details["lessons_learned_json"] = payload.lessons_learned_json
        
    if not details:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar fornecido")
        
    try:
        update_project_details(project_id, user["id"], details)
    except Exception as e:
        logger.exception("Falha ao atualizar projeto %s", str(project_id))
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar projeto")
        
    return {"ok": True}

@router.delete("/{project_id}")
async def delete_project_endpoint(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Remove um projeto permanentemente."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    ok = delete_project(project_id, user["id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Projeto não encontrado ou acesso negado")
    
    return {"ok": True}


@router.patch("/{project_id}/status")
async def update_project_status_endpoint(
    project_id: int,
    payload: ProjectStatusInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Atualiza o status do projeto (draft, ativo, suspenso, encerrado, cancelado)."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if payload.status == 'suspenso' and not (payload.suspension_reason or '').strip():
        raise HTTPException(status_code=400, detail="Justificativa obrigatória para suspensão")

    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    ok = update_project_status(project_id, user["id"], payload.status, payload.suspension_reason)
    if not ok:
        raise HTTPException(status_code=500, detail="Erro ao atualizar status")

    if payload.status in ('suspenso', 'encerrado', 'cancelado'):
        reason_txt = payload.suspension_reason or ''
        append_wiki_entry(
            project_id, user["id"],
            section='change_management',
            content_md=f"**Status alterado para `{payload.status}`** — {reason_txt}",
            author='system'
        )

    return {"ok": True, "status": payload.status}


@router.put("/{project_id}/repository")
async def update_project_repository_endpoint(
    project_id: int,
    payload: ProjectRepositoryInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Configura o repositório do projeto."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    repo_data = {
        "type": payload.type,
        "url": payload.url,
        "credential_present": False,
        "credential_validated_at": None,
        "validation_status": "none"
    }

    if payload.credential:
        _save_repo_credential(user["id"], project_id, payload.credential)
        repo_data["credential_present"] = True

    update_project_repository(project_id, user["id"], repo_data)
    return {"ok": True, "repository": repo_data}


@router.post("/{project_id}/repository/validate")
async def validate_project_repository_endpoint(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Valida acesso ao repositório configurado."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    import json as _json
    repo_data = _json.loads(proj.get("repository_json") or "{}")
    if not repo_data.get("url"):
        raise HTTPException(status_code=400, detail="Repositório não configurado")

    result = await _validate_repository_access(user["id"], project_id, repo_data)

    repo_data["validation_status"] = "valid" if result["ok"] else "invalid"
    repo_data["credential_validated_at"] = result.get("validated_at")
    update_project_repository(project_id, user["id"], repo_data)

    if result["ok"] and repo_data.get("type") == "local":
        try:
            from ..services.fs_watcher import start_project_watcher
            start_project_watcher(project_id, user["id"], repo_data.get("url", ""))
        except Exception:
            pass

    return result


@router.get("/{project_id}/wiki")
async def get_project_wiki_endpoint(
    project_id: int,
    section: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Retorna a wiki do projeto, opcionalmente filtrada por seção."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    if section:
        return {"section": section, "entries": get_wiki_section(project_id, section)}
    else:
        return {"wiki": get_wiki_full(project_id)}


@router.get("/{project_id}/report")
async def get_project_status_report_endpoint(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Gera relatório de status determinístico. Zero tokens."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    from ..services.report_service import generate_status_report
    report_md = generate_status_report(proj, user)
    return {"report_md": report_md, "project_id": project_id}


@router.post("/import-tap")
async def import_tap_endpoint(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Importa documento externo e extrai campos TAP via script."""
    import tempfile as _tempfile
    import os as _os

    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    allowed_types = {'txt', 'md', 'pdf', 'docx'}
    ext = (file.filename or '').rsplit('.', 1)[-1].lower()
    if ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Tipo não suportado: {ext}")

    with _tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from ..services.tap_import_service import extract_tap_from_file
        tap_data, success, message = extract_tap_from_file(tmp_path, ext)
    finally:
        _os.unlink(tmp_path)

    return {
        "tap_data": tap_data,
        "extraction_success": success,
        "message": message,
        "needs_agent_fallback": not success,
    }


# ── Helper functions ─────────────────────────────────────────────────────────

def _save_repo_credential(user_id: int, project_id: int, credential: str) -> None:
    """Cifra e salva credencial de repositório em user_connector_secrets."""
    connector_key = f"project_{project_id}_repo"
    ciphertext = _dpapi_protect_text(credential)
    upsert_user_connector_secret_ciphertext(user_id, connector_key, ciphertext)


async def _validate_repository_access(user_id: int, project_id: int, repo_data: dict) -> dict:
    """Script determinístico de validação. Não consome tokens."""
    from datetime import datetime, timezone

    repo_type = repo_data.get("type", "local")
    url = repo_data.get("url", "")

    try:
        if repo_type == "local":
            import os as _os
            accessible = _os.path.exists(url) and _os.path.isdir(url)
            return {
                "ok": accessible,
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "detail": "Diretório acessível" if accessible else f"Diretório não encontrado: {url}"
            }

        elif repo_type == "github":
            return {"ok": False, "detail": "GitHub validation: implementar com infraestrutura de cifragem existente"}

        elif repo_type == "google_drive":
            return {"ok": False, "detail": "Google Drive validation: implementar via connector existente"}

        else:
            return {"ok": False, "detail": f"Tipo de repositório não suportado: {repo_type}"}

    except Exception as e:
        return {"ok": False, "detail": str(e), "validated_at": None}
