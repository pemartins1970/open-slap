# Open Slap! — Spec P-02: Force-Cancel de Orquestração
**Data:** 2026-06-09  
**Status:** Código existe sem spec formal nem teste validado

---

## Contexto

Um modelo local (llama3.2:1b) entrou em loop infinito de `[[add_step:]]` durante orquestração. Não havia mecanismo de interrupção pelo frontend. A única saída foi matar o processo via terminal. O código de cancelamento foi implementado posteriormente sem spec nem teste. Este documento formaliza o comportamento esperado e define os critérios de aceite que o código existente deve satisfazer — ou que devem ser implementados se o código não os cobrir.

---

## 0. PASSO OBRIGATÓRIO: Auditar o código existente antes de qualquer implementação

Antes de escrever qualquer linha nova, mapear o que existe:

1. Onde está o código de cancelamento no backend? (Suspeito: `ws/orchestrator.py`)
   - Existe uma flag de cancelamento? (`is_cancelled`, `cancel_event`, `CancellationToken`?)
   - A flag é checada dentro do loop de execução de steps?
   - É checada durante o streaming do LLM ou apenas entre steps?

2. No frontend (App_auth.jsx ou componente de chat):
   - Existe um botão de cancelamento?
   - O botão envia alguma mensagem WebSocket? Qual `type`?
   - O botão aparece/desaparece com base no estado de orquestração ativo?

3. O que acontece com o estado após o cancelamento?
   - A mensagem parcial do assistant é persistida no DB ou descartada?
   - O frontend recebe algum evento de confirmação do cancelamento?

**A spec abaixo descreve o comportamento correto. O que não estiver implementado deve ser adicionado. O que estiver implementado mas divergir deve ser corrigido.**

---

## Descrição do problema

Durante orquestração ativa (qualquer estado entre `PLAN` aprovado e `done`), o usuário não tem mecanismo para interromper a execução. Em casos de loop infinito, o sistema fica preso sem saída disponível pelo frontend.

---

## Comportamento esperado

### Frontend

**1. Botão "Cancelar"**

- Aparece **somente** quando há orquestração ativa (estado: entre aprovação do PLAN e recebimento de `done` ou `error`)
- Desaparece ao receber `done`, `error` ou `cancelled` do backend
- Posicionamento: próximo à área de input, visível sem scroll — não enterrado na interface
- Label: "Cancelar" (ou ícone de stop com tooltip)
- Estado de loading: ao clicar, desabilitar o botão imediatamente para evitar double-click (o backend confirma o cancelamento via WS)

**2. Mensagem WebSocket enviada ao clicar**

O frontend envia via WebSocket:
```json
{ "type": "cancel_orch", "run_id": "uuid-da-orquestracao" }
```

E também faz uma requisição HTTP POST para `/api/plan/orchestrate/{run_id}/cancel` como redundância. O backend processa ambos e ativa o evento `asyncio.Event` correspondente ao `run_id`.

**3. Feedback ao usuário**

Ao receber confirmação de cancelamento do backend, exibir na conversa:

```
[Orquestração cancelada pelo usuário]
```

Como mensagem de sistema (não como mensagem do assistant nem do user), estilizada de forma neutra.

---

### Backend

**1. Recepção do evento `cancel`**

O handler WebSocket deve:
- Ao receber `{"type": "cancel"}`, ativar a flag de cancelamento para a sessão/conversa ativa
- Não bloquear — retornar imediatamente; o cancelamento efetivo ocorre na próxima checagem do orchestrator

**2. Flag de cancelamento**

- Deve ser checada **entre cada step** do loop de execução
- Deve ser checada **após cada chunk de streaming** do LLM — este ponto é crítico para o caso de loop infinito de geração de steps
- Se a flag estiver ativa quando checada: interromper imediatamente, não executar o próximo step

**3. Limpeza de estado ao cancelar**

- Encerrar o stream LLM ativo se houver (fechar o generator/iterator)
- Emitir via WebSocket:
  ```json
  { "type": "cancelled", "conversation_id": 123 }
  ```
  (Não emitir `{"type": "done"}` — o frontend diferencia cancelamento de conclusão normal)
