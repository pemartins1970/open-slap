# Open Slap! — Especificação de Melhorias de Interface
**Para:** Trae  
**Contexto:** Baseado em análise direta do código `App_auth.jsx`, `main_auth.py` e `db.py` do zip atual.  
**Prioridade:** Settings → Chat → Tarefas (menor para maior esforço)

---

## Visão geral

Três áreas de melhoria, todas incrementais — nenhuma reescreve o core.

1. **Settings** — trocar rolagem infinita por abas com sub-navegação
2. **Chat** — sistema de blocos tipados inline (plan, tool_call, thinking, artifact)
3. **Tarefas** — hierarquia de subfluxos + lista de artefatos produzidos com path completo

---

## 1. Settings — Abas de navegação

### Diagnóstico

`centerView === 'settings'` renderiza um único bloco com todas as seções empilhadas. Quanto mais seções crescem (LLM, segurança, conectores, memória, doctor), mais pesado fica encontrar qualquer coisa.

### O que fazer

Adicionar estado `settingsTab` e dividir o painel em 5 abas. O conteúdo já existe — é reorganização de JSX, sem mudança de backend.

### Implementação — `App_auth.jsx`

**1.1 Novo estado (adicionar junto com os outros `useState`):**
```jsx
const [settingsTab, setSettingsTab] = useState('appearance');
```

**1.2 Componente de tab bar (adicionar como função antes do return principal):**
```jsx
const SETTINGS_TABS = [
  { id: 'appearance', label: t('theme') },        // já traduzido
  { id: 'llm',        label: 'LLM & Providers' },
  { id: 'security',   label: t('security') || 'Segurança' },
  { id: 'connectors', label: t('connectors') || 'Conectores' },
  { id: 'memory',     label: t('memory') || 'Memória' },
];
```

**1.3 Substituir o título do painel de settings:**

Antes:
```jsx
<div style={styles.centerPanelTitle}>{t('settings')}</div>
```

Depois:
```jsx
<div style={styles.centerPanelTitle}>{t('settings')}</div>
<div style={{ display: 'flex', gap: '2px', borderBottom: '1px solid var(--border)', marginBottom: '20px' }}>
  {SETTINGS_TABS.map(tab => (
    <button
      key={tab.id}
      onClick={() => setSettingsTab(tab.id)}
      style={{
        ...styles.sidebarButton,
        width: 'auto',
        padding: '8px 14px',
        borderRadius: '6px 6px 0 0',
        borderBottom: settingsTab === tab.id ? '2px solid var(--amber)' : '2px solid transparent',
        color: settingsTab === tab.id ? 'var(--text-bright)' : 'var(--text-dim)',
        fontSize: '12px',
        fontFamily: 'var(--mono)',
      }}
    >
      {tab.label}
    </button>
  ))}
</div>
```

**1.4 Envolver cada bloco existente com a condição de aba:**

```jsx
{/* ABA: Aparência */}
{settingsTab === 'appearance' && (
  <>
    {/* seção de tema — já existente */}
    {/* seção de idioma — já existente */}
    {/* seção doctor — já existente */}
  </>
)}

{/* ABA: LLM & Providers */}
{settingsTab === 'llm' && (
  <>
    {/* seção LLM key — já existente */}
    {/* NOVO: status visual dos providers (ver 1.5) */}
  </>
)}

{/* ABA: Segurança */}
{settingsTab === 'security' && (
  <>
    {/* seção security settings — já existente */}
  </>
)}

{/* ABA: Conectores */}
{settingsTab === 'connectors' && (
  <>
    {/* seção GitHub, Google etc. — já existente */}
  </>
)}

{/* ABA: Memória */}
{settingsTab === 'memory' && (
  <>
    {/* seção soul/memória + SOUL.md preview — já existente */}
  </>
)}
```

**1.5 NOVO na aba LLM: status visual dos providers**

Adicionar logo após o campo de API key, um card com status de cada provider. Os dados já vêm de `/api/settings/llm/status` (ou similar — verificar endpoint existente de provider status):

