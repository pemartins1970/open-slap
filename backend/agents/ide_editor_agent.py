from typing import Dict, Any, List
from .base import BaseAgent, agent_registry

IDE_EDITOR_SYSTEM_PROMPT = """
Você é o Editor de IDE do Open Slap!. Sua função é editar código, refatorar, navegar na estrutura
do projeto e realizar alterações precisas nos arquivos do sistema.

Competências principais:
- Editar arquivos de código com precisão (linhas específicas, blocos, funções)
- Refatorar código mantendo a semântica e estilo do projeto
- Navegar na estrutura de diretórios e entender a organização do código
- Identificar e corrigir problemas de sintaxe, estilo e tipagem
- Renomear símbolos (variáveis, funções, classes) em todo o projeto
- Mover e reorganizar arquivos mantendo imports e referências
- Garantir que edições respeitem as convenções do projeto

Linguagens que domina:
- Python, TypeScript/JavaScript, JSX, CSS/SCSS, SQL, YAML, JSON, Markdown

Regras de resposta:
- Responda sempre no mesmo idioma utilizado pelo usuário na mensagem recebida.
- Seja preciso: mostre o diff ou a linha exata antes de editar.
- Nunca edite sem entender o contexto do arquivo primeiro.
- Quando refatorar, explique o que mudou e por quê.
- Respeite o estilo de código existente (indentação, naming, padrões).
- Se uma edição for complexa, quebre em etapas e confirme cada uma.
"""

IDE_EDITOR_SKILLS = [
    {
        "name": "edit_file",
        "description": "Edita linhas específicas de um arquivo",
        "input_schema": {
            "path": "string (caminho do arquivo)",
            "changes": "array (lista de substituições: oldString, newString)",
            "description": "string (resumo do que está sendo alterado)"
        },
        "output_schema": {
            "path": "string (arquivo alterado)",
            "changes_made": "number (quantidade de alterações)",
            "summary": "string (resumo das alterações)"
        }
    },
    {
        "name": "refactor_symbol",
        "description": "Renomeia símbolo em todo o projeto",
        "input_schema": {
            "symbol": "string (nome atual do símbolo)",
            "new_name": "string (novo nome)",
            "scope": "string (escopo: arquivo, diretório ou projeto todo)"
        },
        "output_schema": {
            "renamed_in": "array (arquivos alterados)",
            "total_changes": "number (total de ocorrências renomeadas)"
        }
    },
    {
        "name": "review_syntax",
        "description": "Verifica sintaxe e estilo de um arquivo",
        "input_schema": {
            "path": "string (caminho do arquivo)",
            "language": "string (linguagem do arquivo)"
        },
        "output_schema": {
            "valid": "boolean (sintaxe válida)",
            "issues": "array (problemas encontrados com linha e tipo)",
            "suggestions": "array (sugestões de correção)"
        }
    },
]


class IDEEditorAgent(BaseAgent):
    name = "ide_editor"
    description = "Editor de IDE — edição, refatoração e navegação em código"
    system_prompt = IDE_EDITOR_SYSTEM_PROMPT
    skills = IDE_EDITOR_SKILLS


agent_registry.register(IDEEditorAgent())
