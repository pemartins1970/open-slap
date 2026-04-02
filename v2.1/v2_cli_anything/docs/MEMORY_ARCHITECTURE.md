# Arquitetura de Memória — Open Slap!

## Princípios

- Memória é “pista”, não verdade. Deve ser verificada antes de usar.
- Contexto permanente precisa ser leve para não poluir prompts.
- Consolidação acontece em background com gatilhos estáveis.

## Memória Permanente (RAW)

- Armazenamento integral e imutável do histórico bruto de chat em SQL (mensagens/conversas).
- Nunca apagada por processos de consolidação (“Dream”) ou pruning.
- Pode ser indexada e pesquisada sob demanda por pedido explícito do usuário (“procure o que eu disse sobre X”).
- Fornece “proveniência” para memórias estruturadas (message_id/conversation_id).

## Camadas

- Índice leve (permanente no contexto): linhas curtas com ponteiros para “topic files”. Não guarda fatos brutos.
- Topic files: documentos específicos (por tema/projeto) com conteúdo real. Carregados sob demanda.
- Transcrições e logs: nunca re-injetar inteiros; buscar identificadores específicos.

## Consolidação (“Dream”)

- Subagente que roda com gatilhos:
  - tempo desde último “sonho”
  - número de sessões
  - lock exclusivo para evitar concorrência
- Fases:
  - Orient: listar tópicos e ler índice
  - Gather: coletar sinais novos (logs, memórias desatualizadas, transcrições)
  - Consolidate: atualizar topic files, normalizar datas e deletar contradições
  - Prune: manter índice enxuto (limite de linhas/tamanho)

## Taxonomia

- user (perfil/preferências)
- feedback (correções/confirmacoes)
- project (contexto do trabalho)
- reference (ponteiros para sistemas externos)
- Evitar “deriváveis do código” (estrutura, patterns, history) no índice permanente.

## Aplicação no Open Slap!

- SQLite + FTS possuem os fatos; o índice leve referencia paths/chaves.
- O agente trata hits de memória como pistas; revalida antes de agir.
- O “Dream” consolida tópicos e mantém o índice abaixo de limites.
- O RAW não é alterado pelo Dream; memórias estruturadas referenciam RAW por proveniência.
- Endpoint de busca RAW: filtra mensagens do usuário por consulta textual e retorna resultados com links de origem.
