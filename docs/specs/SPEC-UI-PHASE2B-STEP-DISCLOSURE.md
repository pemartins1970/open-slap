# SPEC-UI-PHASE2B — Step Disclosure

**Status:** Pronto para implementação  
**Bloco:** UI Phase 2B  
**Dependências:** Phase 1 completo (entry point migrado para `App_auth_modular.jsx`)  
**Esforço estimado:** 4–6h

---

## Contexto

Atualmente, execuções de `software_operator` (tool calls, comandos CLI, python-inline) são
renderizadas como blocos `CLIDisplay` expansivos e sempre visíveis no chat. Não há agrupamento,
sumário, nem colapso. O usuário vê todo o output bruto inline, o que polui o fluxo de
conversa quando há múltiplos steps de execução.

O objetivo é introduzir um padrão de **Step Disclosure** — análogo ao que Claude.ai faz com
tool use: uma linha clicável de sumário que expande para mostrar o detalhe da execução, output e
artefatos.

---

## Referência Visual

```
┌─────────────────────────────────────────────────────┐
│  ✓  Mapeou estrutura da codebase via python-inline ▸│  ← colapsado (default)
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  ✓  Mapeou estrutura da codebase via python-inline ▾│  ← expandido
├─────────────────────────────────────────────────────┤
│  [CLIDisplay completo — stdout, tempo, artefatos]   │
└─────────────────────────────────────────────────────┘

Status icons:
  ⟳  running  (animado se possível — sem dependência externa obrigatória)
  ✓  done / success
  ✗  error
```

---

## Escopo

### IN
- Componente `StepDisclosure.jsx` em `frontend/src/components/chat/`
- Integração em `App_auth_modular.jsx` (substituindo render direto de `CLIDisplay`)
- Estilos em `appAuthStyles.js`
- Label derivado de `visual_state_summary` ou do comando (fallback)
- Estado de colapso local por instância (`useState`)
- Suporte a `loadingTick` e `onOpenArtifact` (passados ao `CLIDisplay` interno)

### OUT
- Estado persistido entre sessões (localStorage)
- Animação CSS complexa no chevron (transição simples é suficiente)
- Agrupamento de múltiplos steps em uma única disclosure (cada step é independente)
- Mudanças no `chatSocketReducers.js` ou no backend
- Alteração no protocolo WebSocket

---

## Prerequisito — Entry Point

**Atenção:** a investigação de 13/06/2026 confirmou que o entry point ativo do app é
`main_auth.jsx → App_auth.jsx` (monolito), não `App_auth_modular.jsx`. A SPEC-UI-PHASE1
deve ser concluída e o entry point trocado para `main_auth.jsx → App_auth_modular.jsx`
**antes** de implementar esta spec. Implementar Step Disclosure no monolito geraria
retrabalho no wiring ao migrar para o modular.

---

## Componente `StepDisclosure.jsx`

### Localização
```
frontend/src/components/chat/StepDisclosure.jsx
```

### Interface
```jsx
StepDisclosure({
  cli,            // objeto cli do message (mesmo shape que CLIDisplay recebe via payload)
  loadingTick,    // int — passado ao CLIDisplay para animação de running
  onOpenArtifact, // fn — passado ao CLIDisplay para abrir artefatos
  styles,         // objeto de estilos global
})
```

### Implementação
```jsx
import { useState } from 'react';
import CLIDisplay from '../CLIDisplay';

const STATUS_ICON = {
  success: '✓',
  done:    '✓',
  error:   '✗',
  running: '⟳',
};

function deriveLabel(cli) {
  if (cli.visual_state_summary) return cli.visual_state_summary.slice(0, 80);
  const cmd = String(cli.command_executed || cli.command || '').trim();
  if (!cmd) return 'Executou comando';
  if (cmd.startsWith('python'))       return 'Executou Python';
  if (cmd.startsWith('node'))         return 'Executou Node.js';
  if (cmd.startsWith('git '))         return `git ${cmd.split(' ')[1] || ''}`.trim();
  if (cmd.startsWith('npm') || cmd.startsWith('npx')) return 'Executou npm';
  return cmd.slice(0, 60) + (cmd.length > 60 ? '…' : '');
}

const StepDisclosure = ({ cli, loadingTick, onOpenArtifact, styles }) => {
  const [expanded, setExpanded] = useState(false);
  const status = String(cli?.status || 'running').toLowerCase();
  const icon   = STATUS_ICON[status] || '•';
  const label  = deriveLabel(cli || {});
  const isRunning = status === 'running';

  return (
    <div style={styles.stepDisclosure}>
      <button
        style={{
          ...styles.stepDisclosureHeader,
          ...(isRunning ? styles.stepDisclosureHeaderRunning : {}),
        }}
        onClick={() => !isRunning && setExpanded(v => !v)}
        disabled={isRunning}
        title={isRunning ? 'Em execução…' : (expanded ? 'Colapsar' : 'Expandir')}
      >
        <span style={{
          ...styles.stepStatusIcon,
          color: status === 'error' ? 'var(--red)'
               : status === 'success' || status === 'done' ? 'var(--green)'
               : 'var(--text-dim)',
        }}>
          {icon}
        </span>
        <span style={styles.stepLabel}>{label}</span>
        {!isRunning && (
          <span style={styles.stepChevron}>{expanded ? '▾' : '▸'}</span>
        )}
      </button>

      {expanded && !isRunning && (
        <div style={styles.stepDisclosureBody}>
          <CLIDisplay
            payload={cli}
            loadingTick={loadingTick}
            onOpenArtifact={onOpenArtifact}
            styles={styles}
          />
        </div>
      )}
    </div>
  );
};

export default StepDisclosure;
```

