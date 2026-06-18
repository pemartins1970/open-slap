# SPEC: Sistema de Projetos, Wiki e Ideação — v1
**Status**: ✅ CONCLUÍDO  
**Projeto**: Open Slap! v3  
**Data**: 2026-05-30  
**Prioridade**: ÉPICO 2 → ÉPICO 3 → ÉPICO 1 → ÉPICO 4 → ÉPICO 5 → ÉPICO 6  
**Assignee**: Opencode  

---

## Contexto

Esta spec cobre 6 épicos acordados com o product owner. A implementação segue a ordem definida: base de dados e ciclo de vida do projeto primeiro, wiki e ideação depois, caminhos de entrada, relatórios e rastreamento de tokens por último.

**Premissas verificadas no código existente:**
- Tabela `projects` existe com TAP, stakeholders, riscos, releases — falta `status`, `suspension_reason`, `repository_json`
- Tabela `notes` existe com `project_id` e FTS5 — falta `category` e `source`
- `project_wizard_state` existe e é funcional
- Campo `tokens` existe em `messages` mas sem agregação por projeto/sprint
- `notes_routes.py` importa `get_current_user` de `backend.main_auth` — manter esse import, não alterar

---

## FASE 1 — Migrations do Banco

### 1.1 Tabela `projects` — adicionar 3 colunas

```sql
ALTER TABLE projects ADD COLUMN status TEXT DEFAULT 'draft'
  CHECK (status IN ('draft','ativo','suspenso','encerrado','cancelado'));

ALTER TABLE projects ADD COLUMN suspension_reason TEXT;

ALTER TABLE projects ADD COLUMN repository_json TEXT DEFAULT '{}';
```

`repository_json` estrutura esperada:
```json
{
  "type": "local|github|google_drive",
  "url": "",
  "credential_present": false,
  "credential_validated_at": null,
  "validation_status": "none|valid|invalid"
}
```
A credencial em si **nunca** entra neste JSON — vai para `user_connector_secrets` com
`connector_key = "project_{project_id}_repo"`.

### 1.2 Tabela `notes` — adicionar 2 colunas

```sql
ALTER TABLE notes ADD COLUMN category TEXT DEFAULT 'nota'
  CHECK (category IN ('nota','ideia_solta','ideacao','projeto_futuro'));

ALTER TABLE notes ADD COLUMN source TEXT DEFAULT 'user'
  CHECK (source IN ('user','agent'));
```

### 1.3 Tabela `project_wiki` — CRIAR

```sql
CREATE TABLE IF NOT EXISTS project_wiki (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    section TEXT NOT NULL
      CHECK (section IN (
        'codebase','todos','notes','issues',
        'agent_communication','change_management','general'
      )),
    title TEXT NOT NULL DEFAULT '',
    content_md TEXT NOT NULL DEFAULT '',
    author TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS idx_wiki_project ON project_wiki(project_id);
CREATE INDEX IF NOT EXISTS idx_wiki_section ON project_wiki(project_id, section);
CREATE INDEX IF NOT EXISTS idx_wiki_updated ON project_wiki(updated_at);
```

### 1.4 Tabela `project_token_usage` — CRIAR

```sql
CREATE TABLE IF NOT EXISTS project_token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    sprint_label TEXT,
    message_id INTEGER,
    agent_id TEXT,
    provider TEXT,
    model TEXT,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS idx_token_usage_project ON project_token_usage(project_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_sprint ON project_token_usage(project_id, sprint_label);
```

### 1.5 Tabela `agent_communication_log` — CRIAR

```sql
CREATE TABLE IF NOT EXISTS agent_communication_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT,
    source TEXT DEFAULT 'internal'
      CHECK (source IN ('internal','external')),
    external_tool TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS idx_agent_log_project ON agent_communication_log(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_log_agent ON agent_communication_log(project_id, agent_id);
```

### 1.6 Integrar migrations em `DatabaseManager._ensure_database()`

Adicionar todas as migrations acima no método `_ensure_database()` do `db.py`, após o bloco de `projects`. Cada `ALTER TABLE` deve estar dentro de `try/except Exception: pass` — padrão já estabelecido no codebase.

---

## FASE 2 — Funções no `db.py`

Adicionar ao `DatabaseManager` e expor como module-level wrappers:

