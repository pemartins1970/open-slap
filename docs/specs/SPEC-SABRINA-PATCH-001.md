# SPEC-SABRINA-PATCH-001 — Sequência de Geração de Artefatos

**Status:** Pronto para implementação  
**Prioridade:** Alta — bug recorrente, multi-modelo  
**Esforço estimado:** 15 min (edição de string, dois arquivos)  
**Dependências:** Nenhuma — independente de fases UI

---

## Problema

A Sabrina usa `<FILES_JSON>` para persistir **código Python** em vez do **output resultante da execução** desse código. Esse comportamento é consistente entre modelos (Gemini, Groq, modelos locais), o que confirma que a causa é a ausência de instrução no system prompt — não comportamento pontual de um modelo específico.

Consequências observadas no diálogo de QA:

1. Arquivo `.md` criado contém código Python como corpo (inútil como documentação)
2. Agente dispara `python-inline` como segundo passo gerando um segundo arquivo com nome diferente
3. Ao término da orquestração, nenhum conteúdo é apresentado ao usuário — `"Orquestração concluída"` sem entrega visível do artefato

---

## Causa Raiz

Ausência de regra explícita sobre:
- A sequência obrigatória `executar → capturar output → persistir output`
- O que `<FILES_JSON>` deve ou não deve conter
- A obrigação de apresentar o resultado final ao usuário

---

## Problema Secundário — Dois Sources of Truth

O system prompt da Sabrina existe em **dois lugares** com versões já divergentes:

| Arquivo | Uso |
|---|---|
| `backend/agents/sabrina_agent.py` | `BaseAgent.stream_execute()` |
| `backend/moe_router_simple.py` (linha ~490) | MoE router — roteamento por keywords |

O próprio código marca esse problema com `# TODO futuro: MoE e BaseAgent lerem o mesmo source of truth`. Até essa unificação ser feita, **qualquer patch deve ser aplicado nos dois arquivos**.

---

## Patch — Bloco a Inserir

Inserir o bloco abaixo imediatamente após o bloco `"Execução e Interação:\n"` nos dois arquivos.

```
"Geração de artefatos:\n"
"- Use <FILES_JSON> APENAS para persistir conteúdo já gerado — nunca para salvar código que deveria ser executado.\n"
"- Sequência obrigatória ao gerar arquivo com conteúdo dinâmico: "
"(1) execute o código via python-inline, "
"(2) capture o output, "
"(3) persista o output com <FILES_JSON>.\n"
"- Ao concluir tarefa que gerou arquivo, leia o arquivo e apresente o conteúdo final ao usuário.\n\n"
```

---

## Arquivos Afetados

### `backend/agents/sabrina_agent.py`

**Localização:** após a linha que contém `"Se for um início de fluxo técnico simples, seja curta..."` no bloco `SABRINA_SYSTEM_PROMPT`.

**Antes:**
```python
    "Execução e Interação:\n"
    "- Responda ao usuário de forma natural. Narre seu raciocínio (Chain of Thought narrativo).\n"
    "- REGISTRO DE PROGRESSO: Durante entrevistas ou processos de design, use a tag `[[add_step: Descrição]]` para registrar marcos no menu lateral. Isso informa o progresso de forma silenciosa.\n"
    "- Se for um início de fluxo técnico simples, seja curta, mas em fases de design, seja explicativa.\n\n"
    "Plano executável:\n"
```

**Depois:**
```python
    "Execução e Interação:\n"
    "- Responda ao usuário de forma natural. Narre seu raciocínio (Chain of Thought narrativo).\n"
    "- REGISTRO DE PROGRESSO: Durante entrevistas ou processos de design, use a tag `[[add_step: Descrição]]` para registrar marcos no menu lateral. Isso informa o progresso de forma silenciosa.\n"
    "- Se for um início de fluxo técnico simples, seja curta, mas em fases de design, seja explicativa.\n\n"
    "Geração de artefatos:\n"
    "- Use <FILES_JSON> APENAS para persistir conteúdo já gerado — nunca para salvar código que deveria ser executado.\n"
    "- Sequência obrigatória ao gerar arquivo com conteúdo dinâmico: "
    "(1) execute o código via python-inline, "
    "(2) capture o output, "
    "(3) persista o output com <FILES_JSON>.\n"
    "- Ao concluir tarefa que gerou arquivo, leia o arquivo e apresente o conteúdo final ao usuário.\n\n"
    "Plano executável:\n"
```

---

### `backend/moe_router_simple.py`

**Localização:** o bloco do prompt da Sabrina começa em torno da linha 490, dentro de `prompt=(...)`. Localizar a string `"Se for um início de fluxo técnico simples, seja curta"` e inserir o bloco após ela.

**Antes:**
```python
    "- Se for um início de fluxo técnico simples, seja curta, mas em fases de design, seja explicativa.\n\n"
    "Plano executável (apenas quando necessário):\n"
```

**Depois:**
```python
    "- Se for um início de fluxo técnico simples, seja curta, mas em fases de design, seja explicativa.\n\n"
    "Geração de artefatos:\n"
    "- Use <FILES_JSON> APENAS para persistir conteúdo já gerado — nunca para salvar código que deveria ser executado.\n"
    "- Sequência obrigatória ao gerar arquivo com conteúdo dinâmico: "
    "(1) execute o código via python-inline, "
    "(2) capture o output, "
    "(3) persista o output com <FILES_JSON>.\n"
    "- Ao concluir tarefa que gerou arquivo, leia o arquivo e apresente o conteúdo final ao usuário.\n\n"
    "Plano executável (apenas quando necessário):\n"
```

---

## Limitações do Patch

Este patch reduz a frequência do problema em modelos capazes (Gemini 2.5, Groq 70B). **Não é garantia** para modelos locais menores (llama3.2:1b, Qwen 4B) que têm menor aderência a instruções complexas. A solução arquitetural completa (validação semântica no orchestrator + step obrigatório de entrega) está especificada em item separado do backlog.

---

## Critérios de Aceite

1. Bloco `"Geração de artefatos:\n"` presente em ambos os arquivos, na posição correta
2. Texto idêntico nos dois arquivos
3. Teste de regressão: diálogo `"Mapeie a codebase e gere um md"` produz arquivo `.md` com estrutura de diretórios, não código Python
4. 125/125 testes unitários passando (patch é só string, sem lógica)
