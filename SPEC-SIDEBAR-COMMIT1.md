# SPEC: Sidebar Simplification — Commit 1

**Data:** 2026-06-16  
**Escopo:** Sidebar esquerdo + conversas com busca + placeholder notes + git commit limpo  
**Agente executor:** Opencode  
**Validador:** Claude (via relatório)

---

## Contexto

O frontend está funcional mas o menu lateral exibe itens que ainda não são necessários na fase atual (Chat, Skills, Doctor como navegação direta). A meta é simplificar o sidebar para três ações únicas e preparar o git para commits atômicos e rastreáveis daqui em diante.

---

## Mudanças — 5 arquivos

---

### 1. `frontend/src/i18n/locales/*.json` — adicionar chave `conv_search_placeholder`

Adobe os 5 arquivos de locale com a chave `conv_search_placeholder` (inserir próximo de `note_search_placeholder` em cada arquivo):

```
en.json  : "conv_search_placeholder": "Search conversations…"
pt.json  : "conv_search_placeholder": "Buscar conversas…"
es.json  : "conv_search_placeholder": "Buscar conversaciones…"
ar.json  : "conv_search_placeholder": "…ابحث في المحادثات"
zh.json  : "conv_search_placeholder": "搜索对话…"
```

---

### 2. `frontend/src/components/layout/LeftSidebar.jsx`

**Remover:**
- `DEFAULT_NAV_ITEMS` atual (conversations, chat, skills, doctor)
- Bloco do botão `onCreateConversation` separado (linhas ~78-97)
- Seção "Recent" de conversas (linhas ~148-172)
- `navItems` prop e seu loop de renderização

**Reescrever:** substituir toda a área de conteúdo da sidebar por três itens fixos:

```
1. Conversas       → navItem, key='conversations', i18n t('conversations'), icon '📋'
2. Nova conversa   → button, onClick=onCreateConversation, i18n t('new_conversation')
3. Nova nota       → button, onClick=onCreateNote, i18n t('note_new')
```

**Comportamento collapsed:** mostrar apenas ícone, sem texto.

**Props a adicionar:**
```js
onCreateNote,   // () => void — nova prop
```

**Estrutura JSX alvo (expanded):**
```jsx
<div style={styles.sidebarContent}>
  <div style={styles.sidebarSection}>
    {/* Header: label MENU + botão colapsar */}
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      {!isCollapsed && <div style={styles.sidebarTitle}>{t('menu')}</div>}
      <button
        style={styles.iconButton}
        onClick={() => { if (isMobile) { if (onMobileClose) onMobileClose(); return; } if (onToggle) onToggle(); }}
        title={isCollapsed ? t('menu_expand') : t('menu_collapse')}
        className="slap-collapse-toggle"
        hidden={isMobile}
      >
        {isCollapsed ? '»' : '«'}
      </button>
    </div>

    <div style={{ height: '12px' }} />

    {/* Nav: Conversas */}
    <button
      style={{
        ...styles.sidebarButton,
        ...(centerView === 'conversations' ? styles.sidebarButtonActive : {}),
        textAlign: isCollapsed ? 'center' : 'left',
        justifyContent: isCollapsed ? 'center' : 'flex-start',
      }}
      onClick={() => onNavigate('conversations')}
      title={t('conversations')}
    >
      {'📋'}{!isCollapsed && ` ${t('conversations')}`}
    </button>

    <div style={{ height: '8px' }} />

    {/* Action: Nova conversa */}
    <button
      style={{
        ...styles.sidebarButton,
        fontWeight: 600,
        textAlign: isCollapsed ? 'center' : 'left',
        justifyContent: isCollapsed ? 'center' : 'flex-start',
      }}
      onClick={onCreateConversation}
      title={t('new_conversation')}
    >
      {'+'}{!isCollapsed && ` ${t('new_conversation').replace(/^\+ ?/, '')}`}
    </button>

    <div style={{ height: '8px' }} />

    {/* Action: Nova nota */}
    <button
      style={{
        ...styles.sidebarButton,
        textAlign: isCollapsed ? 'center' : 'left',
        justifyContent: isCollapsed ? 'center' : 'flex-start',
      }}
      onClick={onCreateNote}
      title={t('note_new')}
    >
      {'📝'}{!isCollapsed && ` ${t('note_new')}`}
    </button>
  </div>
</div>
```

**Manter:** logo inferior (bloco `onGoHome`), mobile drawer, collapse toggle.

---

### 3. `frontend/src/components/layout/AppLayout.jsx`

**Adicionar prop:**
```js
onCreateNote,   // () => void
```

**Passar para LeftSidebar:**
```jsx
<LeftSidebar
  ...
  onCreateNote={onCreateNote}   // ← adicionar
/>
```

---

### 4. `frontend/src/App_auth_modular.jsx`

**a) Adicionar estado de busca** (junto dos outros `useState` do componente):
```js
const [convSearchQuery, setConvSearchQuery] = useState('');
```