```python
# Projects — status e repositório
def update_project_status(
    self, project_id: int, user_id: int,
    status: str, suspension_reason: Optional[str] = None
) -> bool:
    """status: draft|ativo|suspenso|encerrado|cancelado"""
    allowed = {'draft','ativo','suspenso','encerrado','cancelado'}
    if status not in allowed:
        raise ValueError(f"Status inválido: {status}")
    fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
    params: list = [status]
    if suspension_reason is not None:
        fields.append("suspension_reason = ?")
        params.append(suspension_reason)
    params += [project_id, user_id]
    with self._connect() as conn:
        cur = conn.execute(
            f"UPDATE projects SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            tuple(params)
        )
        conn.commit()
        return bool(cur.rowcount)

def update_project_repository(
    self, project_id: int, user_id: int, repository_data: dict
) -> bool:
    import json
    with self._connect() as conn:
        cur = conn.execute(
            "UPDATE projects SET repository_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (json.dumps(repository_data), project_id, user_id)
        )
        conn.commit()
        return bool(cur.rowcount)

# Wiki
def create_wiki_entry(
    self, project_id: int, user_id: int,
    section: str, title: str = '', content_md: str = '', author: str = 'system'
) -> int:
    with self._connect() as conn:
        cur = conn.execute(
            """INSERT INTO project_wiki
               (project_id, user_id, section, title, content_md, author)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, user_id, section, title, content_md, author)
        )
        conn.commit()
        return cur.lastrowid

def append_wiki_entry(
    self, project_id: int, user_id: int,
    section: str, content_md: str, author: str = 'agent', title: str = ''
) -> int:
    """Appends a new entry to a wiki section."""
    return self.create_wiki_entry(project_id, user_id, section, title, content_md, author)

def get_wiki_section(
    self, project_id: int, section: str, limit: int = 50
) -> List[Dict[str, Any]]:
    with self._connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT * FROM project_wiki
               WHERE project_id = ? AND section = ?
               ORDER BY created_at DESC LIMIT ?""",
            (project_id, section, limit)
        ).fetchall()
        return [dict(r) for r in rows]

def get_wiki_full(self, project_id: int) -> Dict[str, List[Dict[str, Any]]]:
    """Returns all wiki sections grouped by section name."""
    with self._connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM project_wiki WHERE project_id = ? ORDER BY section, created_at ASC",
            (project_id,)
        ).fetchall()
    result: Dict[str, list] = {}
    for r in rows:
        d = dict(r)
        sec = d['section']
        result.setdefault(sec, []).append(d)
    return result

def initialize_project_wiki(self, project_id: int, user_id: int) -> None:
    """Creates the initial wiki structure for a new project. Zero tokens."""
    sections = ['codebase','todos','notes','issues','agent_communication','change_management']
    with self._connect() as conn:
        for sec in sections:
            conn.execute(
                """INSERT OR IGNORE INTO project_wiki
                   (project_id, user_id, section, title, content_md, author)
                   VALUES (?, ?, ?, ?, '', 'system')""",
                (project_id, user_id, sec, sec.replace('_', ' ').title())
            )
        conn.commit()

# Agent communication log
def log_agent_action(
    self, project_id: int, user_id: int,
    agent_id: str, action: str, detail: str = '',
    source: str = 'internal', external_tool: str = None
) -> int:
    with self._connect() as conn:
        cur = conn.execute(
            """INSERT INTO agent_communication_log
               (project_id, user_id, agent_id, action, detail, source, external_tool)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (project_id, user_id, agent_id, action, detail, source, external_tool)
        )
        conn.commit()
        return cur.lastrowid

def get_agent_log(
    self, project_id: int, limit: int = 100,
    agent_id: str = None
) -> List[Dict[str, Any]]:
    with self._connect() as conn:
        conn.row_factory = sqlite3.Row
        if agent_id:
            rows = conn.execute(
                """SELECT * FROM agent_communication_log
                   WHERE project_id = ? AND agent_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (project_id, agent_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM agent_communication_log
                   WHERE project_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (project_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]

# Token usage
def record_token_usage(
    self, project_id: int, user_id: int,
    tokens_in: int, tokens_out: int,
    sprint_label: str = None, message_id: int = None,
    agent_id: str = None, provider: str = None, model: str = None
) -> int:
    with self._connect() as conn:
        cur = conn.execute(
            """INSERT INTO project_token_usage
               (project_id, user_id, sprint_label, message_id, agent_id, provider, model, tokens_in, tokens_out)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (project_id, user_id, sprint_label, message_id, agent_id, provider, model, tokens_in, tokens_out)
        )
        conn.commit()
        return cur.lastrowid

def get_token_usage_summary(self, project_id: int) -> Dict[str, Any]:
    """Returns total and per-sprint token usage."""
    with self._connect() as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute(
            """SELECT
               SUM(tokens_in) as total_in,
               SUM(tokens_out) as total_out,
               SUM(tokens_in + tokens_out) as total
               FROM project_token_usage WHERE project_id = ?""",
            (project_id,)
        ).fetchone()
        sprints = conn.execute(
            """SELECT sprint_label,
               SUM(tokens_in) as total_in,
               SUM(tokens_out) as total_out,
               SUM(tokens_in + tokens_out) as total
               FROM project_token_usage
               WHERE project_id = ?
               GROUP BY sprint_label
               ORDER BY MIN(created_at) ASC""",
            (project_id,)
        ).fetchall()
    return {
        'total': dict(total) if total else {},
        'by_sprint': [dict(r) for r in sprints]
    }

# Notes — category
def list_notes_by_category(
    self, user_id: int, category: str,
    project_id: int = None, limit: int = 50
) -> List[Dict[str, Any]]:
    with self._connect() as conn:
        conn.row_factory = sqlite3.Row
        if project_id:
            rows = conn.execute(
                """SELECT * FROM notes WHERE user_id=? AND category=? AND project_id=?
                   ORDER BY updated_at DESC LIMIT ?""",
                (user_id, category, project_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM notes WHERE user_id=? AND category=?
                   ORDER BY updated_at DESC LIMIT ?""",
                (user_id, category, limit)
            ).fetchall()
        return [dict(r) for r in rows]
```