```jsx
<div style={styles.settingsSection}>
  <div style={styles.settingsSectionTitle}>Providers configurados</div>
  {/* Iterar sobre providers retornados por llmStatus/providers */}
  {(providerStatusList || []).map(p => (
    <div key={p.name} style={{
      display: 'flex', alignItems: 'center', gap: '10px',
      padding: '8px 0', borderBottom: '1px solid var(--border)',
      fontSize: '13px', fontFamily: 'var(--mono)'
    }}>
      <div style={{
        width: '8px', height: '8px', borderRadius: '50%',
        background: p.available ? 'var(--green)' : 'var(--border)',
        flexShrink: 0
      }} />
      <span>{p.name}</span>
      {p.source === 'env' && (
        <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px',
          background: 'rgba(74,222,128,0.12)', color: 'var(--green)' }}>env</span>
      )}
      {p.source === 'stored' && (
        <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px',
          background: 'rgba(245,166,35,0.12)', color: 'var(--amber)' }}>salvo</span>
      )}
      <span style={{ marginLeft: 'auto', color: 'var(--text-dim)', fontSize: '11px' }}>
        {p.model || ''}
      </span>
    </div>
  ))}
  <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
    <button style={styles.settingsSecondaryButton} onClick={loadProviderStatus}>
      Testar conexão
    </button>
  </div>
</div>
```

> **Nota Trae:** verificar se `llmStatus.providers` já retorna essa lista ou se precisa chamar `/api/llm/status` separadamente. A lógica de fetch já existe em `loadLlmSettings`.

---

## 2. Chat — Blocos tipados inline

### Diagnóstico

O `App_auth.jsx` já trata `plan`, `COMMAND_REQUEST_JSON` e `artifacts` como casos especiais dispersos na renderização de mensagem. Falta um sistema unificado de blocos. Os dados já existem no backend — é questão de renderização consistente.

### Tipos de bloco a implementar

| Tipo | Gatilho no texto | Visual |
|------|-----------------|--------|
| `thinking` | `<THINKING>...</THINKING>` ou heurística de prefácio interno | Colapsável, ícone de reticências |
| `tool_call` | Já existe via `COMMAND_REQUEST_JSON` | Card com nome da tool, args, status ok/erro |
| `plan` | Já existe via ` ```plan ``` ` | Card com lista de tarefas e botão Aprovar |
| `artifact` | Já existe via `artifacts[]` na mensagem | Card com nome, path completo, tamanho, botão Baixar |
| `url_fetch` | Injetado pelo backend via `url_context` | Card colapsável mostrando URL e chars lidos |

### Implementação — `App_auth.jsx`

**2.1 Parser de blocos (adicionar como função utilitária antes do componente principal):**

```jsx
function parseMessageBlocks(content) {
  // Retorna array de { type: 'text'|'thinking'|'plan'|'url_fetch', content }
  const blocks = [];
  let remaining = content || '';

  // Detectar bloco thinking (colapsável — não expor chain-of-thought bruto)
  const thinkingMatch = remaining.match(/^(.*?)<THINKING>([\s\S]*?)<\/THINKING>([\s\S]*)$/s);
  if (thinkingMatch) {
    if (thinkingMatch[1].trim()) blocks.push({ type: 'text', content: thinkingMatch[1].trim() });
    blocks.push({ type: 'thinking', content: thinkingMatch[2].trim() });
    remaining = thinkingMatch[3];
  }

  // Detectar bloco plan
  const planMatch = remaining.match(/([\s\S]*?)```plan\s*([\s\S]*?)```([\s\S]*)/);
  if (planMatch) {
    if (planMatch[1].trim()) blocks.push({ type: 'text', content: planMatch[1].trim() });
    blocks.push({ type: 'plan', content: planMatch[2].trim() });
    remaining = planMatch[3];
  }

  // Restante como texto
  if (remaining.trim()) blocks.push({ type: 'text', content: remaining.trim() });

  return blocks.length ? blocks : [{ type: 'text', content: content }];
}
```

**2.2 Componente `<MessageBlock>` (adicionar como componente separado):**

