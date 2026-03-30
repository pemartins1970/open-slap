# PATCH — Software Tool Context para o software_operator
**Open Slap! v2 · Preparado por revisão externa · 26/03/2026**

---

## Para o Trae: leia esta seção antes de qualquer edição

### O que este patch resolve

O `software_operator` já recebe a lista de softwares instalados no `user_context`
(via `top20_productivity`), mas o prompt dele instrui o LLM a "começar pelos
executáveis permitidos" com uma lista estática (`drawio-cli`, `blender-cli`, etc.).
O LLM lê a lista do contexto e ignora, porque o prompt manda ele usar os exemplos
fixos. Resultado: pedidos como "capture minha tela e analise" falham silenciosamente
— a ferramenta não existe na whitelist, o `cli_bridge` retorna erro, e o usuário
não vê feedback útil.

A solução tem três partes que se complementam:

1. **`main_auth.py`** — nova função `_build_software_tool_context()` que transforma
   a lista de instalados em um bloco categorizado e legível pelo LLM, injetado no
   `user_context` quando o expert é `software_operator`.

2. **`llm_manager_simple.py`** — reescrita do bloco de prompt do `software_operator`
   para incluir um algoritmo de decisão explícito: "verifique a lista → use o que
   está instalado → senão, use `python-inline`".

3. **`cli_bridge.py`** — nova função `build_dynamic_whitelist()` que mescla a
   whitelist fixa com os executáveis resolvidos da lista de instalados, para que o
   executor aceite o que o LLM decidiu usar.

4. **`requirements.txt`** — adição de `mss` (captura de tela, leve, sem GUI).

### Por que foi feito assim e não de outro jeito

- **Não se alterou a whitelist fixa** — ela é a âncora de segurança. A whitelist
  dinâmica só *adiciona* entradas sobre ela, nunca remove.
- **`python-inline` permanece sempre disponível** — é o fallback universal para
  qualquer lógica que não tenha ferramenta instalada. Não há nova dependência de
  runtime para o caso base.
- **A injeção de contexto é condicional** ao `expert == software_operator` — não
  polui o `user_context` de outros experts com dados irrelevantes.
- **A categorização é por keywords no `name`/`id`** — zero dependências externas,
  mesma filosofia do `_score_productivity` já existente.
- **`mss`** é a única dependência nova. É multiplataforma (Win/Mac/Linux), sem
  dependência de display server no modo headless, e pequena (~30 KB).

### O que você precisa assegurar após aplicar

1. `pytest -q` passa com os 50+ testes existentes (nenhum teste novo é necessário
   para estas mudanças — são todas adições/substituições em código de geração de
   contexto e prompt).
2. `npm run build` no frontend não é afetado (zero mudanças no frontend).
3. Em produção Windows: `winget list` continua funcionando para popular o cache.
   Em Linux/Mac: a lista fica vazia e o bloco de ferramentas instaladas simplesmente
   não aparece no contexto — comportamento já existente e correto.
4. A variável `OPENSLAP_EXTERNAL_SOFTWARE` continua sendo o gate de toda a feature.
   Se estiver `0`, nada muda.

---

## PATCH 1 — `src/backend/main_auth.py`

### 1a. Adicionar a função `_build_software_tool_context` logo após `_top20_productivity`

Localização: logo após a função `_top20_productivity` (busque pela linha
`def _collect_web_services_info`).

Inserir o bloco abaixo **antes** de `_collect_web_services_info`:

