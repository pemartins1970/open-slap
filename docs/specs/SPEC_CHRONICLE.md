# Open Slap! — Spec Chronicle: Session Memory
**Data:** 2026-06-09  
**Dependência:** B-06 estável ✅  
**Decisões de produto confirmadas:**
- Escrita: híbrida — entradas incrementais + sumário on close
- Busca: SQLite FTS5 (MVP); LLM search como enhancement posterior
- `/standup`: janela desde o último `/standup`, fallback 7 dias
- Arquivos indexados: somente tool calls do agente (não texto livre)

---

## Contexto e objetivo

B-06 resolve memória de curto prazo dentro da conversa ativa (últimas 10 mensagens). Chronicle resolve memória de médio prazo entre sessões: o que foi discutido ontem, quais arquivos foram tocados, o que a Sabrina "sabe" sobre o trabalho recente.

Referência de produto: VSCode 1.123 (local SQLite, sem cloud sync, truncagem pragmática, `/standup` e `/search` como comandos de UX).

---

## 0. Verificações antes de implementar

1. Confirmar que `strip_internal_markup()` de `soul_extractor.py` (ou `llm_manager_simple.py`) é importável como função pura — Chronicle vai reusar para limpar conteúdo antes de truncar.
2. Confirmar localização exata do bloco do interceptor FILES_JSON em `ws/orchestrator.py` (linhas 211-230) — Chronicle vai registrar arquivos escritos a partir desse ponto.
3. Confirmar que o evento `done` no orchestrator é emitido de um único ponto de saída — Chronicle precisa de um hook confiável para escrita incremental.

---

## 1. Schema — novas tabelas SQLite

```sql
-- Entradas individuais de mensagem (truncadas)
CREATE TABLE IF NOT EXISTS chronicle_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role            TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content         TEXT NOT NULL,          -- truncado: user 1k, assistant 5k
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- FTS5 sobre o conteúdo das entradas
CREATE VIRTUAL TABLE IF NOT EXISTS chronicle_entries_fts
USING fts5(content, content='chronicle_entries', content_rowid='id');

-- Triggers para manter FTS em sincronia
CREATE TRIGGER IF NOT EXISTS chronicle_entries_ai
AFTER INSERT ON chronicle_entries BEGIN
    INSERT INTO chronicle_entries_fts(rowid, content)
    VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS chronicle_entries_ad
AFTER DELETE ON chronicle_entries BEGIN
    INSERT INTO chronicle_entries_fts(chronicle_entries_fts, rowid, content)
    VALUES ('delete', old.id, old.content);
END;

-- Metadados e sumário por conversa
CREATE TABLE IF NOT EXISTS chronicle_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL UNIQUE,
    started_at      TEXT NOT NULL,
    ended_at        TEXT,                   -- NULL = sessão em aberto
    summary         TEXT,                   -- NULL até on-close
    messages_count  INTEGER NOT NULL DEFAULT 0,
    files_count     INTEGER NOT NULL DEFAULT 0,
    standup_at      TEXT                    -- timestamp do último /standup que incluiu esta sessão
);

-- Arquivos tocados por tool calls do agente
CREATE TABLE IF NOT EXISTS chronicle_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    file_path       TEXT NOT NULL,
    action          TEXT NOT NULL CHECK(action IN ('read', 'write', 'create', 'delete')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chronicle_entries_conv
    ON chronicle_entries(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chronicle_files_conv
    ON chronicle_files(conversation_id);
CREATE INDEX IF NOT EXISTS idx_chronicle_sessions_standup
    ON chronicle_sessions(standup_at);
```

---

## 2. Módulo `backend/chronicle.py`

Interface pública do módulo — implementar como funções puras sem dependência de FastAPI:

```python
# Escrita incremental
def append_chronicle_entry(
    conversation_id: int,
    role: str,          # 'user' | 'assistant'
    content: str,       # conteúdo bruto — truncagem e strip aplicados internamente
) -> None: ...

# Registro de arquivo tocado por tool call
def append_chronicle_file(
    conversation_id: int,
    file_path: str,
    action: str,        # 'read' | 'write' | 'create' | 'delete'
) -> None: ...

# Sumário on-close (heurístico, sem LLM)
def close_chronicle_session(conversation_id: int) -> None: ...

# /search
def chronicle_search(query: str, limit: int = 10) -> list[dict]: ...

# /standup
def chronicle_standup(since: str | None = None) -> str: ...
```