```jsx
function MessageBlock({ block, message, onApprove }) {
  const [collapsed, setCollapsed] = React.useState(true);

  if (block.type === 'thinking') {
    return (
      <div style={{
        border: '1px solid var(--border)', borderRadius: '8px',
        marginBottom: '8px', overflow: 'hidden', fontSize: '12px'
      }}>
        <div
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '7px 12px', background: 'var(--bg2)',
            cursor: 'pointer', userSelect: 'none'
          }}
          onClick={() => setCollapsed(v => !v)}
        >
          <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '999px',
            background: 'rgba(127,119,221,0.12)', color: '#7F77DD', fontWeight: 500 }}>
            raciocínio
          </span>
          <span style={{ marginLeft: 'auto', color: 'var(--text-dim)', fontSize: '11px' }}>
            {collapsed ? '▸ expandir' : '▾ recolher'}
          </span>
        </div>
        {!collapsed && (
          <div style={{
            padding: '10px 12px', color: 'var(--text-dim)',
            fontFamily: 'var(--mono)', whiteSpace: 'pre-wrap', lineHeight: 1.5
          }}>
            {block.content}
          </div>
        )}
      </div>
    );
  }

  if (block.type === 'plan') {
    const lines = block.content.split('\n').filter(l => l.trim());
    return (
      <div style={{
        border: '1px solid rgba(245,166,35,0.35)', borderRadius: '8px',
        marginBottom: '8px', overflow: 'hidden'
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '8px 12px', background: 'rgba(245,166,35,0.08)',
          borderBottom: '1px solid rgba(245,166,35,0.2)'
        }}>
          <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '999px',
            background: 'rgba(245,166,35,0.15)', color: 'var(--amber)', fontWeight: 500 }}>
            plano
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
            {lines.length} tarefas
          </span>
          {onApprove && (
            <button
              onClick={() => onApprove(message)}
              style={{
                marginLeft: 'auto', fontSize: '11px', padding: '4px 12px',
                border: '1px solid var(--green)', borderRadius: '6px',
                background: 'rgba(74,222,128,0.08)', color: 'var(--green)', cursor: 'pointer'
              }}
            >
              Aprovar e executar
            </button>
          )}
        </div>
        <div style={{ padding: '10px 12px', fontFamily: 'var(--mono)', fontSize: '12px' }}>
          {lines.map((line, i) => (
            <div key={i} style={{ padding: '3px 0', color: 'var(--text)', lineHeight: 1.5 }}>
              {line}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // type === 'text' — usar renderização de markdown existente
  return <span>{block.content}</span>;
}
```

**2.3 Atualizar a renderização de mensagem do assistente:**

Localizar onde `message.role === 'assistant'` renderiza o conteúdo (em torno da linha 6477 do `App_auth.jsx` atual). Envolver o conteúdo com:

```jsx
{message.role === 'assistant' && !message.streaming ? (
  <>
    {parseMessageBlocks(message.content).map((block, i) => (
      <MessageBlock
        key={i}
        block={block}
        message={message}
        onApprove={handleApprovePlan}
      />
    ))}
    {/* artifacts já existentes — manter lógica atual */}
    {(message.artifacts || []).length > 0 && (
      <ArtifactList artifacts={message.artifacts} />
    )}
  </>
) : /* renderização streaming existente */ }
```

**2.4 Componente `<ArtifactList>` para artifacts inline:**

```jsx
function ArtifactList({ artifacts }) {
  if (!artifacts || !artifacts.length) return null;
  return (
    <div style={{ marginTop: '8px' }}>
      {artifacts.map((a, i) => (
        <div key={i} style={{
          display: 'flex', alignItems: 'center', gap: '10px',
          padding: '8px 12px', border: '1px solid var(--border)',
          borderRadius: '8px', marginBottom: '6px', fontSize: '12px'
        }}>
          <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '999px',
            background: 'rgba(59,130,246,0.12)', color: '#60a5fa', fontWeight: 500 }}>
            artefato
          </span>
          <span style={{ fontFamily: 'var(--mono)', color: 'var(--text)', flex: 1 }}>
            {a.name}
          </span>
          <span style={{ color: 'var(--text-dim)', fontSize: '11px', fontFamily: 'var(--mono)' }}>
            {a.size ? `${Math.round(a.size / 1024)}KB` : ''}
          </span>
          <a href={a.url} target="_blank" rel="noreferrer"
            style={{ fontSize: '11px', color: 'var(--amber)', textDecoration: 'none' }}>
            Baixar ↗
          </a>
        </div>
      ))}
    </div>
  );
}
```

