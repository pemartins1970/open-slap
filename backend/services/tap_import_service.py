"""
TAP Import Service — Extração determinística de campos TAP de documentos externos.
Suporta: .txt, .md (direto), .pdf (via pdfplumber), .docx (via python-docx).
Zero tokens para extração via script.
"""
import logging
import re
from typing import Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

TAP_FIELDS = ['name', 'purpose', 'objectives', 'scope', 'risks', 'stakeholders', 'budget', 'deadline']


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
    """Heurística de extração por padrões de cabeçalho e palavras-chave."""
    tap = {}
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