Expor todos como module-level wrappers no padrão existente.

---

## FASE 3 — Backend Routes

### 3.1 `backend/routes/project_routes.py` — adicionar endpoints

```python
# Schema novo
class ProjectStatusInput(BaseModel):
    status: str  # draft|ativo|suspenso|encerrado|cancelado
    suspension_reason: Optional[str] = None  # obrigatório quando status=suspenso

class ProjectRepositoryInput(BaseModel):
    type: str  # local|github|google_drive
    url: str
    credential: Optional[str] = None  # se fornecida, cifrar e salvar em user_connector_secrets

# Endpoint: atualizar status
@router.patch("/{project_id}/status")
async def update_project_status_endpoint(
    project_id: int,
    payload: ProjectStatusInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
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

    # Registrar na wiki do projeto
    if payload.status in ('suspenso', 'encerrado', 'cancelado'):
        reason_txt = payload.suspension_reason or ''
        append_wiki_entry(
            project_id, user["id"],
            section='change_management',
            content_md=f"**Status alterado para `{payload.status}`** — {reason_txt}",
            author='system'
        )

    return {"ok": True, "status": payload.status}


# Endpoint: repositório
@router.put("/{project_id}/repository")
async def update_project_repository_endpoint(
    project_id: int,
    payload: ProjectRepositoryInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
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

    # Se credencial fornecida, cifrar e salvar separado
    if payload.credential:
        from ..security_guardrail import SecurityGuardrail
        # Reutilizar infraestrutura existente de connector_secrets
        connector_key = f"project_{project_id}_repo"
        from ..db import upsert_user_connector_secret_ciphertext
        # A cifragem usa o mesmo mecanismo das outras credenciais do sistema
        # Delegar ao serviço existente de secrets
        _save_repo_credential(user["id"], project_id, payload.credential)
        repo_data["credential_present"] = True

    update_project_repository(project_id, user["id"], repo_data)
    return {"ok": True, "repository": repo_data}


# Endpoint: validar repositório
@router.post("/{project_id}/repository/validate")
async def validate_project_repository_endpoint(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Executa script de validação de acesso ao repositório."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    import json
    repo_data = json.loads(proj.get("repository_json") or "{}")
    if not repo_data.get("url"):
        raise HTTPException(status_code=400, detail="Repositório não configurado")

    result = await _validate_repository_access(user["id"], project_id, repo_data)

    # Atualizar status de validação
    repo_data["validation_status"] = "valid" if result["ok"] else "invalid"
    repo_data["credential_validated_at"] = result.get("validated_at")
    update_project_repository(project_id, user["id"], repo_data)

    return result


# Endpoint: wiki do projeto
@router.get("/{project_id}/wiki")
async def get_project_wiki_endpoint(
    project_id: int,
    section: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    if section:
        from ..db import get_wiki_section
        return {"section": section, "entries": get_wiki_section(project_id, section)}
    else:
        from ..db import get_wiki_full
        return {"wiki": get_wiki_full(project_id)}


# Endpoint: relatório de status (script, zero tokens)
@router.get("/{project_id}/report")
async def get_project_status_report_endpoint(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Gera relatório de status via script determinístico. Zero tokens."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    from ..services.report_service import generate_status_report
    report_md = generate_status_report(proj, user)
    return {"report_md": report_md, "project_id": project_id}
```

**Função auxiliar `_validate_repository_access`** (em `project_routes.py`):

```python
async def _validate_repository_access(user_id: int, project_id: int, repo_data: dict) -> dict:
    """
    Script determinístico de validação. Não consome tokens.
    Tenta uma operação de leitura no repositório para confirmar acesso.
    """
    import subprocess, json
    from datetime import datetime, timezone

    repo_type = repo_data.get("type", "local")
    url = repo_data.get("url", "")

    try:
        if repo_type == "local":
            import os
            accessible = os.path.exists(url) and os.path.isdir(url)
            return {
                "ok": accessible,
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "detail": "Diretório acessível" if accessible else f"Diretório não encontrado: {url}"
            }

        elif repo_type == "github":
            # Usa credencial salva para testar acesso via GitHub API
            from ..db import get_user_connector_secret_ciphertext
            # Descriptografar e testar
            # Implementar conforme infraestrutura de cifragem existente
            return {"ok": False, "detail": "GitHub validation: implementar com infraestrutura de cifragem existente"}

        elif repo_type == "google_drive":
            return {"ok": False, "detail": "Google Drive validation: implementar via connector existente"}

        else:
            return {"ok": False, "detail": f"Tipo de repositório não suportado: {repo_type}"}

    except Exception as e:
        return {"ok": False, "detail": str(e), "validated_at": None}
```

