# Guidelines — Projetos Node.js e Estrutura de Dependências

Documento de referência para contribuidores ao trabalhar em projetos Node.js neste repositório. Objetivo: evitar proliferação de `node_modules` isolados, `package.json` duplicados e subprojetos Node não consolidados.

---

## O problema que este documento resolve

Durante o desenvolvimento, é comum surgirem múltiplos diretórios Node independentes dentro do mesmo repositório. Isso explode o tamanho do código distribuído (centenas de MB) e torna manutenção/CI mais lenta e frágil.

---

## Regras obrigatórias

### Regra 1 — Um único ponto de entrada Node por produto

Cada produto tem exatamente um diretório com `package.json` ativo. Todos os componentes de frontend vivem dentro dele.

### Regra 2 — Componentes são pastas, não subprojetos

Um componente React (editor, toolbar, widget) não tem seu próprio `package.json`. Ele é uma pasta dentro do projeto frontend principal.

### Regra 3 — Verificar antes de criar

Antes de executar `npm init`, `npx create-vite`, ou qualquer comando que gere um novo `package.json`, verificar:

```bash
find . -name "package.json" -not -path "*/node_modules/*"
```

Se existir qualquer resultado, usar o projeto existente como base antes de criar um novo.

### Regra 4 — Backend TypeScript não é um projeto Node separado por padrão

O backend Python (FastAPI) não precisa de um subprojeto Node. Se houver necessidade real de TypeScript no backend, isso deve ser claramente justificado e documentado. Evitar duplicar stacks sem ganho claro.

### Regra 5 — Experimentos não entram no repositório principal

Se for necessário prototipar um componente isolado:
- Prototipar fora do repositório ou em branch separada.
- Após validação, integrar como pasta dentro do projeto Node existente.
- Nunca versionar `node_modules` de experimentos.

---

## Estrutura de referência — Open Slap!

Estrutura canônica do repositório (alto nível):

```
open-slap/
├── docs/
└── src/
    ├── backend/   (Python/FastAPI)
    └── frontend/  (Node/React/Vite)
```

---

## Checklist antes de qualquer sessão de desenvolvimento Node

```
[ ] Existe apenas um package.json ativo fora de node_modules?
    → find . -name "package.json" -not -path "*/node_modules/*"

[ ] O componente que vou criar é uma pasta, não um subprojeto?

[ ] Se vou usar TypeScript em um componente novo, ele vai para src/frontend/src/?

[ ] Há node_modules órfãos de sessões anteriores?
    → find . -type d -name "node_modules" -maxdepth 4

[ ] O .gitignore cobre todos os node_modules?
    → grep "node_modules" .gitignore
```

---

## Checklist antes de commitar ou gerar ZIP de distribuição

```
[ ] Nenhum node_modules no ZIP/commit
    → node_modules são regenerados com npm install

[ ] O dist/ do frontend está excluído (quando aplicável)

[ ] O .env está excluído (nunca versionar credenciais)

[ ] Nenhum cache/runtime Python no ZIP/commit
    → Excluir: __pycache__/, *.pyc, .pytest_cache/, .mypy_cache/

[ ] Nenhum banco local no ZIP/commit
    → Excluir: *.db / *.sqlite e afins
```

---

# Guidelines — Node.js Projects and Dependency Layout

Reference for contributors working on Node.js projects in this repository. Goal: avoid duplicated `node_modules`, duplicate `package.json` files, and fragmented Node subprojects.

---

## Mandatory rules

- Single active Node entrypoint per product (`src/frontend/` is the canonical one).
- Components are folders, not independent Node projects.
- Check existing `package.json` files before creating a new one.
- Avoid adding TypeScript backend subprojects unless clearly justified.
- Don’t merge experiments with their own dependency trees into main.