```python
# ── Software tool context para o software_operator ───────────────────────────

_SW_CATEGORIES: List[tuple] = [
    # (label, keywords_em_name_ou_id)
    ("captura/visão",    ["sharex", "greenshot", "snagit", "lightshot", "capture", "screenshot", "obs", "camtasia"]),
    ("edição de imagem", ["gimp", "inkscape", "irfanview", "imagemagick", "photoshop", "affinity", "paint.net", "krita", "pixelmator"]),
    ("diagrama",         ["draw.io", "drawio", "visio", "lucidchart", "dia", "pencil", "mermaid", "plantuml", "excalidraw"]),
    ("vídeo/áudio",      ["obs", "vlc", "ffmpeg", "audacity", "kdenlive", "davinci", "handbrake", "avisynth", "virtualdub"]),
    ("dev/runtime",      ["python", "node", "nodejs", "git", "java", "jdk", "go ", "rust", "ruby", "php", "dotnet", ".net", "powershell", "wsl"]),
    ("editor/ide",       ["vscode", "code", "notepad++", "sublime", "vim", "neovim", "emacs", "cursor", "jetbrains", "intellij", "pycharm"]),
    ("compressão",       ["7-zip", "winrar", "bandizip", "peazip"]),
    ("automação/util",   ["autohotkey", "autoit", "nircmd", "everything", "total commander", "winget", "chocolatey", "scoop"]),
]


def _build_software_tool_context(installed: List[Dict[str, Any]]) -> str:
    """
    Transforma a lista de softwares instalados em um bloco estruturado por
    categoria, legível pelo LLM para decidir qual ferramenta usar.
    Sempre inclui python-inline como ferramenta universal disponível.
    """
    if not installed:
        return (
            "Softwares instalados disponíveis como ferramentas:\n"
            "  [universal] python-inline — sempre disponível para lógica customizada\n"
            "  Nenhum outro software detectado no inventário.\n"
        )

    categorized: Dict[str, List[str]] = {}
    uncategorized: List[str] = []

    for item in installed:
        name = str(item.get("name") or "").strip()
        pkg_id = str(item.get("id") or "").strip()
        if not name:
            continue
        label_str = name if not pkg_id else f"{name} [{pkg_id}]"
        nl = name.lower()
        il = pkg_id.lower()
        matched = False
        for cat_label, keywords in _SW_CATEGORIES:
            if any(kw in nl or kw in il for kw in keywords):
                categorized.setdefault(cat_label, []).append(label_str)
                matched = True
                break
        if not matched:
            uncategorized.append(label_str)

    lines = ["Softwares instalados disponíveis como ferramentas:"]
    lines.append("  [universal] python-inline — sempre disponível para lógica customizada")

    for cat_label, _ in _SW_CATEGORIES:
        items = categorized.get(cat_label)
        if items:
            entry = ", ".join(items[:6])
            if len(items) > 6:
                entry += f" (+{len(items) - 6})"
            lines.append(f"  [{cat_label}] {entry}")

    if uncategorized:
        sample = ", ".join(uncategorized[:10])
        if len(uncategorized) > 10:
            sample += f" (+{len(uncategorized) - 10} outros)"
        lines.append(f"  [outros] {sample}")

    return "\n".join(lines)
```

### 1b. Substituir o bloco de injeção do `top20` no WebSocket handler

No WebSocket handler principal (função `websocket_endpoint`), localize o bloco:

```python
                        try:
                            top20 = []
                            d = (stored_profile or {}).get("data") or {}
                            if isinstance(d.get("top20_productivity"), list):
                                top20 = d.get("top20_productivity") or []
                            elif sys.platform == "win32":
                                top20 = _top20_productivity(get_installed_software())
                            if top20:
                                names = []
                                for it in top20[:20]:
                                    nm = str((it or {}).get("name") or "").strip()
                                    pid = str((it or {}).get("id") or "").strip()
                                    if nm:
                                        label = nm if not pid else f"{nm} [{pid}]"
                                        names.append(label)
                                if names:
                                    block = "Softwares instalados relevantes:\n- " + "\n- ".join(names)
                                    user_context = f"{user_context}\n\n{block}".strip()
                        except Exception:
                            pass
```

Substituir por:

```python
                        try:
                            _is_sw_op = (
                                expert is not None
                                and str((expert or {}).get("id") or "").strip().lower()
                                == "software_operator"
                            )
                            _installed_for_ctx: List[Dict[str, Any]] = []
                            d = (stored_profile or {}).get("data") or {}
                            if isinstance(d.get("top20_productivity"), list):
                                _installed_for_ctx = d.get("top20_productivity") or []
                            elif sys.platform == "win32":
                                _installed_for_ctx = get_installed_software()

                            if _is_sw_op:
                                # Para software_operator: bloco completo categorizado
                                _sw_block = _build_software_tool_context(_installed_for_ctx)
                                user_context = f"{user_context}\n\n{_sw_block}".strip()
                            elif _installed_for_ctx:
                                # Para outros experts: top20 resumido (comportamento anterior)
                                names = []
                                for it in _installed_for_ctx[:20]:
                                    nm = str((it or {}).get("name") or "").strip()
                                    pid = str((it or {}).get("id") or "").strip()
                                    if nm:
                                        label = nm if not pid else f"{nm} [{pid}]"
                                        names.append(label)
                                if names:
                                    block = "Softwares instalados relevantes:\n- " + "\n- ".join(names)
                                    user_context = f"{user_context}\n\n{block}".strip()
                        except Exception:
                            pass
```