### Truncagem e limpeza

```python
USER_TRUNCATE = 1000      # chars
ASSISTANT_TRUNCATE = 5000 # chars

def _prepare_content(role: str, content: str) -> str:
    clean = strip_internal_markup(content)   # reusar de soul_extractor ou llm_manager
    limit = USER_TRUNCATE if role == 'user' else ASSISTANT_TRUNCATE
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + " […]"
```

### Sumário heurístico (sem LLM)

```python
def _build_summary(conversation_id: int) -> str:
    entries = db.query(
        "SELECT role, content FROM chronicle_entries "
        "WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,)
    )
    files = db.query(
        "SELECT DISTINCT file_path, action FROM chronicle_files "
        "WHERE conversation_id = ?",
        (conversation_id,)
    )

    first_user = next((e["content"] for e in entries if e["role"] == "user"), "")
    last_assistant = next((e["content"] for e in reversed(entries) if e["role"] == "assistant"), "")
    exchanges = len(entries)
    file_list = [f"{f['action']}: {f['file_path']}" for f in files] if files else []

    parts = [f"Início: {first_user[:200]}"]
    if exchanges:
        parts.append(f"{exchanges} mensagens")
    if file_list:
        parts.append("Arquivos: " + ", ".join(file_list[:10]))
    if last_assistant:
        parts.append(f"Última resposta: {last_assistant[:100]}")

    return " · ".join(parts)
```

---

## 3. Integração — escrita incremental no orchestrator

Em `ws/orchestrator.py`, no ponto de emissão do evento `done` (único ponto de saída confirmado no Passo 0):

```python
from backend.chronicle import append_chronicle_entry

# Após persistir a mensagem do assistant no DB e antes de emitir done:
append_chronicle_entry(
    conversation_id=conversation_id,
    role="assistant",
    content=assistant_message_text,
)
```

Para a mensagem do user, escrever no momento de recepção (antes de iniciar o processamento):

```python
append_chronicle_entry(
    conversation_id=conversation_id,
    role="user",
    content=user_message_text,
)
```

---

## 4. Integração — rastreamento de arquivos

No interceptor FILES_JSON (`ws/orchestrator.py:211-230`), após persistir os arquivos em disco:

```python
from backend.chronicle import append_chronicle_file

for file_entry in bundle:
    append_chronicle_file(
        conversation_id=conversation_id,
        file_path=file_entry["path"],
        action="write",   # FILES_JSON é sempre write/create neste ponto
    )
```

---

## 5. Sumário on-close

Trigger: ao criar uma nova conversa, sumarizar a conversa anterior se `chronicle_sessions.ended_at IS NULL`.

Em `ws/orchestrator.py` ou no endpoint de criação de conversa:

```python
from backend.chronicle import close_chronicle_session

def on_new_conversation(previous_conversation_id: int | None):
    if previous_conversation_id:
        close_chronicle_session(previous_conversation_id)
```

`close_chronicle_session` atualiza `ended_at`, calcula e salva o sumário heurístico, atualiza `messages_count` e `files_count`.

---

## 6. Comando `/standup`

Detectado em SabrinaAgent (name='general') antes de rotear para o LLM:

```python
if user_message.strip().lower().startswith("/standup"):
    return handle_standup_command(conversation_id)
```

```python
def handle_standup_command(current_conversation_id: int) -> str:
    from backend.chronicle import chronicle_standup

    # Determinar 'since': timestamp do último /standup, fallback 7 dias atrás
    last = db.query_one(
        "SELECT MAX(standup_at) as t FROM chronicle_sessions "
        "WHERE standup_at IS NOT NULL"
    )
    since = last["t"] if last and last["t"] else _days_ago(7)

    report = chronicle_standup(since=since)

    # Marcar sessões cobertas com standup_at = now
    db.execute(
        "UPDATE chronicle_sessions SET standup_at = datetime('now') "
        "WHERE started_at >= ? AND standup_at IS NULL",
        (since,)
    )

    return report
```

**Formato do relatório `/standup`:**

```
📋 Standup — últimas X sessões (desde DD/MM)

• [data] [preview da primeira mensagem] — N trocas
  Arquivos: path1, path2
• [data] [preview] — N trocas
...

Use /search <termo> para buscar no histórico.
```

---

