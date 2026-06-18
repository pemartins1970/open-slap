# FIX-002: Sidebar Esquerdo + Boot Screen

**Data:** 2026-06-16  
**Tipo:** Correção visual + restauração de funcionalidade  
**Executor:** Opencode  
**Pré-requisito:** FIX-001 executado e confirmado  
**Supersede:** SPEC-SIDEBAR-COMMIT1.md (deprecado)

---

## Contexto

Dois problemas distintos com causa comum (sessões sem checkpoint git):

1. **Sidebar esquerdo** exibe itens errados (Tarefas em vez de Nova conversa).
2. **Boot screen** regrediu para versão com ASCII art e texto de terminal. A versão funcional anterior exibia apenas saudação dinâmica + textarea estilo Claude.

Arquivos afetados: `LeftSidebar.jsx`, `App_auth_modular.jsx`, `appAuthStyles.js`, locales `*.json`.

---

## PARTE A — Sidebar Esquerdo

### A1. `frontend/src/components/layout/LeftSidebar.jsx`

Substituir o conteúdo do `DEFAULT_NAV_ITEMS` e a área de ações pelo seguinte conjunto fixo de três itens:

```
──────────────────────────────────────
  MENU                             «
──────────────────────────────────────
  📋  Conversas                     (nav → centerView='conversations')
  +   Nova conversa                 (ação → handleCreateConversation)
  📝  Nova nota                     (ação → handleCreateNote, placeholder)
──────────────────────────────────────
  [Logo Open Slap! — base]         (existente, manter)
──────────────────────────────────────
```

**Remover:**
- Todos os `DEFAULT_NAV_ITEMS` atuais (qualquer item além de `conversations`)
- Bloco de "Tarefas" / `tasks`
- Seção "Recent conversations" (lista de conversas no sidebar)
- Qualquer navItem com key `chat`, `skills`, `doctor`, `tasks`, `notes` como navegação do sidebar

**Props existentes a manter:**
- `onCreateConversation` → botão "Nova conversa"
- `onGoHome` → logo na base
- `isCollapsed` / `onToggle` → collapse
- `isMobile` / `onMobileClose` → mobile drawer

**Props a adicionar:**
- `onCreateNote` → botão "Nova nota"
- `centerView` → para highlight do item ativo (já pode existir)

**Collapsed mode:** mostrar apenas ícones (`📋`, `+`, `📝`), sem texto.

**Logo na base:** O bloco do logo (imagem Open Slap! badge) já existe no componente. Garantir que permanece visível e posicionado na base do sidebar em ambos os estados (expanded / collapsed).

---

### A2. `frontend/src/components/layout/AppLayout.jsx`

Adicionar `onCreateNote` como prop e repassar para `<LeftSidebar>`.

---

### A3. `frontend/src/App_auth_modular.jsx` — sidebar

**Adicionar:**
```js
const handleCreateNote = () => {
  setCenterView('notes');
  // Não chamar navigate() — a rota /notes não existe no Router
};
```

Passar `onCreateNote={handleCreateNote}` para `<AppLayout>`.

**Adicionar view `notes`** no bloco condicional de `centerView`:
```jsx
: centerView === 'notes' ? (
  <div style={{ ...styles.centerPanel, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', height: '100%' }}>
    <div style={{ fontSize: '13px', color: 'var(--text-dim)' }}>
      {t('note_select_hint')}
    </div>
  </div>
)
```

**Adicionar view `conversations` com busca** (se ainda não existir):

Adicionar estado: `const [convSearchQuery, setConvSearchQuery] = useState('');`

Na view `conversations`, adicionar input de busca com `t('conv_search_placeholder')` antes da lista. Filtro client-side por `conv.title`.

---

### A4. `frontend/src/i18n/locales/*.json` — 5 arquivos

Adicionar chave `conv_search_placeholder` próximo de `note_search_placeholder`:

```
en.json : "conv_search_placeholder": "Search conversations…"
pt.json : "conv_search_placeholder": "Buscar conversas…"
es.json : "conv_search_placeholder": "Buscar conversaciones…"
ar.json : "conv_search_placeholder": "…ابحث في المحادثات"
zh.json : "conv_search_placeholder": "搜索对话…"
```

---

## PARTE B — Boot Screen

### B1. O que deve aparecer na boot screen

Quando `centerView === 'chat'` e `messages.length === 0` (conversa nova ou sem histórico):

```
────────────────────────────────────────────────

        Boa tarde,              ← dinâmico por horário

        pemartins.              ← username do auth (sem @, sem domínio)


  [ Área de input — ver B2 abaixo ]

────────────────────────────────────────────────
```

**Remover completamente:**
- Todo o bloco de ASCII art (`open_slap > boot #v2.1#`)
- Qualquer texto de terminal/shell (`status▶`, `boot #v2.1#`, separadores `---`)
- A área de "recent conversations" que possa estar na boot screen

**Saudação dinâmica** (por horário local):
```js
const getGreeting = () => {
  const h = new Date().getHours();
  if (h >= 5  && h < 12) return t('greeting_morning');  // Bom dia
  if (h >= 12 && h < 18) return t('greeting_afternoon'); // Boa tarde
  return t('greeting_evening');                           // Boa noite
};
```

**Username:** extrair de `user.email` até o `@`:
```js
const username = user?.email?.split('@')[0] || user?.name || 'maker';
```