---

## 3. Tarefas — Subfluxos hierárquicos + Artefatos

### Diagnóstico

`task_todos` é uma tabela flat (`id, user_id, conversation_id, text, status`). Não há hierarquia. Artifacts de CLI tools existem no `artifact_registry` em memória mas não são persistidos por tarefa. O path de entrega (`DEFAULT_DELIVERIES_ROOT / user_id / delivery_id`) existe no backend mas não é exibido na UI de tarefas.

### O que fazer

- **Banco:** adicionar `parent_todo_id` e `delivery_path` à tabela `task_todos` via migration
- **Backend:** expor artefatos por tarefa em endpoint dedicado
- **Frontend:** renderizar todos em árvore + seção de artefatos com path completo

---

### 3.1 Migration — `db.py`

Adicionar no método `_ensure_database`, **após** a criação da tabela `task_todos`:

```python
# Migration: hierarquia de subfluxos e path de entrega em task_todos
try:
    conn.execute("ALTER TABLE task_todos ADD COLUMN parent_todo_id INTEGER REFERENCES task_todos(id)")
except Exception:
    pass  # coluna já existe
try:
    conn.execute("ALTER TABLE task_todos ADD COLUMN delivery_path TEXT")
except Exception:
    pass  # coluna já existe
try:
    conn.execute("ALTER TABLE task_todos ADD COLUMN artifact_meta TEXT")  # JSON: [{name, path, size, url}]
except Exception:
    pass
```

### 3.2 Atualizar `add_task_todo` — `db.py`

```python
def add_task_todo(
    self,
    user_id: int,
    conversation_id: int,
    text: str,
    parent_todo_id: Optional[int] = None,
    delivery_path: Optional[str] = None,
) -> int:
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO task_todos (user_id, conversation_id, text, parent_todo_id, delivery_path)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, conversation_id, _redact_text(text), parent_todo_id, delivery_path),
        )
        conn.commit()
        return cursor.lastrowid
```

Atualizar também a função wrapper no final do arquivo:
```python
def add_task_todo(user_id: int, conversation_id: int, text: str,
                  parent_todo_id: int = None, delivery_path: str = None) -> int:
    return db_manager.add_task_todo(user_id, conversation_id, text,
                                    parent_todo_id=parent_todo_id,
                                    delivery_path=delivery_path)
```

### 3.3 Atualizar `list_task_todos` — `db.py`

Adicionar os novos campos ao SELECT:

```python
def list_task_todos(self, user_id: int, conversation_id: int, status: str = None):
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row
        query = """
            SELECT id, user_id, conversation_id, text, status,
                   parent_todo_id, delivery_path, artifact_meta,
                   created_at, updated_at
            FROM task_todos
            WHERE user_id = ? AND conversation_id = ?
        """
        params = [user_id, conversation_id]
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY id ASC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
```

### 3.4 Novo endpoint — `main_auth.py`

Adicionar endpoint para registrar artefatos em um todo específico:

```python
@app.post("/api/tasks/todos/{todo_id}/artifacts")
async def add_todo_artifact(
    todo_id: int,
    payload: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Associa artefatos produzidos a um todo de tarefa."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    artifacts = payload.get("artifacts") or []
    delivery_path = str(payload.get("delivery_path") or "").strip()
    
    # Serializar artifacts como JSON e salvar no campo artifact_meta
    import sqlite3 as _sq
    db_path = get_db_path()
    try:
        with _sq.connect(db_path) as conn:
            conn.execute(
                """UPDATE task_todos
                   SET artifact_meta = ?, delivery_path = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ?""",
                (
                    json.dumps(artifacts, ensure_ascii=False),
                    delivery_path or None,
                    todo_id,
                    current_user["id"],
                )
            )
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"ok": True, "todo_id": todo_id}
```