---

## Estilos — Adições em `appAuthStyles.js`

```js
stepDisclosure: {
  border: '1px solid var(--border)',
  borderRadius: '8px',
  overflow: 'hidden',
  background: 'var(--bg2)',
  marginTop: '6px',
},
stepDisclosureHeader: {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  padding: '7px 12px',
  width: '100%',
  textAlign: 'left',
  background: 'transparent',
  border: 'none',
  cursor: 'pointer',
  color: 'var(--text)',
  fontSize: '12px',
  fontFamily: 'var(--mono)',
  transition: 'background 0.15s',
},
stepDisclosureHeaderRunning: {
  cursor: 'default',
  opacity: 0.75,
},
stepDisclosureBody: {
  borderTop: '1px solid var(--border)',
},
stepStatusIcon: {
  fontSize: '11px',
  minWidth: '12px',
},
stepLabel: {
  flex: 1,
  color: 'var(--text-secondary)',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
},
stepChevron: {
  color: 'var(--text-dim)',
  fontSize: '10px',
},
```

---

## Integração em `App_auth_modular.jsx`

### Import
```jsx
import StepDisclosure from './components/chat/StepDisclosure';
```

### Substituição do render de cliBlocks

**Antes** (em torno da linha com `CLIDisplay` no render de mensagens):
```jsx
{cliBlocks.length ? (
  <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
    {cliBlocks.map((cli, i) => (
      <CLIDisplay
        key={`cli-${i}`}
        payload={cli}
        loadingTick={loadingTick}
        onOpenArtifact={openCliArtifact}
        styles={styles}
      />
    ))}
  </div>
) : null}
```

**Depois:**
```jsx
{cliBlocks.length ? (
  <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
    {cliBlocks.map((cli, i) => (
      <StepDisclosure
        key={`cli-${i}-${cli?.command_executed || cli?.command || i}`}
        cli={cli}
        loadingTick={loadingTick}
        onOpenArtifact={openCliArtifact}
        styles={styles}
      />
    ))}
  </div>
) : null}
```

---

## Comportamento por Estado

| Status CLI | Header clicável | Expandido por default | Ícone |
|---|---|---|---|
| `running` | Não (disabled) | Não | ⟳ cinza |
| `done` / `success` | Sim | Não | ✓ verde |
| `error` | Sim | Sim (auto-expand para visibilidade) | ✗ vermelho |

**Nota sobre `error`:** auto-expandir em erro garante que o usuário veja o problema sem
precisar clicar. Implementar via `useState(status === 'error')` na inicialização.

---

## Arquivos Afetados

| Arquivo | Ação |
|---|---|
| `frontend/src/components/chat/StepDisclosure.jsx` | Criar (novo) |
| `frontend/src/styles/appAuthStyles.js` | Adicionar estilos `step*` |
| `frontend/src/App_auth_modular.jsx` | Substituir render `CLIDisplay` → `StepDisclosure` |

Não alterar:
- `chatSocketReducers.js`
- `CLIDisplay.jsx`
- Backend

---

## Critérios de Aceite

1. Steps de execução aparecem colapsados por default no chat
2. Click no header expande e mostra o CLIDisplay completo (output, tempo, artefatos)
3. Step em `running`: header não clicável, ícone ⟳, sem chevron
4. Step com `error`: auto-expandido, ícone ✗ vermelho
5. Step com `success/done`: colapsado, ícone ✓ verde, chevron visível
6. Label derivado de `visual_state_summary` quando disponível
7. Múltiplos steps na mesma mensagem: cada um tem estado independente
8. Sem regressão no fluxo de chat, aprovação de planos e ExecutionPanel
9. 125/125 testes passando
