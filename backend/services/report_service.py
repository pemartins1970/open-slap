import json
from datetime import datetime, timezone
from typing import Dict, Any

def generate_status_report(project: Dict[str, Any], user: Dict[str, Any]) -> str:
    """
    Gera relatório de status em Markdown.
    Entrada: dict do projeto (linha do banco) + dict do usuário.
    Saída: string Markdown pronta para exibição ou export.
    Zero chamadas LLM.
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
    """Gera a parte determinística do relatório de encerramento."""
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