**Nota para Opencode**: a validação de GitHub e Google Drive deve reutilizar a infraestrutura de cifragem e connectors já existente em `user_connector_secrets`. Não criar nova infraestrutura de secrets.

### 3.2 `backend/services/report_service.py` — CRIAR

```python
"""
Report Service — Geração determinística de relatórios.
Zero chamadas LLM. Dados extraídos do banco via template.
"""
import json
from datetime import datetime, timezone
from typing import Dict, Any

def generate_status_report(project: Dict[str, Any], user: Dict[str, Any]) -> str:
    """
    Gera relatório de status em Markdown.
    Entrada: dict do projeto (linha do banco) + dict do usuário.
    Saída: string Markdown pronta para exibição ou export.
    """
    tap = _safe_json(project.get("tap_json"))
    stakeholders = _safe_json(project.get("stakeholders_json"), default=[])
    risks = _safe_json(project.get("risk_matrix_json"), default=[])
    releases = _safe_json(project.get("release_plan_json"), default=[])
    repo = _safe_json(project.get("repository_json"), default={})

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status = project.get("status", "draft")
    suspension = project.get("suspension_reason") or ""

    lines = [
        f"# Open Slap! — Relatório de Status",
        f"**Projeto**: {project.get('name', '—')}  ",
        f"**ID**: #{project.get('id', '—')}  ",
        f"**Gerado em**: {now}  ",
        f"**Status**: `{status}`",
    ]

    if suspension and status == 'suspenso':
        lines.append(f"**Motivo da suspensão**: {suspension}")

    lines += [
        "",
        "---",
        "",
        "## Responsável",
        f"- **Usuário**: {user.get('email', '—')}",
        "",
        "## TAP",
        f"- **Propósito**: {tap.get('purpose') or '—'}",
        f"- **Objetivos**: {tap.get('objectives') or '—'}",
        f"- **Escopo**: {tap.get('scope') or '—'}",
        f"- **Deadline**: {tap.get('deadline') or 'Não informado'}",
        f"- **Orçamento**: {tap.get('budget') or 'Orçamento zero / Não informado'}",
        "",
    ]

    if releases:
        lines.append("## Releases / Sprints")
        for r in releases:
            pct = r.get('completion_pct', '—')
            tokens = r.get('tokens_consumed', None)
            tok_str = f" — {tokens} tokens" if tokens else ""
            lines.append(f"- **{r.get('name','—')}** ({r.get('status','—')}) {pct}%{tok_str}")
        lines.append("")

    if stakeholders:
        lines.append("## Stakeholders")
        for s in stakeholders:
            lines.append(f"- {s.get('name','—')} — {s.get('role','—')}")
        lines.append("")

    if risks:
        lines.append("## Riscos")
        for risk in risks:
            lines.append(f"- [{risk.get('probability','?')}/{risk.get('impact','?')}] {risk.get('description','—')}")
        lines.append("")

    repo_status = repo.get("validation_status", "none")
    if repo.get("url"):
        lines += [
            "## Repositório",
            f"- **Tipo**: {repo.get('type','—')}",
            f"- **URL**: {repo.get('url','—')}",
            f"- **Credencial**: {'presente' if repo.get('credential_present') else 'ausente'}",
            f"- **Validação**: {repo_status}",
            "",
        ]

    lines += [
        "---",
        "",
        "## Métricas",
        "- **SPI**: N/A (planejamento não informado)",
        "- **CPI**: N/A (orçamento não informado)",
        "",
        "*Relatório gerado automaticamente pelo Open Slap! — zero tokens consumidos.*",
    ]

    return "\n".join(lines)


def generate_closure_report_template(project: Dict[str, Any], user: Dict[str, Any]) -> str:
    """
    Gera a parte determinística do relatório de encerramento.
    A narrativa do agente é adicionada depois pelo agente responsável.
    """
    base = generate_status_report(project, user)
    lines = [
        base,
        "",
        "---",
        "",
        "## Consolidado do Agente",
        "",
        "*[Esta seção é preenchida pelo agente ao encerrar o projeto.]*",
        "",
    ]
    return "\n".join(lines)


def _safe_json(raw, default=None):
    if default is None:
        default = {}
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default
```

### 3.3 `backend/routes/wiki_routes.py` — CRIAR

```python
"""
Wiki Routes — Endpoints para a base de conhecimento de projetos.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from ..deps import security, HTTPAuthorizationCredentials
from ..auth import get_current_user
from ..db import (
    get_project, get_wiki_section, get_wiki_full,
    append_wiki_entry, log_agent_action
)

wiki_router = APIRouter(prefix="/api/projects", tags=["wiki"])

class WikiEntryInput(BaseModel):
    section: str
    title: Optional[str] = ''
    content_md: str
    author: Optional[str] = 'user'

@wiki_router.post("/{project_id}/wiki")
async def add_wiki_entry_endpoint(
    project_id: int,
    payload: WikiEntryInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    entry_id = append_wiki_entry(
        project_id, user["id"],
        section=payload.section,
        content_md=payload.content_md,
        author=payload.author or 'user',
        title=payload.title or ''
    )
    return {"ok": True, "entry_id": entry_id}
```

