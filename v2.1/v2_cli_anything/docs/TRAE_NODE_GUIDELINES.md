# Guidelines para Trae — Projetos Node.js e Estrutura de Dependências

> Documento de referência para o agente Trae ao trabalhar em projetos da família Open Slap! / Slap! PRO.  
> Objetivo: evitar a proliferação de diretórios `node_modules` isolados, `package.json` duplicados e subprojetos Node não consolidados.

---

## O problema que este documento resolve

Durante o desenvolvimento do Open Slap! v2.0, foram encontrados **4 diretórios Node independentes** dentro do mesmo repositório:

```
src/frontend/              ← frontend ativo (React + Vite, JSX simples)
src/src/frontend/          ← frontend duplicado (React + Vite + TypeScript + Tailwind)
src/src/backend/           ← servidor TypeScript sem função no produto final
src/src/components/rtwe/   ← editor experimental, nunca integrado
```

Cada um com seu próprio `node_modules`, somando mais de **700 MB** de dependências para um produto cujo frontend ativo tem apenas ~5 MB de código. O ZIP de distribuição teve que excluir manualmente esses diretórios após o fato.

---

## Regras obrigatórias

### Regra 1 — Um único ponto de entrada Node por produto

Cada produto tem **exatamente um** diretório com `package.json` ativo. Todos os componentes de frontend vivem dentro dele.

```
✅ CORRETO
src/
└── frontend/          ← único package.json, único node_modules
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   └── pages/
    ├── package.json
    └── vite.config.js

❌ ERRADO
src/
├── frontend/          ← package.json nº 1
├── src/frontend/      ← package.json nº 2 (duplicado!)
└── src/components/x/  ← package.json nº 3 (componente isolado!)
```

### Regra 2 — Componentes são pastas, não subprojetos

Um componente React (editor, toolbar, widget) **não tem seu próprio `package.json`**. Ele é uma pasta dentro do projeto frontend principal.

```
✅ CORRETO — componente como pasta
src/frontend/src/components/
├── Editor/
│   ├── index.tsx
│   ├── Toolbar.tsx
│   └── editor.css
└── Chat/
    └── index.tsx

❌ ERRADO — componente como subprojeto independente
src/components/editor/
├── package.json      ← não deve existir
├── node_modules/     ← 180 MB desperdiçados
├── vite.config.ts
└── src/
```

### Regra 3 — Verificar antes de criar

Antes de executar `npm init`, `npx create-vite`, ou qualquer comando que gere um novo `package.json`, verificar:

```bash
find . -name "package.json" -not -path "*/node_modules/*"
```

Se existir qualquer resultado, **usar o projeto existente** como base antes de criar um novo.

### Regra 4 — Backend TypeScript não é um projeto Node separado

O backend Python (FastAPI) não precisa de um subprojeto Node. Se houver necessidade de TypeScript no backend (ex: um servidor Express complementar), ele deve:

1. Estar claramente justificado e documentado
2. Compartilhar o `package.json` do frontend quando possível
3. Ou ter um único `package.json` na raiz, não em `src/src/backend/`

### Regra 5 — Experimentos não entram no repositório principal

Se for necessário prototipar um componente isolado (ex: um editor rico, um player, um widget):

1. Prototipar fora do repositório ou em uma branch separada
2. Após validação, **integrar como pasta** dentro do projeto Node existente
3. Nunca fazer merge de um experimento com seu próprio `node_modules` no branch principal

---

## Estrutura de referência — Open Slap!

Esta é a estrutura correta e canônica do Open Slap! após a consolidação:

```
open-slap/
├── docs/                         ← documentação do projeto
│   ├── README.md
│   ├── INSTALLATION.md
│   └── ...
└── src/
    ├── .env.example              ← variáveis de ambiente
    ├── backend/                  ← projeto Python (FastAPI)
    │   ├── main_auth.py
    │   ├── db.py
    │   ├── moe_router_simple.py
    │   ├── llm_manager_simple.py
    │   ├── auth.py
    │   ├── requirements.txt      ← dependências Python (pip, não npm)
    │   └── tests/
    │       ├── test_runtime_gates.py
    │       └── test_new_features.py
    └── frontend/                 ← único projeto Node do repositório
        ├── package.json          ← ÚNICO package.json ativo
        ├── vite_auth.config.js
        ├── index.html
        └── src/
            ├── App_auth.jsx      ← componente raiz
            ├── main_auth.jsx     ← entry point
            ├── hooks/
            │   └── useAuth.js
            └── pages/
                └── Login.jsx
```

**Não existe** `src/src/`, `src/components/`, nem nenhum outro diretório Node fora de `src/frontend/`.

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
    → Os node_modules são regenerados com npm install — nunca devem ser versionados

[ ] Nenhum package.json de experimento ou subprojeto descartado

[ ] O dist/ do frontend está excluído (usuário faz build localmente)

[ ] O .env está excluído (nunca versionar credenciais)

[ ] Nenhum cache/runtime Python no ZIP/commit
    → Excluir: __pycache__/, *.pyc, .pytest_cache/, .mypy_cache/

[ ] Nenhum banco local no ZIP/commit
    → Excluir: src/data/*.db (ex.: auth.db)

[ ] Se o ZIP for gerado por "zip -r" (filesystem), aplicar exclusões explícitas
    → Exemplo:
      zip -r v2.zip src/ docs/ ^
        --exclude "src/.mypy_cache/*" ^
        --exclude "src/**/__pycache__/*" ^
        --exclude "src/.pytest_cache/*" ^
        --exclude "src/frontend/node_modules/*" ^
        --exclude "src/frontend/dist/*" ^
        --exclude "src/data/*.db" ^
        "*.pyc"
```

---

## Por que isso importa — impacto real

| Situação | Tamanho |
|---------|---------|
| Open Slap! código-fonte real (v2.0) | ~2.5 MB |
| Open Slap! com 4 node_modules ativos | ~750 MB |
| Diferença | **300x** |

Um ZIP de 750 MB para um projeto de 2.5 MB não é negligência — é uma falha arquitetural que inviabiliza distribuição, aumenta tempo de clone, e polui o histórico de versões.

---

## Para o Trae: perguntas de verificação obrigatórias

Antes de qualquer ação que crie estrutura de projeto Node, responder:

1. **"Existe algum `package.json` ativo neste repositório?"**  
   → Se sim, usar esse projeto. Não criar outro.

2. **"O que estou criando é um componente ou um produto separado?"**  
   → Componente: pasta dentro do frontend existente.  
   → Produto separado: repositório separado.

3. **"Este experimento vai para produção ou é exploratório?"**  
   → Exploratório: branch isolada ou fora do repo. Nunca no main.

4. **"O usuário vai precisar de `npm install` em mais de um lugar?"**  
   → Se a resposta for sim, algo está errado. Revisar estrutura antes de continuar.

---

*Este documento deve ser lido no início de qualquer sessão de desenvolvimento que envolva frontend, componentes React ou qualquer integração Node.js no ecossistema Open Slap! / Slap! PRO.*
