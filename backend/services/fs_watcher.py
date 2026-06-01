"""
Filesystem Watcher — Detecta mudanças externas em repositórios locais vinculados a projetos.
Usa watchdog. Registra mudanças na wiki do projeto sem consumir tokens.
"""
import logging
import threading
from pathlib import Path
from typing import Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_watchers: Dict[int, object] = {}
_lock = threading.Lock()


def start_project_watcher(project_id: int, user_id: int, repo_path: str) -> bool:
    """Inicia watcher para um projeto com repositório local."""
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

        with _lock:
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
    with _lock:
        observer = _watchers.pop(project_id, None)
    if observer:
        try:
            observer.stop()
            observer.join(timeout=3)
        except Exception:
            pass


def _log_external_change(project_id: int, user_id: int, action: str, path: str) -> None:
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
