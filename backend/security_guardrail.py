"""
Security Guardrail - B.E.N. 2.0 (Behavioral Ethics Network)
Implementação de heurísticas robustas para sanitização de comandos OS, detecção de prompt injection e execução de código.
"""

import re
import logging
import unicodedata
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Mapa de homoglifos Cyrillic → ASCII (cobre os mais comuns usados em ataques evasivos)
_HOMOGLYPH_MAP = {
    '\u0430': 'a',  # Cyrillic а → a
    '\u0435': 'e',  # Cyrillic е → e
    '\u0456': 'i',  # Cyrillic і → i
    '\u043e': 'o',  # Cyrillic о → o
    '\u0440': 'r',  # Cyrillic р → r
    '\u0441': 'c',  # Cyrillic с → c
    '\u0445': 'x',  # Cyrillic х → x
    '\u0443': 'y',  # Cyrillic у → y
    '\u0455': 's',  # Cyrillic ѕ → s
    '\u0501': 'd',  # Cyrillic ԁ → d
}


def normalize_text(text: str) -> str:
    """
    Normaliza texto para detecção consistente de ataques evasivos.
    Cobre: unicode homoglifos, leet speak, espaçamento excessivo.
    """
    # 1. Substituir homoglifos Cyrillic conhecidos antes do NFKD
    for homoglyph, latin in _HOMOGLYPH_MAP.items():
        text = text.replace(homoglyph, latin)
    # 2. Normalizar unicode NFKD → ASCII (cobre outros homoglifos)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    # 3. Detectar letras isoladas separadas por espaço simples e juntar por grupo
    #    (cobre "i g n o r e   p r e v i o u s" → "ignore previous")
    #    Grupos de palavras são separados por 2+ espaços; letras dentro do grupo por 1 espaço
    parts = re.split(r' {2,}', text)
    text = ' '.join(
        re.sub(r'^(\w)(?: (\w))+$', lambda m: m.group(0).replace(' ', ''), part)
        for part in parts
    )
    # 4. Colapsar espaços extras restantes
    text = re.sub(r'\s+', ' ', text).strip()
    # 5. Leet speak → texto normal
    leet_map = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b'}
    for leet, normal in leet_map.items():
        text = text.replace(leet, normal)
    return text.lower()

# Heurísticas de Prompt Injection (Regex e Substrings)
PROMPT_INJECTION_PATTERNS: List[re.Pattern] = [
    # Diretivas diretas para ignorar instruções anteriores
    re.compile(r"\b(ignore|ignorar)\b.*\b(previous|anterior(es)?)\b", re.IGNORECASE),
    re.compile(r"\b(disregard|desconsiderar)\b.*\b(instructions|instru(c|ç)ões)\b", re.IGNORECASE),
    re.compile(r"\b(forget|esquecer)\b.*\b(guidelines|rules|regras|diretrizes)\b", re.IGNORECASE),
    # Modos de override / jailbreak (ambas as ordens para developer mode + unrestricted)
    re.compile(r"\b(system\s+override|sobrescrever\s+sistema)\b", re.IGNORECASE),
    re.compile(r"\b(jailbreak|jail-break|dan\s+mode|modo\s+dan)\b", re.IGNORECASE),
    re.compile(r"\b(developer\s+mode|modo\s+desenvolvedor)\b.*\b(unrestricted|sem\s+restri(c|ç)ões)\b", re.IGNORECASE),
    re.compile(r"\b(unrestricted|sem\s+restri(c|ç)ões)\b.*\b(developer\s+mode|modo\s+desenvolvedor)\b", re.IGNORECASE),
    # Vazamento/Leitura de prompt do sistema
    re.compile(r"\b(print|mostrar|revelar|exibir|show|dump)\b.*\b(system\s+prompt|prompt\s+do\s+sistema|system\s+instructions)\b", re.IGNORECASE),
    re.compile(r"\b(what\s+is\s+your\s+system\s+prompt|qual\s+é\s+o\s+seu\s+prompt)\b", re.IGNORECASE),
    # Mudança de persona maliciosa
    re.compile(r"\byou\s+are\s+now\s+a\b.*\b(unrestricted|sem\s+limites|malicious|malicioso)\b", re.IGNORECASE),
    # Multilíngue: Espanhol
    re.compile(r"\b(olvidar|ignorar)\b.*\b(reglas|instrucciones|directrices)\b", re.IGNORECASE),
    # Multilíngue: Francês (inclui conjugações oublier/oubliez e ignorer/ignorez; règles → regles após NFKD)
    re.compile(r"\b(oublier|oubliez|ignorer|ignorez)\b.*\b(instructions|regles|directives)\b", re.IGNORECASE),
]

# Heurísticas de Comandos OS Maliciosos / Destrutivos
BLOCKED_COMMAND_PATTERNS: List[re.Pattern] = [
    # Deleção recursiva ou destrutiva
    re.compile(r"\brm\s+-(rf|fr|r|f)\b", re.IGNORECASE),
    re.compile(r"\b(rmdir|rd)\b.*(?:\s|^|/)(s|q)\b", re.IGNORECASE),
    re.compile(r"\bdel\b.*(?:\s|^|/)(f|s|q)\b", re.IGNORECASE),
    # Formatação e particionamento
    re.compile(r"\bformat\b.*\b(volume|[A-Z]:)", re.IGNORECASE),
    re.compile(r"\bdiskpart\b", re.IGNORECASE),
    re.compile(r"\bmkfs\b", re.IGNORECASE),
    # Modificações de boot/registro perigosas
    re.compile(r"\bbcdedit\b", re.IGNORECASE),
    re.compile(r"\breg\s+delete\b", re.IGNORECASE),
    # Desabilitação de segurança (Firewall, Windows Defender)
    re.compile(r"\bnetsh\s+advfirewall\s+set\b", re.IGNORECASE),
    re.compile(r"\bSet-MpPreference\b.*(?:\s|^)-(DisableRealtimeMonitoring|DisableIOAVProtection|DisableBehaviorMonitoring|Disable)\b", re.IGNORECASE),
    # Desligamento / Reinicialização remota ou forçada
    re.compile(r"\bshutdown\b.*(?:\s|^|/)(s|r|g|h|p|f)\b", re.IGNORECASE),
    re.compile(r"\b(restart-computer|stop-computer)\b", re.IGNORECASE),
    # Criação não autorizada de administradores
    re.compile(r"\bnet\s+user\b.*\b/add\b", re.IGNORECASE),
    re.compile(r"\bnet\s+localgroup\b.*\b/add\b", re.IGNORECASE)
]

