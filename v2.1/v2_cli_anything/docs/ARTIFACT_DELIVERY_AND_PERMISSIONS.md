# Entrega de artefatos e permissões (sandbox / escrita de arquivos / conectores)

Este documento registra o comportamento esperado do Open Slap ao “entregar” artefatos (arquivos, scaffolds de projeto, Markdown etc.) sob diferentes permissões de segurança.

Objetivo: servir como base de conhecimento para orientar a Sabrina e outros agentes no momento de planejar a entrega, especialmente quando a escrita local estiver desabilitada.

## Conceitos e termos

- **Artefato**: qualquer saída “entregável” gerada pelo agente (ex.: `README.md`, um pacote com múltiplos arquivos, um template de projeto, um relatório, um zip lógico, um preview).
- **Escrita local**: gravar arquivos no disco do computador onde o servidor do Open Slap está rodando.
- **Conectores**: integrações externas (ex.: GitHub, Google Drive, Google Calendar, Gmail, Telegram etc.).
- **Automation client (externo)**: um serviço remoto (ex.: Tera/automator) que executa automações fora do Open Slap, autenticado por Base URL + API key (Bearer). Um endpoint típico para teste é `GET /health`.
- **Sandbox mode**: modo mais restritivo, pensado para reduzir risco de exfiltração/alteração local e limitar capacidades do agente.

## Matriz de entrega (visão prática)

### 1) Escrita local **ativada**

Quando **Permitir escrita de arquivos = ativado**, o agente pode:

- Criar/atualizar arquivos no disco local (ex.: gerar um projeto completo com múltiplos arquivos).
- Retornar ao usuário um resumo do que foi criado e, quando aplicável, um link de preview local.
- Registrar a entrega para visualização/consulta.

Uso típico:
- Scaffold de projetos (backend/frontend), geração de templates, atualização de arquivos de configuração, criação de relatórios em arquivo.

### 2) Escrita local **desativada**

Quando **Permitir escrita de arquivos = desativado**, o agente **não deve gravar nada no disco local**.

Nessa condição, a entrega muda de estratégia:

- **Markdown/arquivo único**: entregar o conteúdo diretamente no chat (ex.: bloco Markdown), com instruções claras de como salvar localmente se o usuário quiser.
- **Pacote com múltiplos arquivos (“um sistema”)**: entregar como:
  - Árvore de diretórios (estrutura) + conteúdo de cada arquivo em blocos.
  - Passo a passo para o usuário criar o projeto manualmente.
  - Checklist de validação (ex.: como rodar lint/build/test).
- **Entrega externa (se conectores permitidos)**: preferir “materializar fora do computador local”, por exemplo:
  - GitHub: criar branch/PR com os arquivos.
  - Google Drive: enviar arquivo(s) e compartilhar link.
  - Gmail/Telegram: enviar o artefato ou link (quando aplicável).
  - Automation client: criar o pacote em um ambiente remoto e devolver link/preview.

Notas importantes:
- Mesmo com escrita local desativada, o agente ainda pode entregar “artefatos” no sentido de **conteúdo e instruções**. A diferença é que o resultado não aparece automaticamente como arquivos no disco local.
- Se o objetivo é evitar escrita local, mas permitir “entrega pronta”, habilitar conectores/automation client costuma ser o caminho mais fluido.

### 3) Sandbox mode

O sandbox deve ser tratado como “modo mais restritivo”:

- Tipicamente restringe capacidades como escrita local, execução de comandos e conectores (dependendo da política do servidor).
- Se sandbox estiver ativado e conectores também estiverem bloqueados, a entrega tende a ser:
  - Conteúdo no chat + instruções, sem materializar em disco e sem publicar em serviços externos.

Recomendação operacional:
- Se o usuário quer máxima privacidade/segurança, use sandbox e entregue em texto.
- Se o usuário quer entrega pronta (fora do disco local), mantenha sandbox desativado, desative escrita local e use conectores/automation client.

## Diretrizes para a Sabrina (tom de produto)

Quando o usuário pedir “entregar um sistema” e a escrita local estiver desativada:

1) Avisar claramente que o Open Slap não vai gravar arquivos no disco local por causa das permissões.
2) Perguntar (ou assumir, se já estiver definido) o canal de entrega:
   - “Você quer que eu entregue como conteúdo no chat (estrutura + arquivos), ou prefere publicar via GitHub/Drive?”
3) Se o canal escolhido for “chat”, entregar com:
   - Estrutura de pastas
   - Conteúdo dos arquivos
   - Comandos para rodar
   - Checklist final (lint/test/build)
4) Se o canal escolhido for conector:
   - Confirmar qual conector e quais credenciais estão conectadas
   - Executar a entrega no destino e devolver link/PR/ID

## Comportamento atual (implementação)

No backend atual, quando uma solicitação é interpretada como “pedido de escrita de arquivos”, mas **allow_file_write** está desabilitado, a resposta retorna uma mensagem de aviso informando que a escrita de arquivos está desabilitada. O sistema não grava arquivos localmente.

Referência de código (para manutenção):
- `src/backend/main_auth.py` — bloco de tratamento de “file request” e checagem de `allow_file_write`.