**b) Adicionar handler de nova nota** (após `handleSelectConversation`):
```js
const handleCreateNote = () => {
  setCenterView('notes');
  navigate('/notes');
};
```

**c) Passar para AppLayout:**
```jsx
<AppLayout
  ...
  onCreateNote={handleCreateNote}   // ← adicionar
>
```

**d) Adicionar view `notes`** no bloco condicional de centerView (após o bloco `'doctor'`):
```jsx
: centerView === 'notes' ? (
  <div style={{ ...styles.centerPanel, display: 'flex', flexDirection: 'column', height: '100%' }}>
    <div style={styles.centerPanelTitle}>{t('notes_label')}</div>
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ fontSize: '13px', color: 'var(--text-dim)', textAlign: 'center' }}>
        {t('note_select_hint')}
      </div>
    </div>
  </div>
)
```

**e) Substituir a view `conversations`** pelo bloco com busca:
```jsx
: centerView === 'conversations' ? (
  <div style={{ ...styles.centerPanel, display: 'flex', flexDirection: 'column', height: '100%' }}>
    <div style={styles.centerPanelTitle}>{t('conversations')}</div>

    {/* Busca */}
    <div style={{ padding: '0 0 12px 0' }}>
      <input
        type="text"
        value={convSearchQuery}
        onChange={e => setConvSearchQuery(e.target.value)}
        placeholder={t('conv_search_placeholder')}
        style={{
          width: '100%',
          background: 'var(--bg2)',
          border: '1px solid var(--border)',
          borderRadius: '6px',
          padding: '8px 12px',
          fontSize: '13px',
          color: 'var(--text)',
          outline: 'none',
          boxSizing: 'border-box'
        }}
      />
    </div>

    <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0' }}>
      {(() => {
        const filtered = convSearchQuery.trim()
          ? conversations.filter(c =>
              (c.title || '').toLowerCase().includes(convSearchQuery.toLowerCase())
            )
          : conversations;
        if (filtered.length === 0) {
          return (
            <div style={{ fontSize: '13px', color: 'var(--text-dim)', textAlign: 'center', padding: '40px 0' }}>
              {t('no_conversations')}
            </div>
          );
        }
        return filtered.map((conv) => (
          <button
            key={conv.id}
            type="button"
            onClick={() => handleSelectConversation(conv.id)}
            style={{
              display: 'block',
              width: '100%',
              background: currentConversation === conv.id ? 'var(--accent-bg)' : 'transparent',
              border: 'none',
              borderBottom: '1px solid var(--border)',
              padding: '12px 16px',
              cursor: 'pointer',
              fontSize: '13px',
              color: 'var(--text)',
              textAlign: 'left'
            }}
          >
            <div style={{ fontWeight: 500 }}>{conv.title || t('new_conversation')}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
              {formatCompactDateTime(conv.created_at || conv.createdAt || '')}
            </div>
          </button>
        ));
      })()}
    </div>
  </div>
)
```

---

## Checklist pós-implementação (Opencode deve reportar)

- [ ] Sidebar exibe apenas: 📋 Conversas / + Nova conversa / 📝 Nova nota
- [ ] Collapsed mode: apenas ícones visíveis, sem texto
- [ ] Clicar em "Conversas" → centerView = 'conversations' com input de busca visível
- [ ] Busca filtra conversas pelo título em tempo real (sem requisição ao backend)
- [ ] Clicar em "Nova conversa" → comportamento idêntico ao anterior
- [ ] Clicar em "Nova nota" → centerView = 'notes', placeholder exibido
- [ ] Nenhum erro de console relacionado a props indefinidas (onCreateNote, etc.)
- [ ] Seção "Recent" não aparece no sidebar
- [ ] `t('conv_search_placeholder')` retorna texto correto (não a própria key)
- [ ] Itens de Skills, Doctor, Chat não aparecem no sidebar

---

## Git commit (executar APÓS validação visual)

```bash
cd C:\Agent\open-slap-v3
git add frontend/src/components/layout/LeftSidebar.jsx
git add frontend/src/components/layout/AppLayout.jsx
git add frontend/src/App_auth_modular.jsx
git add frontend/src/i18n/locales/en.json
git add frontend/src/i18n/locales/pt.json
git add frontend/src/i18n/locales/es.json
git add frontend/src/i18n/locales/ar.json
git add frontend/src/i18n/locales/zh.json
git commit -m "feat(sidebar): simplify nav to Conversas / Nova conversa / Nova nota

- Remove Chat, Skills, Doctor from sidebar nav
- Remove Recent conversations list from sidebar
- Add Nova nota placeholder (centerView='notes')
- Add search filter to conversations view (client-side, no backend call)
- Add onCreateNote prop through AppLayout -> LeftSidebar
- Add conv_search_placeholder i18n key (5 locales)"
```

**Não usar `git add -A`** — commitar apenas os arquivos listados acima.

---

## Fora de escopo (próximos commits)

- Wire-up real do editor de notas (fetch /api/notes, save, delete)
- Mobile drawer behavior com os novos itens
- Busca server-side de conversas (quando volume crescer)
- Animações de transição entre views
