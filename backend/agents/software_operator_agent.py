from typing import Dict, Any, List
from .base import BaseAgent, agent_registry

SOFTWARE_OPERATOR_SYSTEM_PROMPT = """
Você é o Operador de Software do Open Slap!. Sua função é executar comandos, scripts, automações
e interagir com o sistema de arquivos e CLI para realizar tarefas operacionais no projeto.

Competências principais:
- Executar comandos no terminal e interpretar resultados
- Criar e modificar arquivos e diretórios
- Automatizar tarefas repetitivas com scripts
- Navegar na estrutura do projeto e entender a organização do código
- Executar testes, linters e ferramentas de build
- Gerenciar processos e serviços
- Ler e interpretar logs, traces e saídas de diagnóstico

Ferramentas que domina:
- CLI: bash, PowerShell, git, npm, pip, docker
- Sistema: manipulação de arquivos, permissões, processos
- Monitoramento: logs, status, health checks

Regras de resposta:
- Responda sempre no mesmo idioma utilizado pelo usuário na mensagem recebida.
- Seja direto: comando executado → resultado → próximo passo.
- Quando um comando falhar, analise o erro e tente uma alternativa.
- Prefira comandos seguros (read-only) quando possível.
- Nunca execute comandos destrutivos sem confirmação explícita.
- Documente comandos importantes para referência futura.
"""

SOFTWARE_OPERATOR_SKILLS = [
    {
        "name": "execute_command",
        "description": "Executa comando no terminal e retorna resultado",
        "input_schema": {
            "command": "string (comando a ser executado)",
            "workdir": "string (diretório opcional para execução)",
            "timeout": "number (timeout em segundos, opcional)"
        },
        "output_schema": {
            "stdout": "string (saída padrão)",
            "stderr": "string (saída de erro)",
            "exit_code": "number (código de retorno)",
            "duration_ms": "number (tempo de execução)"
        }
    },
    {
        "name": "read_file",
        "description": "Lê conteúdo de arquivo",
        "input_schema": {
            "path": "string (caminho do arquivo)",
            "encoding": "string (codificação, padrão utf-8)"
        },
        "output_schema": {
            "content": "string (conteúdo do arquivo)",
            "size_bytes": "number (tamanho do arquivo)",
            "lines": "number (número de linhas)"
        }
    },
    {
        "name": "list_directory",
        "description": "Lista conteúdo de diretório",
        "input_schema": {
            "path": "string (caminho do diretório)",
            "recursive": "boolean (listar recursivamente)"
        },
        "output_schema": {
            "entries": "array (arquivos e diretórios)",
            "total": "number (total de entradas)"
        }
    },
]


class SoftwareOperatorAgent(BaseAgent):
    name = "software_operator"
    description = "Operador de Software — comandos, scripts, automação de tarefas"
    system_prompt = SOFTWARE_OPERATOR_SYSTEM_PROMPT
    skills = SOFTWARE_OPERATOR_SKILLS


agent_registry.register(SoftwareOperatorAgent())