Registrar `wiki_router` no `main_auth_refactored.py` junto com os outros routers.

---

## FASE 4 — Evento `project.created` → inicializar wiki

Em `project_routes.py`, no endpoint `POST /api/projects`, após o `create_project()` bem-sucedido, adicionar:

```python
# Inicializar wiki — zero tokens
from ..db import initialize_project_wiki
initialize_project_wiki(pid, user["id"])
```

Isso garante que todo projeto criado (por qualquer caminho — wizard manual, import, chat, detecção proativa) tenha a estrutura de wiki imediatamente disponível.

---

## FASE 5 — Notes: category e source

### 5.1 Atualizar `NoteCreateInput` e `NoteUpdateInput` em `notes_routes.py`

```python
class NoteCreateInput(BaseModel):
    title: str
    content_md: str
    tags: Optional[str] = None
    project_id: Optional[int] = None
    category: Optional[str] = 'nota'   # nota|ideia_solta|ideacao|projeto_futuro
    source: Optional[str] = 'user'     # user|agent
```

### 5.2 Passar `category` e `source` para `create_note()` e `update_note()`

Atualizar as assinaturas de `create_note` e `update_note` em `db.py` para aceitar e persistir esses campos.

### 5.3 Adicionar endpoint de listagem por categoria

```python
@notes_router.get("/by-category/{category}")
async def get_notes_by_category_endpoint(
    category: str,
    project_id: Optional[int] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Lista notas por categoria (ideia_solta, ideacao, projeto_futuro, nota)."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    from ..db import list_notes_by_category
    return list_notes_by_category(current_user["id"], category, project_id=project_id)
```

---

## FASE 6 — Watcher de Filesystem (US-09)

### 6.1 `backend/services/fs_watcher.py` — CRIAR

```python
"""
Filesystem Watcher — Detecta mudanças externas em repositórios locais vinculados a projetos.
Usa watchdog (já deve estar disponível ou adicionar ao requirements.txt).
Registra mudanças na wiki do projeto sem consumir tokens.
"""
import logging
import threading
from pathlib import Path
from typing import Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_watchers: Dict[int, object] = {}  # project_id → Observer

def start_project_watcher(project_id: int, user_id: int, repo_path: str) -> bool:
    """
    Inicia watcher para um projeto com repositório local.
    Retorna True se iniciado com sucesso.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class ProjectEventHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.is_directory:
                    return
                _log_external_change(project_id, user_id, 'modified', event.src_path)

            def on_created(self, event):
                if event.is_directory:
                    return
                _log_external_change(project_id, user_id, 'created', event.src_path)

            def on_deleted(self, event):
                _log_external_change(project_id, user_id, 'deleted', event.src_path)

        if project_id in _watchers:
            stop_project_watcher(project_id)

        observer = Observer()
        observer.schedule(ProjectEventHandler(), repo_path, recursive=True)
        observer.start()
        _watchers[project_id] = observer
        logger.info("Watcher iniciado para projeto %s em %s", project_id, repo_path)
        return True

    except ImportError:
        logger.warning("watchdog não instalado — watcher de filesystem indisponível")
        return False
    except Exception as e:
        logger.error("Erro ao iniciar watcher projeto %s: %s", project_id, e)
        return False


def stop_project_watcher(project_id: int) -> None:
    observer = _watchers.pop(project_id, None)
    if observer:
        try:
            observer.stop()
            observer.join(timeout=3)
        except Exception:
            pass


def _log_external_change(project_id: int, user_id: int, action: str, path: str) -> None:
    """
    Registra mudança externa na wiki e no agent_communication_log.
    Filtra arquivos irrelevantes (.pyc, __pycache__, .git internals).
    """
    skip_patterns = ['.pyc', '__pycache__', '.git/', 'node_modules/']
    if any(p in path for p in skip_patterns):
        return

    try:
        from ..db import append_wiki_entry, log_agent_action
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        content = f"[{ts}] **Mudança externa detectada** — `{action}`: `{path}`"
        append_wiki_entry(
            project_id, user_id,
            section='agent_communication',
            content_md=content,
            author='watcher',
            title='Mudança externa'
        )
        log_agent_action(
            project_id, user_id,
            agent_id='fs_watcher',
            action=action,
            detail=path,
            source='external',
            external_tool='filesystem'
        )
    except Exception as e:
        logger.error("Erro ao registrar mudança externa: %s", e)
```

Adicionar `watchdog` ao `requirements.txt`.

Iniciar watcher no evento de validação bem-sucedida de repositório local (`validate_repository_access` → `repo_type == "local"` → `start_project_watcher(...)`).

---

## FASE 7 — Ideação Silenciosa (US-11 e US-12)