## 7. Comando `/search`

```python
if user_message.strip().lower().startswith("/search "):
    query = user_message[8:].strip()
    return handle_search_command(query)
```

```python
def handle_search_command(query: str) -> str:
    from backend.chronicle import chronicle_search

    results = chronicle_search(query, limit=5)

    if not results:
        return f"Nenhum resultado para '{query}' no histórico."

    lines = [f"🔍 Resultados para '{query}':\n"]
    for r in results:
        date = r["created_at"][:10]
        preview = r["content"][:150].replace("\n", " ")
        lines.append(f"• [{date}] {preview}…")

    lines.append("\nUse /standup para ver o resumo das sessões recentes.")
    return "\n".join(lines)
```

`chronicle_search` internamente:

```python
def chronicle_search(query: str, limit: int = 10) -> list[dict]:
    return db.query(
        "SELECT ce.conversation_id, ce.role, ce.content, ce.created_at "
        "FROM chronicle_entries_fts fts "
        "JOIN chronicle_entries ce ON ce.id = fts.rowid "
        "WHERE chronicle_entries_fts MATCH ? "
        "ORDER BY rank LIMIT ?",
        (query, limit)
    )
```

---

## Acceptance criteria

- [ ] Após enviar 3+ mensagens, `chronicle_entries` contém entradas truncadas para cada turno
- [ ] Mensagem assistant >5000 chars: armazenada truncada com ` […]`; conversa no chat não afetada
- [ ] Criar nova conversa: conversa anterior recebe `ended_at` e `summary` populados
- [ ] Arquivo escrito via FILES_JSON: aparece em `chronicle_files` com `action='write'`
- [ ] `/standup` retorna sessões desde o último `/standup` (ou 7 dias), marca `standup_at`
- [ ] `/standup` consecutivo sem novas sessões: retorna "Nenhuma sessão nova desde o último standup"
- [ ] `/search python` retorna entradas contendo "python" (case-insensitive via FTS5)
- [ ] `/search` sem resultados: mensagem amigável, sem erro
- [ ] Markup interno (`[[add_step:]]`, `<FILES_JSON>`) não aparece nas entradas do Chronicle
- [ ] B-06 não afetado: `load_conversation_history()` continua lendo de `messages`, não de `chronicle_entries`
- [ ] 162 testes existentes: 0 regressões

---

## Testes formais

| # | Cenário | Esperado |
|---|---|---|
| 1 | append_chronicle_entry role='user', 2000 chars | Armazenado com 1000 chars + ` […]` |
| 2 | append_chronicle_entry role='assistant', 3000 chars | Armazenado completo (< 5000) |
| 3 | append_chronicle_entry com `[[add_step:3]]` no conteúdo | Markup removido antes de truncar |
| 4 | close_chronicle_session | ended_at preenchido, summary não nulo, counts corretos |
| 5 | chronicle_search query com match | Lista de entradas com conversation_id e preview |
| 6 | chronicle_search query sem match | Lista vazia, sem exception |
| 7 | chronicle_standup since=7 dias atrás com 2 sessões | Relatório com 2 bullets |
| 8 | chronicle_standup sem sessões no período | Mensagem "nenhuma sessão" |
| 9 | /standup marca standup_at das sessões cobertas | standup_at preenchido no DB |
| 10 | /standup consecutivo | Não duplica marcação; retorna "nenhuma sessão nova" |
| 11 | append_chronicle_file FILES_JSON | Linha em chronicle_files com path e action='write' |
| 12 | FTS trigger: insert em chronicle_entries | chronicle_entries_fts indexa conteúdo automaticamente |
| 13 | FTS trigger: delete em chronicle_entries | chronicle_entries_fts remove entrada |
| 14 | Migração DB: tabelas e índices criados sem erro em DB limpo | Sem exception |
| 15 | B-06 + Chronicle coexistem: load_conversation_history() não lê chronicle_entries | Histórico vem de messages, Chronicle é write-only do ponto de vista de B-06 |

---

## Fora do escopo deste item

- LLM search semântico (enhancement posterior)
- Sumário gerado por LLM (enhancement posterior — substituir `_build_summary` heurístico)
- UI dedicada para Chronicle (consulta via `/standup` e `/search` no chat)
- Expiração/poda automática de entradas antigas
- Indexação de arquivos mencionados em texto livre (não tool calls)
- Sincronização cloud
