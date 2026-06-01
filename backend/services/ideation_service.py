"""
Ideation Service — Captura silenciosa de ideias pela Sabrina.
Registra em notes com category='ideacao' sem interromper o fluxo.
Zero tokens para registro.
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
    """Registra uma ideação silenciosamente."""
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
    """Busca ideações similares por keyword matching (FTS5)."""
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
    """Formata mensagem de resgate para apresentar ao usuário."""
    ts = str(ideation.get('created_at', ''))[:10]
    title = ideation.get('title', 'ideia sem título')
    content = ideation.get('content_md', '')[:200]
    return (
        f"Em {ts} registrei uma ideia semelhante: **{title}**.\n"
        f"> {content}...\n\n"
        f"Quer resgatar esse conceito e adaptá-lo, ou prefere seguir por outro caminho?"
    )