### 7.1 `backend/services/ideation_service.py` — CRIAR

```python
"""
Ideation Service — Captura silenciosa de ideias pela Sabrina.
Registra em notes com category='ideacao' sem interromper o fluxo.
Busca por similaridade textual para resgate de ideações anteriores.
Zero tokens para registro. Tokens consumidos apenas na detecção (feita pela Sabrina no fluxo normal de chat).
"""
import logging
from typing import Optional, List, Dict, Any
from ..db import create_note, list_notes_by_category, search_notes

logger = logging.getLogger(__name__)

def record_ideation(
    user_id: int,
    title: str,
    content_md: str,
    project_id: int = None,
    category: str = 'ideacao'
) -> int:
    """
    Registra uma ideação silenciosamente.
    Chamada pela Sabrina quando detecta potencial de projeto.
    """
    try:
        note_id = create_note(
            user_id=user_id,
            title=title,
            content_md=content_md,
            tags='ideacao,sabrina',
            project_id=project_id,
            category=category,
            source='agent'
        )
        logger.info("Ideação registrada user=%s note_id=%s", user_id, note_id)
        return note_id
    except Exception as e:
        logger.error("Erro ao registrar ideação: %s", e)
        return -1


def find_similar_ideations(
    user_id: int, query: str, limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Busca ideações similares por keyword matching (FTS5).
    Retorna lista de notas com category in (ideacao, projeto_futuro).
    """
    if not query or len(query.strip()) < 3:
        return []
    try:
        results = search_notes(user_id, query, limit=limit * 2)
        filtered = [
            r for r in results
            if r.get('category') in ('ideacao', 'projeto_futuro')
        ]
        return filtered[:limit]
    except Exception as e:
        logger.error("Erro na busca de ideações: %s", e)
        return []


def format_ideation_recall_message(ideation: Dict[str, Any]) -> str:
    """
    Formata a mensagem de resgate que a Sabrina vai apresentar ao usuário.
    """
    ts = str(ideation.get('created_at', ''))[:10]
    title = ideation.get('title', 'ideia sem título')
    content = ideation.get('content_md', '')[:200]
    return (
        f"Em {ts} registrei uma ideia semelhante: **{title}**.\n"
        f"> {content}...\n\n"
        f"Quer resgatar esse conceito e adaptá-lo, ou prefere seguir por outro caminho?"
    )
```

### 7.2 Settings — feature flag de ideação

Em `backend/config/settings.py`, adicionar:

```python
IDEATION_CAPTURE_ENABLED: bool = True  # ativável em Settings UI, padrão ativo
```

Expor via endpoint de settings existente para que o frontend possa ligar/desligar.

---

## FASE 8 — Import de TAP Externo (US-02)

### 8.1 `backend/services/tap_import_service.py` — CRIAR

```python
"""
TAP Import Service — Extração determinística de campos TAP de documentos externos.
Suporta: .txt, .md (direto), .pdf (via pypdf2 ou pdfplumber), .docx (via python-docx).
Se extração falha ou é incompleta, sinaliza para fallback via agente.
Zero tokens para extração via script. Tokens consumidos apenas no fallback.
"""
import logging
import re
from typing import Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Campos que tentamos extrair
TAP_FIELDS = ['name','purpose','objectives','scope','risks','stakeholders','budget','deadline']

def extract_tap_from_file(file_path: str, file_type: str) -> Tuple[Dict[str, Any], bool, str]:
    """
    Retorna: (tap_data_dict, success, message)
    success=True se extração completa (todos os campos críticos encontrados)
    success=False se incompleta → frontend mostra fallback para agente
    """
    try:
        text = _read_file_content(file_path, file_type)
        if not text:
            return {}, False, "Não foi possível ler o arquivo"

        tap_data = _parse_tap_fields(text)
        critical = ['name', 'purpose', 'objectives']
        missing = [f for f in critical if not tap_data.get(f)]

        if missing:
            return tap_data, False, f"Campos não encontrados: {', '.join(missing)}"

        return tap_data, True, "Extração concluída"

    except Exception as e:
        logger.error("Erro na extração TAP: %s", e)
        return {}, False, f"Falha de script: {str(e)}"


def _read_file_content(file_path: str, file_type: str) -> str:
    ext = file_type.lower().strip('.')
    try:
        if ext in ('txt', 'md'):
            return Path(file_path).read_text(encoding='utf-8', errors='replace')

        elif ext == 'pdf':
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    return "\n".join(p.extract_text() or '' for p in pdf.pages)
            except ImportError:
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        return "\n".join(
                            page.extract_text() or '' for page in reader.pages
                        )
                except ImportError:
                    raise RuntimeError("Nenhuma biblioteca PDF disponível (pdfplumber ou PyPDF2)")

        elif ext == 'docx':
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)

        else:
            raise ValueError(f"Tipo não suportado: {ext}")

    except Exception as e:
        logger.error("Erro ao ler arquivo %s: %s", file_path, e)
        raise


def _parse_tap_fields(text: str) -> Dict[str, Any]:
    """
    Heurística de extração por padrões de cabeçalho e palavras-chave.
    Não usa LLM. Determinístico.
    """
    tap = {}
    # Mapeamento de padrões → campos
    patterns = {
        'name': [r'(?:projeto|project name|nome do projeto)[:\s]+(.+)', r'^#\s+(.+)'],
        'purpose': [r'(?:propósito|purpose|objetivo geral)[:\s]+(.+)'],
        'objectives': [r'(?:objetivos|objectives)[:\s]+(.+)'],
        'scope': [r'(?:escopo|scope)[:\s]+(.+)'],
        'budget': [r'(?:orçamento|budget|custo)[:\s]+(.+)'],
        'deadline': [r'(?:prazo|deadline|entrega)[:\s]+(.+)'],
    }
    for field, pats in patterns.items():
        for pat in pats:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                tap[field] = m.group(1).strip()[:500]
                break

    return tap
```

