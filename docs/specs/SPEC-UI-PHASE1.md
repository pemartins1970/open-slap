# SPEC-UI-PHASE1 — Three-Zone Shell

**Status:** Pronto para implementação  
**Bloco:** UI Phase 1  
**Dependências:** B-09 fechado, Chronicle integrado (162/162 passando)

---

## Contexto

`App_auth_modular.jsx` é o entry point ativo (substitui o monolito `App_auth.jsx`).  
Os componentes em `components/layout/` (`AppLayout`, `LeftSidebar`, `MainContent`, `RightPanel`, `RightSidebar`) existem como scaffold mas **não estão conectados** ao app modular — o layout atual é inline no próprio `App_auth_modular.jsx`.

---

## Objetivo

Conectar o three-zone layout shell ao `App_auth_modular.jsx`, migrar i18n para sistema baseado em arquivos com 5 idiomas, e converter a settings view em modal. Funcionalidade existente deve operar identicamente após a refatoração.

**Regra absoluta:** zero features novas nesta fase.

---

## Escopo

### IN
- Wiring do `AppLayout` no `App_auth_modular.jsx` (substituir layout inline)
- Left sidebar: item "Conversas" + botão "Nova Conversa"
- Right panel: coluna persistente presente na estrutura, **conteúdo placeholder** (Phase 3 preenche)
- Settings: modal overlay (remover `centerView === 'settings'`)
- i18n: migração para react-i18next com arquivos por idioma
- Navbar: wiring do `Header` existente ao `AppLayout`
- Routing: rotas React Router para as views principais

### OUT
- Nenhuma feature nova
- Conteúdo novo no settings
- Conteúdo real do painel direito (consumo de sessão, artefatos, previews) — Phase 3
- Integrações externas — Phase 4
- MarkItDown, model selector — Phase 2

---

## Especificação de Layout

### Três Zonas

| Zona | Largura | Comportamento |
|---|---|---|
| Left sidebar | 240px expandida / 0px colapsada | Toggle via botão no header |
| Center main | flex-1 | Tabs VS Code-style |
| Right panel | 320px fixo | Persistente, sempre visível |

Right panel oculto em viewports < 900px (mobile: drawer opcional, fora de escopo desta fase).

### Left Sidebar — Conteúdo Phase 1

```
[ Nova Conversa ]          ← botão topo, sempre visível
─────────────────
Conversas →                ← item de navegação; clique → view ConversationList
                           (exibe listagem com recursos atuais existentes)
```

A lista inline de conversas recentes no sidebar atual (`slice(0,10)`) pode ser mantida como está — refinamento posterior conforme nota do produto.

### Center Main — Tabs Phase 1

```
[ Chat ] [ Skills ] [ Doctor ]
```

Settings removido das tabs — migrado para modal.  
Tab ativa por padrão: Chat.

### Right Panel — Especificação

- **Tipo:** coluna fixa persistente, parte do layout (não drawer/overlay)
- **Conteúdo Phase 1:** placeholder — label "Status" ou similar, área vazia estilizada
- **Conteúdo Phase 3:** consumo da sessão, artefatos, previews (fora de escopo agora)
- **Sem overlay de fundo** — é parte fixa do layout
- Chat e ExecutionPanel permanecem no centro, sem alteração

> `RightPanel.jsx` atual é um drawer com `position: fixed` + overlay. Reescrever como coluna fixa dentro do `AppLayout`. `RightSidebar.jsx` pode ser o ponto de partida se tiver estrutura de coluna — verificar antes de escolher qual reaproveitar.

### Header (Navbar)

```
[ ☰ toggle ]   [ ● connected  runtime_llm_label ]   [ ⚙ settings ] [ sign out ]
```

Wiring do componente `Header.jsx` existente. Sem mudança de conteúdo.

---

## i18n — Migração

### Estado atual

```javascript
// src/i18n/translations_auth.js
export const translations = {
  pt: { key: "valor", ... },
  en: { key: "value", ... },
  es: { key: "valor", ... }  // parcialmente incompleto
}

// Uso via prop drilling em todos os componentes:
const t = (key) => translations[lang][key] || key
```

### Target

**Biblioteca:** `react-i18next` + `i18next`

**Estrutura de arquivos:**
```
src/i18n/
  index.js          ← configuração i18next
  locales/
    en.json         ← idioma padrão (instalação limpa)
    pt.json
    es.json
    ar.json         ← placeholder: keys ausentes fallback para EN
    zh.json         ← placeholder: keys ausentes fallback para EN
```

**Idioma padrão:** `en` (instalação limpa)

**RTL:** quando `lang === 'ar'`, aplicar `document.documentElement.dir = 'rtl'`; demais idiomas: `'ltr'`.

**Regras de migração:**
1. `npm install react-i18next i18next`
2. Criar `src/i18n/index.js` com configuração padrão i18next
3. Extrair todas as chaves de `translations_auth.js` para os arquivos `.json` — **sem renomear chaves**
4. AR e ZH: arquivos com objeto vazio `{}` (fallback automático para EN via `fallbackLng`)
5. Substituir `t` prop drilling por hook `const { t } = useTranslation()` em cada componente
6. Remover `translations_auth.js` após migração validada