**Atenção**: este bloco está dentro de `if (ENABLE_SYSTEM_PROFILE and ATTACH_SYSTEM_PROFILE and sec.get("allow_system_profile")):`. Verifique que a substituição respeita o nível de indentação original.

---

## PATCH 2 — `src/backend/llm_manager_simple.py`

### Substituir o bloco do `software_operator` em `_build_full_prompt`

Localizar o bloco (busque por `if str((expert or {}).get("id") or "").strip().lower() == "software_operator":`):

```python
        if str((expert or {}).get("id") or "").strip().lower() == "software_operator":
            strict = (
                "Formato de saída obrigatório:\n"
                "- Retorne APENAS um único comando CLI em uma única linha.\n"
                "- Não use Markdown, crases, explicações, JSON, ou texto extra.\n"
                "- Comece pelo executável permitido (ex.: drawio-cli, blender-cli, gimp-cli, irfanview, winget).\n"
                "- Inclua sempre: --action <acao>\n"
                "- Se precisar de parâmetros, use flags (ex.: --type circle).\n"
                "- Se faltar dado, use placeholders explícitos (ex.: <FILE>, <TEXT>, <X>, <Y>).\n"
                "- Se precisar instalar um software no Windows, use: winget --action install --id <PACKAGE_ID> --accept-source-agreements --accept-package-agreements --silent.\n"
                "- Mantenha o diretório de trabalho consistente entre captura e edição de arquivos.\n"
                "- Se não existir uma ferramenta local adequada para a lógica solicitada, crie uma ferramenta temporária em Python usando:\n"
                "  python-inline --action run --code \"<código python>\" [--cwd <pasta_opcional>]\n"
                "  O terminal exibirá uma linha: [AUTO-BUILD] Criando ferramenta customizada para esta tarefa...\n"
            )
            base = f"{base}\n\n{strict}".strip()
            if ctx:
                base = f"{base}\n\nContexto adicional (se aplicável):\n{ctx}".strip()
            return f"{base}\n\nPedido do usuário:\n{prompt}\n\nComando:".strip()
```

Substituir por:

```python
        if str((expert or {}).get("id") or "").strip().lower() == "software_operator":
            strict = (
                "ALGORITMO DE SELEÇÃO DE FERRAMENTA (obrigatório — execute nesta ordem):\n"
                "1. Leia a seção 'Softwares instalados disponíveis como ferramentas' no contexto.\n"
                "2. Se existe um software instalado adequado para a tarefa → gere o comando para ele.\n"
                "3. Se NÃO existe nenhum software adequado → use python-inline com um script Python.\n"
                "4. python-inline está SEMPRE disponível como ferramenta universal, mesmo sem contexto.\n"
                "5. NUNCA invente executáveis que não estejam na lista de instalados ou nas exceções abaixo.\n"
                "\n"
                "Executáveis sempre disponíveis (independente do inventário):\n"
                "- python-inline --action run --code \"<script>\" [--cwd <pasta>]\n"
                "- winget --action install --id <PACKAGE_ID> (Windows)\n"
                "- apt --action install <pacote> (Linux)\n"
                "- brew --action install <pacote> (macOS)\n"
                "\n"
                "Exemplos de uso do python-inline para tarefas comuns:\n"
                "  Screenshot:\n"
                "    python-inline --action run --code \"import mss,mss.tools; m=mss.mss(); p=m.shot(output='screen.png'); print('Capturado:',p)\"\n"
                "  Screenshot + retângulo vermelho:\n"
                "    python-inline --action run --code \"import mss; from PIL import Image,ImageDraw; m=mss.mss(); d=m.grab(m.monitors[0]); img=Image.frombytes('RGB',d.size,d.rgb); draw=ImageDraw.Draw(img); draw.rectangle([100,100,400,300],outline='red',width=3); img.save('result.png'); print('Salvo: result.png')\"\n"
                "  Redimensionar imagem:\n"
                "    python-inline --action run --code \"from PIL import Image; img=Image.open('<FILE>'); img.thumbnail((800,600)); img.save('<OUTPUT>')\"\n"
                "  Converter imagem:\n"
                "    python-inline --action run --code \"from PIL import Image; Image.open('<INPUT>').save('<OUTPUT>')\"\n"
                "\n"
                "Formato de saída obrigatório:\n"
                "- Retorne APENAS um único comando CLI em uma única linha.\n"
                "- Não use Markdown, crases, explicações, JSON, ou texto extra.\n"
                "- Inclua sempre: --action <acao> (exceto para python-inline que usa --action run).\n"
                "- Se faltar dado, use placeholders explícitos (ex.: <FILE>, <OUTPUT>, <TEXT>).\n"
                "- Mantenha --cwd consistente entre captura e edição quando a tarefa tiver múltiplos passos.\n"
                "- Se precisar instalar antes de usar, instale primeiro com winget/apt/brew.\n"
            )
            base = f"{base}\n\n{strict}".strip()
            if ctx:
                base = f"{base}\n\nContexto do sistema (lista de softwares, hardware, etc.):\n{ctx}".strip()
            return f"{base}\n\nPedido do usuário:\n{prompt}\n\nComando:".strip()
```