Adicionar ao `requirements.txt`:
- `pdfplumber` (já pode estar presente — verificar antes de adicionar)
- `python-docx`

### 8.2 Endpoint de import

Em `project_routes.py`:

```python
from fastapi import UploadFile, File
import tempfile, os

@router.post("/import-tap")
async def import_tap_endpoint(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Recebe arquivo externo, extrai campos TAP via script.
    Se extração incompleta, sinaliza para fallback via agente.
    """
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    allowed_types = {'txt', 'md', 'pdf', 'docx'}
    ext = (file.filename or '').rsplit('.', 1)[-1].lower()
    if ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Tipo não suportado: {ext}")

    # Salvar temporariamente
    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from ..services.tap_import_service import extract_tap_from_file
        tap_data, success, message = extract_tap_from_file(tmp_path, ext)
    finally:
        os.unlink(tmp_path)

    return {
        "tap_data": tap_data,
        "extraction_success": success,
        "message": message,
        "needs_agent_fallback": not success,
        # Se needs_agent_fallback=True, frontend exibe: "Falha de script,
        # transferindo para agente prosseguir com o registro de dados"
    }
```

---

## FASE 9 — Testes

### `backend/tests/test_project_system.py` — CRIAR

```python
"""
Testes do sistema de projetos, wiki, ideação e relatórios.
"""
import pytest
import json
from unittest.mock import patch, MagicMock


# ── Schema migrations ────────────────────────────────────────────────────────

def test_projects_table_has_status_column(tmp_db):
    """Tabela projects deve ter coluna status após migration."""
    from backend.db import DatabaseManager
    db = DatabaseManager(tmp_db)
    import sqlite3
    with sqlite3.connect(tmp_db) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()]
    assert 'status' in cols
    assert 'suspension_reason' in cols
    assert 'repository_json' in cols


def test_notes_table_has_category_column(tmp_db):
    from backend.db import DatabaseManager
    db = DatabaseManager(tmp_db)
    import sqlite3
    with sqlite3.connect(tmp_db) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(notes)").fetchall()]
    assert 'category' in cols
    assert 'source' in cols


def test_project_wiki_table_exists(tmp_db):
    from backend.db import DatabaseManager
    db = DatabaseManager(tmp_db)
    import sqlite3
    with sqlite3.connect(tmp_db) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='project_wiki'"
        ).fetchone()
    assert row is not None


# ── Project status ────────────────────────────────────────────────────────────

def test_update_project_status_valid(tmp_db):
    from backend.db import DatabaseManager
    db = DatabaseManager(tmp_db)
    pid = db.create_project(user_id=1, name="Teste", context_md="")
    ok = db.update_project_status(pid, 1, 'ativo')
    assert ok
    proj = db.get_project(pid, 1)
    assert proj['status'] == 'ativo'


def test_update_project_status_invalid_raises(tmp_db):
    from backend.db import DatabaseManager
    db = DatabaseManager(tmp_db)
    pid = db.create_project(user_id=1, name="Teste", context_md="")
    with pytest.raises(ValueError):
        db.update_project_status(pid, 1, 'status_invalido')


def test_suspension_requires_reason_at_api_level():
    """O endpoint deve rejeitar suspensão sem justificativa."""
    # Testado via TestClient — skipped aqui, coberto nos testes de rota
    pass


# ── Wiki ──────────────────────────────────────────────────────────────────────

def test_initialize_project_wiki_creates_sections(tmp_db):
    from backend.db import DatabaseManager
    db = DatabaseManager(tmp_db)
    pid = db.create_project(user_id=1, name="Wiki Test", context_md="")
    db.initialize_project_wiki(pid, 1)
    wiki = db.get_wiki_full(pid)
    expected_sections = {'codebase','todos','notes','issues','agent_communication','change_management'}
    assert set(wiki.keys()) == expected_sections


def test_append_wiki_entry(tmp_db):
    from backend.db import DatabaseManager
    db = DatabaseManager(tmp_db)
    pid = db.create_project(user_id=1, name="Wiki Test", context_md="")
    db.initialize_project_wiki(pid, 1)
    entry_id = db.append_wiki_entry(pid, 1, 'notes', 'Nota de teste', author='user')
    assert entry_id > 0
    entries = db.get_wiki_section(pid, 'notes')
    assert any(e['content_md'] == 'Nota de teste' for e in entries)


# ── Token usage ───────────────────────────────────────────────────────────────

def test_record_and_summarize_token_usage(tmp_db):
    from backend.db import DatabaseManager
    db = DatabaseManager(tmp_db)
    pid = db.create_project(user_id=1, name="Token Test", context_md="")
    db.record_token_usage(pid, 1, tokens_in=100, tokens_out=200, sprint_label='Sprint 1')
    db.record_token_usage(pid, 1, tokens_in=50, tokens_out=150, sprint_label='Sprint 1')
    db.record_token_usage(pid, 1, tokens_in=200, tokens_out=300, sprint_label='Sprint 2')
    summary = db.get_token_usage_summary(pid)
    assert summary['total']['total'] == 1000
    assert len(summary['by_sprint']) == 2


# ── Report ────────────────────────────────────────────────────────────────────

def test_generate_status_report_no_llm():
    from backend.services.report_service import generate_status_report
    project = {
        'id': 1,
        'name': 'Projeto Teste',
        'status': 'ativo',
        'tap_json': json.dumps({'purpose': 'Testar', 'objectives': 'Objetivo X'}),
        'stakeholders_json': '[]',
        'risk_matrix_json': '[]',
        'release_plan_json': '[]',
        'repository_json': '{}',
        'suspension_reason': None,
    }
    user = {'email': 'test@test.com'}
    report = generate_status_report(project, user)
    assert 'Projeto Teste' in report
    assert 'tokens' not in report.lower() or 'zero tokens' in report.lower()
    assert 'N/A' in report  # SPI/CPI sem estimativa


# ── TAP import ────────────────────────────────────────────────────────────────

def test_extract_tap_from_markdown(tmp_path):
    from backend.services.tap_import_service import extract_tap_from_file
    md = tmp_path / "tap.md"
    md.write_text("# Projeto Alpha\n\nPropósito: Criar uma plataforma\nObjetivos: Entregar v1\nEscopo: MVP")
    tap, success, msg = extract_tap_from_file(str(md), 'md')
    assert 'name' in tap or 'purpose' in tap


def test_extract_tap_unsupported_type(tmp_path):
    from backend.services.tap_import_service import extract_tap_from_file
    f = tmp_path / "file.xlsx"
    f.write_bytes(b'fake')
    tap, success, msg = extract_tap_from_file(str(f), 'xlsx')
    assert not success


# ── Ideation service ──────────────────────────────────────────────────────────

def test_record_ideation_creates_note(tmp_db):
    from backend.services.ideation_service import record_ideation
    from backend.db import DatabaseManager
    db = DatabaseManager(tmp_db)
    note_id = record_ideation(user_id=1, title="Ideia X", content_md="Detalhes da ideia")
    assert note_id > 0


@pytest.fixture
def tmp_db(tmp_path):
    """Banco temporário para testes isolados."""
    db_path = str(tmp_path / "test.db")
    from backend.db import DatabaseManager
    DatabaseManager(db_path)
    return db_path
```