**Configuração mínima `src/i18n/index.js`:**
```javascript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import pt from './locales/pt.json';
import es from './locales/es.json';
import ar from './locales/ar.json';
import zh from './locales/zh.json';

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, pt: { translation: pt },
                es: { translation: es }, ar: { translation: ar }, zh: { translation: zh } },
  lng: 'en',
  fallbackLng: 'en',
  interpolation: { escapeValue: false }
});

export default i18n;
```

---

## Settings — Migração para Modal

### Estado atual
`centerView === 'settings'` renderiza o settings content na área principal, com tabs `general | system | llm | security` e componentes `SystemSettingsPanel`, `LlmSettingsPanel`, `SecuritySettingsPanel`.

### Target

**Modal overlay** acionado pelo botão ⚙ no header.

**Comportamento:**
- Abre: clique no botão ⚙ no header
- Fecha: botão `×`, tecla `Escape`, clique no overlay
- Mantém estado da tab ativa durante a sessão
- Conteúdo idêntico ao atual (sem mudanças nos painéis)

**Implementação:**
```jsx
// Estado
const [settingsOpen, setSettingsOpen] = useState(false);

// No Header: onClick={() => setSettingsOpen(true)}

// Modal (no App_auth_modular.jsx, acima do AppLayout):
{settingsOpen && (
  <div style={styles.modalOverlay} onClick={() => setSettingsOpen(false)}>
    <div style={styles.settingsModal} onClick={e => e.stopPropagation()}>
      {/* tabs + painéis existentes, sem alteração */}
    </div>
  </div>
)}
```

`centerView === 'settings'` removido do switch de views.

---

## Routing

### Estado atual
Apenas `/login` existe. Navegação principal via `centerView` state.

### Target

```
/login          → Login (sem alteração)
/               → redirect → /chat (se autenticado) ou /login
/chat           → Chat view (centerView = 'chat')
/chat/:convId   → Chat + seleciona conversa
/conversations  → ConversationList view
/skills         → Skills view (centerView = 'skills')
/doctor         → Doctor view (centerView = 'doctor')
*               → redirect → /chat (autenticado) ou /login
```

`centerView` pode permanecer como mecanismo interno — as rotas sincronizam com ele via `useNavigate` / `useParams`.

---

## Arquivos Afetados

### Criar
| Arquivo | Ação |
|---|---|
| `src/i18n/index.js` | novo — config react-i18next |
| `src/i18n/locales/en.json` | novo — extraído de translations_auth.js |
| `src/i18n/locales/pt.json` | novo |
| `src/i18n/locales/es.json` | novo |
| `src/i18n/locales/ar.json` | novo — objeto vazio, fallback EN |
| `src/i18n/locales/zh.json` | novo — objeto vazio, fallback EN |

### Modificar
| Arquivo | Mudança |
|---|---|
| `App_auth_modular.jsx` | wiring AppLayout, settings modal, routing sync, remoção layout inline |
| `components/layout/AppLayout.jsx` | conectar right panel persistente |
| `components/layout/LeftSidebar.jsx` | wire dados reais de conversas |
| `components/layout/RightPanel.jsx` | reescrever como coluna fixa (remover fixed+overlay) |
| `components/layout/Header.jsx` | wire ao AppLayout, adicionar trigger settings modal |
| `package.json` | adicionar react-i18next, i18next |
| todos os componentes com prop `t` | migrar para `useTranslation()` |

### Arquivar (não deletar imediatamente)
| Arquivo | Ação |
|---|---|
| `src/i18n/translations_auth.js` | manter até i18n validada, então remover |

---

## Riscos

**Alto**
- `App_auth_modular.jsx` tem estado e handlers extensos atrelados ao layout inline — o wiring do `AppLayout` exige threading cuidadoso de props. Risco de regressão no WebSocket e no fluxo de chat.
- Migração de i18n é uma mudança transversal: afeta todos os componentes que recebem `t` como prop.

**Médio**
- `RightPanel.jsx` precisa ser reescrito (de `position: fixed` + overlay para coluna fixa). O componente atual não é aproveitável sem refatoração significativa.
- AR/ZH: verificar que keys ausentes fazem fallback corretamente para EN em runtime.

**Baixo**
- `react-i18next` adiciona ~30KB ao bundle — irrelevante no perfil de hardware alvo.
- `RightSidebar.jsx` (9.2KB) pode ser removido ou absorvido — verificar se tem dependências antes de descartar.

---

## Critérios de Aceite

1. Três zonas renderizam: left sidebar, center tabs, right panel persistente (placeholder)
2. Left sidebar: "Conversas" navega para a view de listagem; "Nova Conversa" funciona
3. Sidebar colapsa/expande via toggle no header; estado persiste em `localStorage`
4. Settings abre como modal; fecha via `×`, `Escape` e overlay; todas as tabs funcionam
5. i18n: `useTranslation()` em uso; 5 idiomas carregam sem erro; EN é o padrão em instalação limpa
6. AR ativa `dir="rtl"` no `document.documentElement`
7. Rotas `/chat`, `/chat/:convId`, `/conversations`, `/skills`, `/doctor` funcionam
8. Chat central, ExecutionPanel e aprovação de planos funcionam sem regressão
9. Todos os testes passam — 162/162
10. Sem degradação perceptível de performance no i5-6200U / 16GB
