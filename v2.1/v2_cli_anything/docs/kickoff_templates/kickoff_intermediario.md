# Kickoff (Intermediário) — Dashboard de Vendas (CSV → Insights)

## Contexto

Tenho exports CSV de vendas e quero um dashboard local para análise e relatórios.

## Objetivo

Importar CSV, limpar dados, gerar métricas e gráficos e permitir exportação de relatórios.

## Escopo

- Importar 1 ou mais CSVs (layout documentado)
- Normalizar/validar campos
- Métricas: total, ticket médio, top produtos, top clientes, evolução temporal
- Filtros: período, produto, canal, região
- Exportar: CSV filtrado e relatório em Markdown

## Restrições

- Rodar localmente (Windows)
- Dados podem ser sensíveis: evitar logs com conteúdo bruto

## Requisitos não-funcionais

- Tempo de carga aceitável para ~100k linhas
- UI responsiva, com estados de loading/erro claros

## Entregáveis

- Spec do formato CSV esperado + exemplos
- Plano com tarefas (frontend, backend, parsing, testes)
- Artefatos: relatório de exemplo em Markdown e dataset de teste (falso)

## Critérios de aceite

- Importo um CSV e vejo métricas básicas em menos de 10 segundos
- Filtros funcionam e exportação gera arquivo
- Erros de parsing são mostrados com linha/coluna

