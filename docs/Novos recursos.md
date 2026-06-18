Precisamos repensar em como integrar agentes cli ao Open Slap!. Tínhamos um conceito, que visava termos um painel de controle de operação de agentes externos, que se perdeu, mas foi apropriado pelo Hermes. Isso foi pensado no início do projeto, cogitamos usar Containers (ao invés de vmc) como ambiente local - e que pode ser convertido em uma VPS, caso seja de interesse do usuário - mas nunca aplicamos na prática. Seria algo interessante para avaliarmos, pensarmos e estruturarmos corretamente, caso prossigamos nesta direção. 

Agentes considerados inicialmente para uma integração:

- pi
- open claw
- Hermes
- kimi

Como o Open Claw vai em breve vai receber intergação nativa do Windows, será fundamental estarmos acompanhando isso e preparados. Os agentes externos seriam exibidos na nova interface do Open Slap!, usariam nossa estrutura de memória e outros recursos, e a Sabrina poderia utilizá-los sempre que fosse necessário. Como temos a possibilidade de exportar/importar histórico de chats de outros agentes, isso poderia ser muito bem utilizado aqui.

Notas importantes:

- Vale a pena clonarmos localmente os projetos e analisarmos o src em profundidade, para avaliarmos oportunidades e insights. Aliás, antes de avançarmos nas mudanças de frontend e feaures, seria realmente bom fazer isso.

- A vercel lançou um agente browser que dizem ser melhor do que playwright e afins: https://github.com/vercel-labs/agent-browser

- O Google lançou o Gemma 4 12B multimodal, com a promessa de rodar locaslmente em equipamentos de 8 e 16 gb de ram. Vou testá-la hoje. Não me parece ser viável para programação, mas para conversação, transcrição de áudios curtos (30 segundos) em textos pode ser um candidato. 

Messengers: Temos alta demanda de cobrança de usuários para termos algo nativo, intuitivo e simples de configurar na interface, que permita ao agente enviar e receber mensagens.

Mensageiros prioritários:

- Telegram (o mais simples de implementar)
- Slack
- Discord


Na sequência:

- Whatsapp (mais complexo, pode implicar em custos, a não ser que tenhamos alguma solução "simples" para conectar o agente à interface whatsapp web usando QR Code. Ou verificarmos bibliotecas python gratuitas). Uma opção que me foi sugerida seria usar a biblioteca pywhatkit, importá-la como kit e abrir o whatsapp web. Segundo mencionado, isso permitiria ao sistema usar o comando sendwhatmsg_intantly() para usar mensagens na hora.
- IRC
- Microsoft Teams
- Signal

Conectores:

- Google (e-mail, calendar, chat...)
- sms (twilio)
- Meu navegador (permitir que o agente acesse o navegador com credenciais logadas)


importante: Podemos transformar em Yalms nativos as integrações e conectores adicionais, para o usuário poder selecionar quais 'projetos" internos deseja acrescentar em seu sistema, de formaa personalizá-lo? Já tínhamos conversado sobre isso antes. Por exemplo, o usuário qe quiser utilizar o remotion (https://github.com/remotion-dev/remotion), ou o Canvas para a criação de vídeos através do Open Slap!


Notas

- Agent Notes
- User Notes
- Projet Notes
- Events (Derivado de cron Jobs e eventos de calendário do usuário).

MCPs para o open slap!

- Google Adsense

https://developers.google.com/google-ads/api/docs/developer-toolkit/mcp-server?hl=pt-br

- AI Studio

https://github.com/eternnoir/aistudio-mcp-server
C:\Agent\mcp-servers\aistudio-mcp-bridge (o que pedimos para o AI Studio gerar)

Aqui está um resumo de como configurar e utilizar o bridge:
🔑 O que colocar como MCP_API_KEY?
A MCP_API_KEY é o token de autenticação estrito enviado no cabeçalho X-MCP-API-KEY.
Como funciona hoje: Caso você não configure essa variável de ambiente, o sistema gera um UUID aleatório seguro a cada inicialização e o mostra no painel.
Como deixar permanente: Vá até o menu Settings / Secrets (Segredos) na barra lateral esquerda da interface do Google AI Studio e adicione uma nova chave com o nome MCP_API_KEY e defina um valor à sua escolha (como uma senha longa e forte). Desse modo, o token será persistido e você não precisará alterar o arquivo do Claude Desktop/Cursor toda vez que reiniciar.
📄 Conteúdo Estruturado no README.md
O novo arquivo README.md detalha todas as diretivas operacionais do servidor:
Configurações Prontas: Modelos de JSON pré-formatados prontos para copiar e colar no arquivo claude_desktop_config.json tanto para macOS quanto para Windows.
Fronteiras de Segurança (O que permite vs. O que não permite):
Permitido: Leitura e alteração de arquivos de desenvolvimento sob src/, criação automática de subdiretórios, ping de conexão e chamadas seguras de prompts ao Gemini (gemini-2.5-flash) sem expor sua chave de IA no lado do cliente.
Bloqueado (Anti-traversal): Qualquer tentativa externa de acessar arquivos do sistema operacional ou configurações fora da pasta src (ex: interceptando ataques como ../server.ts ou .env).
Detalhamento das Ferramentas (Tools):
health: Validação rápida de status e verificação do timestamp do servidor.
prompt: Integração de contexto para desenvolvimento assistido com inteligência artificial.
bundle: Empacotamento de toda a estrutura em base64.
write_file: Escrita robusta e persistência de novos códigos gerados pelo agente externo.
Comandos Úteis de Terminal: Instruções das tarefas de script (npm run dev, build, start, lint).

- ColdFusion 

https://github.com/pemartins1970/ben-cfml-mcp-system