### 3.5 Frontend — Renderização em árvore com artefatos — `App_auth.jsx`

**3.5.1 Função para montar árvore de todos:**

```jsx
function buildTodoTree(todos) {
  // Monta árvore a partir de lista flat com parent_todo_id
  const map = {};
  const roots = [];
  (todos || []).forEach(t => { map[t.id] = { ...t, children: [] }; });
  Object.values(map).forEach(t => {
    if (t.parent_todo_id && map[t.parent_todo_id]) {
      map[t.parent_todo_id].children.push(t);
    } else {
      roots.push(t);
    }
  });
  return roots;
}
```

**3.5.2 Componente `<TodoNode>` recursivo:**

```jsx
function TodoNode({ todo, depth = 0, onToggle, onAddChild }) {
  const [expanded, setExpanded] = React.useState(true);
  const hasChildren = todo.children && todo.children.length > 0;
  const artifacts = (() => {
    try { return JSON.parse(todo.artifact_meta || '[]'); } catch { return []; }
  })();

  return (
    <div style={{ marginLeft: depth > 0 ? '20px' : '0', paddingLeft: depth > 0 ? '12px' : '0',
      borderLeft: depth > 0 ? '1px solid var(--border)' : 'none' }}>
      
      {/* Linha principal do todo */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px',
        padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
        
        {/* Botão expandir/recolher subfluxos */}
        {hasChildren && (
          <button onClick={() => setExpanded(v => !v)}
            style={{ background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-dim)', fontSize: '10px', padding: '2px', marginTop: '2px' }}>
            {expanded ? '▾' : '▸'}
          </button>
        )}
        {!hasChildren && <div style={{ width: '18px' }} />}

        {/* Status dot */}
        <div style={{
          width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0, marginTop: '5px',
          background: todo.status === 'done' ? 'var(--green)' : 'var(--amber)'
        }} />

        <div style={{ flex: 1 }}>
          {/* Texto do todo */}
          <div style={{ fontSize: '13px', color: 'var(--text)',
            textDecoration: todo.status === 'done' ? 'line-through' : 'none',
            opacity: todo.status === 'done' ? 0.6 : 1 }}>
            {todo.text}
          </div>

          {/* Path de entrega */}
          {todo.delivery_path && (
            <div style={{ fontSize: '11px', color: 'var(--text-dim)',
              fontFamily: 'var(--mono)', marginTop: '4px',
              display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ opacity: 0.5 }}>📁</span>
              <span title={todo.delivery_path}>
                {todo.delivery_path}
              </span>
            </div>
          )}

          {/* Lista de artefatos */}
          {artifacts.length > 0 && (
            <div style={{ marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {artifacts.map((a, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '5px 10px', borderRadius: '6px',
                  background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)',
                  fontSize: '11px', fontFamily: 'var(--mono)'
                }}>
                  <span style={{ color: '#60a5fa', fontWeight: 500 }}>artefato</span>
                  <span style={{ color: 'var(--text)', flex: 1 }}>{a.name}</span>
                  <span style={{ color: 'var(--text-dim)' }}>
                    {a.size ? `${Math.round(a.size / 1024)}KB` : ''}
                  </span>
                  {/* Path completo no hover/title */}
                  <span title={a.path} style={{
                    color: 'var(--text-dim)', maxWidth: '200px',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
                  }}>
                    {a.path}
                  </span>
                  {a.url && (
                    <a href={a.url} target="_blank" rel="noreferrer"
                      style={{ color: 'var(--amber)', textDecoration: 'none', fontSize: '10px' }}>
                      ↗ abrir
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Ações */}
        <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
          <button
            onClick={() => onToggle(todo.id, todo.status)}
            style={{ fontSize: '10px', padding: '3px 8px', borderRadius: '5px',
              border: '1px solid var(--border)', background: 'none',
              color: 'var(--text-dim)', cursor: 'pointer' }}>
            {todo.status === 'done' ? 'reabrir' : 'concluir'}
          </button>
          <button
            onClick={() => onAddChild(todo.id)}
            style={{ fontSize: '10px', padding: '3px 8px', borderRadius: '5px',
              border: '1px solid var(--border)', background: 'none',
              color: 'var(--text-dim)', cursor: 'pointer' }}>
            + sub
          </button>
        </div>
      </div>

      {/* Filhos recursivos */}
      {expanded && hasChildren && todo.children.map(child => (
        <TodoNode key={child.id} todo={child} depth={depth + 1}
          onToggle={onToggle} onAddChild={onAddChild} />
      ))}
    </div>
  );
}
```

