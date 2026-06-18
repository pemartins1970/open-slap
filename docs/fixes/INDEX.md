# FIXES — Índice de Execução

**Gerado:** 2026-06-16  
**Contexto:** Reorganização pós-sessões 1781308737698 (2026-06-12) e 1781630495017 (2026-06-16)

---

## Ordem obrigatória

```
FIX-001  →  FIX-002 + FIX-003 (paralelos)  →  FIX-004
```

FIX-002 e FIX-003 tocam arquivos distintos e podem ser executados na mesma sessão, mas cada um deve ser **validado visualmente antes do seu commit**.

FIX-004 só executa após os três anteriores validados. É destrutivo (deleta arquivos).

---

## Resumo

| Fix | Arquivo | Escopo | Commit esperado |
|-----|---------|--------|-----------------|
| [FIX-001](FIX-001-GIT-SNAPSHOT.md) | — | `git add -A` snapshot de segurança | `wip: snapshot pre-cleanup` |
| [FIX-002](FIX-002-SIDEBAR-BOOT.md) | `LeftSidebar.jsx`, `AppLayout.jsx`, `App_auth_modular.jsx`, 5 locales | Sidebar (3 itens) + boot screen clean + textarea fix | `feat: sidebar + boot screen` |
| [FIX-003](FIX-003-SETTINGS-MODAL.md) | `App_auth_modular.jsx`, 5 locales | Settings modal: i18n fix, props Security, activeProvider mount | `fix(settings): props + i18n` |
| [FIX-004](FIX-004-CLEAN-SRC.md) | 18 arquivos deletados, `node_modules` reinstalado | Remoção de monolito legado e scripts de debug | `chore: clean src` |

---

## Regras de execução

1. **Um fix por vez.** Não acumular alterações de vários fixes no mesmo estado não-commitado.
2. **Validar antes de commitar.** O checklist de cada fix deve ser verificado no browser antes do `git commit`.
3. **Reportar diverguides.** Se algum arquivo não estiver no estado esperado pelo fix, reportar antes de implementar — não assumir e prosseguir.
4. **Não usar `git add -A` nos commits de FIX-002 e FIX-003.** Apenas os arquivos listados em cada fix.
5. **FIX-004 usa `git add -A`** propositalmente (captura as deleções e o novo `package-lock.json`).

---

## Arquivos NÃO tocar nesta sequência

- `frontend/src/hooks/useChatSocket.js` — WebSocket estável, não incluir nos fixes
- `frontend/src/components/layout/RightPanel.jsx` — collapse já funciona, não regredir
- `backend/` — nenhuma alteração de backend nesta sequência
- `frontend/vite_auth.config.js` — não alterar

---

## Pós-FIX-004: backlog confirmado

Pós limpeza, as pendências são:

- [ ] Settings modal: tab "Central de Habilidades" (Skills) com `SkillsPanel`
- [ ] Settings modal: System tab com props completos (Doctor + System Map)
- [ ] Wire-up real de Notas (`/api/notes`, editor, lista)
- [ ] Harmonização dos dois padrões de collapse (sidebar esquerdo vs painel direito)
- [ ] Collapse do sidebar esquerdo: alinhar ao padrão do RightPanel
