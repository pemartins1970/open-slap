# FIX-004: Clean Src — Remoção de Resíduos e Reinstalação

**Data:** 2026-06-16  
**Tipo:** Limpeza de repositório + reinstalação limpa  
**Executor:** Opencode  
**Pré-requisito:** FIX-001 + FIX-002 + FIX-003 todos executados E validados visualmente  
**Não executar antes** dos fixes anteriores estarem confirmados funcionando

---

## Contexto

O diretório `frontend/src/` contém dois tipos de resíduos que causam ruído:

1. **Arquivos legados de app** — `App_auth.jsx` (401KB, 7772 linhas) e `App_auth_backup_ref.jsx` (440KB, 8520 linhas). Dois produtos completos dormentes no mesmo `src/`, potencialmente confundindo o cache do Vite e qualquer ferramenta de análise.

2. **Scripts de debug de sessões anteriores** — 16 arquivos `.cjs`, `.mjs`, `.js`, `.ps1` criados para depurar o `App_auth.jsx` durante as sessões de junho. Não fazem parte do produto.

Total a remover: 18 arquivos, ~855KB de código morto.

---

## Pré-verificação obrigatória (antes de deletar qualquer coisa)

```bash
# Confirmar que nenhum arquivo ativo importa App_auth.jsx
grep -r "from.*App_auth[^_]" frontend/src --include="*.jsx" --include="*.js"
# Resultado esperado: nenhuma linha

# Confirmar entry point
cat frontend/index.html | grep script
# Deve conter: src/main_auth.jsx

# Confirmar que main_auth.jsx importa App_auth_modular.jsx (não App_auth.jsx)
head -10 frontend/src/main_auth.jsx
```

Se algum import ativo de `App_auth.jsx` for encontrado: **parar e reportar**. Não deletar.

---

## Arquivos a deletar

### Grupo 1 — Legado de app (2 arquivos, ~841KB)

```
frontend/src/App_auth.jsx              ← monolito legado, 7772 linhas
frontend/src/App_auth_backup_ref.jsx   ← backup de referência, 8520 linhas
```

### Grupo 2 — Scripts de debug (16 arquivos)

```
frontend/src/debug_chars.cjs
frontend/src/end_depth.cjs
frontend/src/find_exact.cjs
frontend/src/find_exact_lines.cjs
frontend/src/find_problem.cjs
frontend/src/fix_message_list.mjs
frontend/src/test_parse.cjs
frontend/src/test_parse.js
frontend/src/trace_accurate.cjs
frontend/src/trace_depth.cjs
frontend/src/trace_depth.ps1
frontend/src/trace_key_lines.cjs
frontend/src/trace_v2.cjs
frontend/src/track_depth.cjs
frontend/src/track_depth.js
frontend/src/track_full.cjs
```

### Grupo 3 — Spec obsoleta na raiz do projeto

```
SPEC-SIDEBAR-COMMIT1.md   ← supersedida por FIX-002-SIDEBAR-BOOT.md
```

---

## Comando de deleção

```bash
cd C:\Agent\open-slap-v3

# Grupo 1
del frontend\src\App_auth.jsx
del frontend\src\App_auth_backup_ref.jsx

# Grupo 2
del frontend\src\debug_chars.cjs
del frontend\src\end_depth.cjs
del frontend\src\find_exact.cjs
del frontend\src\find_exact_lines.cjs
del frontend\src\find_problem.cjs
del frontend\src\fix_message_list.mjs
del frontend\src\test_parse.cjs
del frontend\src\test_parse.js
del frontend\src\trace_accurate.cjs
del frontend\src\trace_depth.cjs
del frontend\src\trace_depth.ps1
del frontend\src\trace_key_lines.cjs
del frontend\src\trace_v2.cjs
del frontend\src\track_depth.cjs
del frontend\src\track_depth.js
del frontend\src\track_full.cjs

# Grupo 3
del SPEC-SIDEBAR-COMMIT1.md
```

---

## Reinstalação limpa do frontend

```bash
cd C:\Agent\open-slap-v3\frontend

# Remover node_modules e lock
rmdir /s /q node_modules
del package-lock.json

# Reinstalar
npm install
```

**Observação:** `package.json` tem `"postinstall": "npm audit --audit-level=high"` — o audit roda automaticamente. Se retornar vulnerabilidades críticas: reportar antes de continuar. Se retornar apenas warnings de severity baixa: prosseguir.

---

## Verificação pós-instalação

```bash
# Dev server sobe sem erros?
npm run dev
# Aguardar: "Local: http://localhost:517X/" sem erros de módulo
# Abrir browser e confirmar que o produto carrega normalmente

# Build de produção compila sem erros?
npm run build
# Deve terminar com: "built in Xs" sem erros de transform ou import
```

**Erros esperados que são aceitáveis:** warnings de bundle size. **Não aceitáveis:** `Cannot resolve module`, `Failed to transform`, `SyntaxError`.

---

## Checklist de validação visual pós-limpeza

Retestar o fluxo completo após a reinstalação:

- [ ] Login funciona
- [ ] Boot screen exibe saudação dinâmica + username (FIX-002 preservado)
- [ ] Sidebar exibe Conversas / Nova conversa / Nova nota (FIX-002 preservado)
- [ ] Logo na base do sidebar visível
- [ ] Modal de settings abre, todas as 4 tabs respondem (FIX-003 preservado)
- [ ] JWT exibe valores reais (FIX-003 preservado)
- [ ] Envio de mensagem funciona (WebSocket conecta, resposta aparece)
- [ ] Console sem erros críticos no browser DevTools

---

## Commit final

```bash
cd C:\Agent\open-slap-v3
git add -A
git commit -m "chore: clean src — remove legacy monolith and debug scripts

- Delete App_auth.jsx (7772 lines, 401KB) — monolith superseded by App_auth_modular.jsx
- Delete App_auth_backup_ref.jsx (8520 lines, 440KB) — reference no longer needed
- Delete 16 debug scripts (*.cjs, *.mjs, *.js, *.ps1) from src/
- Delete SPEC-SIDEBAR-COMMIT1.md (superseded by docs/fixes/FIX-002-SIDEBAR-BOOT.md)
- Fresh npm install: node_modules regenerated from package.json
- Build verified: npm run build succeeds without errors"
```

---

## Estrutura esperada de `src/` após limpeza

```
frontend/src/
├── App_auth_modular.jsx     ← único arquivo de app ativo
├── main_auth.jsx            ← entry point
├── components/
├── hooks/
├── i18n/
├── lib/
├── pages/
├── styles/
```

Nenhum arquivo `.cjs`, `.mjs`, `.ps1` ou monolito legado em `src/`.

---

## Próximos passos após FIX-004

Com o repositório limpo e o build verificado, o projeto entra em modo de 
**desenvolvimento incremental com commit por entrega**: cada feature nova ou 
correção confirmada gera um commit atômico antes de avançar.

Pendências pós-cleanup identificadas:
- Wire-up real do editor de notas (`/api/notes`)
- Settings modal: tab Skills (Central de Habilidades)
- Settings modal: System tab com props completos do Doctor
- Harmonização dos dois mecanismos de collapse (sidebar esquerdo vs painel direito)