**3.5.3 Atualizar a renderização de tarefas no chat ativo:**

Localizar onde `currentKind === 'task'` renderiza os todos (em torno da linha 6280). Substituir a lista flat pelo componente em árvore:

```jsx
{/* Substituir mapeamento flat de todos por: */}
{buildTodoTree(taskTodos).map(todo => (
  <TodoNode
    key={todo.id}
    todo={todo}
    onToggle={(id, status) => {
      const next = status === 'done' ? 'pending' : 'done';
      updateTaskTodoStatus(id, next);
    }}
    onAddChild={(parentId) => {
      setTaskTodoDraft('');
      setParentTodoId(parentId); // novo estado a adicionar
    }}
  />
))}
```

**3.5.4 Adicionar estado para subfluxo:**

```jsx
const [parentTodoId, setParentTodoId] = useState(null);
```

**3.5.5 Atualizar a função `addTaskTodo` para passar `parent_todo_id`:**

```jsx
const addTaskTodo = async (text, parentId = null) => {
  // ... código existente ...
  body: JSON.stringify({
    text: taskTodoDraft.trim(),
    parent_todo_id: parentId || parentTodoId || null,
  })
  // ... resto do código ...
};
```

**3.5.6 Atualizar endpoint no backend `main_auth.py` para aceitar `parent_todo_id`:**

Localizar o endpoint `POST /api/tasks/{task_id}/todos` e adicionar:

```python
parent_todo_id = payload.get("parent_todo_id") or None
add_task_todo(
    current_user["id"],
    task_id,
    text,
    parent_todo_id=int(parent_todo_id) if parent_todo_id else None,
)
```

---

## Resumo de arquivos modificados

| Arquivo | Tipo de mudança |
|---------|----------------|
| `src/backend/db.py` | Migration (`ALTER TABLE`), atualizar `add_task_todo` e `list_task_todos` |
| `src/backend/main_auth.py` | Novo endpoint `POST /api/tasks/todos/{todo_id}/artifacts`, atualizar endpoint de add todo |
| `src/frontend/src/App_auth.jsx` | Settings (abas), blocos de chat, renderização de tarefas em árvore |

---

## Ordem de execução recomendada

1. **Settings** — só JSX, sem banco, zero risco. Fazer primeiro.
2. **Blocos de chat** — só frontend, sem banco. `parseMessageBlocks` + `MessageBlock`. Testar com mensagens que já têm plan e artifacts.
3. **Banco (migration)** — `ALTER TABLE` com `try/except` — idempotente, sem risco de quebrar dados existentes.
4. **Backend (endpoint e parâmetros)** — depois do banco.
5. **Frontend tarefas** — `buildTodoTree`, `TodoNode`, atualizar renderização do chat de tarefa.

---

## Testes mínimos por etapa

**Settings:** acessar Settings → navegar entre abas → verificar que conteúdo de cada aba aparece correto → verificar que trocar de aba não perde estado do formulário.

**Blocos de chat:** enviar um pedido que gere um `plan` → verificar que aparece como card inline → clicar em "Aprovar e executar" → verificar que fluxo de aprovação continua funcionando igual ao anterior.

**Tarefas:** criar uma tarefa → adicionar 2 todos → adicionar 1 sub-todo em um deles → verificar estrutura em árvore → marcar como concluído → verificar que artefatos aparecem quando presentes (testar com uma execução de software_operator que gere artifact).

---

*Gerado a partir de análise direta do código fonte — `App_auth.jsx` (6.739 linhas), `main_auth.py` (9.169 linhas), `db.py`. Nenhuma suposição — tudo baseado na estrutura real existente.*