- Persistir no DB a mensagem parcial do assistant como cancelada (ou descartar — **escolher uma política e documentar**)
  - **Recomendação:** persistir com flag `status = 'cancelled'` para não perder contexto, mas não exibir como mensagem completa no histórico
- Resetar a flag de cancelamento para a sessão

**4. Caso de loop infinito especificamente**

O loop de `[[add_step:]]` ocorre quando o LLM gera steps indefinidamente. O cancel deve interromper o streaming mid-geração — não apenas entre steps completos. Verificar se a checagem da flag está dentro do loop de chunks do stream, não apenas no loop externo de steps.

---

## Casos de teste formais

### Teste 1 — Cancel entre steps (fluxo normal)
```
1. Enviar tarefa que gera plano com 3+ steps
2. Aprovar o plano
3. Aguardar início da execução do step 1
4. Clicar "Cancelar"
5. Verificar:
   - Botão desaparece
   - Mensagem "[Orquestração cancelada pelo usuário]" aparece na conversa
   - Nenhum step adicional é executado após o cancelamento
   - Backend para de processar (log confirma)
```

### Teste 2 — Cancel durante streaming do LLM
```
1. Enviar tarefa que gera resposta longa do LLM (ex: "escreva um texto longo sobre Python")
2. Clicar "Cancelar" enquanto o texto ainda está sendo streamado
3. Verificar:
   - Stream para imediatamente (não continua chegando texto)
   - Mensagem de cancelamento aparece
   - Sem erro 500 ou exception não tratada no backend
```

### Teste 3 — Cancel em loop infinito (caso crítico)
```
1. Forçar condição de loop: enviar prompt que induza geração contínua de [[add_step:]]
   (ex: com llama3.2:1b em tarefa ambígua/aberta)
2. Aguardar 2-3 segundos de loop visível
3. Clicar "Cancelar"
4. Verificar:
   - Loop para em no máximo 1-2 chunks após o clique (não aguarda step completo)
   - Sistema volta ao estado idle
   - Nova mensagem pode ser enviada normalmente após o cancelamento
```

### Teste 4 — Idempotência: double-click no botão
```
1. Iniciar orquestração
2. Clicar "Cancelar" duas vezes rapidamente
3. Verificar:
   - Apenas um evento "cancel" processado no backend
   - Sem duplicate de mensagem de cancelamento na conversa
   - Sem erro no backend
```

### Teste 5 — Botão não aparece quando não há orquestração ativa
```
1. Conversa em estado idle (sem orquestração)
2. Verificar: botão "Cancelar" não está visível
3. Enviar mensagem simples (sem orquestração)
4. Verificar: botão não aparece para resposta direta da Sabrina
```

---

## Acceptance criteria (resumo)

- [ ] Botão "Cancelar" visível apenas durante orquestração ativa
- [ ] Clique envia `{"type": "cancel_orch", "run_id": "..." }` via WebSocket + HTTP POST redundante
- [ ] Backend interrompe execução na próxima checagem (entre steps E dentro do stream)
- [ ] Mensagem de cancelamento aparece na conversa
- [ ] Sistema volta ao estado idle — nova mensagem pode ser enviada imediatamente
- [ ] Sem exceções não tratadas no backend durante cancelamento
- [ ] Double-click idempotente — sem duplicatas nem erros
- [ ] Teste 3 (loop infinito) passa: sistema recuperável sem restart

---

## Riscos

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Flag checada apenas entre steps, não dentro do stream | Alta — loop infinito sugere isso | Verificar posição da checagem no código existente; mover para dentro do loop de chunks se necessário |
| Estado do frontend não reseta após cancelamento (botão some mas input fica bloqueado) | Média | Garantir que `cancelled` do backend dispara o mesmo reset de estado que `done` |
| Mensagem parcial do assistant persiste no DB sem flag, poluindo histórico B-06 | Média | Definir política de persistência agora; `status='cancelled'` é mais seguro que discard |