# Heurísticas de Python / Scripts Inseguros
BLOCKED_CODE_PATTERNS: List[re.Pattern] = [
    # Execução oculta ou dinâmica perigosa
    re.compile(r"\b(eval|exec)\b\s*\(\s*.*(base64|b64decode|getattr|__import__|globals|locals)\b", re.IGNORECASE),
    # Criação de socket reverso ou escuta (Shell reverso)
    re.compile(r"\bsocket\.socket\b.*\bconnect\b.*(cmd\.exe|/bin/sh|/bin/bash)", re.IGNORECASE | re.DOTALL),
    # Tentativas diretas de download e execução remota maliciosa
    re.compile(r"\b(urllib|requests|urllib2|wget|curl)\b.*\b(exec|eval|system|popen)\b", re.IGNORECASE | re.DOTALL),
    # Importações ocultas via dunder methods
    re.compile(r"__import__\s*\(\s*['\"](os|subprocess|socket|requests)['\"]\s*\)\s*\.(system|popen|Popen|connect)", re.IGNORECASE)
]

class SecurityGuardrail:
    """
    B.E.N. 2.0 (Behavioral Ethics Network)
    Filtro de segurança e conformidade para o ecossistema Open Slap!
    """

    @staticmethod
    def evaluate(message: str) -> Dict[str, Any]:
        """
        Avalia uma mensagem de chat do usuário contra tentativas de Prompt Injection
        e intenções de comandos destrutivos.
        """
        if not message or not message.strip():
            return {
                "action": "block",
                "reason": "Mensagem vazia ou inválida",
                "severity": "low",
                "confidence": 1.0
            }

        # Normalizar para detectar variações evasivas (leet speak, homoglifos, espaçamento)
        message_normalized = normalize_text(message)

        # 1. Verificar Prompt Injection (usar texto normalizado)
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(message_normalized):
                logger.warning(f"B.E.N. 2.0 detectou tentativa de Prompt Injection: {pattern.pattern}")
                return {
                    "action": "block",
                    "reason": "Tentativa de injeção de prompt ou alteração de diretrizes do sistema bloqueada.",
                    "severity": "high",
                    "confidence": 0.98
                }

        # 2. Verificar Comandos Destrutivos Diretos (Heurística de intenção) (usar texto normalizado)
        for pattern in BLOCKED_COMMAND_PATTERNS:
            if pattern.search(message_normalized):
                logger.warning(f"B.E.N. 2.0 detectou intenção de comando destrutivo no prompt: {pattern.pattern}")
                return {
                    "action": "block",
                    "reason": "O prompt contém solicitações para executar comandos potencialmente destrutivos ou de configuração restrita.",
                    "severity": "high",
                    "confidence": 0.95
                }

        # 3. Verificar Padrões de Code Injection no prompt (mensagem de chat)
        for pattern in BLOCKED_CODE_PATTERNS:
            if pattern.search(message):
                logger.warning(f"B.E.N. 2.0 detectou padrão de code injection no prompt: {pattern.pattern}")
                return {
                    "action": "block",
                    "reason": "Padrão de código malicioso detectado no prompt.",
                    "severity": "high",
                    "confidence": 0.95
                }

        return {
            "action": "allow",
            "reason": "Mensagem aprovada nas políticas de segurança",
            "severity": "none",
            "confidence": 0.99
        }

    @staticmethod
    def validate_code_execution(code: str) -> Dict[str, Any]:
        """
        Avalia código de automação/ferramenta (Python ou scripts) para evitar comandos 
        maliciosos, backdoors, reverse shells ou deleção arbitrária do sistema.
        """
        if not code or not code.strip():
            return {
                "action": "block",
                "reason": "Conteúdo de código vazio",
                "severity": "low"
            }

        # 1. Verificar Comandos OS Perigosos dentro do script
        for pattern in BLOCKED_COMMAND_PATTERNS:
            if pattern.search(code):
                logger.warning(f"B.E.N. 2.0 bloqueou execução de código contendo comando perigoso: {pattern.pattern}")
                return {
                    "action": "block",
                    "reason": f"Uso de comandos de sistema restritos detectado: {pattern.pattern}",
                    "severity": "high"
                }

        # 2. Verificar Padrões Maliciosos específicos em Scripts (Reverse shells, dynamic imports perigosos)
        for pattern in BLOCKED_CODE_PATTERNS:
            if pattern.search(code):
                logger.warning(f"B.E.N. 2.0 detectou padrão de código malicioso estrutural: {pattern.pattern}")
                return {
                    "action": "block",
                    "reason": "Execução bloqueada devido a padrões suspeitos de rede ou evasão de sandbox no código.",
                    "severity": "high"
                }

        return {
            "action": "allow",
            "reason": "Código validado com sucesso",
            "severity": "none"
        }