**Chaves i18n a adicionar** (se ausentes) em todos os 5 locales:
```
greeting_morning   : "Bom dia," / "Good morning," / "Buenos días," ...
greeting_afternoon : "Boa tarde," / "Good afternoon," / "Buenas tardes," ...
greeting_evening   : "Boa noite," / "Good evening," / "Buenas noches," ...
```
(Verificar se já existem antes de adicionar.)

---

### B2. Área de input da boot screen — estilo Claude

O input da boot screen deve ser uma versão expandida e centralizada do textarea de chat,
posicionada na **metade inferior** da área central.

**Estrutura visual:**

```
┌───────────────────────────────────────────────────────────────┐
│  O que você quer fazer hoje?                                    │
│                                                                 │
│  (textarea auto-resize, mín 3 linhas)                           │
├───────────────────────────────────────────────────────────────┤
│  📎 Anexar          Gemini 2.5 Flash ▾              🚀 Enviar  │
└───────────────────────────────────────────────────────────────┘
```

**Componentes da toolbar inferior (esquerda para direita):**

1. **Botão Anexar** (`📎 Anexar`)
   - `<input type="file" multiple hidden ref={fileInputRef} />`
   - Clicar no botão dispara `fileInputRef.current.click()`
   - Por ora, apenas abre o seletor de arquivo (upload em si é escopo futuro)
   - Se já existir implementação de upload no `useChatSocket.js` ou no orquestrador, manter

2. **Seletor de modelo** — reutilizar o seletor que já existe na toolbar inferior do chat:
   - Deve exibir: `[provider] · [model] ▾`
   - Ao clicar, abre dropdown com modelos disponíveis (comportamento já implementado)
   - **Não duplicar lógica** — extrair ou reutilizar o componente existente

3. **Botão Enviar** (`🚀 Enviar`) — existente, manter comportamento via `<form onSubmit>`

**Placeholder do textarea da boot screen:** `t('boot_input_placeholder')` ou fallback `'O que você quer fazer hoje?'`

**Comportamento ao enviar:** idêntico ao atual — `sendMessage(v)`, `setCenterView('chat')`, sem `navigate()`.

> **Nota:** Seletor de esforço do modelo (Rápido / Padrão / Profundo) **não faz parte desta entrega.**
> Reservado para quando o backend suportar o parâmetro nativamente.

---

### B3. Placeholder do textarea do chat (bug ativo)

O textarea principal do chat exibe "Buscar no chat..." como placeholder — string errada.

Localizar em `App_auth_modular.jsx` ou `appAuthStyles.js` onde o placeholder está definido e corrigir para:
```js
placeholder={t('chat_input_placeholder') || 'Escreva uma mensagem…'}
```

Verificar se a chave `chat_input_placeholder` existe nos locales. Se não, adicionar:
```
en.json : "chat_input_placeholder": "Write a message…"
pt.json : "chat_input_placeholder": "Escreva uma mensagem…"
es.json : "chat_input_placeholder": "Escribe un mensaje…"
ar.json : "chat_input_placeholder": "…اكتب رسالة"
zh.json : "chat_input_placeholder": "输入消息…"
```

---

## Checklist de validação

### Sidebar
- [ ] Sidebar exibe exatamente: 📋 Conversas / + Nova conversa / 📝 Nova nota
- [ ] Nenhum item "Tarefas", "Chat", "Skills", "Doctor" visível
- [ ] Logo Open Slap! visível na base (expanded e collapsed)
- [ ] Collapsed: apenas ícones, sem texto
- [ ] "Conversas" ativa highlight quando `centerView === 'conversations'`
- [ ] View `conversations` tem input de busca funcional
- [ ] "Nova nota" abre placeholder (sem erro de console)

### Boot screen
- [ ] Nenhum ASCII art, nenhum texto `boot #v2.1#` ou `status▶`
- [ ] Saudação correta pelo horário (bom dia / boa tarde / boa noite)
- [ ] Username correto (prefixo do email, sem domínio)
- [ ] Textarea com placeholder correto e auto-resize mín 3 linhas
- [ ] Botão Anexar abre seletor de arquivo
- [ ] Seletor de modelo exibe provider e modelo ativos
- [ ] Enviar via Enter ou botão funciona e transiciona para o chat
- [ ] Placeholder do textarea do chat corrigido (não diz "Buscar no chat...")

---

## Commit (após validação visual)

```bash
git add frontend/src/components/layout/LeftSidebar.jsx
git add frontend/src/components/layout/AppLayout.jsx
git add frontend/src/App_auth_modular.jsx
git add frontend/src/styles/appAuthStyles.js
git add frontend/src/i18n/locales/en.json
git add frontend/src/i18n/locales/pt.json
git add frontend/src/i18n/locales/es.json
git add frontend/src/i18n/locales/ar.json
git add frontend/src/i18n/locales/zh.json
git commit -m "feat: sidebar simplification + boot screen restoration

- Sidebar: Conversas / Nova conversa / Nova nota (remove Tarefas, Chat, Skills, Doctor)
- Boot screen: remove ASCII art, show dynamic greeting + username
- Boot textarea: attach button + model selector + send (effort selector deferred)
- Fix chat textarea placeholder (was showing search string)
- Add conv_search_placeholder, chat_input_placeholder, greeting_* i18n keys"
```
