# QA Validation — B-06 Context Persistence
**Data:** 2026-06-09
**Autor:** QA / Pê

---

## Test 1: Pipeline Sanity (Baseline)

**Comando:** "planeje a refatoração do arquivo C:\Agent\teste\main_auth.py com 3 tarefas"

**Resultado:** ✅ Pipeline de orquestração operacional
- PLAN gerado → auto-aprovado → EXECUÇÃO concluída, 0 falhas
- Observação: truncagem visível no output (corte abrupto em "ex") — confirmar se é bug de renderização ou artefato de copy-paste

---

## Test 2: B-06 Context (Same Session, No Reload)

**Turno 1:** "meu nome é Pê e estou trabalhando em Python"
**Turno 2:** "qual é o meu nome e em que linguagem trabalho?"

**Resultado:** ❌ Parcial — ambiguidade no prompt
- Nome "Pê" recuperado ✅
- Linguagem: respondeu "português" (interpretou como idioma, não Python)
- Inconclusivo: pode ser ambiguidade linguística ou "Salvar informações" mascarando o resultado

---

## Test 3: B-06 Context (After Page Reload)

**Turno 1:** "meu nome é Pê e a linguagem de programação que uso é Python"
→ Reload da página
**Turno 2 (mesma conversa):** "qual é o meu nome e qual linguagem de programação uso?"

**Resultado:** ❌❌ B-06 NÃO está funcionando
- Nome "Pê" recuperado ✅ (via "Salvar informações", não via histórico)
- Python: NÃO recuperado ❌ — LLM confabulou: "O sistema no qual estou operando utiliza Python para automação e lógica"

---

## Conclusões

1. **B-06 não funciona** — histórico da conversa não sobrevive a reload. Prioridade crítica confirmada.
2. **"Salvar informações" mascara B-06** — usuário percebe que o sistema "lembra" parcialmente e assume que contexto funciona, até o LLM confabular algo errado.
3. **Bug no "Salvar informações"** — salvou nome mas não Python da mesma frase. Falha de extração que merece investigação separada.
4. **Confabulação confirmada** — LLM sem contexto fabrica resposta plausível em vez de admitir que não sabe. Risco de produção.

---

## Recomendação

Ordem mantida: B-06 → B-07 → B-08. Adicionar "B-09: Bug no Salvar informações (extração seletiva)" como item separado.
