# SPEC P-01: Auto-aprovação de Steps Não-Destrutivos (``plan_auto``)
**Status**: ✅ CONCLUÍDO
**Projeto**: Open Slap! v3
**Data**: 2026-06-08
**Prioridade**: Alta
**Assignee**: Opencode

---

## Contexto

Steps de tipo `plan` renderizam laranja com botão "Aprovar", exigindo intervenção manual do usuário. Steps de pesquisa, análise ou documentação (informacionais, sem efeito colateral) deveriam executar automaticamente. O frontend já suporta o tipo `plan_auto` no renderer (verde, label "Automático", sem botão) e no `useEffect` de auto-aprovação, mas o parser `parseMessageBlocks` jamais emitia `plan_auto`.

## Diagnóstico

`parseMessageBlocks` (linha 744) usava `remaining.startsWith('```plan')` — verdadeiro para ambos `plan` e `plan_auto`. O slice era sempre feito em `'```plan'.length` (7 chars), então um bloco ````plan_auto` virava `{ type: 'plan', content: '_auto\n...' }`. O tipo `plan_auto` jamais era emitido.

### Consequências em cascata
1. Renderer mostra laranja com botão "Aprovar" em vez de verde com "Automático"
2. `useEffect` de auto-aprovação (`b.type === 'plan_auto'`) nunca dispara
3. Usuário precisa aprovar manualmente tarefas que deveriam executar automaticamente

## Mudança

**Arquivo**: `frontend/src/App_auth.jsx`

**Função**: `parseMessageBlocks`, dentro do bloco `if (remaining.startsWith('```plan'))`:

```javascript
// ANTES
if (remaining.startsWith('```plan')) {
  const fenceEnd = remaining.indexOf('```', '```plan'.length);
  if (fenceEnd === -1) break;
  const inner = remaining.slice('```plan'.length, fenceEnd);
  blocks.push({ type: 'plan', content: inner.replace(/^\s+/, '').replace(/\s+$/, '') });
  remaining = remaining.slice(fenceEnd + 3);
  continue;
}

// DEPOIS
if (remaining.startsWith('```plan')) {
  const isAuto = remaining.startsWith('```plan_auto');
  const headerLen = isAuto ? '```plan_auto'.length : '```plan'.length;
  const fenceEnd = remaining.indexOf('```', headerLen);
  if (fenceEnd === -1) break;
  const inner = remaining.slice(headerLen, fenceEnd);
  blocks.push({
    type: isAuto ? 'plan_auto' : 'plan',
    content: inner.replace(/^\s+/, '').replace(/\s+$/, '')
  });
  remaining = remaining.slice(fenceEnd + 3);
  continue;
}
```

### O que NÃO muda
- `MessageBlock` — já renderiza `plan_auto` corretamente (verde, label "Automático", sem botão)
- `useEffect` de auto-aprovação — já busca `b.type === 'plan_auto'` e dispara orquestração
- `planAutoApproveAll` — comportamento inalterado
- `planAutoApproveInformational` — removido como dívida técnica (toggle órfão, não controlava nada)

## Cleanup Associado

Removido toggle `planAutoApproveInformational` do `SystemSettingsPanel.jsx` — estava visível mas o `useEffect` no chat não o consultava como condição. Toggle não fazia nada desde a implementação original.

Removida função `buildStartProjectPrompt` de `App_auth.jsx` — órfã desde a remoção dos CTAs (`ask_sabrina`, `start_project`) da sidebar. Seu único consumidor restante (`OnboardingModal`) foi atualizado para iniciar conversa sem `internalPrompt`.

## Smoke Test

Pedir à Sabrina uma análise que gere `plan_auto`, ou injetar manualmente:
````
```plan_auto
Verificar dependências desatualizadas | data_science
Gerar relatório de análise | project
```
````

Bloco deve aparecer **verde** com label **"Automático"** e executar sem pedir aprovação.