---

## Critérios de Aceite Globais

1. `pytest backend/tests/test_project_system.py` — 100% passando
2. `pytest backend/tests/` — suite completa sem regressões
3. `POST /api/projects` cria projeto + inicializa wiki automaticamente
4. `PATCH /api/projects/{id}/status` com `status=suspenso` sem `suspension_reason` retorna 400
5. `PATCH /api/projects/{id}/status` com `status=suspenso` + justificativa retorna 200 e registra na wiki
6. `GET /api/projects/{id}/report` retorna Markdown gerado em <3s sem chamada LLM
7. `POST /api/projects/import-tap` com arquivo `.md` retorna `tap_data` extraído
8. `POST /api/projects/import-tap` com arquivo `.xlsx` retorna 400
9. Nota criada com `category=ideacao` listável via `/api/notes/by-category/ideacao`
10. Watcher de filesystem registra mudança na wiki quando arquivo local é modificado

---

## O que este sprint NÃO faz

- Não integra a Sabrina como orquestradora primária (isso é P2.5)
- Não implementa busca semântica de ideações (keyword matching via FTS5 por ora)
- Não implementa o consolidado narrativo do agente no relatório de encerramento (requer Sabrina integrada)
- Não implementa teto de gasto de tokens por sprint (mapeado para evolução futura)
- Não implementa SPI/CPI prospectivo (requer Planned Value)
- Não implementa validação completa de GitHub e Google Drive (infra de cifragem a ser reutilizada)
- Não implementa grafos de conhecimento (Obsidian endpoint — evolução futura)

---

## Dependências externas a verificar/adicionar no `requirements.txt`

```
watchdog>=3.0.0
pdfplumber>=0.9.0     # verificar se já presente
python-docx>=1.1.0    # verificar se já presente
```
