Proposta Técnica: Agente de Navegação com Interação Visual (v2.2+)

1. Motivador (O "Porquê")
A evolução do Open Slap! exige que o agente saia do isolamento de APIs estáticas e passe a operar a web "como um humano". O estímulo visual de ver o agente navegando aumenta a confiança do usuário (Maker) e transforma a automação de uma "caixa preta" em um processo transparente e educativo, alinhado ao propósito de laboratório do projeto. A ideia é inspirada em processos como os da Manus.im e ChatGPT, e exibem em um widget o processo/artefato em execução.

Seja um acesso a um website, ou a construção de um, o widget reproduz e renderiza isso visualmente. 

Digamos que eu solicite a um agente acessar o reddit e efetuar uma pesquisa. Muitos grupos e perfis não são públicos, e o acesso demanda login e senha. Ao solicitar a pesquisa, na mesma tela da conversa, abaixo da "bolha de chat" do agente é exibido um widget, que renderiza em "tempo real" o que o agente está "vendo". Ao identificar a necessidade de login e senha, o agente abriria um segundo widget (daqueles padrões, que surgem próximos à barra de status/footer) solicitando o username e senha, que seriam injetados diretamente no campo correspondente do site, viabilizando a autenticação e o acesso do agente ao site. Tudo acompanhado visualmente pelo usuário.

2. O Problema
Atualmente, automações que exigem interação em tempo real (como sites com login/senha ou conteúdos privados como Reddit) enfrentam três barreiras no modelo agêntico tradicional:

Acesso Restrito: APIs simples não conseguem transpor áreas logadas ou SPAs (Single Page Applications) complexas.

Desconexão Visual: O usuário não vê o "desdobramento" da tarefa, perdendo o momento exato de intervir ou validar uma ação.

Segurança de Dados: Inserir senhas diretamente no prompt de chat é perigoso, pois expõe PII (dados sensíveis) ao histórico de treinamento ou logs de memória.

3. Solução Pretendida
Implementar um Widget de Agente Inline dentro do fluxo de chat que ofereça:

Mini-tela de Navegação: Espelhamento visual do que o agente está acessando em tempo real.

Pausa Reativa para Autenticação: O agente interrompe o plano (PLAN) ao detectar um bloqueio de login e solicita credenciais via campos nativos.

Injeção de Credenciais Segura: Uso de formulários locais que injetam dados diretamente no navegador remoto, sem persistir senhas no banco de dados ou na memória RAG.

4. Caminhos Técnicos Viáveis
A. Infraestrutura de Navegação (Backend)
Motor: Integração do software_operator com Playwright ou Puppeteer em modo headless ou headed virtual (XVFB).

Streaming de Estado: Utilizar o canal de WebSockets (já existente para o streaming de texto) para enviar capturas de tela comprimidas (JPEG/WebP) ou atualizações do DOM para o frontend.

B. Interface de Interação (Frontend React)
Widget Inline: Componente condicional posicionado abaixo da última mensagem de chat, evitando pop-ups e mantendo o foco no histórico.

Campos Nativos: Uso de componentes input do sistema (respeitando os 8 temas de cor) para coleta de login e senha.

C. Protocolo de Segurança e Memória
Firewall de PII: Implementação de uma camada de limpeza automática que detecta o evento de login e garante que o conteúdo inserido não seja gravado no db.py ou indexado nas 4 fases de memória.

Barreira contra Zombie Prompts: As instruções de navegação são tratadas como "untrusted content", impedindo que scripts maliciosos de sites externos tentem reprogramar o sistema via widget.

5. Fluxo de Execução (WorkFlow)
Tarefa Agêntica: O usuário pede: "Pesquise no Reddit sobre X".

Detecção de Bloqueio: O agente navega, encontra a tela de login e emite o sinal WAITING_FOR_AUTH via WebSocket.

Abertura do Widget: O chat renderiza inline os campos de usuário/senha.

Intervenção do Maker: O usuário preenche e confirma.

Injeção e Retomada: O backend injeta as teclas no navegador remoto e o orquestrador retoma a execução do plano original.

Preview do Artefato: O resultado final (resumo ou dados) aparece no widget como uma prévia de artefato antes de ser salvo no WORKSPACE.

Nota de Arquitetura: Esta implementação mantém a fidelidade ao hardware legado, priorizando a transmissão de dados leves (campos nativos e frames de imagem) em vez de soluções de vídeo pesado que comprometeriam o desempenho do i5.