---

## PATCH 3 — `src/backend/cli_bridge.py`

### 3a. Adicionar import de `sys` no topo do arquivo

O arquivo já usa `sys.executable` dentro de `_default_whitelist` mas não tem o import.
Localizar o bloco de imports no início do arquivo:

```python
import os
import re
import json
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List
```

Substituir por:

```python
import os
import re
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List
```

(`shutil` é usado pela função nova para resolver executáveis no PATH.)

### 3b. Corrigir `sys.executable` em `_default_whitelist`

A linha atual usa `sys.executable if "sys" in globals() else "python"` — isso é
um workaround frágil que surgiu porque `sys` não estava importado. Com o import
adicionado acima, substituir:

```python
        "python-inline": {
            "exe": sys.executable if "sys" in globals() else "python",
            "artifacts_env": "",
        },
```

Por:

```python
        "python-inline": {
            "exe": sys.executable or "python",
            "artifacts_env": "",
        },
```

### 3c. Adicionar a função `build_dynamic_whitelist` após `_default_whitelist`

Inserir logo após o fechamento de `_default_whitelist`:

```python
# ── Mapeamento de nome/id de pacote → executável provável ────────────────────

_EXE_HINTS: List[tuple] = [
    # (keyword_em_name_ou_id, executavel_no_path)
    ("gimp",         "gimp"),
    ("inkscape",     "inkscape"),
    ("irfanview",    "i_view64"),
    ("imagemagick",  "magick"),
    ("drawio",       "drawio"),
    ("draw.io",      "drawio"),
    ("blender",      "blender"),
    ("ffmpeg",       "ffmpeg"),
    ("vlc",          "vlc"),
    ("obs",          "obs64"),
    ("sharex",       "sharex"),
    ("greenshot",    "greenshot"),
    ("7-zip",        "7z"),
    ("notepad++",    "notepad++"),
    ("autohotkey",   "autohotkey"),
    ("nircmd",       "nircmd"),
]


def _resolve_exe_from_item(item: Dict[str, Any]) -> Optional[str]:
    """
    Tenta resolver o executável real de um item do inventário de softwares.
    Usa shutil.which para confirmar se está no PATH antes de retornar.
    """
    name = str(item.get("name") or "").strip().lower()
    pkg_id = str(item.get("id") or "").strip().lower()
    for keyword, exe_candidate in _EXE_HINTS:
        if keyword in name or keyword in pkg_id:
            resolved = shutil.which(exe_candidate)
            if resolved:
                return resolved
    return None


def build_dynamic_whitelist(
    installed: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Retorna a whitelist padrão mesclada com os executáveis encontrados no
    inventário de softwares instalados.

    Segurança: só adiciona entradas para executáveis que existem no PATH
    (verificado por shutil.which). Nunca remove entradas da whitelist fixa.
    """
    wl = _default_whitelist()
    if not installed:
        return wl

    for item in installed:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in wl:
            # já existe — não sobrescreve a entrada fixa
            continue
        exe = _resolve_exe_from_item(item)
        if exe:
            wl[key] = {
                "exe": exe,
                "artifacts_env": "",
            }
    return wl
```

### 3d. Atualizar o import em `main_auth.py` para expor `build_dynamic_whitelist`

