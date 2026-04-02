# Kickoff (Alta complexidade) — Automação + Auditoria (Processo Multi-Etapas)

## Contexto

Quero automatizar um processo recorrente de escritório com múltiplas etapas, revisão humana e auditoria completa.

Exemplo de processo:
- coletar dados (arquivos locais + e-mail)
- transformar/validar
- gerar entregáveis (documentos + planilhas)
- publicar/arquivar
- registrar histórico e permitir reprocessamento

## Objetivo

Criar uma solução local que execute o fluxo com aprovação por etapa e rastreabilidade (quem aprovou o quê, quando, com quais entradas/saídas).

## Escopo (primeira versão)

- Definir o pipeline em etapas explícitas
- Cada etapa produz artefatos e logs de auditoria
- Aprovação humana por etapa (pause/resume)
- Reexecução: rerun de uma etapa com inputs preservados

## Restrições e segurança

- Rodar localmente
- Não persistir credenciais; apenas tokens efêmeros por sessão/domínio
- Guardrails: proibir comandos perigosos por padrão; permitir por whitelist

## Requisitos não-funcionais

- Observabilidade: status por etapa + logs estruturados
- Idempotência: reexecutar não deve duplicar entregáveis sem intenção explícita
- Limites: timeout por etapa, tamanho máximo de arquivo, tamanho máximo de log

## Entregáveis

- Documento de design técnico (fluxo + estado + eventos)
- Schema de auditoria (SQLite)
- Protótipo de UI: timeline de etapas + botão de aprovação + área de artefatos
- Backlog inicial com prioridades

## Critérios de aceite

- Consigo executar o fluxo até um ponto e pausar para revisão
- Ao aprovar, o sistema continua do ponto correto
- Consigo ver artefatos gerados por etapa e o histórico completo