Localizar a linha de import:

```python
from .cli_bridge import parse_cli_command_text, execute_cli_command
```

Substituir por:

```python
from .cli_bridge import parse_cli_command_text, execute_cli_command, build_dynamic_whitelist
```

### 3e. Usar `build_dynamic_whitelist` em `_run_one_attempt`

Em `_run_external_software_skill`, dentro de `_run_one_attempt`, localizar:

```python
        wl = _default_whitelist()
        app_key = _sanitize_text(app_name)
        if app_key not in wl or not _is_safe_token(action):
```

Substituir por:

```python
        _installed_sw = get_installed_software() if sys.platform == "win32" else []
        wl = build_dynamic_whitelist(_installed_sw)
        app_key = _sanitize_text(app_name)
        if app_key not in wl or not _is_safe_token(action):
```

**Nota de performance**: `get_installed_software()` tem cache em memória e em banco
com TTL de 6 horas (`max_age_s=21600`). Esta chamada é quase sempre O(1).

---

## PATCH 4 — `src/backend/requirements.txt`

Adicionar ao final da seção de utilitários:

```
# Captura de tela e visão (python-inline)
mss>=9.0.1
```

`mss` não tem dependências de sistema (não requer display server no Windows).
`Pillow` já costuma estar presente como dependência indireta; se não estiver, adicionar:

```
Pillow>=10.0.0
```

Verificar com `pip show Pillow` antes de adicionar para evitar duplicata.

---

## Verificação após aplicar os patches

```bash
# 1. Confirmar imports
cd src
python3 -c "from backend.cli_bridge import build_dynamic_whitelist; print('OK cli_bridge')"
python3 -c "from backend.main_auth import _build_software_tool_context; print('OK main_auth')"

# 2. Smoke test da categorização
python3 - <<'PYEOF'
from backend.main_auth import _build_software_tool_context
sample = [
    {"name": "GIMP", "id": "GIMP.GIMP"},
    {"name": "ShareX", "id": "ShareX.ShareX"},
    {"name": "Git", "id": "Git.Git"},
    {"name": "Python 3.12", "id": "Python.Python.3"},
    {"name": "VLC media player", "id": "VideoLAN.VLC"},
    {"name": "Notepad++", "id": "Notepad++.Notepad++"},
]
print(_build_software_tool_context(sample))
PYEOF

# 3. Smoke test da whitelist dinâmica
python3 - <<'PYEOF'
from backend.cli_bridge import build_dynamic_whitelist
wl = build_dynamic_whitelist([{"name": "GIMP", "id": "GIMP.GIMP"}])
print("python-inline in wl:", "python-inline" in wl)
print("gimp in wl (se instalado):", "gimp" in wl)
PYEOF

# 4. Testes existentes
pytest -q
```

Resultado esperado do smoke test de categorização:
```
Softwares instalados disponíveis como ferramentas:
  [universal] python-inline — sempre disponível para lógica customizada
  [captura/visão] ShareX [ShareX.ShareX]
  [edição de imagem] GIMP [GIMP.GIMP]
  [vídeo/áudio] VLC media player [VideoLAN.VLC]
  [dev/runtime] Python 3.12 [Python.Python.3], Git [Git.Git]
  [editor/ide] Notepad++ [Notepad++.Notepad++]
```

---

## Comportamento esperado após o patch

### Cenário 1 — Software instalado detectado

Usuário: "Abra o GIMP e redimensione esta imagem para 800×600."

Contexto injetado incluirá:
```
[edição de imagem] GIMP [GIMP.GIMP]
```

LLM do `software_operator` seguirá o algoritmo:
→ GIMP está na lista → gera: `gimp --action resize --file <FILE> --width 800 --height 600`

Se `gimp` estiver no PATH, `build_dynamic_whitelist` adicionou a entrada e a execução passa.
Se não estiver no PATH (instalado mas fora do PATH), o `cli_bridge` retorna erro informativo.

### Cenário 2 — Nenhum software adequado instalado (o caso original)

Usuário: "Capture minha tela, analise e desenhe um retângulo vermelho ao redor do texto."

Contexto injetado:
```
[universal] python-inline — sempre disponível para lógica customizada
[dev/runtime] Python 3.12 [Python.Python.3]
Nenhuma ferramenta de captura/visão detectada.
```

LLM segue o algoritmo:
→ Sem ferramenta de captura → usa python-inline
→ Gera o script com `mss` + `PIL.ImageDraw`

### Cenário 3 — Hardware Linux/Mac sem inventário

`get_installed_software()` retorna lista vazia.
`_build_software_tool_context([])` retorna o bloco mínimo com só `python-inline`.
O LLM ainda pode usar `python-inline` para tudo — funciona corretamente.

---

## Análise para atualização do `docs/DEV_JOURNAL.md`

Sugerimos adicionar a seguinte entrada na seção de Março de 2026, após o bloco
"v2.0 — MCP autônomo: inventário, execução e rastreio":

---

```markdown
### v2.0 — Software Tool Context: inventário de instalados como ferramenta do LLM (26/03/2026)

**Problema identificado**

O `software_operator` já recebia a lista de softwares instalados via
`top20_productivity` no `user_context`, mas o prompt do expert listava
executáveis fixos (`drawio-cli`, `blender-cli`, etc.) como exemplos canônicos.
O LLM ignorava o inventário real e tentava usar os exemplos — que na maioria
das instalações não existem. O `cli_bridge` retornava `"Executável não permitido"`
silenciosamente, sem feedback útil ao usuário.

**Decisão arquitetural**

Em vez de expandir a whitelist estática com mais exemplos, a solução inverte
a lógica: o LLM recebe o inventário real e um algoritmo explícito de decisão.
A whitelist passa a ser gerada dinamicamente (`build_dynamic_whitelist`) mesclando
as entradas fixas com os executáveis resolvidos via `shutil.which` — garantindo
que só entram na whitelist executáveis que realmente existem no PATH.

**Três camadas da solução**

1. `_build_software_tool_context()` em `main_auth.py` — transforma a lista de
   instalados em um bloco categorizado (captura/visão, edição de imagem, diagrama,
   etc.) legível pelo LLM. Injetado apenas quando o expert é `software_operator`,
   para não poluir o contexto de outros experts.

2. Prompt do `software_operator` reescrito em `llm_manager_simple.py` — substitui
   exemplos fixos por um algoritmo de 5 passos: leia a lista → use o instalado →
   senão, use `python-inline`. Inclui exemplos concretos de `python-inline` para
   screenshot, visão e manipulação de imagem.

3. `build_dynamic_whitelist()` em `cli_bridge.py` — usa `shutil.which` para
   confirmar executáveis antes de adicioná-los à whitelist. Nunca remove entradas
   fixas. Cache de inventário (TTL 6h) garante que a chamada é quase sempre O(1).

**Dependência adicionada**

`mss>=9.0.1` — captura de tela multiplataforma, sem dependências de sistema.
`Pillow` (se ausente) — manipulação de imagem para os scripts `python-inline`.

**Comportamento em plataformas sem inventário**

Linux/Mac: `get_installed_software()` retorna lista vazia. O contexto exibe apenas
`python-inline` como ferramenta disponível. O LLM usa `python-inline` para tudo.
Comportamento correto e consistente.

**O que ficou fora deste patch**

- Executáveis fora do PATH mas instalados via Microsoft Store ou caminhos não
  convencionais: o `shutil.which` não os encontra. Para esses casos, o fallback
  para `python-inline` é o comportamento esperado.
- Visão computacional real (OCR, detecção de texto): os exemplos de screenshot
  geram a imagem e desenham retângulos de placeholder. A análise real de texto
  requer integração com a API de visão do LLM (envio da imagem capturada como
  parte da mensagem) — mapeado para v2.1.
- Testes unitários: as funções adicionadas são funções de geração de texto/contexto.
  Testes de integração via `pytest -q` existentes continuam sendo o gate de qualidade.
```

---

## Resumo dos arquivos modificados

| Arquivo | Tipo de mudança | Linhas estimadas |
|---|---|---|
| `src/backend/main_auth.py` | Nova função + substituição de bloco | +60 / ~15 alteradas |
| `src/backend/llm_manager_simple.py` | Substituição de bloco de prompt | ~20 alteradas |
| `src/backend/cli_bridge.py` | Novos imports + correção + nova função | +60 |
| `src/backend/requirements.txt` | 1–2 linhas adicionadas | +2 |

Nenhuma alteração de schema de banco, nenhuma migration necessária, nenhuma
alteração de frontend.
