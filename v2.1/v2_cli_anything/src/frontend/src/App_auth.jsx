/**
 * 🚀 APP AUTH - Aplicação Principal com Autenticação
 * Versão completa segundo WINDSURF_AGENT.md - AUTH-02
 */

import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import useAuth from './hooks/useAuth';

const OPEN_SLAP_LOGO_SRC = '/open_slap.png';
const AGENT_AVATAR_SRC = '/agent/slap.png';
const OPEN_SLAP_REPO_URL = 'https://github.com/pemartins1970/slap-ecosystem';
const OPEN_SLAP_ASCII_FONT =
  '"Cascadia Mono", Consolas, "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, "Liberation Mono", "Courier New", monospace';
const OPEN_SLAP_ASCII = `open_slap > boot
---------------------------------------------------------

 ██████╗ ██████╗ ███████╗███╗   ██╗    ███████╗██╗      █████╗ ██████╗ ██╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ██╔════╝██║     ██╔══██╗██╔══██╗██║
██║   ██║██████╔╝█████╗  ██╔██╗ ██║    ███████╗██║     ███████║██████╔╝██║
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║    ╚════██║██║     ██╔══██║██╔═══╝ ╚═╝
╚██████╔╝██║     ███████╗██║ ╚████║    ███████║███████╗██║  ██║██║     ██╗
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝    ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
                                                                          
---------------------------------------------------------`;

const App = () => {
  const { user, loading, login, register, logout, getAuthHeaders, isAuthenticated, token, requestPasswordReset, confirmPasswordReset } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [runtimeLlmLabel, setRuntimeLlmLabel] = useState('');
  const [experts, setExperts] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [currentKind, setCurrentKind] = useState('conversation');
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const hasHttpHydratedRef = useRef(false);
  const pendingAutoSendRef = useRef(null);
  const autoStartRef = useRef(false);
  const tempSkillResetTimerRef = useRef(null);
  const chunkBufferRef = useRef('');
  const chunkFlushRef = useRef(null);
  const listsRefreshTimerRef = useRef(null);
  const sessionId = useRef(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [centerView, setCenterView] = useState('chat');
  const [chatSearch, setChatSearch] = useState('');
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsError, setSettingsError] = useState('');
  const [settingsTab, setSettingsTab] = useState('appearance');
  const [providerStatusList, setProviderStatusList] = useState([]);
  const [providerStatusLoading, setProviderStatusLoading] = useState(false);
  const [providerStatusError, setProviderStatusError] = useState('');
  const [llmMode, setLlmMode] = useState('env');
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [llmModel, setLlmModel] = useState('');
  const [llmBaseUrl, setLlmBaseUrl] = useState('');
  const [llmApiKey, setLlmApiKey] = useState('');
  const [llmHasApiKey, setLlmHasApiKey] = useState(false);
  const [llmApiKeySource, setLlmApiKeySource] = useState('none');
  const [llmHasStoredApiKey, setLlmHasStoredApiKey] = useState(false);
  const [llmHasEnvApiKey, setLlmHasEnvApiKey] = useState(false);
  const [llmApiKeyOpen, setLlmApiKeyOpen] = useState(false);
  const llmApiKeyInputRef = useRef(null);
  const pendingSettingsActionRef = useRef(null);
  const [soulData, setSoulData] = useState({
    name: '',
    age_range: '',
    gender: '',
    education: '',
    interests: '',
    goals: '',
    learning_style: '',
    language: 'pt-BR',
    audience: '',
    notes: ''
  });
  const [soulMarkdown, setSoulMarkdown] = useState('');
  const [soulUpdate, setSoulUpdate] = useState('');
  const [systemProfileMarkdown, setSystemProfileMarkdown] = useState('');
  const [systemProfileUpdatedAt, setSystemProfileUpdatedAt] = useState('');
  const [systemProfileEnabled, setSystemProfileEnabled] = useState(true);
  const [systemProfileError, setSystemProfileError] = useState('');
  const [securitySettings, setSecuritySettings] = useState({
    sandbox: false,
    allow_os_commands: true,
    allow_file_write: true,
    allow_web_retrieval: true,
    allow_connectors: true,
    allow_system_profile: true
  });
  const [securitySettingsUpdatedAt, setSecuritySettingsUpdatedAt] = useState('');
  const [automationClientBaseUrl, setAutomationClientBaseUrl] = useState('');
  const [automationClientApiKey, setAutomationClientApiKey] = useState('');
  const [automationClientHasApiKey, setAutomationClientHasApiKey] = useState(false);
  const [doctorReport, setDoctorReport] = useState(null);
  const [doctorError, setDoctorError] = useState('');
  const [doctorLoading, setDoctorLoading] = useState(false);
  const hasDoctorBootedRef = useRef(false);
  const hasLangLoadedRef = useRef(false);
  const [commandModal, setCommandModal] = useState(null);
  const [executingCommandId, setExecutingCommandId] = useState('');
  const [executedCommandIds, setExecutedCommandIds] = useState({});
  const [streamStatusText, setStreamStatusText] = useState('');
  const [loadingTick, setLoadingTick] = useState(0);
  const [chatFontScale, setChatFontScale] = useState(1);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [conversationSearch, setConversationSearch] = useState('');
  const [tasksSearch, setTasksSearch] = useState('');
  const [tasksTab, setTasksTab] = useState('project');
  const [conversationSearchResults, setConversationSearchResults] = useState([]);
  const [tasksSearchResults, setTasksSearchResults] = useState([]);
  const [globalTodos, setGlobalTodos] = useState([]);
  const [taskTodos, setTaskTodos] = useState([]);
  const [taskTodosLoading, setTaskTodosLoading] = useState(false);
  const [taskTodoDraft, setTaskTodoDraft] = useState('');
  const [showTaskDoneTodos, setShowTaskDoneTodos] = useState(false);
  const [renameModal, setRenameModal] = useState(null);
  const [renameDraft, setRenameDraft] = useState('');
  const [todoModal, setTodoModal] = useState(null);
  const [sidebarHoverKey, setSidebarHoverKey] = useState('');
  const [genericModal, setGenericModal] = useState(null);
  const [customizeView, setCustomizeView] = useState('home');
  const [skills, setSkills] = useState([]);
  const [selectedSkillId, setSelectedSkillId] = useState('');
  const [skillDraft, setSkillDraft] = useState('');
  const [skillEditMode, setSkillEditMode] = useState(false);
  const [skillsSaveStatus, setSkillsSaveStatus] = useState('');
  const skillsSaveStatusTimeoutRef = useRef(null);
  const [connectors, setConnectors] = useState({
    github: { connected: false },
    google_drive: { connected: false },
    google_calendar: { connected: false },
    gmail: { connected: false },
    tera: { connected: false }
  });
  const [connectorsLoading, setConnectorsLoading] = useState(false);
  const [connectorModal, setConnectorModal] = useState(null);
  const [lang, setLang] = useState('en');
  const [theme, setTheme] = useState('deep-space');
  const [agentConfigs, setAgentConfigs] = useState({});
  const [agentConfigModal, setAgentConfigModal] = useState(null);
  // Plan→build
  const [planTasks, setPlanTasks] = useState([]);       // [{id, title, skill_id, status}]
  const [activePlanConvId, setActivePlanConvId] = useState(null);
  const [activePlanMessageId, setActivePlanMessageId] = useState(null);
  const [activePlanLocalMsgId, setActivePlanLocalMsgId] = useState(null);
  const pendingPlanTasksRef = useRef({});
  // Message feedback
  const [messageFeedback, setMessageFeedback] = useState({}); // {message_id: 1|-1}
  // MoE expert override
  const [forceExpertId, setForceExpertId] = useState('');
  const [lastExpertReason, setLastExpertReason] = useState('');
  const [lastExpertKeywords, setLastExpertKeywords] = useState([]);
  const [showRoutingDebug, setShowRoutingDebug] = useState(false);
  const [showExecutionPanel, setShowExecutionPanel] = useState(true);
  const streamingRef = useRef(false);
  // Onboarding
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  // Projects
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const [projectContextDraft, setProjectContextDraft] = useState('');
  const [projectContextSaving, setProjectContextSaving] = useState(false);
  // Orchestration
  const [orchRunId, setOrchRunId] = useState(null);
  const [orchStatus, setOrchStatus] = useState('');  // '' | 'running' | 'completed' | 'failed'
  const [orchLog, setOrchLog] = useState([]);
  const orchPollRef = React.useRef(null);

  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const translations = {
    pt: {
      app_title: 'Open Slap! Motor agêntico para makers',
      connected: 'Conectado',
      disconnected: 'Desconectado',
      settings: 'Configurações',
      sign_out: 'Sair',
      menu: 'MENU',
      menu_expand: 'Expandir menu',
      menu_collapse: 'Recolher menu',
      new_task: '➕ Tarefa',
      conversations: 'Conversas',
      tasks: 'Tarefas',
      my_team: 'Minha equipe',
      customize: 'Personalizar',
      donate: 'Doações',
      loading: 'Carregando Open Slap!...',
      clear: 'Limpar',
      new_conversation: '+ Nova conversa',
      search_conversations_placeholder: 'Buscar conversas...',
      no_conversations: 'Nenhuma conversa ainda.',
      history_results: 'Resultados no histórico',
      search_tasks_placeholder: 'Buscar tarefas...',
      no_tasks: 'Nenhuma tarefa ainda.',
      open_in_chat: 'Abrir no chat',
      create_new_agent: '+ Criar novo agente',
      connectors: 'Conectores',
      connect: 'Conectar',
      disconnect: 'Desconectar',
      test: 'Testar',
      connected_ok: 'Conectado',
      not_connected: 'Não conectado',
      save: 'Salvar',
      remove: 'Remover',
      cancel: 'Cancelar',
      confirm: 'Confirmar',
      language: 'Idioma',
      connector_token_label: 'Token',
      connector_token_placeholder: 'Cole aqui o token',
      github_token_help: 'Personal access token do GitHub (classic ou fine-grained).',
      google_token_help: 'Access token OAuth do Google (Bearer).',
      telegram_token_help: 'Token do bot do Telegram. Depois de conectar, clique em “Gerar código” e envie “/link SEU_CODIGO” para o bot.',
      telegram_link_code_title: 'Telegram — Vincular',
      telegram_link_code_body_1: '1) No app: Conectores → Telegram → Gerar código',
      telegram_link_code_body_2: '2) No Telegram: envie para o bot: /link SEU_CODIGO',
      telegram_link_code_body_3: 'Para desconectar: /unlink',
      telegram_link_code_label: 'Código',
      telegram_link_code_expires: 'Expira em',
      generate_code: 'Gerar código',
      automation_client_help_tooltip: 'Entenda o cliente de automação',
      automation_client_help_title: 'Cliente de automação (externo)',
      automation_client_help_body_1: 'Este conector aponta para um serviço externo (ex.: Tera) que executa automações fora do Open Slap (browser, integrações, rotinas).',
      automation_client_help_body_2: 'O agente chama esse serviço via Base URL com uma API key (Bearer). O endpoint /health é usado para teste.',
      automation_client_help_body_3: 'Exemplo: Base URL = https://seu-automator.com  |  Health check = GET https://seu-automator.com/health',
      success: 'Sucesso',
      error: 'Erro',
      back: 'Voltar',
      donate_page_title: 'Doações',
      remove_credential_question: 'Remover esta credencial?',
      connector_validated: 'Conector validado.',
      command_confirm_title: 'Confirmar execução de comando',
      executing: 'Executando...',
      execute: 'Executar',
      decrease_font: 'Diminuir fonte',
      increase_font: 'Aumentar fonte',
      by_title: 'Por título',
      no_history_results: 'Nenhum resultado no histórico.',
      list_label: 'Lista',
      in_progress: 'Em andamento',
      completed: 'Realizada',
      todos: 'TODOs',
      add_todo: 'Adicionar TODO',
      todo_placeholder: 'Descreva um TODO desta tarefa…',
      no_todos: 'Nenhum TODO nesta tarefa.',
      show_done: 'Exibir concluídos',
      hide_done: 'Ocultar concluídos',
      refresh: 'Atualizar',
      pending_items: 'pendentes',
      done_items: 'feitas',
      last: 'Última',
      open: 'Abrir',
      complete: 'Concluir',
      global_todo: 'TODO global',
      no_pending: 'Nenhuma pendência.',
      available_agents: 'Agentes disponíveis',
      no_agents: 'Nenhum agente disponível.',
      chat: 'Chat',
      conversation_label: 'Conversa',
      task_label: 'Tarefa',
      search_chat_placeholder: 'Buscar no chat...',
      theme: 'Tema',
      theme_deep_space: 'Deep Space',
      theme_midnight_blue: 'Midnight Blue',
      theme_forest: 'Forest',
      theme_crimson: 'Crimson',
      theme_slate: 'Slate',
      theme_solarized: 'Solarized',
      theme_light: 'Claro',
      theme_paper: 'Papel',
      create_new_agent_prompt: 'Crie um novo agente. Faça perguntas para coletar os dados necessários (nome, objetivo, habilidades, limites) e no final gere o pacote do agente.',
      send: 'Enviar',
      create_new_skill: 'Criar nova skill',
      skills: 'Habilidades',
      skills_center: 'Central de habilidades',
      llm_providers: 'LLM e Providers',
      llm_free_keys_title: 'Chaves de API gratuitas',
      llm_free_keys_body: 'Se você não utiliza serviços de provedores pagos ou LLMs locais, pode obter uma ou mais chaves gratuitas nos serviços abaixo.',
      llm_free_keys_gemini: 'Gemini',
      llm_free_keys_groq: 'Groq',
      llm_free_keys_openrouter: 'Open Router',
      security: 'Segurança',
      memory: 'Memória',
      execution_transparency: 'Execução e transparência',
      show_execution_panel: 'Mostrar painel de execução no chat',
      show_routing_debug: 'Mostrar detalhes de roteamento (debug)',
      routing_debug_hint: 'Por padrão, o chat mostra só o agente e o modelo. O modo debug exibe o motivo do roteamento.',
      skills_hint_open: 'Clique em uma habilidade para abrir em modo leitura.',
      open_skill: 'Abrir habilidade',
      run_skill: 'Executar',
      edit: 'Editar',
      saved: 'Salvo.',
      failed_to_save: 'Falha ao salvar.',
      save_error_title: 'Erro ao salvar',
      save_error_body: 'Não foi possível salvar as habilidades. Tente novamente.',
      invalid_json_title: 'JSON inválido',
      invalid_json_body: 'Não foi possível salvar. Corrija o JSON e tente novamente.',
      settings_load_error: 'Não foi possível carregar as configurações.',
      provider_status_load_error: 'Não foi possível carregar o status dos providers.',
      llm_key_remove_error: 'Não foi possível remover a chave.',
      llm_settings_save_error: 'Não foi possível salvar as configurações de LLM.',
      security_settings_save_error: 'Não foi possível salvar as configurações de segurança.',
      automation_client_save_error: 'Não foi possível salvar o cliente de automação.',
      automation_client_delete_error: 'Não foi possível remover o cliente de automação.',
      automation_client_test_error: 'Não foi possível testar o cliente de automação.',
      soul_save_error: 'Não foi possível salvar as informações do SOUL.',
      soul_update_error: 'Não foi possível adicionar a atualização ao SOUL.',
      ask_sabrina: 'Chame a Sabrina',
      start_project: 'Iniciar projeto',
      home: 'Tela inicial',
      view_available_agents: 'Ver agentes disponíveis',
      open_agents_in_settings: 'Ver agentes em configurações',
      create_agent_assistant_message: 'Ok, vou te ajudar a criar um novo agente. Me explique o que você quer que ele faça.',
      configure: 'Configurar',
      agent_prompt: 'Prompt do agente',
      agent_prompt_placeholder: 'Defina um prompt base (tom, limites, prioridades, contexto).',
      agent_skills: 'Skills do agente',
      default_skill: 'Skill padrão',
      none: 'Nenhuma',
      segment_system: 'System',
      segment_admin: 'Administração',
      segment_finance: 'Finanças',
      segment_marketing: 'Marketing',
      segment_it_devops: 'TI / DevOps',
      segment_other: 'Outros',
      sandbox_help_title: 'Segurança do agente',
      sandbox_help_tooltip: 'Entenda o modo sandbox',
      sandbox_help_body_off_title: 'Sandbox: OFF (desativado)',
      sandbox_help_body_on_title: 'Sandbox: ON (ativado)',
      sandbox_help_privacy_title: 'Importante sobre privacidade:',
      sandbox_help_line_1: 'Modo sandbox define o quanto o agente pode interagir com o seu computador e com recursos externos.',
      sandbox_help_off_1: 'Pode executar comandos no SO (quando permitido).',
      sandbox_help_off_2: 'Pode escrever arquivos locais e gerar entregas/artefatos.',
      sandbox_help_off_3: 'Pode usar conectores (GitHub/Drive/Calendar/Gmail etc.).',
      sandbox_help_off_4: 'Pode fazer busca/ler links na web (quando permitido).',
      sandbox_help_on_1: 'Bloqueia comandos no SO e escrita de arquivos (reduz risco de alterações locais).',
      sandbox_help_on_2: 'Desabilita conectores e web retrieval (reduz exposição de dados a serviços externos).',
      sandbox_help_on_3: 'Mantém apenas capacidades “de texto” (planejar, explicar, revisar, orientar).',
      sandbox_help_privacy_1: 'Sandbox não impede que o texto que você envia seja encaminhado ao provider LLM configurado.',
      sandbox_help_privacy_2: 'Para máxima privacidade de código, prefira LLM local e evite colar segredos.',
      agent_security: 'Segurança do agente',
      sandbox_mode: 'Modo sandbox',
      allow_os_commands: 'Permitir comandos do sistema',
      allow_file_write: 'Permitir escrita de arquivos',
      allow_web_retrieval: 'Permitir consulta à web',
      allow_connectors: 'Permitir conectores',
      allow_system_profile: 'Permitir perfil do sistema',
      security_caps_warning: 'Isso reduz a capacidade do agente de escrever e entregar código/artefatos locais.',
      close: 'Fechar',
      reset: 'Resetar',
      off: 'Desativado',
      on: 'Ativado',
      last_updated: 'Atualizado em',
      updating: 'Atualizando...',
      update_profile: 'Atualizar perfil',
      recommendations: 'Recomendações',
      status_failed: 'Falhou',
      doctor_diagnostics: 'Doctor (diagnóstico)',
      doctor_all_ok: 'Tudo certo.',
      doctor_some_attention: 'Há itens pendentes.',
      doctor_click_run: 'Clique em “Rodar diagnóstico”.',
      run_diagnostics: 'Rodar diagnóstico',
      llm_settings_title: 'LLM (chave API ou local)',
      mode: 'Modo',
      server_default: 'Padrão do servidor',
      api_cloud: 'API (nuvem)',
      local_ollama: 'Local (Ollama)',
      provider: 'Provider',
      model: 'Modelo',
      base_url: 'Base URL',
      api_key: 'Chave API',
      api_key_close: 'Fechar',
      api_key_switch: 'Trocar chave',
      api_key_register: 'Cadastrar chave',
      api_key_placeholder: 'Cole sua chave aqui',
      llm_api_key_hint_env: 'Chave disponível via .env (não salva no servidor). Para sobrescrever, clique em “Trocar chave”.',
      llm_api_key_hint_saved: 'Chave cadastrada (não exibida). Para trocar, clique em “Trocar chave”.',
      llm_api_key_hint_none: 'Nenhuma chave cadastrada. Clique em “Cadastrar chave”.',
      llm_api_key_hint_storage: 'A chave fica salva de forma protegida no servidor local deste computador. Não aparece novamente depois de salvar.',
      llm_api_key_warning_shared: 'Atenção: em um computador compartilhado, outras pessoas com acesso ao mesmo usuário do Windows podem usar este servidor local e consumir suas credenciais. Use perfis separados do SO.',
      llm_key_from_env: 'Chave vem do .env',
      llm_remove_key: 'Remover chave',
      save_llm: 'Salvar LLM',
      llm_saving: 'Salvando...',
      configured_providers: 'Providers configurados',
      provider_enabled: 'ativo',
      provider_disabled: 'inativo',
      provider_keys: 'chaves',
      no_provider_status: 'Sem status disponível.',
      automation_client_external: 'Cliente de automação (externo)',
      automation_client_hint: 'Configure um serviço remoto de automação. O servidor armazenará credenciais localmente e o agente poderá usá-lo como conector.',
      saved_keep: 'Salvo (deixe em branco para manter)',
      paste_here: 'Cole aqui',
      system_profile_local: 'Perfil do sistema (local)',
      system_profile_hint_1: 'Esse perfil é coletado pelo servidor local (Windows/macOS/Linux) e fica disponível para evitar perguntas recorrentes do tipo “qual versão do seu sistema?”.',
      system_profile_hint_2: 'Atenção: pode conter informações sensíveis (nome do computador, rede, etc.). Use “Remover” se preferir não armazenar.',
      system_profile_feature_disabled: 'Funcionalidade desativada no servidor (OPENSLAP_SYSTEM_PROFILE=0).',
      system_profile_disabled_by_security: 'Desativado pelas configurações de segurança do usuário.',
      soul_user_profile: 'SOUL (perfil do usuário)',
      name_label: 'Nome',
      age_range_label: 'Faixa etária',
      learning_style_label: 'Estilo de aprendizagem',
      profile_language_label: 'Idioma',
      audience_label: 'Público',
      notes_label: 'Notas',
      not_set: 'Não definido',
      audience_youth: 'Jovem',
      audience_adult: 'Adulto',
      audience_mixed: 'Misto',
      save_soul: 'Salvar SOUL',
      soul_updates: 'Atualizações do SOUL',
      add_update: 'Adicionar atualização',
      soul_md_preview: 'Prévia do SOUL.md',
      onboarding_title: '👋 Bem-vindo ao Open Slap!',
      onboarding_intro: 'O Open Slap! é um workspace agêntico. Veja como começar rapidamente:',
      onboarding_step_task_title: '➕ Nova tarefa',
      onboarding_step_task_desc: 'Clique em “➕ Tarefa” no menu. A skill do CTO carrega automaticamente — descreva seu projeto e ela cria um plano estruturado.',
      onboarding_step_skills_title: '🧠 Skills',
      onboarding_step_skills_desc: 'Vá em Configurações → Central de habilidades para ver as skills (CTO, DevOps, SEO…). Clique em uma skill para abrir e executar.',
      onboarding_step_connectors_title: '🔌 Conectores',
      onboarding_step_connectors_desc: 'Vá em Configurações → Conectores para integrar GitHub, Google Calendar ou Gmail.',
      onboarding_step_feedback_title: '👍 Feedback',
      onboarding_step_feedback_desc: 'Avalie respostas do assistente com 👍/👎. Isso ajuda a calibrar o que é útil.',
      onboarding_step_projects_title: '🗂️ Projetos',
      onboarding_step_projects_desc: 'Crie um projeto em Configurações → Projetos para compartilhar contexto entre tarefas.',
      onboarding_start_first_task: '🚀 Iniciar minha primeira tarefa',
      onboarding_explore: 'Explorar por conta própria',
      rename_title: 'Renomear',
      running: 'Rodando...'
    },
    en: {
      app_title: 'Open Slap! Agentic engine for makers',
      connected: 'Connected',
      disconnected: 'Disconnected',
      settings: 'Settings',
      sign_out: 'Sign out',
      menu: 'MENU',
      menu_expand: 'Expand menu',
      menu_collapse: 'Collapse menu',
      new_task: '➕ Task',
      conversations: 'Conversations',
      tasks: 'Tasks',
      my_team: 'My team',
      customize: 'Customize',
      donate: 'Donations',
      loading: 'Loading Open Slap!...',
      clear: 'Clear',
      new_conversation: '+ New conversation',
      search_conversations_placeholder: 'Search conversations...',
      no_conversations: 'No conversations yet.',
      history_results: 'History results',
      search_tasks_placeholder: 'Search tasks...',
      no_tasks: 'No tasks yet.',
      open_in_chat: 'Open in chat',
      create_new_agent: '+ Create new agent',
      connectors: 'Connectors',
      connect: 'Connect',
      disconnect: 'Disconnect',
      test: 'Test',
      connected_ok: 'Connected',
      not_connected: 'Not connected',
      save: 'Save',
      remove: 'Remove',
      cancel: 'Cancel',
      confirm: 'Confirm',
      language: 'Language',
      connector_token_label: 'Token',
      connector_token_placeholder: 'Paste the token here',
      github_token_help: 'GitHub personal access token (classic or fine-grained).',
      google_token_help: 'Google OAuth access token (Bearer).',
      telegram_token_help: 'Telegram bot token. After connecting, click “Generate code” and send “/link YOUR_CODE” to the bot.',
      telegram_link_code_title: 'Telegram — Link',
      telegram_link_code_body_1: '1) In the app: Connectors → Telegram → Generate code',
      telegram_link_code_body_2: '2) In Telegram: send to the bot: /link YOUR_CODE',
      telegram_link_code_body_3: 'To disconnect: /unlink',
      telegram_link_code_label: 'Code',
      telegram_link_code_expires: 'Expires at',
      generate_code: 'Generate code',
      automation_client_help_tooltip: 'Understand automation client',
      automation_client_help_title: 'Automation client (external)',
      automation_client_help_body_1: 'This connector points to an external service (e.g., Tera) that runs automations outside Open Slap (browser, integrations, routines).',
      automation_client_help_body_2: 'The agent calls this service via Base URL with an API key (Bearer). The /health endpoint is used for testing.',
      automation_client_help_body_3: 'Example: Base URL = https://your-automator.com  |  Health check = GET https://your-automator.com/health',
      success: 'Success',
      error: 'Error',
      back: 'Back',
      donate_page_title: 'Donations',
      remove_credential_question: 'Remove this credential?',
      connector_validated: 'Connector validated.',
      command_confirm_title: 'Confirm command execution',
      executing: 'Executing...',
      execute: 'Run',
      decrease_font: 'Decrease font',
      increase_font: 'Increase font',
      by_title: 'By title',
      no_history_results: 'No results in history.',
      list_label: 'List',
      in_progress: 'In progress',
      completed: 'Done',
      todos: 'TODOs',
      add_todo: 'Add TODO',
      todo_placeholder: 'Describe a TODO for this task…',
      no_todos: 'No TODOs for this task.',
      show_done: 'Show done',
      hide_done: 'Hide done',
      refresh: 'Refresh',
      pending_items: 'pending',
      done_items: 'done',
      last: 'Last',
      open: 'Open',
      complete: 'Complete',
      global_todo: 'Global TODO',
      no_pending: 'No pending items.',
      available_agents: 'Available agents',
      no_agents: 'No agents available.',
      chat: 'Chat',
      conversation_label: 'Conversation',
      task_label: 'Task',
      search_chat_placeholder: 'Search chat...',
      theme: 'Theme',
      theme_deep_space: 'Deep Space',
      theme_midnight_blue: 'Midnight Blue',
      theme_forest: 'Forest',
      theme_crimson: 'Crimson',
      theme_slate: 'Slate',
      theme_solarized: 'Solarized',
      theme_light: 'Light',
      theme_paper: 'Paper',
      create_new_agent_prompt: 'Create a new agent. Ask questions to collect the necessary data (name, goal, skills, limits) and generate the agent package at the end.',
      send: 'Send',
      create_new_skill: 'Create new skill',
      skills: 'Skills',
      skills_center: 'Skills center',
      llm_providers: 'LLM & Providers',
      llm_free_keys_title: 'Free API keys',
      llm_free_keys_body: 'If you don’t use paid providers or local LLMs, you can get one or more free API keys from the services below.',
      llm_free_keys_gemini: 'Gemini',
      llm_free_keys_groq: 'Groq',
      llm_free_keys_openrouter: 'Open Router',
      security: 'Security',
      memory: 'Memory',
      execution_transparency: 'Execution & transparency',
      show_execution_panel: 'Show execution panel in chat',
      show_routing_debug: 'Show routing details (debug)',
      routing_debug_hint: 'By default, chat shows only agent and model. Debug mode shows routing rationale.',
      skills_hint_open: 'Click a skill to open in read mode.',
      open_skill: 'Open skill',
      run_skill: 'Run',
      edit: 'Edit',
      saved: 'Saved.',
      failed_to_save: 'Failed to save.',
      save_error_title: 'Save error',
      save_error_body: 'Could not save skills. Please try again.',
      invalid_json_title: 'Invalid JSON',
      invalid_json_body: 'Could not save. Fix the JSON and try again.',
      settings_load_error: 'Could not load settings.',
      provider_status_load_error: 'Could not load provider status.',
      llm_key_remove_error: 'Could not remove the key.',
      llm_settings_save_error: 'Could not save LLM settings.',
      security_settings_save_error: 'Could not save security settings.',
      automation_client_save_error: 'Could not save automation client.',
      automation_client_delete_error: 'Could not delete automation client.',
      automation_client_test_error: 'Could not test automation client.',
      soul_save_error: 'Could not save SOUL information.',
      soul_update_error: 'Could not add update to SOUL.',
      ask_sabrina: 'Call Sabrina',
      start_project: 'Start project',
      home: 'Home',
      view_available_agents: 'View available agents',
      open_agents_in_settings: 'Open agents in settings',
      create_agent_assistant_message: "Ok — I'll help you create a new agent. Tell me what you want it to do.",
      configure: 'Configure',
      agent_prompt: 'Agent prompt',
      agent_prompt_placeholder: 'Define a base prompt (tone, limits, priorities, context).',
      agent_skills: 'Agent skills',
      default_skill: 'Default skill',
      none: 'None',
      segment_system: 'System',
      segment_admin: 'Administration',
      segment_finance: 'Finance',
      segment_marketing: 'Marketing',
      segment_it_devops: 'IT / DevOps',
      segment_other: 'Other',
      sandbox_help_title: 'Agent security',
      sandbox_help_tooltip: 'Understand sandbox mode',
      sandbox_help_body_off_title: 'Sandbox: OFF',
      sandbox_help_body_on_title: 'Sandbox: ON',
      sandbox_help_privacy_title: 'Privacy note:',
      sandbox_help_line_1: 'Sandbox mode defines how much the agent can interact with your computer and external resources.',
      sandbox_help_off_1: 'Can run OS commands (when allowed).',
      sandbox_help_off_2: 'Can write local files and generate deliveries/artifacts.',
      sandbox_help_off_3: 'Can use connectors (GitHub/Drive/Calendar/Gmail etc.).',
      sandbox_help_off_4: 'Can browse/retrieve web content (when allowed).',
      sandbox_help_on_1: 'Blocks OS commands and file writes (reduces local change risk).',
      sandbox_help_on_2: 'Disables connectors and web retrieval (reduces exposure to external services).',
      sandbox_help_on_3: 'Keeps “text-only” capabilities (plan, explain, review, guide).',
      sandbox_help_privacy_1: 'Sandbox does not prevent the text you send from being forwarded to the configured LLM provider.',
      sandbox_help_privacy_2: 'For maximum code privacy, prefer a local LLM and avoid pasting secrets.',
      agent_security: 'Agent security',
      sandbox_mode: 'Sandbox mode',
      allow_os_commands: 'Allow OS commands',
      allow_file_write: 'Allow file writing',
      allow_web_retrieval: 'Allow web retrieval',
      allow_connectors: 'Allow connectors',
      allow_system_profile: 'Allow system profile',
      security_caps_warning: 'This reduces the agent ability to write and deliver local code/artifacts.',
      close: 'Close',
      reset: 'Reset',
      off: 'Off',
      on: 'On',
      last_updated: 'Last updated',
      updating: 'Updating...',
      update_profile: 'Update profile',
      recommendations: 'Recommendations',
      status_failed: 'Failed',
      doctor_diagnostics: 'Doctor (diagnostics)',
      doctor_all_ok: 'All systems OK.',
      doctor_some_attention: 'Some items need attention.',
      doctor_click_run: 'Click “Run diagnostics”.',
      run_diagnostics: 'Run diagnostics',
      llm_settings_title: 'LLM (API key or local)',
      mode: 'Mode',
      server_default: 'Server default',
      api_cloud: 'API (cloud)',
      local_ollama: 'Local (Ollama)',
      provider: 'Provider',
      model: 'Model',
      base_url: 'Base URL',
      api_key: 'API key',
      api_key_close: 'Close',
      api_key_switch: 'Change key',
      api_key_register: 'Add key',
      api_key_placeholder: 'Paste your key here',
      llm_api_key_hint_env: 'Key available via .env (not saved on the server). To override, click “Change key”.',
      llm_api_key_hint_saved: 'Key saved (not shown). To change, click “Change key”.',
      llm_api_key_hint_none: 'No key saved. Click “Add key”.',
      llm_api_key_hint_storage: 'The key is stored securely on this computer local server. It will not be shown again after saving.',
      llm_api_key_warning_shared: 'Warning: on a shared computer, others with access to the same Windows user may use this local server and consume your credentials. Use separate OS profiles.',
      llm_key_from_env: 'Key comes from .env',
      llm_remove_key: 'Remove key',
      save_llm: 'Save LLM',
      llm_saving: 'Saving...',
      configured_providers: 'Configured providers',
      provider_enabled: 'enabled',
      provider_disabled: 'disabled',
      provider_keys: 'keys',
      no_provider_status: 'No status available.',
      automation_client_external: 'Automation client (external)',
      automation_client_hint: 'Configure a remote automation service. The server will store credentials locally and the agent may use it as a connector.',
      saved_keep: 'Saved (leave blank to keep)',
      paste_here: 'Paste here',
      system_profile_local: 'System profile (local)',
      system_profile_hint_1: 'This profile is collected by the local server (Windows/macOS/Linux) and helps avoid recurring questions like “what OS version are you on?”.',
      system_profile_hint_2: 'Warning: it may contain sensitive information (computer name, network, etc.). Use “Remove” if you prefer not to store it.',
      system_profile_feature_disabled: 'Feature disabled on server (OPENSLAP_SYSTEM_PROFILE=0).',
      system_profile_disabled_by_security: 'Disabled by user security settings.',
      soul_user_profile: 'SOUL (user profile)',
      name_label: 'Name',
      age_range_label: 'Age range',
      learning_style_label: 'Learning style',
      profile_language_label: 'Language',
      audience_label: 'Audience',
      notes_label: 'Notes',
      not_set: 'Not set',
      audience_youth: 'Youth',
      audience_adult: 'Adult',
      audience_mixed: 'Mixed',
      save_soul: 'Save SOUL',
      soul_updates: 'SOUL updates',
      add_update: 'Add update',
      soul_md_preview: 'SOUL.md preview',
      onboarding_title: '👋 Welcome to Open Slap!',
      onboarding_intro: "Open Slap! is an agentic workspace. Here's how to get started quickly:",
      onboarding_step_task_title: '➕ New task',
      onboarding_step_task_desc: 'Click “➕ Task” in the sidebar. The CTO skill loads automatically — describe your project and it will create a structured plan.',
      onboarding_step_skills_title: '🧠 Skills',
      onboarding_step_skills_desc: 'Go to Settings → Skills center to see built-in skills (CTO, DevOps, SEO…). Click a skill to open and run it.',
      onboarding_step_connectors_title: '🔌 Connectors',
      onboarding_step_connectors_desc: 'Go to Settings → Connectors to link GitHub, Google Calendar or Gmail.',
      onboarding_step_feedback_title: '👍 Feedback',
      onboarding_step_feedback_desc: "Rate any assistant reply with 👍/👎. This helps the system learn what's useful.",
      onboarding_step_projects_title: '🗂️ Projects',
      onboarding_step_projects_desc: 'Create a project in Settings → Projects to share context across multiple tasks.',
      onboarding_start_first_task: '🚀 Start my first task',
      onboarding_explore: 'Explore on my own',
      rename_title: 'Rename',
      running: 'Running...'
    },
    es: {
      app_title: 'Open Slap! Motor agéntico para makers',
      connected: 'Conectado',
      disconnected: 'Desconectado',
      settings: 'Configuración',
      sign_out: 'Salir',
      menu: 'MENÚ',
      menu_expand: 'Expandir menú',
      menu_collapse: 'Contraer menú',
      new_task: '➕ Tarea',
      conversations: 'Conversaciones',
      tasks: 'Tareas',
      my_team: 'Mi equipo',
      customize: 'Personalizar',
      donate: 'Donaciones',
      loading: 'Cargando Open Slap!...',
      clear: 'Limpiar',
      new_conversation: '+ Nueva conversación',
      search_conversations_placeholder: 'Buscar conversaciones...',
      no_conversations: 'Aún no hay conversaciones.',
      history_results: 'Resultados en el historial',
      search_tasks_placeholder: 'Buscar tareas...',
      no_tasks: 'Aún no hay tareas.',
      open_in_chat: 'Abrir en chat',
      create_new_agent: '+ Crear nuevo agente',
      connectors: 'Conectores',
      connect: 'Conectar',
      disconnect: 'Desconectar',
      test: 'Probar',
      connected_ok: 'Conectado',
      not_connected: 'No conectado',
      save: 'Guardar',
      cancel: 'Cancelar',
      confirm: 'Confirmar',
      language: 'Idioma',
      connector_token_label: 'Token',
      connector_token_placeholder: 'Pega el token aquí',
      github_token_help: 'Token de acceso personal de GitHub (classic o fine-grained).',
      google_token_help: 'Token de acceso OAuth de Google (Bearer).',
      telegram_token_help: 'Token del bot de Telegram. Después de conectar, haz clic en “Generar código” y envía “/link TU_CODIGO” al bot.',
      telegram_link_code_title: 'Telegram — Vincular',
      telegram_link_code_body_1: '1) En la app: Conectores → Telegram → Generar código',
      telegram_link_code_body_2: '2) En Telegram: envía al bot: /link TU_CODIGO',
      telegram_link_code_body_3: 'Para desconectar: /unlink',
      telegram_link_code_label: 'Código',
      telegram_link_code_expires: 'Expira en',
      generate_code: 'Generar código',
      automation_client_help_tooltip: 'Entender el cliente de automatización',
      automation_client_help_title: 'Cliente de automatización (externo)',
      automation_client_help_body_1: 'Este conector apunta a un servicio externo (p. ej., Tera) que ejecuta automatizaciones fuera de Open Slap (browser, integraciones, rutinas).',
      automation_client_help_body_2: 'El agente llama a este servicio via Base URL con una API key (Bearer). El endpoint /health se usa para la prueba.',
      automation_client_help_body_3: 'Ejemplo: Base URL = https://tu-automator.com  |  Health check = GET https://tu-automator.com/health',
      success: 'Éxito',
      error: 'Error',
      back: 'Volver',
      donate_page_title: 'Donaciones',
      remove_credential_question: '¿Eliminar esta credencial?',
      connector_validated: 'Conector validado.',
      command_confirm_title: 'Confirmar ejecución de comando',
      executing: 'Ejecutando...',
      execute: 'Ejecutar',
      decrease_font: 'Disminuir fuente',
      increase_font: 'Aumentar fuente',
      by_title: 'Por título',
      no_history_results: 'No hay resultados en el historial.',
      list_label: 'Lista',
      in_progress: 'En progreso',
      completed: 'Hecha',
      todos: 'TODOs',
      add_todo: 'Agregar TODO',
      todo_placeholder: 'Describe un TODO para esta tarea…',
      no_todos: 'No hay TODOs en esta tarea.',
      show_done: 'Ver hechas',
      hide_done: 'Ocultar hechas',
      refresh: 'Actualizar',
      pending_items: 'pendientes',
      done_items: 'hechas',
      last: 'Última',
      open: 'Abrir',
      complete: 'Completar',
      global_todo: 'TODO global',
      no_pending: 'No hay pendientes.',
      available_agents: 'Agentes disponibles',
      no_agents: 'No hay agentes disponibles.',
      chat: 'Chat',
      conversation_label: 'Conversación',
      task_label: 'Tarea',
      search_chat_placeholder: 'Buscar en el chat...',
      theme: 'Tema',
      theme_deep_space: 'Deep Space',
      theme_midnight_blue: 'Midnight Blue',
      theme_forest: 'Bosque',
      theme_crimson: 'Carmesí',
      theme_slate: 'Pizarra',
      theme_solarized: 'Solarizado',
      theme_light: 'Claro',
      theme_paper: 'Papel',
      create_new_agent_prompt: 'Crea un nuevo agente. Haz preguntas para recopilar los datos necesarios (nombre, objetivo, habilidades, límites) y genera el paquete del agente al final.',
      send: 'Enviar',
      create_new_skill: 'Crear nueva skill',
      skills: 'Habilidades',
      onboarding_title: '👋 ¡Bienvenido a Open Slap!',
      onboarding_intro: 'Open Slap! es un workspace agéntico. Así puedes empezar rápidamente:',
      onboarding_step_task_title: '➕ Nueva tarea',
      onboarding_step_task_desc: 'Haz clic en “➕ Tarea” en el menú. La skill de CTO se carga automáticamente — describe tu proyecto y creará un plan estructurado.',
      onboarding_step_skills_title: '🧠 Skills',
      onboarding_step_skills_desc: 'Ve a Configuración → Central de habilidades para ver las skills (CTO, DevOps, SEO…). Haz clic en una skill para abrirla y ejecutarla.',
      onboarding_step_connectors_title: '🔌 Conectores',
      onboarding_step_connectors_desc: 'Ve a Configuración → Conectores para integrar GitHub, Google Calendar o Gmail.',
      onboarding_step_feedback_title: '👍 Feedback',
      onboarding_step_feedback_desc: 'Califica respuestas del asistente con 👍/👎. Esto ayuda a ajustar lo que es útil.',
      onboarding_step_projects_title: '🗂️ Proyectos',
      onboarding_step_projects_desc: 'Crea un proyecto en Configuración → Proyectos para compartir contexto entre tareas.',
      onboarding_start_first_task: '🚀 Iniciar mi primera tarea',
      onboarding_explore: 'Explorar por mi cuenta',
      rename_title: 'Renombrar',
      running: 'Ejecutando...'
    },
    ar: {
      app_title: 'Open Slap! محرّك وكلائي للصنّاع',
      connected: 'متصل',
      disconnected: 'غير متصل',
      settings: 'الإعدادات',
      sign_out: 'تسجيل الخروج',
      menu: 'القائمة',
      menu_expand: 'توسيع القائمة',
      menu_collapse: 'طيّ القائمة',
      new_task: 'مهمة جديدة',
      conversations: 'المحادثات',
      tasks: 'المهام',
      my_team: 'فريقي',
      customize: 'تخصيص',
      donate: 'تبرعات',
      loading: 'جارٍ تحميل Open Slap!...',
      clear: 'مسح',
      new_conversation: '+ محادثة جديدة',
      search_conversations_placeholder: 'بحث في المحادثات...',
      no_conversations: 'لا توجد محادثات بعد.',
      history_results: 'نتائج في السجل',
      search_tasks_placeholder: 'بحث في المهام...',
      no_tasks: 'لا توجد مهام بعد.',
      open_in_chat: 'فتح في الدردشة',
      create_new_agent: '+ إنشاء وكيل جديد',
      connectors: 'الروابط',
      connect: 'اتصال',
      disconnect: 'قطع الاتصال',
      test: 'اختبار',
      connected_ok: 'متصل',
      not_connected: 'غير متصل',
      save: 'حفظ',
      cancel: 'إلغاء',
      confirm: 'تأكيد',
      language: 'اللغة',
      connector_token_label: 'رمز',
      connector_token_placeholder: 'ألصق الرمز هنا',
      github_token_help: 'رمز وصول شخصي من GitHub.',
      google_token_help: 'رمز وصول OAuth من Google (Bearer).',
      telegram_token_help: 'رمز بوت Telegram. بعد الاتصال اضغط “إنشاء رمز” ثم أرسل “/link YOUR_CODE” إلى البوت.',
      telegram_link_code_title: 'Telegram — ربط',
      telegram_link_code_body_1: '1) في التطبيق: الموصلات → Telegram → إنشاء رمز',
      telegram_link_code_body_2: '2) في Telegram: أرسل إلى البوت: /link YOUR_CODE',
      telegram_link_code_body_3: 'لإلغاء الربط: /unlink',
      telegram_link_code_label: 'الرمز',
      telegram_link_code_expires: 'ينتهي في',
      generate_code: 'إنشاء رمز',
      automation_client_help_tooltip: 'فهم عميل الأتمتة',
      automation_client_help_title: 'عميل الأتمتة (خارجي)',
      automation_client_help_body_1: 'هذا الموصل يشير إلى خدمة خارجية (مثل Tera) لتشغيل الأتمتة خارج Open Slap (متصفح، تكاملات، مهام).',
      automation_client_help_body_2: 'يستدعي الوكيل هذه الخدمة عبر Base URL مع API key (Bearer). ويُستخدم المسار /health للاختبار.',
      automation_client_help_body_3: 'مثال: Base URL = https://your-automator.com  |  Health check = GET https://your-automator.com/health',
      success: 'تم',
      error: 'خطأ',
      back: 'رجوع',
      donate_page_title: 'تبرعات',
      remove_credential_question: 'هل تريد إزالة هذه البيانات؟',
      connector_validated: 'تم التحقق من الرابط.',
      command_confirm_title: 'تأكيد تنفيذ الأمر',
      executing: 'جارٍ التنفيذ...',
      execute: 'تنفيذ',
      decrease_font: 'تصغير الخط',
      increase_font: 'تكبير الخط',
      by_title: 'حسب العنوان',
      no_history_results: 'لا توجد نتائج في السجل.',
      list_label: 'القائمة',
      in_progress: 'قيد التنفيذ',
      completed: 'مكتملة',
      todos: 'المهام',
      add_todo: 'إضافة مهمة',
      todo_placeholder: 'اكتب مهمة لهذه المهمة…',
      no_todos: 'لا توجد مهام لهذه المهمة.',
      show_done: 'إظهار المكتملة',
      hide_done: 'إخفاء المكتملة',
      refresh: 'تحديث',
      pending_items: 'قيد الانتظار',
      done_items: 'منجزة',
      last: 'الأخيرة',
      open: 'فتح',
      complete: 'إنهاء',
      global_todo: 'TODO عام',
      no_pending: 'لا توجد مهام معلّقة.',
      available_agents: 'الوكلاء المتاحون',
      no_agents: 'لا يوجد وكلاء متاحون.',
      chat: 'الدردشة',
      conversation_label: 'محادثة',
      task_label: 'مهمة',
      search_chat_placeholder: 'بحث في الدردشة...',
      theme: 'السمة',
      theme_deep_space: 'الفضاء العميق',
      theme_midnight_blue: 'أزرق منتصف الليل',
      theme_forest: 'الغابة',
      theme_crimson: 'القرمزي',
      theme_slate: 'الأردواز',
      theme_solarized: 'شمسي',
      theme_light: 'فاتح',
      theme_paper: 'ورق',
      create_new_agent_prompt: 'إنشاء وكيل جديد. اطرح أسئلة لجمع البيانات اللازمة (الاسم، الهدف، المهارات، الحدود) وقم بإنشاء حزمة الوكيل في النهاية.',
      send: 'إرسال',
      create_new_skill: 'إنشاء مهارة جديدة'
    },
    zh: {
      app_title: 'Open Slap! 面向创作者的智能代理引擎',
      connected: '已连接',
      disconnected: '未连接',
      settings: '设置',
      sign_out: '退出',
      menu: '菜单',
      menu_expand: '展开菜单',
      menu_collapse: '收起菜单',
      new_task: '新任务',
      conversations: '对话',
      tasks: '任务',
      my_team: '我的团队',
      customize: '个性化',
      donate: '捐赠',
      loading: '正在加载 Open Slap!...',
      clear: '清除',
      new_conversation: '+ 新对话',
      search_conversations_placeholder: '搜索对话...',
      no_conversations: '暂无对话。',
      history_results: '历史结果',
      search_tasks_placeholder: '搜索任务...',
      no_tasks: '暂无任务。',
      open_in_chat: '在聊天中打开',
      create_new_agent: '+ 创建新代理',
      connectors: '连接器',
      connect: '连接',
      disconnect: '断开',
      test: '测试',
      connected_ok: '已连接',
      not_connected: '未连接',
      save: '保存',
      cancel: '取消',
      confirm: '确认',
      language: '语言',
      connector_token_label: '令牌',
      connector_token_placeholder: '在此粘贴令牌',
      github_token_help: 'GitHub 个人访问令牌。',
      google_token_help: 'Google OAuth 访问令牌（Bearer）。',
      telegram_token_help: 'Telegram 机器人令牌。连接后点击“生成代码”，然后给机器人发送“/link YOUR_CODE”。',
      telegram_link_code_title: 'Telegram — 绑定',
      telegram_link_code_body_1: '1) 在应用中：连接器 → Telegram → 生成代码',
      telegram_link_code_body_2: '2) 在 Telegram：发送给机器人：/link YOUR_CODE',
      telegram_link_code_body_3: '解除绑定：/unlink',
      telegram_link_code_label: '代码',
      telegram_link_code_expires: '过期时间',
      generate_code: '生成代码',
      automation_client_help_tooltip: '了解自动化客户端',
      automation_client_help_title: '自动化客户端（外部）',
      automation_client_help_body_1: '此连接器指向外部服务（例如 Tera），在 Open Slap 之外运行自动化（浏览器、集成、流程）。',
      automation_client_help_body_2: '代理会通过 Base URL + API key（Bearer）调用该服务；/health 用于测试。',
      automation_client_help_body_3: '示例：Base URL = https://your-automator.com  |  Health check = GET https://your-automator.com/health',
      success: '成功',
      error: '错误',
      back: '返回',
      donate_page_title: '捐赠',
      remove_credential_question: '移除此凭证？',
      connector_validated: '连接器已验证。',
      command_confirm_title: '确认执行命令',
      executing: '正在执行...',
      execute: '执行',
      decrease_font: '减小字号',
      increase_font: '增大字号',
      by_title: '按标题',
      no_history_results: '历史中没有结果。',
      list_label: '列表',
      in_progress: '进行中',
      completed: '已完成',
      todos: 'TODOs',
      add_todo: '添加 TODO',
      todo_placeholder: '为此任务写一个 TODO…',
      no_todos: '此任务暂无 TODO。',
      show_done: '显示已完成',
      hide_done: '隐藏已完成',
      refresh: '刷新',
      pending_items: '待办',
      done_items: '已完成',
      last: '最后',
      open: '打开',
      complete: '完成',
      global_todo: '全局 TODO',
      no_pending: '暂无待办。',
      available_agents: '可用代理',
      no_agents: '暂无可用代理。',
      chat: '聊天',
      conversation_label: '对话',
      task_label: '任务',
      search_chat_placeholder: '搜索聊天...',
      theme: '主题',
      theme_deep_space: '深空',
      theme_midnight_blue: '午夜蓝',
      theme_forest: '森林',
      theme_crimson: '深红',
      theme_slate: '石板',
      theme_solarized: '日光化',
      theme_light: '明亮',
      theme_paper: '纸张',
      create_new_agent_prompt: '创建一个新代理。提出问题以收集必要的数据（名称，目标，技能，限制），并在最后生成代理包。',
      send: '发送',
      create_new_skill: '创建新技能'
    }
  };

  useEffect(() => {
    streamingRef.current = Boolean(streaming);
  }, [streaming]);
  const t = (key) => {
    const table = translations[lang] || translations.pt;
    return table[key] || translations.pt[key] || key;
  };
  const segmentOrder = ['system', 'admin', 'finance', 'marketing', 'it_devops', 'other'];
  const getSkillSegmentId = (skill) => {
    const id = String(skill?.id || '').toLowerCase();
    if (['cto', 'systems-architect', 'chat-assistant', 'skill-creator'].includes(id)) return 'system';
    if (['coo', 'project-manager'].includes(id)) return 'admin';
    if (['cfo', 'excel-expert'].includes(id)) return 'finance';
    if (['seo', 'marketing'].includes(id)) return 'marketing';
    if (['backend-dev', 'frontend-dev', 'devops', 'security', 'data-scientist', 'code-review', 'tests'].includes(id)) return 'it_devops';
    return 'other';
  };
  const getExpertSegmentId = (expert) => {
    const id = String(expert?.id || '').toLowerCase();
    if (['general', 'cto', 'systems-architect', 'chat-assistant', 'skill-creator'].includes(id)) return 'system';
    if (['coo', 'project-manager'].includes(id)) return 'admin';
    if (['cfo', 'excel-expert'].includes(id)) return 'finance';
    if (['seo', 'marketing'].includes(id)) return 'marketing';
    if (['backend-dev', 'frontend-dev', 'devops', 'security', 'data-scientist', 'code-review', 'tests'].includes(id)) return 'it_devops';
    return 'other';
  };
  const BUILTIN_SKILL_I18N = {
    'chat-assistant': {
      pt: { name: 'Sabrina (Assistente de chat)', description: 'Orquestra conversas, encaminha para especialistas e mantém a conversa no rumo.' },
      en: { name: 'Sabrina (Chat Assistant)', description: 'Orchestrates conversations, routes to specialists and keeps you on track.' },
      es: { name: 'Sabrina (Asistente de chat)', description: 'Orquesta conversaciones, deriva a especialistas y mantiene el rumbo.' }
    },
    'skill-creator': {
      pt: { name: 'Criador de skills', description: 'Cria e refina skills com base no seu objetivo, incluindo estrutura, prompt e validação.' },
      en: { name: 'Skill creator', description: 'Creates and refines skills from your goal, including structure, prompt and validation.' },
      es: { name: 'Creador de skills', description: 'Crea y refina skills a partir de tu objetivo, incluyendo estructura, prompt y validación.' }
    },
    'systems-architect': {
      pt: { name: 'Arquiteto de sistemas', description: 'Desenha sistemas escaláveis e fáceis de manter. Avalia padrões, trade-offs e pontos de integração.' },
      en: { name: 'Systems Architect', description: 'Designs scalable, maintainable systems. Evaluates patterns, trade-offs and integration points.' },
      es: { name: 'Arquitecto de sistemas', description: 'Diseña sistemas escalables y mantenibles. Evalúa patrones, trade-offs y puntos de integración.' }
    },
    'project-manager': {
      pt: { name: 'Gerente de projetos', description: 'Documenta tudo. Mantém registros, decisões, riscos e notas de reuniões.' },
      en: { name: 'Project Manager', description: 'Documents everything. Keeps records, decisions, risks and meeting notes.' },
      es: { name: 'Gerente de proyectos', description: 'Documenta todo. Mantiene registros, decisiones, riesgos y notas de reuniones.' }
    },
    cfo: {
      pt: { name: 'CFO', description: 'Orquestrador de finanças. Orçamento, runway, precificação, KPIs e controles. Primeiro o plano.' },
      en: { name: 'CFO', description: 'Finance orchestrator. Budgets, runway, pricing, KPIs and controls. Plan-first.' },
      es: { name: 'CFO', description: 'Orquestador financiero. Presupuesto, runway, precios, KPIs y controles. Primero el plan.' }
    },
    coo: {
      pt: { name: 'COO', description: 'Orquestrador de operações. Processos, entrega, times, SLAs e execução. Primeiro o plano.' },
      en: { name: 'COO', description: 'Operations orchestrator. Processes, delivery, teams, SLAs and execution. Plan-first.' },
      es: { name: 'COO', description: 'Orquestador de operaciones. Procesos, entrega, equipos, SLAs y ejecución. Primero el plan.' }
    },
    'excel-expert': {
      pt: { name: 'Especialista em Excel', description: 'Modelos financeiros, dashboards, fórmulas e validação/limpeza de dados.' },
      en: { name: 'Excel Expert', description: 'Financial models, dashboards, formulas and data validation/cleanup.' },
      es: { name: 'Experto en Excel', description: 'Modelos financieros, dashboards, fórmulas y validación/limpieza de datos.' }
    },
    'data-scientist': {
      pt: { name: 'Cientista de dados', description: 'Analytics, machine learning, métricas, qualidade de dados e integração de IA.' },
      en: { name: 'Data Scientist', description: 'Analytics, machine learning, metrics, data quality and AI integration.' },
      es: { name: 'Científico de datos', description: 'Analítica, machine learning, métricas, calidad de datos e integración de IA.' }
    },
    cto: {
      pt: { name: 'CTO', description: 'Discute, analisa, avalia, planeja e orquestra. Ativa plan→build para projetos complexos.' },
      en: { name: 'CTO', description: 'Discusses, analyses, evaluates, plans and orchestrates. Activates plan→build mode for complex projects.' },
      es: { name: 'CTO', description: 'Discute, analiza, evalúa, planifica y orquesta. Activa plan→build para proyectos complejos.' }
    },
    'backend-dev': {
      pt: { name: 'Desenvolvedor Backend', description: 'Ajuda com APIs, bancos de dados, performance, autenticação e integrações.' },
      en: { name: 'Backend Developer', description: 'Helps with APIs, databases, performance, auth and integrations.' },
      es: { name: 'Desarrollador Backend', description: 'Ayuda con APIs, bases de datos, rendimiento, autenticación e integraciones.' }
    },
    'frontend-dev': {
      pt: { name: 'Desenvolvedor Frontend', description: 'Ajuda com UI/UX, React, gerenciamento de estado, acessibilidade e performance.' },
      en: { name: 'Frontend Developer', description: 'Helps with UI/UX, React, state management, accessibility and performance.' },
      es: { name: 'Desarrollador Frontend', description: 'Ayuda con UI/UX, React, gestión de estado, accesibilidad y rendimiento.' }
    },
    devops: {
      pt: { name: 'DevOps', description: 'Ajuda com deploy, ambientes, CI/CD, observabilidade e automação.' },
      en: { name: 'DevOps', description: 'Helps with deploy, environments, CI/CD, observability and automation.' },
      es: { name: 'DevOps', description: 'Ayuda con despliegue, entornos, CI/CD, observabilidad y automatización.' }
    },
    security: {
      pt: { name: 'Revisor de segurança', description: 'Revisa riscos e fortalece autenticação, dados e fronteiras do sistema.' },
      en: { name: 'Security Reviewer', description: 'Reviews risks, hardens auth, data handling and system boundaries.' },
      es: { name: 'Revisor de seguridad', description: 'Revisa riesgos y refuerza autenticación, manejo de datos y límites del sistema.' }
    },
    'code-review': {
      pt: { name: 'Revisão de código', description: 'Revisão objetiva: bugs, legibilidade, casos de borda e complexidade.' },
      en: { name: 'Code Review', description: 'Objective review of changes — bugs, readability, edge cases.' },
      es: { name: 'Revisión de código', description: 'Revisión objetiva: bugs, legibilidad, casos límite y complejidad.' }
    },
    tests: {
      pt: { name: 'Testes', description: 'Cria e ajusta testes, valida cenários críticos e cobre regressões.' },
      en: { name: 'Tests', description: 'Creates and adjusts tests, validates critical scenarios.' },
      es: { name: 'Pruebas', description: 'Crea y ajusta pruebas, valida escenarios críticos.' }
    },
    seo: {
      pt: { name: 'Especialista em SEO', description: 'Pesquisa de palavras-chave, on-page, SEO técnico e estratégia de conteúdo.' },
      en: { name: 'SEO Specialist', description: 'Keyword research, on-page optimisation, technical SEO and content strategy.' },
      es: { name: 'Especialista en SEO', description: 'Investigación de keywords, on-page, SEO técnico y estrategia de contenido.' }
    },
    marketing: {
      pt: { name: 'Marketing', description: 'Posicionamento, mensagens, campanhas, copy e estratégia de crescimento.' },
      en: { name: 'Marketing', description: 'Positioning, messaging, campaigns, copy and growth strategy.' },
      es: { name: 'Marketing', description: 'Posicionamiento, mensajes, campañas, copy y estrategia de crecimiento.' }
    }
  };
  const BUILTIN_EXPERT_I18N = {
    general: {
      pt: { name: 'Sabrina (Assistente de chat)' },
      en: { name: 'Sabrina (Chat Assistant)' },
      es: { name: 'Sabrina (Asistente de chat)' }
    }
  };
  const getBuiltinMeta = (table, id, key, fallback) => {
    const cleanId = String(id || '').toLowerCase();
    const langKey = String(lang || 'en').toLowerCase();
    const byId = table?.[cleanId];
    const fromLang = byId?.[langKey]?.[key];
    const fromEn = byId?.en?.[key];
    return String(fromLang || fromEn || fallback || '').trim();
  };
  const getSkillDisplayName = (skill) => getBuiltinMeta(BUILTIN_SKILL_I18N, skill?.id, 'name', skill?.name || skill?.id);
  const getSkillDisplayDescription = (skill) => getBuiltinMeta(BUILTIN_SKILL_I18N, skill?.id, 'description', skill?.description || '');
  const getExpertDisplayName = (expert) => (
    getBuiltinMeta(BUILTIN_EXPERT_I18N, expert?.id, 'name', '') ||
    getBuiltinMeta(BUILTIN_SKILL_I18N, expert?.id, 'name', expert?.name || expert?.id)
  );
  const getExpertDisplayDescription = (expert) => (
    getBuiltinMeta(BUILTIN_EXPERT_I18N, expert?.id, 'description', '') ||
    getBuiltinMeta(BUILTIN_SKILL_I18N, expert?.id, 'description', expert?.description || '')
  );
  const SKILL_SEGMENT_PREFERRED_ORDER = {
    system: ['skill-creator', 'chat-assistant', 'cto', 'systems-architect'],
    finance: ['cfo', 'excel-expert'],
    admin: ['coo', 'project-manager'],
    it_devops: ['backend-dev', 'frontend-dev', 'devops', 'security', 'data-scientist', 'code-review', 'tests'],
    marketing: ['marketing', 'seo'],
    other: []
  };
  const EXPERT_SEGMENT_PREFERRED_ORDER = {
    system: ['skill-creator', 'general', 'chat-assistant', 'cto', 'systems-architect'],
    finance: ['cfo', 'excel-expert'],
    admin: ['coo', 'project-manager'],
    it_devops: ['backend-dev', 'frontend-dev', 'devops', 'security', 'data-scientist', 'code-review', 'tests'],
    marketing: ['marketing', 'seo'],
    other: []
  };
  const sortByPreferredOrder = (items, preferred, getId, getLabel) => {
    const order = Array.isArray(preferred) ? preferred : [];
    const idx = (v) => {
      const id = String(getId(v) || '').toLowerCase();
      const i = order.indexOf(id);
      return i === -1 ? 1e9 : i;
    };
    const label = (v) => String(getLabel(v) || '').toLowerCase();
    return (items || []).slice().sort((a, b) => {
      const da = idx(a);
      const db = idx(b);
      if (da !== db) return da - db;
      return label(a).localeCompare(label(b));
    });
  };
  const sortSkillsForSegment = (items, seg) => sortByPreferredOrder(items, SKILL_SEGMENT_PREFERRED_ORDER?.[seg], (s) => s?.id, getSkillDisplayName);
  const sortExpertsForSegment = (items, seg) => sortByPreferredOrder(items, EXPERT_SEGMENT_PREFERRED_ORDER?.[seg], (e) => e?.id, getExpertDisplayName);
  const groupBySegment = (items, getId) => {
    const map = {};
    (items || []).forEach((item) => {
      const seg = getId(item);
      if (!map[seg]) map[seg] = [];
      map[seg].push(item);
    });
    return map;
  };
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  }, [lang]);
  const formatCompactDateTime = (value) => {
    const d = value ? new Date(value) : null;
    if (!d || Number.isNaN(d.getTime())) return '';
    return d.toLocaleString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  };
  const getMessageTimestamp = (message) => message?.created_at || message?.createdAt || message?.timestamp || message?.time || '';

  // Estilos conforme WINDSURF_AGENT.md
  const styles = {
    app: {
      height: '100vh',
      background: 'var(--bg)',
      color: 'var(--text)',
      fontFamily: 'var(--sans)',
      display: 'flex',
      flexDirection: 'column'
    },
    header: {
      background: 'var(--bg2)',
      borderBottom: '1px solid var(--border)',
      padding: '16px 24px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    },
    headerTitle: {
      fontSize: '16px',
      fontWeight: '600',
      color: 'var(--text)',
      fontFamily: 'var(--sans)',
      lineHeight: '1.2',
      maxWidth: '520px'
    },
    headerRight: {
      display: 'flex',
      alignItems: 'center',
      gap: '16px'
    },
    iconButton: {
      background: 'transparent',
      border: '1px solid var(--border)',
      borderRadius: '6px',
      width: '36px',
      height: '36px',
      color: 'var(--text)',
      fontSize: '16px',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'all 0.15s'
    },
    connectionStatus: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      color: connected ? 'var(--green)' : 'var(--red)'
    },
    connectionDot: {
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      background: connected ? 'var(--green)' : 'var(--red)'
    },
    userButton: {
      background: 'transparent',
      border: '1px solid var(--border)',
      borderRadius: '6px',
      padding: '8px 12px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      cursor: 'pointer',
      transition: 'all 0.15s'
    },
    main: {
      flex: 1,
      display: 'flex',
      overflow: 'hidden'
    },
    sidebar: {
      width: '220px',
      background: 'var(--bg2)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      minHeight: 0
    },
    sidebarContent: {
      flex: 1,
      minHeight: 0,
      overflowY: 'auto'
    },
    sidebarSection: {
      padding: '16px',
      borderBottom: '1px solid var(--border)'
    },
    sidebarTitle: {
      fontSize: '10px',
      letterSpacing: '2',
      textTransform: 'uppercase',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)',
      marginBottom: '12px'
    },
    sidebarButton: {
      background: 'transparent',
      border: '1px solid transparent',
      borderRadius: '6px',
      padding: '10px 12px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      cursor: 'pointer',
      transition: 'all 0.15s',
      width: '100%',
      textAlign: 'left',
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    },
    sidebarButtonHover: {
      background: 'rgba(245, 166, 35, 0.08)',
      borderColor: 'rgba(245, 166, 35, 0.18)'
    },
    sidebarButtonActive: {
      background: 'rgba(245, 166, 35, 0.10)',
      borderColor: 'rgba(245, 166, 35, 0.35)',
      color: 'var(--text-bright)'
    },
    sidebarFooter: {
      padding: '16px',
      borderTop: '1px solid var(--border)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center'
    },
    sidebarBottom: {
      marginTop: 'auto',
      display: 'flex',
      flexDirection: 'column'
    },
    sidebarDonateArea: {
      padding: '16px',
      display: 'grid',
      gap: '10px'
    },
    sidebarLogo: {
      width: '100%',
      maxWidth: '300px',
      maxHeight: '160px',
      height: 'auto',
      display: 'block',
      objectFit: 'contain',
      alignSelf: 'center'
    },
    conversationList: {
      flex: 1,
      overflow: 'auto',
      padding: '8px'
    },
    conversationItem: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '6px',
      padding: '12px',
      marginBottom: '8px',
      cursor: 'pointer',
      transition: 'all 0.15s'
    },
    todoItem: {
      background: 'var(--bg3)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '10px',
      padding: '12px',
      transition: 'all 0.15s'
    },
    todoCheck: {
      width: '22px',
      height: '22px',
      borderRadius: '6px',
      border: '1px solid rgba(255,255,255,0.18)',
      background: 'rgba(255,255,255,0.04)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'var(--text-dim)',
      fontSize: '14px',
      flex: '0 0 auto'
    },
    conversationItemActive: {
      borderColor: 'var(--amber)',
      background: 'rgba(245, 166, 35, 0.1)'
    },
    conversationTitle: {
      fontSize: '14px',
      fontWeight: '500',
      color: 'var(--text)',
      marginBottom: '4px',
      fontFamily: 'var(--sans)'
    },
    conversationMeta: {
      fontSize: '11px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)'
    },
    newConversationButton: {
      background: 'var(--amber)',
      border: 'none',
      borderRadius: '6px',
      padding: '10px 16px',
      color: 'var(--bg)',
      fontSize: '12px',
      fontWeight: '600',
      fontFamily: 'var(--mono)',
      cursor: 'pointer',
      transition: 'all 0.15s',
      width: '100%'
    },
    chatArea: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column'
    },
    chatToolbar: {
      padding: '12px 24px',
      borderBottom: '1px solid var(--border)',
      background: 'var(--bg2)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '12px'
    },
    toolbarTitleRow: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      minWidth: 0
    },
    toolbarTitleText: {
      fontFamily: 'var(--mono)',
      fontSize: '12px',
      color: 'var(--text-dim)',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    },
    chatSearchInput: {
      width: '320px',
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '10px 12px',
      fontSize: '12px',
      color: 'var(--text-bright)',
      fontFamily: 'var(--mono)',
      outline: 'none'
    },
    chatSearchClear: {
      background: 'transparent',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '10px 12px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      cursor: 'pointer'
    },
    smallIconButton: {
      background: 'transparent',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      width: '34px',
      height: '34px',
      color: 'var(--text)',
      fontSize: '14px',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    },
    listTwoCols: {
      display: 'grid',
      gridTemplateColumns: '1.2fr 0.8fr',
      gap: '12px'
    },
    lightCard: {
      background: 'rgba(255,255,255,0.06)',
      border: '1px solid rgba(255,255,255,0.10)',
      borderRadius: '12px',
      padding: '12px'
    },
    skillGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
      gap: '10px'
    },
    skillCard: {
      background: 'rgba(255,255,255,0.06)',
      border: '1px solid rgba(255,255,255,0.10)',
      borderRadius: '12px',
      padding: '12px',
      cursor: 'pointer'
    },
    skillName: {
      fontSize: '13px',
      color: 'var(--text)',
      fontFamily: 'var(--sans)',
      fontWeight: 600
    },
    skillDesc: {
      marginTop: '6px',
      fontSize: '12px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)',
      lineHeight: 1.5
    },
    connectorGrid: {
      marginTop: '10px',
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
      gap: '10px'
    },
    connectorCard: {
      background: 'rgba(0,0,0,0.18)',
      border: '1px solid rgba(255,255,255,0.10)',
      borderRadius: '12px',
      padding: '12px',
      display: 'grid',
      gap: '10px'
    },
    connectorRow: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '10px'
    },
    connectorTitle: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      minWidth: 0
    },
    connectorDot: {
      width: '10px',
      height: '10px',
      borderRadius: '50%',
      background: 'var(--red)',
      flex: '0 0 auto'
    },
    monoTextarea: {
      width: '100%',
      minHeight: '320px',
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '12px',
      padding: '12px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      outline: 'none',
      resize: 'vertical'
    },
    messagesContainer: {
      flex: 1,
      overflow: 'auto',
      padding: '24px'
    },
    message: {
      marginBottom: '24px',
      display: 'flex',
      gap: '12px'
    },
    messageUser: {
      flexDirection: 'row-reverse'
    },
    messageAvatar: {
      width: '32px',
      height: '32px',
      borderRadius: '6px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '16px',
      flexShrink: 0
    },
    messageAvatarImg: {
      width: '100%',
      height: '100%',
      objectFit: 'cover',
      borderRadius: '6px',
      display: 'block'
    },
    messageContent: {
      flex: 1,
      maxWidth: '600px'
    },
    messageBubble: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '12px',
      padding: '12px 16px',
      fontSize: '14px',
      lineHeight: '1.6',
      fontFamily: 'var(--sans)',
      whiteSpace: 'pre-wrap'
    },
    messageBubbleUser: {
      background: 'var(--amber)',
      color: 'var(--bg)',
      borderColor: 'var(--amber)'
    },
    messageTimestamp: {
      marginTop: '6px',
      fontSize: '11px',
      fontFamily: 'var(--mono)',
      color: 'var(--text-dim)'
    },
    expertTag: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: '16px',
      padding: '4px 8px',
      fontSize: '11px',
      fontFamily: 'var(--mono)',
      color: 'var(--text-dim)',
      marginTop: '8px'
    },
    expertIcon: {
      fontSize: '12px'
    },
    inputArea: {
      padding: '16px 24px',
      borderTop: '1px solid var(--border)',
      background: 'var(--bg2)'
    },
    inputContainer: {
      display: 'flex',
      gap: '12px',
      alignItems: 'flex-end'
    },
    inputWrapper: {
      flex: 1
    },
    input: {
      width: '100%',
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '12px 16px',
      fontSize: '14px',
      color: 'var(--text-bright)',
      fontFamily: 'var(--sans)',
      outline: 'none',
      resize: 'none',
      minHeight: '48px',
      maxHeight: '200px'
    },
    sendButton: {
      background: 'var(--amber)',
      border: 'none',
      borderRadius: '8px',
      padding: '12px 20px',
      color: 'var(--bg)',
      fontSize: '14px',
      fontWeight: '600',
      fontFamily: 'var(--mono)',
      cursor: 'pointer',
      transition: 'all 0.15s',
      height: '48px'
    },
    sendButtonDisabled: {
      opacity: 0.6,
      cursor: 'not-allowed'
    },
    loadingScreen: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: 'var(--bg)',
      color: 'var(--text)',
      fontFamily: 'var(--sans)'
    },
    centerPanel: {
      flex: 1,
      overflow: 'auto',
      padding: '24px'
    },
    centerPanelTitle: {
      fontSize: '14px',
      fontWeight: '600',
      fontFamily: 'var(--mono)',
      color: 'var(--text)',
      marginBottom: '16px'
    },
    emptyState: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '10px',
      padding: '16px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--sans)'
    },
    settingsSection: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '10px',
      padding: '16px',
      marginBottom: '16px'
    },
    settingsSectionTitle: {
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      color: 'var(--text)',
      marginBottom: '12px'
    },
    settingsGrid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '12px'
    },
    settingsField: {
      display: 'flex',
      flexDirection: 'column',
      gap: '6px'
    },
    settingsLabel: {
      fontSize: '11px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)'
    },
    settingsInput: {
      width: '100%',
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '10px 12px',
      fontSize: '12px',
      color: 'var(--text-bright)',
      fontFamily: 'var(--mono)',
      outline: 'none'
    },
    settingsTextarea: {
      width: '100%',
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '10px 12px',
      fontSize: '12px',
      color: 'var(--text-bright)',
      fontFamily: 'var(--mono)',
      outline: 'none',
      resize: 'vertical',
      minHeight: '90px'
    },
    settingsActions: {
      display: 'flex',
      gap: '10px',
      justifyContent: 'flex-end',
      marginTop: '12px'
    },
    settingsPrimaryButton: {
      background: 'var(--amber)',
      border: 'none',
      borderRadius: '8px',
      padding: '10px 14px',
      color: 'var(--bg)',
      fontSize: '12px',
      fontWeight: '600',
      fontFamily: 'var(--mono)',
      cursor: 'pointer'
    },
    settingsSecondaryButton: {
      background: 'transparent',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '10px 14px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      cursor: 'pointer'
    },
    settingsHint: {
      fontSize: '11px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--sans)',
      marginTop: '8px'
    },
    settingsError: {
      background: 'rgba(248, 113, 113, 0.12)',
      border: '1px solid rgba(248, 113, 113, 0.4)',
      borderRadius: '10px',
      padding: '12px',
      color: 'var(--text)',
      fontFamily: 'var(--sans)',
      marginBottom: '16px'
    },
    doctorCard: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '10px',
      padding: '14px',
      marginBottom: '16px'
    },
    doctorRow: {
      display: 'flex',
      justifyContent: 'space-between',
      gap: '12px',
      alignItems: 'flex-start',
      padding: '8px 0',
      borderBottom: '1px solid rgba(255,255,255,0.06)'
    },
    doctorRowLast: {
      borderBottom: 'none'
    },
    doctorLabel: {
      fontSize: '12px',
      color: 'var(--text)',
      fontFamily: 'var(--sans)'
    },
    doctorDetail: {
      fontSize: '11px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)',
      marginTop: '4px'
    },
    doctorStatus: {
      fontSize: '11px',
      fontFamily: 'var(--mono)',
      padding: '4px 8px',
      borderRadius: '999px',
      border: '1px solid var(--border)',
      whiteSpace: 'nowrap'
    },
    commandCard: {
      marginTop: '10px',
      border: '1px solid rgba(245, 166, 35, 0.35)',
      background: 'rgba(245, 166, 35, 0.08)',
      borderRadius: '8px',
      padding: '12px'
    },
    commandTitle: {
      fontSize: '12px',
      fontWeight: '600',
      color: 'var(--text)',
      fontFamily: 'var(--sans)'
    },
    commandMeta: {
      marginTop: '6px',
      fontSize: '11px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)',
      whiteSpace: 'pre-wrap'
    },
    commandActions: {
      marginTop: '10px',
      display: 'flex',
      gap: '10px',
      alignItems: 'center'
    },
    modalOverlay: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.55)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '24px'
    },
    modal: {
      width: '100%',
      maxWidth: '640px',
      borderRadius: '10px',
      border: '1px solid var(--border)',
      background: 'var(--bg2)',
      padding: '16px'
    },
    modalHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '12px'
    },
    modalTitle: {
      fontSize: '14px',
      fontWeight: '600',
      color: 'var(--text)',
      fontFamily: 'var(--sans)'
    },
    modalBody: {
      marginTop: '12px',
      fontSize: '12px',
      color: 'var(--text)',
      fontFamily: 'var(--sans)',
      whiteSpace: 'pre-wrap'
    }
  };

  const openCliArtifact = async (artifact) => {
    const url = String(artifact?.url || '').trim();
    const name = String(artifact?.name || 'artefato').trim() || 'artefato';
    if (!url) return;
    try {
      const res = await fetch(url, { headers: getAuthHeaders() });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const objUrl = URL.createObjectURL(blob);
      const ext = name.split('.').pop()?.toLowerCase() || '';
      const isImage = ['png', 'jpg', 'jpeg', 'webp'].includes(ext);
      if (isImage) {
        window.open(objUrl, '_blank', 'noopener,noreferrer');
        setTimeout(() => URL.revokeObjectURL(objUrl), 60000);
        return;
      }
      const a = document.createElement('a');
      a.href = objUrl;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(objUrl), 60000);
    } catch (e) {
      console.error('Falha ao abrir artefato:', e);
    }
  };

  const CLIDisplay = ({ payload }) => {
    const status = String(payload?.status || '').toLowerCase();
    const borderColor =
      status === 'success' ? 'var(--green)' : status === 'error' ? 'var(--red)' : 'var(--border)';
    const titleIcon =
      status === 'success' ? '✅' : status === 'error' ? '❌' : '⏳';
    const attempt = Number(payload?.attempt) || 1;
    const cmd = String(payload?.command_executed || payload?.command || '').trim();
    const stdout = String(payload?.stdout || '').trim();
    const stderr = String(payload?.stderr || '').trim();
    const visual = String(payload?.visual_state_summary || '').trim();
    const cursor = status === 'running' && loadingTick % 2 === 0 ? '▌' : '';
    const artifacts = Array.isArray(payload?.artifacts) ? payload.artifacts : [];
    const dots = status === 'running' ? '.'.repeat((loadingTick % 4) + 1) : '';
    const startedAtMs = Number(payload?.started_at_ms) || 0;
    const timeoutS = Number(payload?.timeout_s) || 0;
    const returnMs = Number(payload?.return_ms) || 0;
    const elapsedMs =
      status === 'running'
        ? Math.max(0, Date.now() - (startedAtMs || Date.now()))
        : Math.max(0, returnMs);

    const fmtTime = (ms) => {
      const total = Math.max(0, Math.floor(Number(ms || 0) / 1000));
      const m = String(Math.floor(total / 60)).padStart(2, '0');
      const s = String(total % 60).padStart(2, '0');
      return `${m}:${s}`;
    };

    const ratio = timeoutS ? Math.min(1, elapsedMs / (timeoutS * 1000)) : null;
    const pct = ratio === null ? (loadingTick % 20) / 20 : ratio;
    const barColor =
      ratio === null
        ? 'rgba(212,212,212,0.35)'
        : ratio < 0.7
          ? 'var(--green)'
          : ratio < 0.9
            ? '#f6c177'
            : 'var(--red)';

    return (
      <div
        style={{
          background: '#1e1e1e',
          border: `1px solid ${borderColor}`,
          borderRadius: '10px',
          padding: '10px 12px',
          fontFamily: 'JetBrains Mono, Consolas, var(--mono)',
          fontSize: '12px',
          color: '#d4d4d4',
          boxShadow: '0 6px 24px rgba(0,0,0,0.35)',
          maxWidth: '100%',
          overflowX: 'auto'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <div style={{ fontSize: '12px', color: 'rgba(212,212,212,0.75)' }}>
            {titleIcon} ExternalSoftwareSkill • tentativa {attempt}
          </div>
        </div>
        <div style={{ color: 'var(--green)', whiteSpace: 'pre-wrap' }}>
          {'> '}
          {cmd}
          {cursor}
        </div>
        {status === 'running' ? (
          <>
            <div style={{ marginTop: '8px', color: 'rgba(212,212,212,0.75)', whiteSpace: 'pre-wrap' }}>
              Processando no Sistema{dots}
            </div>
            <div style={{ marginTop: '6px', color: 'rgba(212,212,212,0.75)' }}>
              Tempo: {fmtTime(elapsedMs)}{timeoutS ? ` / ${fmtTime(timeoutS * 1000)}` : ''}
            </div>
            <div
              style={{
                marginTop: '6px',
                height: '6px',
                width: '100%',
                background: 'rgba(255,255,255,0.08)',
                borderRadius: '999px',
                overflow: 'hidden'
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${Math.max(2, Math.min(100, Math.floor(pct * 100)))}%`,
                  background: barColor,
                  transition: 'width 250ms linear'
                }}
              />
            </div>
          </>
        ) : null}
        {stdout ? (
          <div style={{ marginTop: '10px', whiteSpace: 'pre-wrap', color: '#d4d4d4' }}>
            {stdout}
          </div>
        ) : null}
        {stderr ? (
          <div style={{ marginTop: '10px', whiteSpace: 'pre-wrap', color: 'var(--red)' }}>
            {stderr}
          </div>
        ) : null}
        {visual ? (
          <div style={{ marginTop: '10px', whiteSpace: 'pre-wrap', color: 'rgba(212,212,212,0.75)' }}>
            {visual}
          </div>
        ) : null}
        {artifacts.length ? (
          <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {artifacts.map((a) => {
              const name = String(a?.name || '').trim();
              const ext = name.split('.').pop()?.toLowerCase() || '';
              const isImage = ['png', 'jpg', 'jpeg', 'webp'].includes(ext);
              const label = isImage ? '🖼️ Ver Diagrama' : '📂 Abrir Arquivo';
              return (
                <button
                  key={String(a?.id || a?.url || name || Math.random())}
                  style={{
                    ...styles.settingsSecondaryButton,
                    background: 'transparent',
                    border: `1px solid ${borderColor}`,
                    color: '#d4d4d4'
                  }}
                  onClick={() => openCliArtifact(a)}
                >
                  {label}{name ? ` — ${name}` : ''}
                </button>
              );
            })}
          </div>
        ) : null}
      </div>
    );
  };

  const parseMessageBlocks = (content) => {
    const blocks = [];
    let remaining = String(content || '');
    while (remaining) {
      const thinkingStart = remaining.indexOf('<THINKING>');
      const planStart = remaining.indexOf('```plan');
      const candidates = [thinkingStart, planStart].filter((n) => n >= 0);
      if (!candidates.length) break;
      const nextStart = Math.min(...candidates);
      if (nextStart > 0) {
        const prefix = remaining.slice(0, nextStart);
        if (prefix.trim()) blocks.push({ type: 'text', content: prefix.trim() });
        remaining = remaining.slice(nextStart);
      }

      if (remaining.startsWith('<THINKING>')) {
        const end = remaining.indexOf('</THINKING>');
        if (end === -1) break;
        const inner = remaining.slice('<THINKING>'.length, end);
        blocks.push({ type: 'thinking', content: inner.trim() });
        remaining = remaining.slice(end + '</THINKING>'.length);
        continue;
      }

      if (remaining.startsWith('```plan')) {
        const fenceEnd = remaining.indexOf('```', '```plan'.length);
        if (fenceEnd === -1) break;
        const inner = remaining.slice('```plan'.length, fenceEnd);
        blocks.push({ type: 'plan', content: inner.replace(/^\s+/, '').replace(/\s+$/, '') });
        remaining = remaining.slice(fenceEnd + 3);
        continue;
      }

      break;
    }
    if (remaining.trim()) blocks.push({ type: 'text', content: remaining.trim() });
    return blocks.length ? blocks : [{ type: 'text', content: String(content || '') }];
  };

  const parsePlanTasksFromText = (raw) => {
    const lines = String(raw || '')
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean);
    const out = [];
    for (const line of lines) {
      if (!line.includes('|')) continue;
      const [left, right] = line.split('|');
      const title = String(left || '').trim();
      const skill_id = String(right || '').trim();
      if (!title || title.toLowerCase() === 'tarefa') continue;
      out.push({ title, skill_id });
    }
    return out;
  };

  const MessageBlock = ({ block, onApprovePlan }) => {
    const [collapsed, setCollapsed] = React.useState(true);

    if (block?.type === 'thinking') {
      return (
        <div style={{
          border: '1px solid var(--border)',
          borderRadius: '8px',
          marginTop: '10px',
          overflow: 'hidden',
          fontSize: '12px'
        }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '7px 12px',
              background: 'var(--bg2)',
              cursor: 'pointer',
              userSelect: 'none'
            }}
            onClick={() => setCollapsed(v => !v)}
          >
            <span style={{
              fontSize: '10px',
              padding: '2px 8px',
              borderRadius: '999px',
              background: 'rgba(127,119,221,0.12)',
              color: '#7F77DD',
              fontWeight: 500
            }}>
              raciocínio
            </span>
            <span style={{ marginLeft: 'auto', color: 'var(--text-dim)', fontSize: '11px' }}>
              {collapsed ? '▸ expandir' : '▾ recolher'}
            </span>
          </div>
          {!collapsed ? (
            <div style={{
              padding: '10px 12px',
              color: 'var(--text-dim)',
              fontFamily: 'var(--mono)',
              whiteSpace: 'pre-wrap',
              lineHeight: 1.5
            }}>
              {block.content}
            </div>
          ) : null}
        </div>
      );
    }

    if (block?.type === 'plan') {
      const tasks = parsePlanTasksFromText(block.content || '');
      return (
        <div style={{
          border: '1px solid rgba(245,166,35,0.35)',
          borderRadius: '8px',
          marginTop: '10px',
          overflow: 'hidden'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '8px 12px',
            background: 'rgba(245,166,35,0.10)'
          }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--amber)', letterSpacing: '0.04em' }}>
              PLAN
            </div>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                style={{ ...styles.settingsPrimaryButton, padding: '6px 10px', fontSize: '11px' }}
                onClick={() => onApprovePlan?.(tasks)}
                disabled={!tasks.length}
              >
                Aprovar
              </button>
            </div>
          </div>
          <div style={{ padding: '10px 12px' }}>
            {tasks.length ? (
              <div style={{ display: 'grid', gap: '6px' }}>
                {tasks.map((t, i) => (
                  <div key={`${t.title}-${t.skill_id}-${i}`} style={{ display: 'flex', gap: '10px', alignItems: 'baseline' }}>
                    <div style={{ width: '18px', textAlign: 'center', color: 'var(--amber)', fontFamily: 'var(--mono)' }}>•</div>
                    <div style={{ flex: 1, minWidth: 0, fontFamily: 'var(--sans)', fontSize: '13px', color: 'var(--text)' }}>
                      {t.title}
                    </div>
                    {t.skill_id ? (
                      <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                        {t.skill_id}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-dim)', whiteSpace: 'pre-wrap' }}>
                {block.content}
              </div>
            )}
          </div>
        </div>
      );
    }

    return block?.content ? <div style={{ whiteSpace: 'pre-wrap' }}>{block.content}</div> : null;
  };

  const extractTaggedJsonBlocks = (text, startTag, endTag) => {
    const blocks = [];
    if (!text) return { text: '', blocks };

    let cursor = 0;
    let out = '';
    while (true) {
      const start = text.indexOf(startTag, cursor);
      if (start === -1) break;
      const end = text.indexOf(endTag, start + startTag.length);
      if (end === -1) break;

      out += text.slice(cursor, start);
      const raw = text.slice(start + startTag.length, end).trim();
      let obj = null;
      try {
        obj = raw ? JSON.parse(raw) : null;
      } catch {
        obj = null;
      }
      if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
        blocks.push(obj);
      } else {
        out += text.slice(start, end + endTag.length);
      }
      cursor = end + endTag.length;
    }
    out += text.slice(cursor);
    return { text: out.trim(), blocks };
  };

  const parseCommandRequestsFromContent = (content) => {
    const first = extractTaggedJsonBlocks(
      content || '',
      '<COMMAND_REQUEST_JSON>',
      '</COMMAND_REQUEST_JSON>'
    );
    const second = extractTaggedJsonBlocks(
      first.text || '',
      '<COMMAND_JSON>',
      '</COMMAND_JSON>'
    );
    return {
      text: second.text || '',
      requests: [...(first.blocks || []), ...(second.blocks || [])]
    };
  };

  const riskLabel = (riskLevel) => {
    const v = Number(riskLevel);
    if (v === 0) return 'Somente leitura';
    if (v === 1) return 'Altera projeto (confirmar)';
    if (v === 2) return 'Impacto no sistema (confirmar)';
    return 'Alto risco/bloqueado';
  };

  const openCommandModal = (req) => {
    setCommandModal(req);
  };

  const executePendingCommand = async (req) => {
    if (!req?.id) return;
    if (executingCommandId) return;

    try {
      setExecutingCommandId(req.id);
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      headers['Content-Type'] = 'application/json';

      const res = await fetch(
        `/api/commands/pending/${encodeURIComponent(req.id)}/execute`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({ confirm: true })
        }
      );

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data?.detail || 'Failed to execute command.';
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `❌ ${msg}`,
            id: `${Date.now()}-${Math.random().toString(16).slice(2)}`
          }
        ]);
        return;
      }

      setExecutedCommandIds((prev) => ({ ...prev, [req.id]: true }));
      const output = data?.output || data?.stdout || '(sem saída)';
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `✅ Comando executado:\n${data?.command || req.command}\n\n${output}`,
          id: `${Date.now()}-${Math.random().toString(16).slice(2)}`
        }
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ Error executing command: ${e?.message || String(e)}`,
          id: `${Date.now()}-${Math.random().toString(16).slice(2)}`
        }
      ]);
    } finally {
      setExecutingCommandId('');
      setCommandModal(null);
    }
  };

  const createTaskWithPrefill = async (prefill, autoSend = false) => {
    await createNewTask();
    setInput(String(prefill || ''));
    if (autoSend) {
      pendingAutoSendRef.current = String(prefill || '');
    }
  };

  useEffect(() => {
    if (user && token) {
      const headers = getAuthHeaders();
      fetch('/api/experts', { headers })
        .then(async (res) => {
          const json = await res.json().catch(() => ({}));
          if (!res.ok) {
            throw new Error(json?.detail || 'Não foi possível carregar os agentes.');
          }
          return json;
        })
        .then(data => setExperts(data.experts || data.experts || []))
        .catch(err => console.error('Error loading agents:', err));
    }
  }, [user, token]);

  const buildSabrinaBellPrompt = () => {
    let greeted = false;
    try {
      greeted = localStorage.getItem('open_slap_sabrina_greeted_v1') === '1';
      if (!greeted) localStorage.setItem('open_slap_sabrina_greeted_v1', '1');
    } catch {}
    if (!greeted) {
      return lang === 'pt'
        ? 'Sabrina? Pode se apresentar brevemente e me perguntar qual é minha prioridade de hoje. Depois, conduza com 3 perguntas objetivas e proponha próximos passos.'
        : "Sabrina? Please introduce yourself briefly and ask what my top priority is today. Then ask 3 objective questions and propose next steps.";
    }
    return lang === 'pt'
      ? 'Sabrina? Estou aqui. Sem apresentação/repetição: faça só 1–3 perguntas objetivas e conduza para os próximos passos.'
      : "Sabrina? I'm here. No intro/repetition: ask only 1–3 objective questions and drive to the next steps.";
  };

  useEffect(() => {
    try {
      const raw = localStorage.getItem('open_slap_lang_v1');
      const v = (raw || '').trim().toLowerCase();
      if (v && ['pt', 'en', 'es', 'ar', 'zh'].includes(v)) {
        setLang(v);
      }
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('open_slap_lang_v1', String(lang || 'en'));
    } catch {}
    try {
      document.documentElement.lang = lang === 'pt' ? 'pt-BR' : lang;
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    } catch {}
  }, [lang]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('open_slap_agent_configs_v1');
      const parsed = raw ? JSON.parse(raw) : {};
      if (parsed && typeof parsed === 'object') setAgentConfigs(parsed);
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('open_slap_agent_configs_v1', JSON.stringify(agentConfigs || {}));
    } catch {}
  }, [agentConfigs]);

  useEffect(() => {
    if (centerView === 'team') {
      setCenterView('settings');
      setSettingsTab('team');
      return;
    }
    if (centerView === 'customize') {
      setCenterView('settings');
      setSettingsTab('skills');
    }
  }, [centerView]);

  // Theme persistence
  useEffect(() => {
    try {
      const saved = localStorage.getItem('open_slap_theme_v1');
      if (saved) setTheme(saved);
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('open_slap_theme_v1', theme || 'deep-space');
      document.documentElement.setAttribute('data-theme', theme === 'deep-space' ? '' : theme);
    } catch {}
  }, [theme]);

  useEffect(() => {
    const defaults = [
      // ── Strategic ────────────────────────────────────────────────────────────
      {
        id: 'cto',
        name: 'CTO',
        description: 'Discusses, analyses, evaluates, plans and orchestrates. Activates plan→build mode for complex projects.',
        content: {
          role: 'Chief Technology Officer',
          mode: 'plan→build',
          focus: ['architecture', 'trade-offs', 'roadmap', 'team coordination', 'risk'],
          prompt:
            'Você é o CTO — Arquiteto de Soluções.\n' +
            'Regra de Ouro: NUNCA forneça uma linha de código sem antes apresentar um Documento de Design Técnico (TDD) e obter aprovação explícita.\n' +
            'Regra de credenciais: NUNCA solicite chaves de API ou secrets no chat. Se precisar de credenciais, direcione para Settings → LLM (token: [[open_settings:llm_api_key]]).\n' +
            'Fluxo obrigatório: PLAN → DELEGATE → BUILD.\n\n' +
            'PLAN:\n' +
            '- Faça 3–7 perguntas objetivas para esclarecer: objetivo de negócio, usuários, escopo, restrições, prazo, integrações, dados sensíveis e escala.\n' +
            '- Depois gere um TDD em Markdown com:\n' +
            '  1) Objetivo de Negócio\n' +
            '  2) Premissas\n' +
            '  3) Escopo e Não-Objetivos\n' +
            '  4) Arquitetura proposta (diagrama em Mermaid)\n' +
            '  5) Stack (Backend/Frontend/Infra)\n' +
            '  6) Contratos (APIs e dados em alto nível)\n' +
            '  7) Segurança e Privacidade (LGPD/GDPR quando aplicável)\n' +
            '  8) Observabilidade (logs/métricas/traces)\n' +
            '  9) Riscos (segurança e custo) + mitigação\n' +
            '  10) Trade-offs: para cada decisão relevante, liste 2 prós e 2 contras\n' +
            '  11) Plano de entrega: milestones/sprints, dependências, gargalos e riscos de burnout\n' +
            '- Em seguida, produza IMEDIATAMENTE um breakdown no formato:\n' +
            '  ```plan\n' +
            '  Tarefa | skill_id\n' +
            '  ```\n' +
            '  skill_ids válidos: cto, cfo, coo, project-manager, systems-architect, backend-dev, frontend-dev, devops, security, data-scientist, code-review, tests, excel-expert, seo, marketing, chat-assistant\n' +
            '- Termine pedindo aprovação do TDD/plano. Se não aprovado, pergunte o que mudar.\n\n' +
            'DELEGATE (contratos de serviço):\n' +
            '- [BACKEND] Antes de codar: ERD + endpoints (OpenAPI/Swagger). Foque em Clean Architecture, erros e performance.\n' +
            '- [FRONTEND] Antes de codar: hierarquia de componentes + estratégia de estado. Foque em Core Web Vitals e acessibilidade (WCAG).\n' +
            '- [DEVOPS] Antes de executar: pipeline CI/CD + arquitetura cloud/IaC. Foque em observabilidade e custos.\n' +
            '- [SECURITY] Revise planos de backend/frontend antes de implementar. Foque em OWASP, cripto, OAuth2/JWT e LGPD/GDPR.\n' +
            '- [DATA] Antes de modelar: pipeline de dados + métricas (Acurácia/F1). Foque em integridade e ética.\n' +
            '- [PM] Organize em sprints, MoSCoW e critérios de aceite; mantenha backlog e documentação.\n\n' +
            'BUILD:\n' +
            '- Só execute após aprovação.\n' +
            '- Integre as respostas, valide contra o plano e rejeite dívida técnica sem justificativa.\n' +
            '- Testes unitários obrigatórios nos módulos relevantes; segurança by design.'
        }
      },
      {
        id: 'cfo',
        name: 'CFO',
        description: 'Finance orchestrator. Budgets, runway, pricing, KPIs and controls. Plan-first.',
        content: {
          role: 'Chief Financial Officer',
          mode: 'plan→build',
          focus: ['budgeting', 'runway', 'pricing', 'unit economics', 'KPIs', 'risk', 'controls'],
          prompt:
            'Você é o CFO — orquestrador de Finanças.\n' +
            'Fluxo obrigatório: PLAN → DELEGATE → EXECUTE.\n' +
            'Regra: não proponha ações irreversíveis (contratação, gastos, mudança de preço) sem um plano aprovado.\n\n' +
            'Regra de credenciais: NUNCA solicite chaves de API ou secrets no chat. Se precisar, direcione para Settings → LLM (token: [[open_settings:llm_api_key]]).\n\n' +
            'PLAN:\n' +
            '- Faça 3–7 perguntas objetivas: objetivo (reduzir custo, aumentar receita, planejamento), horizonte (30/90/180 dias), moeda/país, restrições, fonte de dados, nível de detalhe e tolerância a risco.\n' +
            '- Gere um Plano Financeiro em Markdown com:\n' +
            '  1) Objetivo e contexto\n' +
            '  2) Premissas (receita, custos, churn, CAC, conversão, impostos quando aplicável)\n' +
            '  3) Modelo de custos (fixos/variáveis) e alavancas\n' +
            '  4) KPIs (definições e como medir)\n' +
            '  5) Cenários (base/otimista/pessimista) e trade-offs (2 prós/2 contras)\n' +
            '  6) Riscos e controles (fraude, compliance, caixa)\n' +
            '  7) Plano de execução (passos, donos, datas)\n' +
            '- Em seguida, gere um bloco:\n' +
            '  ```plan\n' +
            '  Tarefa | skill_id\n' +
            '  ```\n' +
            '  Use skill_ids como: cfo, project-manager, excel-expert, marketing, security, chat-assistant.\n' +
            '- Peça aprovação explícita.\n\n' +
            'DELEGATE:\n' +
            '- [EXCEL] Modelo financeiro, dashboards e validação de dados.\n' +
            '- [PM] Backlog financeiro, sprints, critérios de aceite e registro de decisões.\n' +
            '- [MARKETING] Testes de precificação/mensagens e impacto em conversão.\n' +
            '- [SECURITY] Controles, auditoria, risco e conformidade quando aplicável.\n\n' +
            'EXECUTE:\n' +
            '- Só após aprovação. Execute incrementalmente e revise métricas a cada entrega.'
        }
      },
      {
        id: 'coo',
        name: 'COO',
        description: 'Operations orchestrator. Processes, delivery, teams, SLAs and execution. Plan-first.',
        content: {
          role: 'Chief Operating Officer',
          mode: 'plan→build',
          focus: ['operations', 'processes', 'SOPs', 'execution', 'SLAs', 'org design', 'risk'],
          prompt:
            'Você é o COO — orquestrador de Operações.\n' +
            'Fluxo obrigatório: PLAN → DELEGATE → EXECUTE.\n' +
            'Regra: não proponha mudanças organizacionais/processuais grandes sem um plano aprovado e critérios de sucesso.\n\n' +
            'Regra de credenciais: NUNCA solicite chaves de API ou secrets no chat. Se precisar, direcione para Settings → LLM (token: [[open_settings:llm_api_key]]).\n\n' +
            'PLAN:\n' +
            '- Faça 3–7 perguntas objetivas: área (suporte, vendas, entrega, logística, produto), métricas atuais, gargalos, stakeholders, restrições e horizonte.\n' +
            '- Produza um Plano Operacional em Markdown com:\n' +
            '  1) Objetivo e escopo\n' +
            '  2) Situação atual (processos, papéis, SLAs)\n' +
            '  3) Proposta (processos/SOPs, RACI, cadência, ferramentas)\n' +
            '  4) Métricas e metas (OKRs/KPIs) + como medir\n' +
            '  5) Riscos e mitigação\n' +
            '  6) Trade-offs (2 prós/2 contras) para mudanças relevantes\n' +
            '  7) Plano de execução (fases, donos, prazos)\n' +
            '- Em seguida, gere um bloco:\n' +
            '  ```plan\n' +
            '  Tarefa | skill_id\n' +
            '  ```\n' +
            '  Use skill_ids como: coo, project-manager, chat-assistant, systems-architect, security.\n' +
            '- Peça aprovação explícita.\n\n' +
            'DELEGATE:\n' +
            '- [PM] Organização em sprints, critérios de aceite, gestão de impedimentos e documentação.\n' +
            '- [ARCH] Se houver sistema/automação, desenhe integrações e fluxos.\n' +
            '- [SECURITY] Se envolver dados sensíveis e controles, revise riscos.\n\n' +
            'EXECUTE:\n' +
            '- Só após aprovação. Entregue melhorias por incrementos e valide por métricas.'
        }
      },
      {
        id: 'project-manager',
        name: 'Project Manager',
        description: 'Documents everything. Keeps records, decisions, risks and meeting notes.',
        content: {
          role: 'Project Manager',
          focus: ['documentation', 'decisions log', 'risk register', 'meeting notes', 'status reports'],
          prompt:
            'You are acting as Project Manager. Your primary output is written documentation.\n' +
            'For every interaction: capture decisions made, open items, risks identified and owners. ' +
            'Produce structured artefacts (meeting notes, ADRs, risk register entries, status reports) in Markdown. ' +
            'Ask who owns each action item and what the due date is. ' +
            'Never leave a conversation without a written summary.'
        }
      },
      {
        id: 'systems-architect',
        name: 'Systems Architect',
        description: 'Designs scalable, maintainable systems. Evaluates patterns, trade-offs and integration points.',
        content: {
          role: 'Systems Architect',
          mode: 'plan→build',
          focus: ['system design', 'patterns', 'APIs', 'data models', 'scalability', 'observability'],
          prompt:
            'You are acting as Systems Architect. When given a requirement:\n' +
            '1. Ask about scale, SLAs, team size and existing constraints.\n' +
            '2. Propose 2–3 architectural options with trade-offs (complexity, cost, flexibility).\n' +
            '3. Recommend one and justify it.\n' +
            '4. Produce a design artefact: component diagram description, data model sketch, API contracts, and a list of cross-cutting concerns (auth, logging, error handling, migrations).\n' +
            'Prefer simple, boring technology unless there is a clear reason not to.'
        }
      },
      // ── Engineering ──────────────────────────────────────────────────────────
      {
        id: 'backend-dev',
        name: 'Backend Developer',
        description: 'Helps with APIs, databases, performance, auth and integrations.',
        content: {
          role: 'Backend Developer',
          focus: ['FastAPI', 'Python', 'SQL', 'authentication', 'migrations', 'performance'],
          prompt:
            'Você é o Engenheiro Backend Sênior sob comando do CTO.\n' +
            'Regra de credenciais: NUNCA solicite chaves de API ou secrets no chat. Se precisar, direcione para Settings → LLM.\n' +
            'Regra: antes de escrever código, apresente:\n' +
            '- Esquema do banco (ERD: tabelas, chaves, relacionamentos, índices)\n' +
            '- Contrato da API (lista de endpoints estilo OpenAPI: método, path, payload, respostas, erros)\n' +
            'Depois de aprovado, entregue: implementação com tratamento de erros, validação de entrada, migrações e testes.\n' +
            'Foque em Clean Architecture, integridade, performance de queries e segurança (injeção, auth bypass, segredos).'
        }
      },
      {
        id: 'frontend-dev',
        name: 'Frontend Developer',
        description: 'Helps with UI/UX, React, state management, accessibility and performance.',
        content: {
          role: 'Frontend Developer',
          focus: ['React', 'TypeScript', 'CSS', 'accessibility', 'state management', 'performance'],
          prompt:
            'Você é o Especialista Frontend sob comando do CTO.\n' +
            'Regra de credenciais: NUNCA solicite chaves de API ou secrets no chat. Se precisar, direcione para Settings → LLM.\n' +
            'Regra: antes de escrever código, descreva:\n' +
            '- Hierarquia de componentes (páginas → componentes → subcomponentes)\n' +
            '- Estratégia de gerenciamento de estado (local/context/query cache) e fluxo de dados\n' +
            '- Responsividade (breakpoints) + acessibilidade (WCAG) + performance (Core Web Vitals)\n' +
            'Depois de aprovado, entregue: componentes, estilos, comportamento responsivo e notas de a11y.\n' +
            'Prefira HTML semântico e interações progressivas.'
        }
      },
      {
        id: 'devops',
        name: 'DevOps',
        description: 'Helps with deploy, environments, CI/CD, observability and automation.',
        content: {
          role: 'DevOps Engineer',
          focus: ['Docker', 'CI/CD', 'monitoring', 'secrets management', 'IaC'],
          prompt:
            'Você é o Especialista em Infraestrutura e CI/CD sob comando do CTO.\n' +
            'Regra de credenciais: NUNCA solicite chaves de API ou secrets no chat. Se precisar, direcione para Settings → LLM.\n' +
            'Regra: antes de executar, descreva:\n' +
            '- Fluxo de pipeline (CI/CD) com etapas, gates e artefatos\n' +
            '- Arquitetura cloud (ou self-hosted) e IaC (o que será provisionado)\n' +
            '- Observabilidade (logs/métricas/traces) e estratégia de custos\n' +
            'Depois de aprovado, entregue: configs (pipeline, Docker/compose), estratégia de deploy/rollback e gestão de segredos.\n' +
            'Nunca coloque segredos no código.'
        }
      },
      {
        id: 'security',
        name: 'Security Reviewer',
        description: 'Reviews risks, hardens auth, data handling and system boundaries.',
        content: {
          role: 'Security Engineer',
          focus: ['OWASP', 'auth', 'PII', 'secrets', 'threat modelling', 'hardening'],
          prompt:
            'Você é o Guardião da Segurança sob comando do CTO.\n' +
            'Regra de credenciais: NUNCA solicite chaves de API ou secrets no chat. Se precisar orientar configuração, direcione para Settings → LLM.\n' +
            'Regra: revise o plano de backend e frontend antes de qualquer implementação.\n' +
            'Entregue:\n' +
            '- Threat model (STRIDE) com severidade (Critical/High/Medium/Low)\n' +
            '- Mitigações e prioridades\n' +
            '- Checklist OWASP Top 10\n' +
            '- Recomendações de autenticação (OAuth2/JWT), criptografia e manuseio de segredos\n' +
            '- Conformidade (LGPD/GDPR) quando aplicável\n' +
            'Aponte riscos de logging de dados sensíveis e dependências vulneráveis.'
        }
      },
      {
        id: 'data-scientist',
        name: 'Data Scientist',
        description: 'Analytics, machine learning, metrics, data quality and AI integration.',
        content: {
          role: 'Data Scientist',
          focus: ['data pipelines', 'analytics', 'ML', 'metrics', 'data quality', 'ethics'],
          prompt:
            'Você é o Especialista em Dados e IA sob comando do CTO.\n' +
            'Regra de credenciais: NUNCA solicite chaves de API ou secrets no chat. Se precisar, direcione para Settings → LLM.\n' +
            'Regra: antes de treinar modelos, defina:\n' +
            '- Pipeline de dados (coleta → limpeza → validação → features → treino → avaliação → deploy)\n' +
            '- Métricas de sucesso (ex.: Acurácia, F1, precisão/recall) e como medir\n' +
            '- Requisitos de integridade de dados e privacidade\n' +
            '- Riscos e ética em IA (viés, explicabilidade, segurança)\n' +
            'Depois de aprovado, entregue o plano de implementação e validação.'
        }
      },
      {
        id: 'code-review',
        name: 'Code Review',
        description: 'Objective review of changes — bugs, readability, edge cases.',
        content: {
          focus: ['quality', 'readability', 'bugs', 'edge cases', 'naming', 'complexity'],
          prompt:
            'You are doing a code review. For the code pasted:\n' +
            '1. Bugs and correctness issues (must fix).\n' +
            '2. Edge cases not handled (should fix).\n' +
            '3. Readability and naming (nice to have).\n' +
            '4. Overall assessment in one sentence.\n' +
            'Be direct. Do not praise code for being correct — that is the baseline.'
        }
      },
      {
        id: 'tests',
        name: 'Test Engineer',
        description: 'Creates and adjusts tests, validates critical scenarios.',
        content: {
          focus: ['unit', 'integration', 'e2e', 'regression', 'property-based'],
          prompt:
            'You are acting as Test Engineer.\n' +
            'For the behaviour described: list test cases (happy path, edge cases, error paths), then write the tests.\n' +
            'Prioritise: critical business logic, security boundaries, regression of past bugs.\n' +
            'Name tests so they read as specifications.'
        }
      },
      // ── Data & Productivity ──────────────────────────────────────────────────
      {
        id: 'excel-expert',
        name: 'Excel Expert',
        description: 'Formulas, pivot tables, VBA macros, data modelling and automation in Excel/Sheets.',
        content: {
          role: 'Excel & Spreadsheet Expert',
          focus: ['formulas', 'pivot tables', 'VBA', 'Power Query', 'data modelling', 'dashboards'],
          prompt:
            'You are acting as Excel Expert.\n' +
            'Ask for: the goal (analysis, report, automation), data structure, Excel version or Google Sheets.\n' +
            'Deliver: exact formulas with explanation, step-by-step instructions for pivot/charts, or VBA/Apps Script code if automation is needed.\n' +
            'Always explain what each formula does so the user can adapt it.'
        }
      },
      // ── Growth & Marketing ───────────────────────────────────────────────────
      {
        id: 'seo',
        name: 'SEO Specialist',
        description: 'Keyword research, on-page optimisation, technical SEO and content strategy.',
        content: {
          role: 'SEO Specialist',
          focus: ['keyword research', 'on-page SEO', 'technical SEO', 'content strategy', 'link building', 'Core Web Vitals'],
          prompt:
            'You are acting as SEO Specialist.\n' +
            'Ask for: website URL or topic, target audience, current traffic/rankings if known, main competitors.\n' +
            'Deliver: keyword opportunities (intent-mapped), on-page recommendations, technical issues checklist, and a content brief for the primary target keyword.\n' +
            'Ground recommendations in what is measurable and actionable within 30 days.'
        }
      },
      {
        id: 'marketing',
        name: 'Marketing Strategist',
        description: 'Positioning, messaging, campaigns, copy and growth strategy.',
        content: {
          role: 'Marketing Strategist',
          focus: ['positioning', 'messaging', 'copywriting', 'campaigns', 'funnels', 'growth'],
          prompt:
            'You are acting as Marketing Strategist.\n' +
            'Ask for: product, target persona, main differentiator, stage (awareness/consideration/conversion), channel and budget constraints.\n' +
            'Deliver: positioning statement, key messages per audience segment, campaign concept, and copy variants for the primary channel.\n' +
            'Always connect tactics to a measurable outcome (conversion, sign-up, revenue).'
        }
      },
      // ── Assistant ────────────────────────────────────────────────────────────
      {
        id: 'chat-assistant',
        name: 'Chat Assistant',
        description: 'Thoughtful general assistant. Searches the web when information may be outdated or unknown.',
        content: {
          role: 'General Assistant',
          focus: ['research', 'analysis', 'writing', 'problem-solving'],
          web_search: true,
          prompt:
            'You are a thoughtful general-purpose assistant.\n' +
            'Security rule: NEVER ask the user to paste API keys, tokens or secrets in chat. If credentials are needed, direct them to Settings → LLM (token: [[open_settings:llm_api_key]]).\n' +
            'IMPORTANT: When asked about current events, recent data, prices, persons, or anything that may have changed, say so clearly and search the web for up-to-date information before answering.\n' +
            'Structure your answers: lead with the direct answer, then supporting details, then sources if applicable.\n' +
            'If you are uncertain, say so. Do not confabulate facts — acknowledge the limit and offer to look it up.'
        }
      },
      // ── Meta ─────────────────────────────────────────────────────────────────
      {
        id: 'skill-creator',
        name: 'Skill Creator',
        description: 'Creates and edits skills safely, guiding the user step by step.',
        content: {
          purpose: 'Create/edit skills',
          inputs: ['goal', 'examples', 'constraints'],
          outputs: ['implementation', 'validation', 'test plan'],
          prompt:
            'You are Skill Creator. Guide the user to build a new skill:\n' +
            '1. Ask: what should this skill do? What inputs does it receive? What outputs should it produce? Any constraints or examples?\n' +
            '2. Draft the skill JSON (id, name, description, content with prompt and focus).\n' +
            '3. Review: does the prompt clearly define the role, ask for needed context, and specify the output format?\n' +
            '4. Enforce: the skill must never request API keys/tokens/secrets in chat; credentials are configured via Settings → LLM.\n' +
            '5. Suggest 2–3 test prompts to validate the skill before saving.'
        }
      }
    ];

    try {
      // v2: bump key to invalidate old default skills from previous versions
      const raw = localStorage.getItem('open_slap_skills_v2');
      const parsed = raw ? JSON.parse(raw) : null;
      if (Array.isArray(parsed) && parsed.length) {
        // Merge: keep user-created skills, ensure all defaults are present
        const defaultIds = new Set(defaults.map((d) => d.id));
        const userCustom = parsed.filter((s) => !defaultIds.has(s.id));
        setSkills([...defaults, ...userCustom]);
      } else {
        setSkills(defaults);
      }
    } catch {
      setSkills(defaults);
    }
  }, []);

  useEffect(() => {
    try {
      if (Array.isArray(skills) && skills.length) {
        localStorage.setItem('open_slap_skills_v2', JSON.stringify(skills));
      }
    } catch {}
  }, [skills]);

  useEffect(() => {
    if (centerView !== 'customize') {
      setCustomizeView('home');
      setSelectedSkillId('');
      setSkillDraft('');
      setSkillEditMode(false);
    }
  }, [centerView]);

  useEffect(() => {
    if (!streaming) {
      setLoadingTick(0);
      setStreamStatusText('');
      return;
    }

    const id = setInterval(() => {
      setLoadingTick((t) => (t + 1) % 1000000);
    }, 450);

    return () => clearInterval(id);
  }, [streaming]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const update = () => setIsMobile(window.innerWidth <= 900);
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  useEffect(() => {
    if (isMobile) {
      setMobileSidebarOpen(false);
    }
  }, [centerView, isMobile]);

  const fetchDoctorReport = async ({ silent = false } = {}) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    if (!silent) {
      setDoctorLoading(true);
      setDoctorError('');
    }
    try {
      const res = await fetch('/api/doctor', { headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error running diagnostics.');
      }
      setDoctorReport(json || null);
    } catch (e) {
      setDoctorError('Could not run diagnostics.');
      setDoctorReport(null);
    } finally {
      if (!silent) {
        setDoctorLoading(false);
      }
    }
  };

  const loadSettings = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return;
      }
      setSettingsLoading(true);
      setSettingsError('');
      setSystemProfileError('');
      setDoctorError('');
      setLlmApiKey('');
      setLlmApiKeyOpen(false);

      const llmRes = await fetch('/api/settings/llm', { headers });
      const llmJson = await llmRes.json();
      const llm = llmJson?.settings || {};
      const normalizedLlmBaseUrl = (llm.base_url || '').toString().trim().replace(/[`'"]/g, '').replace(/,+$/, '');
      const patchedGeminiBaseUrl = (llm.provider === 'gemini' && normalizedLlmBaseUrl.endsWith('/v1beta'))
        ? `${normalizedLlmBaseUrl.slice(0, -6)}v1`
        : normalizedLlmBaseUrl;
      setLlmMode(llm.mode || 'env');
      setLlmProvider(llm.provider || 'ollama');
      setLlmModel(llm.model || '');
      setLlmBaseUrl(patchedGeminiBaseUrl || '');
      setLlmHasApiKey(Boolean(llmJson?.has_api_key));
      setLlmApiKeySource((llmJson?.api_key_source || (llmJson?.has_api_key ? 'stored' : 'none')));
      setLlmHasStoredApiKey(Boolean(llmJson?.has_stored_api_key));
      setLlmHasEnvApiKey(Boolean(llmJson?.has_env_api_key));

      const soulRes = await fetch('/api/soul', { headers });
      const soulJson = await soulRes.json();
      setSoulData({
        name: soulJson?.data?.name || '',
        age_range: soulJson?.data?.age_range || '',
        gender: soulJson?.data?.gender || '',
        education: soulJson?.data?.education || '',
        interests: soulJson?.data?.interests || '',
        goals: soulJson?.data?.goals || '',
        learning_style: soulJson?.data?.learning_style || '',
        language: soulJson?.data?.language || 'pt-BR',
        audience: soulJson?.data?.audience || '',
        notes: soulJson?.data?.notes || ''
      });
      setSoulMarkdown(soulJson?.markdown || '');

      try {
        const sysRes = await fetch('/api/system_profile', { headers });
        const sysJson = await sysRes.json();
        setSystemProfileMarkdown(sysJson?.markdown || '');
        setSystemProfileUpdatedAt(sysJson?.updated_at || '');
        setSystemProfileEnabled(sysJson?.enabled !== false);
      } catch {
        setSystemProfileMarkdown('');
        setSystemProfileUpdatedAt('');
      }

      try {
        const secRes = await fetch('/api/settings/security', { headers });
        const secJson = await secRes.json().catch(() => ({}));
        if (secRes.ok) {
          setSecuritySettings(normalizeSecuritySettings(secJson?.settings || {}));
          setSecuritySettingsUpdatedAt(secJson?.updated_at || '');
        }
      } catch {}

      try {
        const acRes = await fetch('/api/automation_client', { headers });
        const acJson = await acRes.json().catch(() => ({}));
        if (acRes.ok) {
          setAutomationClientBaseUrl(acJson?.settings?.base_url || '');
          setAutomationClientApiKey('');
          setAutomationClientHasApiKey(Boolean(acJson?.has_api_key));
        }
      } catch {}

      await fetchDoctorReport({ silent: true });
    } catch (error) {
      setSettingsError(t('settings_load_error'));
    } finally {
      setSettingsLoading(false);
    }
  };

  const loadProviderStatus = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      setProviderStatusLoading(true);
      setProviderStatusError('');
      const res = await fetch('/api/providers', { headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error loading provider status.');
      }
      const raw = (json?.providers && typeof json.providers === 'object') ? json.providers : {};
      const list = Object.entries(raw).map(([id, p]) => ({
        id: String(id || ''),
        name: String(p?.name || id || ''),
        enabled: Boolean(p?.enabled),
        online: Boolean(p?.online),
        model: String(p?.model || ''),
        keys_count: Number(p?.keys_count) || 0
      }));
      setProviderStatusList(list);
    } catch (e) {
      setProviderStatusError(t('provider_status_load_error'));
      setProviderStatusList([]);
    } finally {
      setProviderStatusLoading(false);
    }
  };

  useEffect(() => {
    if (!user || !token) return;
    if (centerView !== 'settings') return;
    if (settingsTab !== 'llm') return;
    if (providerStatusLoading) return;
    if (providerStatusList?.length) return;
    loadProviderStatus();
  }, [user, token, centerView, settingsTab]);

  const getStoredLlmPrefs = () => {
    try {
      const raw = localStorage.getItem('open_slap_llm_prefs');
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object') return null;
      return parsed;
    } catch {
      return null;
    }
  };

  const setStoredLlmPrefs = (prefs) => {
    try {
      localStorage.setItem('open_slap_llm_prefs', JSON.stringify(prefs || {}));
    } catch {}
  };

  const removeLlmApiKey = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    setSettingsLoading(true);
    setSettingsError('');
    try {
      const res = await fetch('/api/settings/llm/api_key', { method: 'DELETE', headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error removing key.');
      }
      setLlmApiKey('');
      setLlmApiKeyOpen(false);
      setLlmHasApiKey(Boolean(json?.has_api_key));
      setLlmApiKeySource((json?.api_key_source || (json?.has_api_key ? 'stored' : 'none')));
      setLlmHasStoredApiKey(Boolean(json?.has_stored_api_key));
      setLlmHasEnvApiKey(Boolean(json?.has_env_api_key));
    } catch (e) {
      setSettingsError(t('llm_key_remove_error'));
    } finally {
      setSettingsLoading(false);
    }
  };

  const refreshSystemProfile = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    setSettingsLoading(true);
    setSystemProfileError('');
    try {
      const res = await fetch('/api/system_profile/refresh', { method: 'POST', headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error updating profile.');
      }
      setSystemProfileMarkdown(json?.markdown || '');
      setSystemProfileUpdatedAt(json?.updated_at || '');
    } catch (e) {
      setSystemProfileError('Could not update system profile.');
    } finally {
      setSettingsLoading(false);
    }
  };

  const deleteSystemProfile = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    setSettingsLoading(true);
    setSystemProfileError('');
    try {
      const res = await fetch('/api/system_profile', { method: 'DELETE', headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error removing profile.');
      }
      setSystemProfileMarkdown('');
      setSystemProfileUpdatedAt('');
    } catch (e) {
      setSystemProfileError('Could not remove system profile.');
    } finally {
      setSettingsLoading(false);
    }
  };

  const saveLlmSettings = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return;
      }
      setSettingsLoading(true);
      setSettingsError('');

      const rawKey = llmApiKey.trim() ? llmApiKey.trim() : '';
      const inferredProvider = rawKey.startsWith('AIza')
        ? 'gemini'
        : rawKey.startsWith('gsk_')
          ? 'groq'
          : rawKey.startsWith('sk-')
            ? 'openai'
            : '';

      const providerToSave = inferredProvider || llmProvider;
      const normalizedBaseUrl = (llmBaseUrl || '').trim();
      const cleanedBaseUrl = normalizedBaseUrl.replace(/[`'"]/g, '').replace(/,+$/, '');
      const baseUrlToSave = (llmMode === 'api' && providerToSave === 'gemini')
        ? (
          !cleanedBaseUrl
            ? 'https://generativelanguage.googleapis.com/v1'
            : cleanedBaseUrl.endsWith('/v1beta')
              ? `${cleanedBaseUrl.slice(0, -6)}v1`
              : cleanedBaseUrl
        )
        : (cleanedBaseUrl || null);

      const payload = {
        mode: llmMode,
        provider: providerToSave,
        model: llmModel || null,
        base_url: baseUrlToSave,
        api_key: rawKey ? rawKey : null
      };

      const res = await fetch('/api/settings/llm', {
        method: 'PUT',
        headers,
        body: JSON.stringify(payload)
      });

      const json = await res.json();
      if (!res.ok) {
        throw new Error(json?.detail || 'Error saving LLM settings.');
      }

      if (payload.api_key) {
        setLlmApiKey('');
        setLlmApiKeyOpen(false);
      }
      setLlmHasApiKey(Boolean(json?.has_api_key));
      setLlmApiKeySource((json?.api_key_source || (json?.has_api_key ? 'stored' : 'none')));
      setLlmHasStoredApiKey(Boolean(json?.has_stored_api_key));
      setLlmHasEnvApiKey(Boolean(json?.has_env_api_key));
      setStoredLlmPrefs({
        mode: payload.mode,
        provider: payload.provider,
        model: payload.model,
        base_url: payload.base_url
      });
      setLlmProvider(payload.provider);
      setLlmBaseUrl(payload.base_url || '');
    } catch (error) {
      setSettingsError(t('llm_settings_save_error'));
    } finally {
      setSettingsLoading(false);
    }
  };

  const normalizeSecuritySettings = (raw) => {
    const base = {
      sandbox: false,
      allow_os_commands: true,
      allow_file_write: true,
      allow_web_retrieval: true,
      allow_connectors: true,
      allow_system_profile: true
    };
    const out = { ...base };
    if (raw && typeof raw === 'object') {
      Object.keys(base).forEach((k) => {
        if (raw[k] === undefined || raw[k] === null) return;
        out[k] = Boolean(raw[k]);
      });
    }
    if (out.sandbox) {
      out.allow_os_commands = false;
      out.allow_file_write = false;
      out.allow_web_retrieval = false;
      out.allow_connectors = false;
    }
    return out;
  };

  const saveSecuritySettings = async (override) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      setSettingsLoading(true);
      setSettingsError('');
      const toSave = normalizeSecuritySettings(override || securitySettings);
      const res = await fetch('/api/settings/security', {
        method: 'PUT',
        headers,
        body: JSON.stringify(toSave)
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error saving security settings.');
      }
      setSecuritySettings(normalizeSecuritySettings(json?.settings || toSave));
      setSecuritySettingsUpdatedAt(json?.updated_at || '');
    } catch {
      setSettingsError(t('security_settings_save_error'));
    } finally {
      setSettingsLoading(false);
    }
  };

  const applySecuritySettingChange = (patch, { needsConfirm }) => {
    const next = normalizeSecuritySettings({ ...securitySettings, ...(patch || {}) });
    if (needsConfirm) {
      setGenericModal({
        title: t('agent_security'),
        body: `${t('security_caps_warning')}\n\n${JSON.stringify(next, null, 2)}`,
        onConfirm: () => {
          setSecuritySettings(next);
          saveSecuritySettings(next);
        }
      });
      return;
    }
    setSecuritySettings(next);
    saveSecuritySettings(next);
  };

  const saveAutomationClientSettings = async (override) => {
    const next = override || {
      base_url: automationClientBaseUrl,
      api_key: automationClientApiKey
    };
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      setSettingsLoading(true);
      setSettingsError('');
      const payload = {
        base_url: String(next.base_url || '').trim(),
        api_key: String(next.api_key || '').trim() || null
      };
      const res = await fetch('/api/automation_client', {
        method: 'PUT',
        headers,
        body: JSON.stringify(payload)
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error saving automation client.');
      }
      setAutomationClientBaseUrl(json?.settings?.base_url || payload.base_url || '');
      setAutomationClientApiKey('');
      setAutomationClientHasApiKey(Boolean(json?.has_api_key));
    } catch {
      setSettingsError(t('automation_client_save_error'));
    } finally {
      setSettingsLoading(false);
    }
  };

  const deleteAutomationClientSettings = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      setSettingsLoading(true);
      setSettingsError('');
      const res = await fetch('/api/automation_client', { method: 'DELETE', headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error deleting automation client.');
      }
      setAutomationClientApiKey('');
      setAutomationClientHasApiKey(Boolean(json?.has_api_key));
    } catch {
      setSettingsError(t('automation_client_delete_error'));
    } finally {
      setSettingsLoading(false);
    }
  };

  const testAutomationClientSettings = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      setSettingsLoading(true);
      setSettingsError('');
      const res = await fetch('/api/automation_client/test', { method: 'POST', headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error testing automation client.');
      }
      setGenericModal({
        title: t('automation_client_external'),
        body: `ok: ${Boolean(json?.ok)}\nstatus: ${json?.status ?? '—'}`
      });
    } catch {
      setSettingsError(t('automation_client_test_error'));
    } finally {
      setSettingsLoading(false);
    }
  };

  useEffect(() => {
    if (centerView !== 'settings') return;
    if (settingsLoading) return;
    const action = pendingSettingsActionRef.current;
    if (!action) return;
    pendingSettingsActionRef.current = null;
    if (action === 'llm_api_key') {
      setSettingsTab('llm');
      setLlmMode('api');
      setLlmApiKeyOpen(true);
      setTimeout(() => {
        if (llmApiKeyInputRef.current) {
          try {
            llmApiKeyInputRef.current.focus();
          } catch {}
        }
      }, 50);
    }
  }, [centerView, settingsLoading]);

  const saveSoul = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return;
      }
      setSettingsLoading(true);
      setSettingsError('');

      const res = await fetch('/api/soul', {
        method: 'PUT',
        headers,
        body: JSON.stringify({ data: soulData })
      });
      const json = await res.json();
      if (!res.ok) {
        throw new Error(json?.detail || 'Error saving SOUL.');
      }
      setSoulMarkdown(json?.markdown || '');
    } catch (error) {
      setSettingsError(t('soul_save_error'));
    } finally {
      setSettingsLoading(false);
    }
  };

  const appendSoulUpdate = async () => {
    const content = soulUpdate.trim();
    if (!content) return;
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return;
      }
      setSettingsLoading(true);
      setSettingsError('');
      const res = await fetch('/api/soul/events', {
        method: 'POST',
        headers,
        body: JSON.stringify({ content, source: 'user' })
      });
      const json = await res.json();
      if (!res.ok) {
        throw new Error(json?.detail || 'Error updating SOUL.');
      }
      setSoulMarkdown(json?.markdown || '');
      setSoulUpdate('');
    } catch (error) {
      setSettingsError(t('soul_update_error'));
    } finally {
      setSettingsLoading(false);
    }
  };

  useEffect(() => {
    if (centerView === 'settings' && user && token) {
      loadSettings();
    }
  }, [centerView, user, token]);

  useEffect(() => {
    if (user && token && !hasDoctorBootedRef.current) {
      hasDoctorBootedRef.current = true;
      fetchDoctorReport({ silent: true });
    }
  }, [user, token]);

  // Carregar conversas
  useEffect(() => {
    if (user && token) {
      loadConversations();
      loadTasks();
      loadSkills();
      loadConnectors();
      loadProjects();
      if (!hasLangLoadedRef.current) {
        hasLangLoadedRef.current = true;
        loadLanguageSettings();
      }
      // Onboarding check
      if (!onboardingChecked) {
        setOnboardingChecked(true);
        fetch('/api/onboarding/status', { headers: getAuthHeaders() })
          .then(r => r.json())
          .then(d => { if (!d.completed) setShowOnboarding(true); })
          .catch(() => {});
      }
    }
  }, [user, token]);

  useEffect(() => {
    const q = conversationSearch.trim();
    if (!user || !token) return;
    if (!q) {
      setConversationSearchResults([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const headers = getAuthHeaders();
        const res = await fetch(`/api/search/messages?q=${encodeURIComponent(q)}&kind=conversation&limit=50`, { headers });
        const json = await res.json().catch(() => ({}));
        setConversationSearchResults(Array.isArray(json?.results) ? json.results : []);
      } catch {
        setConversationSearchResults([]);
      }
    }, 250);
    return () => clearTimeout(t);
  }, [conversationSearch, user, token]);

  useEffect(() => {
    const q = tasksSearch.trim();
    if (!user || !token) return;
    if (!q) {
      setTasksSearchResults([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const headers = getAuthHeaders();
        const res = await fetch(`/api/search/messages?q=${encodeURIComponent(q)}&kind=task&limit=50`, { headers });
        const json = await res.json().catch(() => ({}));
        setTasksSearchResults(Array.isArray(json?.results) ? json.results : []);
      } catch {
        setTasksSearchResults([]);
      }
    }, 250);
    return () => clearTimeout(t);
  }, [tasksSearch, user, token]);

  useEffect(() => {
    if (!user || !token) return;
    if (centerView !== 'tasks') return;
    loadGlobalTodos();
  }, [centerView, user, token]);

  // Conectar WebSocket
  useEffect(() => {
    if (user && token && !wsRef.current) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [user, token]);

  const loadConversations = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return;
      }
      const response = await fetch('/api/conversations?kind=conversation&source=user', { headers });
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const scheduleListsRefresh = () => {
    if (listsRefreshTimerRef.current) return;
    listsRefreshTimerRef.current = setTimeout(() => {
      listsRefreshTimerRef.current = null;
      loadConversations().catch(() => {});
      loadTasks().catch(() => {});
      loadGlobalTodos().catch(() => {});
    }, 700);
  };

  const loadTasks = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return;
      }
      const response = await fetch('/api/conversations?kind=task', { headers });
      const data = await response.json();
      setTasks(data.conversations || []);
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  };

  const openRename = (kind, item) => {
    const title = String(item?.title || '').trim();
    setRenameDraft(title);
    setRenameModal({
      kind,
      id: item?.id,
      title
    });
  };

  const submitRename = async () => {
    const kind = renameModal?.kind;
    const id = renameModal?.id;
    const nextTitle = String(renameDraft || '').trim();
    if (!kind || !id || !nextTitle) return;
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      headers['Content-Type'] = 'application/json';
      const url =
        kind === 'task'
          ? `/api/tasks/${encodeURIComponent(id)}/title`
          : `/api/conversations/${encodeURIComponent(id)}/title`;
      const res = await fetch(url, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ title: nextTitle })
      });
      if (!res.ok) {
        setGenericModal({ title: 'Erro', body: 'Não foi possível renomear. Tente novamente.' });
        return;
      }
      if (kind === 'task') {
        setTasks((prev) => (prev || []).map((t) => (String(t.id) === String(id) ? { ...t, title: nextTitle } : t)));
        setGlobalTodos((prev) =>
          (prev || []).map((g) => (String(g.conversation_id) === String(id) ? { ...g, task_title: nextTitle } : g))
        );
      } else {
        setConversations((prev) => (prev || []).map((c) => (String(c.id) === String(id) ? { ...c, title: nextTitle } : c)));
      }
      setRenameModal(null);
    } catch (e) {
      console.error('Error renaming:', e);
      setGenericModal({ title: 'Erro', body: 'Não foi possível renomear. Verifique sua conexão.' });
    }
  };

  const saveSkillsToBackend = async (nextSkills, { silent = false } = {}) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      headers['Content-Type'] = 'application/json';
      const res = await fetch('/api/skills', {
        method: 'PUT',
        headers,
        body: JSON.stringify({ skills: Array.isArray(nextSkills) ? nextSkills : [] })
      });
      const ok = !!res.ok;
      if (!silent) {
        if (skillsSaveStatusTimeoutRef.current) {
          clearTimeout(skillsSaveStatusTimeoutRef.current);
          skillsSaveStatusTimeoutRef.current = null;
        }
        if (ok) {
          setSkillsSaveStatus(t('saved'));
          skillsSaveStatusTimeoutRef.current = setTimeout(() => {
            setSkillsSaveStatus('');
            skillsSaveStatusTimeoutRef.current = null;
          }, 2200);
        } else {
          setSkillsSaveStatus(t('failed_to_save'));
          skillsSaveStatusTimeoutRef.current = setTimeout(() => {
            setSkillsSaveStatus('');
            skillsSaveStatusTimeoutRef.current = null;
          }, 3500);
          setGenericModal({
            title: t('save_error_title'),
            body: t('save_error_body')
          });
        }
      }
      return ok;
    } catch {
      if (!silent) {
        if (skillsSaveStatusTimeoutRef.current) {
          clearTimeout(skillsSaveStatusTimeoutRef.current);
          skillsSaveStatusTimeoutRef.current = null;
        }
        setSkillsSaveStatus(t('failed_to_save'));
        skillsSaveStatusTimeoutRef.current = setTimeout(() => {
          setSkillsSaveStatus('');
          skillsSaveStatusTimeoutRef.current = null;
        }, 3500);
        setGenericModal({
          title: t('save_error_title'),
          body: t('save_error_body')
        });
      }
      return false;
    }
  };

  const loadSkills = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      const res = await fetch('/api/skills', { headers });
      const json = await res.json().catch(() => ({}));
      const list = Array.isArray(json?.skills) ? json.skills : [];
      if (list.length) {
        // Merge: ensure built-in skill IDs are always present.
        // User-created skills (not in builtInIds) are kept on top.
        const builtInIds = new Set([
          'cto','project-manager','systems-architect',
          'backend-dev','frontend-dev','devops','security',
          'code-review','tests','excel-expert','seo','marketing',
          'chat-assistant','skill-creator'
        ]);
        const serverIds = new Set(list.map((s) => s.id));
        const currentDefaults = (skills || []).filter((s) => builtInIds.has(s.id));
        const missing = currentDefaults.filter((s) => !serverIds.has(s.id));
        const merged = [...list, ...missing];
        setSkills(merged);
        if (missing.length) {
          // Persist the merged set so next load is clean
          await saveSkillsToBackend(merged, { silent: true });
        }
        return;
      }
      if (Array.isArray(skills) && skills.length) {
        await saveSkillsToBackend(skills, { silent: true });
        return;
      }
    } catch {}
  };

  const loadConnectors = async ({ silent = true } = {}) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      if (!silent) setConnectorsLoading(true);
      const res = await fetch('/api/connectors', { headers });
      const json = await res.json().catch(() => ({}));
      const next = json?.connectors && typeof json.connectors === 'object' ? json.connectors : null;
      if (next) {
        setConnectors((prev) => ({
          ...(prev || {}),
          ...next
        }));
      }
    } catch {
    } finally {
      if (!silent) setConnectorsLoading(false);
    }
  };

  const loadLanguageSettings = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      const res = await fetch('/api/settings/language', { headers });
      const json = await res.json().catch(() => ({}));
      const nextLang = String(json?.lang || '').trim().toLowerCase();
      if (nextLang && ['pt', 'en', 'es', 'ar', 'zh'].includes(nextLang)) {
        setLang(nextLang);
      }
    } catch {}
  };

  const saveLanguageSettings = async (nextLang) => {
    const value = String(nextLang || '').trim().toLowerCase();
    if (!value || !['pt', 'en', 'es', 'ar', 'zh'].includes(value)) return;
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      headers['Content-Type'] = 'application/json';
      const res = await fetch('/api/settings/language', {
        method: 'PUT',
        headers,
        body: JSON.stringify({ lang: value })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || 'Failed to save language.');
    } catch (e) {
      setGenericModal({
        title: t('error'),
        body: e?.message || 'Failed to save language.'
      });
    }
  };

  const openConnectorModal = (connectorKey) => {
    const key = String(connectorKey || '').trim();
    if (!key) return;
    const labelMap = {
      github: 'GitHub',
      google_drive: 'Google Drive',
      google_calendar: 'Google Calendar',
      gmail: 'Gmail',
      telegram: 'Telegram',
      tera: 'Tera'
    };
    const helpMap = {
      github: t('github_token_help'),
      google_drive: t('google_token_help'),
      google_calendar: t('google_token_help'),
      gmail: t('google_token_help'),
      telegram: t('telegram_token_help'),
      tera: ''
    };
    setConnectorModal({
      key,
      title: `${t('connect')} — ${labelMap[key] || key}`,
      help: helpMap[key] || '',
      token: ''
    });
  };

  const createTelegramLinkCode = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      const res = await fetch('/api/connectors/telegram/link-code', {
        method: 'POST',
        headers
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || 'Failed to generate link code.');
      const code = String(json?.code || '').trim();
      const expiresAtRaw = json?.expires_at;
      let expiresText = '';
      try {
        const d = new Date(expiresAtRaw);
        expiresText = Number.isFinite(d.getTime()) ? d.toLocaleString() : String(expiresAtRaw || '').trim();
      } catch {
        expiresText = String(expiresAtRaw || '').trim();
      }
      setGenericModal({
        title: t('telegram_link_code_title'),
        body: [
          t('telegram_link_code_body_1'),
          t('telegram_link_code_body_2'),
          t('telegram_link_code_body_3'),
          '',
          `${t('telegram_link_code_label')}: ${code || '-'}`,
          expiresText ? `${t('telegram_link_code_expires')}: ${expiresText}` : ''
        ].filter(Boolean).join('\n')
      });
    } catch (e) {
      setGenericModal({
        title: t('error'),
        body: e?.message || 'Failed to generate link code.'
      });
    }
  };

  const saveConnector = async (connectorKey, tokenValue) => {
    const key = String(connectorKey || '').trim();
    const tokenText = String(tokenValue || '').trim();
    if (!key) return false;
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      headers['Content-Type'] = 'application/json';
      const res = await fetch(`/api/connectors/${encodeURIComponent(key)}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ token: tokenText })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Failed to connect.');
      }
      await loadConnectors({ silent: true });
      return true;
    } catch (e) {
      setGenericModal({
        title: t('error'),
        body: e?.message || 'Failed to connect.'
      });
      return false;
    }
  };

  const disconnectConnector = async (connectorKey) => {
    const key = String(connectorKey || '').trim();
    if (!key) return;
    setGenericModal({
      title: `${t('disconnect')} — ${key}`,
      body: t('remove_credential_question'),
      onConfirm: async () => {
        try {
          const headers = getAuthHeaders();
          if (!headers.Authorization) return;
          const res = await fetch(`/api/connectors/${encodeURIComponent(key)}`, {
            method: 'DELETE',
            headers
          });
          if (!res.ok) return;
          await loadConnectors({ silent: true });
        } catch {}
      }
    });
  };

  const testConnector = async (connectorKey) => {
    const key = String(connectorKey || '').trim();
    if (!key) return;
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      const res = await fetch(`/api/connectors/${encodeURIComponent(key)}/test`, {
        method: 'POST',
        headers
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Failed to test.');
      }
      setGenericModal({
        title: t('success'),
        body: t('connector_validated')
      });
    } catch (e) {
      setGenericModal({
        title: t('error'),
        body: e?.message || 'Failed to test.'
      });
    }
  };

  const loadProjects = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      const res = await fetch('/api/projects', { headers });
      const json = await res.json().catch(() => ({}));
      setProjects(Array.isArray(json?.projects) ? json.projects : []);
    } catch {}
  };

  const createProject = async (name) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return null;
      headers['Content-Type'] = 'application/json';
      const res = await fetch('/api/projects', {
        method: 'POST', headers, body: JSON.stringify({ name })
      });
      const json = await res.json().catch(() => ({}));
      if (res.ok) { await loadProjects(); return json.project_id; }
    } catch {}
    return null;
  };

  const updateProjectContext = async (projectId, contextMd) => {
    const pid = Number(projectId || 0);
    if (!pid) return false;
    try {
      setProjectContextSaving(true);
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      headers['Content-Type'] = 'application/json';
      const res = await fetch(`/api/projects/${pid}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ context_md: String(contextMd || '') })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Failed to save project context.');
      }
      await loadProjects();
      return true;
    } catch (e) {
      setGenericModal({
        title: t('error'),
        body: e?.message || 'Failed to save project context.'
      });
      return false;
    } finally {
      setProjectContextSaving(false);
    }
  };

  const assignConversationProject = async (convId, projectId) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      headers['Content-Type'] = 'application/json';
      await fetch(`/api/conversations/${convId}/project`, {
        method: 'PUT', headers, body: JSON.stringify({ project_id: projectId || null })
      });
    } catch {}
  };

  useEffect(() => {
    const pid = Number(activeProjectId || 0);
    if (!pid) return;
    const proj = projects.find((p) => Number(p?.id || 0) === pid);
    if (!proj) return;
    setProjectContextDraft(String(proj?.context_md || ''));
  }, [activeProjectId, projects]);

  const postFeedback = async (messageId, rating) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      headers['Content-Type'] = 'application/json';
      await fetch('/api/feedback', {
        method: 'POST', headers, body: JSON.stringify({ message_id: messageId, rating })
      });
      setMessageFeedback(prev => ({ ...prev, [messageId]: rating }));
    } catch {}
  };

  const approvePlan = async (convId, tasks) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        setGenericModal({ title: t('error'), body: lang === 'pt' ? 'Não autenticado.' : 'Not authenticated.' });
        return false;
      }
      headers['Content-Type'] = 'application/json';
      const res = await fetch('/api/plan/approve', {
        method: 'POST', headers,
        body: JSON.stringify({ conversation_id: convId, tasks })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        setGenericModal({
          title: t('error'),
          body: String(json?.detail || (lang === 'pt' ? 'Não foi possível aprovar o plano.' : 'Could not approve the plan.'))
        });
        return false;
      }
      setActivePlanConvId(convId);
      const tr = await fetch(`/api/plan/tasks/${convId}`, { headers: getAuthHeaders() });
      const td = await tr.json().catch(() => ({}));
      setPlanTasks(Array.isArray(td?.tasks) ? td.tasks : []);
      return true;
    } catch {}
    setGenericModal({
      title: t('error'),
      body: lang === 'pt' ? 'Falha ao aprovar o plano.' : 'Failed to approve plan.'
    });
    return false;
  };

  const loadPlanTasks = async (convId) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      const res = await fetch(`/api/plan/tasks/${convId}`, { headers });
      const json = await res.json().catch(() => ({}));
      const tasks = Array.isArray(json?.tasks) ? json.tasks : [];
      setPlanTasks(tasks);
      if (tasks.length) setActivePlanConvId(convId);
      return tasks;
    } catch {}
    return [];
  };

  const updatePlanTaskStatus = async (taskId, status) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      headers['Content-Type'] = 'application/json';
      await fetch(`/api/plan/tasks/${taskId}/status`, {
        method: 'PUT', headers, body: JSON.stringify({ status })
      });
      setPlanTasks(prev => prev.map(t => t.id === taskId ? { ...t, status } : t));
    } catch {}
  };

  const startOrchestration = async (convId) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      headers['Content-Type'] = 'application/json';
      const res = await fetch(`/api/plan/orchestrate/${convId}`, {
        method: 'POST', headers
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        setGenericModal({ title: 'Orchestration error', body: json?.detail || 'Could not start.' });
        return;
      }
      const runId = json.run_id;
      setOrchRunId(runId);
      setOrchStatus('running');
      setOrchLog([]);
      // Start polling
      if (orchPollRef.current) clearInterval(orchPollRef.current);
      orchPollRef.current = setInterval(async () => {
        try {
          const pr = await fetch(`/api/plan/orchestrate/${runId}/status`, { headers: getAuthHeaders() });
          const pd = await pr.json().catch(() => ({}));
          setOrchLog(pd.log || []);
          setOrchStatus(pd.status || 'running');
          if (pd.status === 'completed' || pd.status === 'failed') {
            clearInterval(orchPollRef.current);
            orchPollRef.current = null;
            // Reload plan tasks to reflect done statuses
            if (activePlanConvId) loadPlanTasks(activePlanConvId);
            await loadTasks();
          }
        } catch {}
      }, 2000);
    } catch {}
  };

  // Cleanup polling on unmount
  React.useEffect(() => () => {
    if (orchPollRef.current) clearInterval(orchPollRef.current);
  }, []);

  const loadGlobalTodos = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      const res = await fetch('/api/tasks/todos', { headers });
      const json = await res.json().catch(() => ({}));
      setGlobalTodos(Array.isArray(json?.todos) ? json.todos : []);
    } catch {
      setGlobalTodos([]);
    }
  };

  const loadTaskTodos = async (taskId) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      setTaskTodosLoading(true);
      const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/todos`, { headers });
      const json = await res.json().catch(() => ({}));
      setTaskTodos(Array.isArray(json?.todos) ? json.todos : []);
    } catch {
      setTaskTodos([]);
    } finally {
      setTaskTodosLoading(false);
    }
  };

  const addTaskTodo = async (taskId, text) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      const clean = String(text || '').trim();
      if (!clean) return false;
      headers['Content-Type'] = 'application/json';
      const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/todos`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ text: clean })
      });
      if (!res.ok) return false;
      await loadTaskTodos(taskId);
      await loadGlobalTodos();
      await loadTasks();
      return true;
    } catch {
      return false;
    }
  };

  const markTaskTodoDone = async (taskId, todoId) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      headers['Content-Type'] = 'application/json';
      const res = await fetch(`/api/tasks/todos/${encodeURIComponent(todoId)}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ status: 'done' })
      });
      if (!res.ok) return false;
      await loadTaskTodos(taskId);
      await loadGlobalTodos();
      await loadTasks();
      return true;
    } catch {
      return false;
    }
  };

  const markTodoDone = async (todoId) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      headers['Content-Type'] = 'application/json';
      const res = await fetch(`/api/tasks/todos/${encodeURIComponent(todoId)}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ status: 'done' })
      });
      if (!res.ok) return;
      setGlobalTodos((prev) => (prev || []).filter((t) => String(t.id) !== String(todoId)));
    } catch {}
  };

  const truncatePath = (value, maxLen = 44) => {
    const s = String(value || '');
    if (!s) return '';
    if (s.length <= maxLen) return s;
    const head = Math.max(12, Math.floor(maxLen * 0.55));
    const tail = Math.max(10, maxLen - head - 3);
    return `${s.slice(0, head)}...${s.slice(-tail)}`;
  };

  const getTodoArtifacts = (todo) => {
    const meta = todo?.artifact_meta;
    if (Array.isArray(meta)) return meta;
    if (meta && typeof meta === 'object' && Array.isArray(meta.artifacts)) return meta.artifacts;
    return [];
  };

  const buildTodoTree = (todos) => {
    const list = Array.isArray(todos) ? todos : [];
    const map = new Map();
    for (const td of list) {
      if (!td || td.id == null) continue;
      map.set(String(td.id), { ...td, children: [] });
    }
    const roots = [];
    for (const node of map.values()) {
      const pidRaw = node.parent_todo_id;
      const pid = pidRaw == null ? null : String(pidRaw);
      if (pid && map.has(pid)) {
        map.get(pid).children.push(node);
      } else {
        roots.push(node);
      }
    }
    const sortByCreatedAtDesc = (a, b) => {
      const ta = (a?.created_at ? Date.parse(a.created_at) : 0) || 0;
      const tb = (b?.created_at ? Date.parse(b.created_at) : 0) || 0;
      return tb - ta;
    };
    const sortRec = (nodes) => {
      nodes.sort(sortByCreatedAtDesc);
      for (const n of nodes) {
        if (Array.isArray(n.children) && n.children.length) sortRec(n.children);
      }
    };
    sortRec(roots);
    return roots;
  };

  const formatRuntimeLlmLabel = (provider, model, mode) => {
    const p = (provider || '').toString().trim().toLowerCase();
    const m = (model || '').toString().trim();
    const mm = (mode || '').toString().trim().toLowerCase();

    const providerName = p === 'gemini'
      ? 'Gemini'
      : p === 'openai'
        ? 'OpenAI'
        : p === 'groq'
          ? 'Groq'
          : p === 'ollama'
            ? 'Local'
            : provider || '';

    if (p === 'ollama' || mm === 'local') {
      return m ? `${m} LLM Local` : 'LLM Local';
    }

    if (mm === 'env') {
      return 'Padrão do servidor';
    }

    if (providerName && m) {
      return `${providerName} — ${m}`;
    }

    if (providerName) {
      return providerName;
    }

    return '';
  };

  const fetchRuntimeLlmLabel = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      const res = await fetch('/api/settings/llm', { headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) return;
      const s = json?.settings || {};
      const label = formatRuntimeLlmLabel(s.provider, s.model, s.mode);
      setRuntimeLlmLabel(label);
    } catch {}
  };

  const flushChunkBuffer = () => {
    const buffered = chunkBufferRef.current;
    if (!buffered) return;
    chunkBufferRef.current = '';
    setMessages(prev => {
      const newMessages = [...prev];
      const lastMessage = newMessages[newMessages.length - 1];
      if (lastMessage && lastMessage.role === 'assistant' && lastMessage.streaming) {
        newMessages[newMessages.length - 1] = {
          ...lastMessage,
          content: `${lastMessage.content}${buffered}`
        };
        return newMessages;
      }
      newMessages.push({
        role: 'assistant',
        content: buffered,
        streaming: true,
        id: `chunk-${Date.now()}-${Math.random().toString(16).slice(2)}`
      });
      return newMessages;
    });
  };

  const scheduleChunkFlush = () => {
    if (chunkFlushRef.current) return;
    const raf = typeof window !== 'undefined' ? window.requestAnimationFrame : null;
    if (raf) {
      chunkFlushRef.current = raf(() => {
        chunkFlushRef.current = null;
        flushChunkBuffer();
      });
      return;
    }
    chunkFlushRef.current = setTimeout(() => {
      chunkFlushRef.current = null;
      flushChunkBuffer();
    }, 16);
  };

  const connectWebSocket = () => {
    const tokenValue = token || localStorage.getItem('agentic_token');
    if (!tokenValue) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${wsProtocol}://${window.location.host}/ws/${sessionId.current}?token=${tokenValue}`);
    wsRef.current = ws;

    ws.onopen = () => {
      if (wsRef.current !== ws) return;
      setConnected(true);
      console.log('WebSocket conectado');
      fetchRuntimeLlmLabel();

      if (pendingAutoSendRef.current) {
        const pending = pendingAutoSendRef.current;
        pendingAutoSendRef.current = null;

        const pendingContent =
          typeof pending === 'string'
            ? pending
            : String(pending?.content || '');
        const internalPrompt =
          typeof pending === 'string'
            ? ''
            : String(pending?.internalPrompt || '');
        const forceExpertOverride =
          typeof pending === 'string'
            ? ''
            : String(pending?.forceExpertId || '');

        const now = Date.now();
        const userMessage = {
          role: 'user',
          content: pendingContent,
          id: `${now}-${Math.random().toString(16).slice(2)}`
        };

        setStreaming(true);
        setMessages(prev => [
          ...prev,
          userMessage,
          {
            role: 'assistant',
            content: '',
            streaming: true,
            id: `${now + 1}-${Math.random().toString(16).slice(2)}`
          }
        ]);
        setInput('');

        const activeSkill = (skills || []).find((s) => s.id === selectedSkillId) || null;
        ws.send(JSON.stringify({
          type: 'chat',
          content: pendingContent,
          internal_prompt: internalPrompt || null,
          skill_id: activeSkill?.id || null,
          skill_web_search: activeSkill?.content?.web_search === true,
          force_expert_id: (forceExpertOverride || forceExpertId) || null,
          debug_router: Boolean(showRoutingDebug),
        }));
      }
    };

    ws.onmessage = (event) => {
      if (wsRef.current !== ws) return;
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'history') {
          if (hasHttpHydratedRef.current) {
            return;
          }
          const msg = data.message || {};
          setMessages(prev => [
            ...prev,
            {
              ...msg,
              id: msg.id ?? `history-${Date.now()}-${Math.random().toString(16).slice(2)}`
            }
          ]);
        } else if (data.type === 'chunk') {
          chunkBufferRef.current = `${chunkBufferRef.current}${String(data.content || '')}`;
          scheduleChunkFlush();
        } else if (data.type === 'done') {
          const selectionReason = String(data.selection_reason || '').trim();
          const matchedKeywords = Array.isArray(data.matched_keywords) ? data.matched_keywords : [];
          if (selectionReason) setLastExpertReason(selectionReason);
          if (matchedKeywords?.length) setLastExpertKeywords(matchedKeywords || []);
          const _doneMessageId = data.message_id || null;
          flushChunkBuffer();
          let actionsToRun = [];
          let assistantPartsToSchedule = [];
          let anchorLocalId = null;
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage && lastMessage.role === 'assistant') {
              anchorLocalId = lastMessage.id || null;
              const extracted = parseAssistantDirectivesFromText(lastMessage.content);
              actionsToRun = extracted.actions || [];
              assistantPartsToSchedule = (extracted.parts || []).slice(1);
              newMessages[newMessages.length - 1] = {
                ...lastMessage,
                content: extracted.cleaned,
                streaming: false,
                expert: data.expert,
                expert_reason: selectionReason,
                expert_keywords: matchedKeywords,
                provider: data.provider,
                model: data.model,
                message_id: _doneMessageId,
              };
            }
            return newMessages;
          });
          if (data.plan_detected && data.plan_tasks?.length && currentConversation) {
            const tasks = Array.isArray(data.plan_tasks) ? data.plan_tasks : [];
            if (tasks.length) setShowExecutionPanel(true);
            setActivePlanMessageId(_doneMessageId || null);
            setActivePlanLocalMsgId(anchorLocalId || null);
            pendingPlanTasksRef.current = {
              ...(pendingPlanTasksRef.current || {}),
              [String(currentConversation)]: tasks
            };
          }
          if (actionsToRun.length) {
            runUiActions(actionsToRun);
          }
          if (assistantPartsToSchedule.length) {
            for (const p of assistantPartsToSchedule) {
              const delay = Number(p?.delayMs) || 0;
              const content = String(p?.text || '').trim();
              if (!content) continue;
              setTimeout(() => {
                setMessages(prev => [
                  ...prev,
                  {
                    role: 'assistant',
                    content,
                    streaming: false,
                    id: `split-${Date.now()}-${Math.random().toString(16).slice(2)}`
                  }
                ]);
              }, Math.max(0, delay));
            }
          }
          if (data.provider || data.model) {
            const label = formatRuntimeLlmLabel(data.provider, data.model, llmMode);
            if (label) {
              setRuntimeLlmLabel(label);
            }
          }
          setStreaming(false);
          setStreamStatusText('');
          scheduleListsRefresh();
        } else if (data.type === 'status') {
          const txt = String(data.content || '').trim();
          if (txt) setStreamStatusText(txt);
          if (txt && currentConversation && currentKind === 'task' && txt.toLowerCase().includes('todo')) {
            loadTaskTodos(currentConversation);
            loadGlobalTodos();
            loadTasks();
          }
          scheduleListsRefresh();
        } else if (data.type === 'software_operator') {
          const executionId = String(data.execution_id || '').trim() || `cli-${Date.now()}`;
          const status = String(data.status || '').trim().toLowerCase() || 'running';
          const nowMs = Date.now();
          setMessages((prev) => {
            const next = [...prev];
            const idx = next.findIndex((m) => m?.cli_execution_id === executionId);
            const base = {
              role: 'assistant',
              content: '',
              streaming: false,
              id: `cli-${executionId}`,
              cli_execution_id: executionId,
              cli: {
                status,
                attempt: data.attempt,
                command: data.command,
                command_executed: data.command_executed,
                started_at_ms: data.started_at_ms,
                timeout_s: data.timeout_s,
                elapsed_ms: data.elapsed_ms,
                return_ms: data.return_ms,
                stdout: data.stdout,
                stderr: data.stderr,
                stdout_chunk: data.stdout_chunk,
                stderr_chunk: data.stderr_chunk,
                visual_state_summary: data.visual_state_summary,
                artifacts: data.artifacts
              }
            };
            if (idx >= 0) {
              const prevCli = next[idx]?.cli || {};
              const appendedStdout = (prevCli.stdout || '') + (String(data.stdout_chunk || ''));
              const appendedStderr = (prevCli.stderr || '') + (String(data.stderr_chunk || ''));
              const finalStdout = typeof data.stdout === 'string' ? data.stdout : appendedStdout;
              const finalStderr = typeof data.stderr === 'string' ? data.stderr : appendedStderr;
              const startedAtMs =
                Number(base?.cli?.started_at_ms) ||
                Number(prevCli?.started_at_ms) ||
                (status === 'running' ? nowMs : 0);
              const timeoutS =
                Number(base?.cli?.timeout_s) || Number(prevCli?.timeout_s) || 0;
              const returnMs =
                Number(base?.cli?.return_ms) || Number(prevCli?.return_ms) || 0;
              next[idx] = {
                ...next[idx],
                ...base,
                cli: {
                  ...(prevCli || {}),
                  ...(base.cli || {}),
                  started_at_ms: startedAtMs,
                  timeout_s: timeoutS,
                  return_ms: returnMs,
                  stdout: finalStdout,
                  stderr: finalStderr
                }
              };
              return next;
            }
            let parentIdx = -1;
            for (let i = next.length - 1; i >= 0; i -= 1) {
              const m = next[i];
              if (!m) continue;
              if (m.role !== 'assistant') continue;
              if (m.streaming) continue;
              if (m.cli_execution_id) continue;
              parentIdx = i;
              break;
            }
            if (parentIdx >= 0) {
              const parent = next[parentIdx] || {};
              const runs = { ...(parent.cli_runs || {}) };
              const prevCli = runs[executionId] || {};
              const startedAtMs =
                Number(base?.cli?.started_at_ms) ||
                Number(prevCli?.started_at_ms) ||
                (status === 'running' ? nowMs : 0);
              const timeoutS =
                Number(base?.cli?.timeout_s) || Number(prevCli?.timeout_s) || 0;
              const returnMs =
                Number(base?.cli?.return_ms) || Number(prevCli?.return_ms) || 0;
              runs[executionId] = {
                ...prevCli,
                ...(base.cli || {}),
                started_at_ms: startedAtMs,
                timeout_s: timeoutS,
                return_ms: returnMs,
              };
              next[parentIdx] = { ...parent, cli_runs: runs };
              return next;
            }
            if (!base?.cli?.started_at_ms && status === 'running') {
              base.cli.started_at_ms = nowMs;
            }
            next.push(base);
            return next;
          });
          setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
          }, 0);
        } else if (data.type === 'error') {
          const txt = String(data.content || '').trim() || 'Erro no processamento.';
          console.error('WebSocket error:', txt);
          flushChunkBuffer();
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.role === 'assistant' && last.streaming) {
              next[next.length - 1] = {
                ...last,
                content: txt,
                streaming: false,
              };
              return next;
            }
            next.push({
              role: 'assistant',
              content: txt,
              streaming: false,
              id: `ws-error-${Date.now()}-${Math.random().toString(16).slice(2)}`
            });
            return next;
          });
          setStreaming(false);
          setStreamStatusText('');
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      if (wsRef.current !== ws) return;
      const wasStreaming = Boolean(streamingRef.current) || Boolean((chunkBufferRef.current || '').length);
      setConnected(false);
      setStreaming(false);
      setStreamStatusText('');
      flushChunkBuffer();
      if (wasStreaming) {
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          const txt = 'Conexão perdida durante o processamento. Reabrindo…';
          if (last && last.role === 'assistant' && last.streaming) {
            next[next.length - 1] = { ...last, content: txt, streaming: false };
            return next;
          }
          next.push({
            role: 'assistant',
            content: txt,
            streaming: false,
            id: `ws-close-${Date.now()}-${Math.random().toString(16).slice(2)}`
          });
          return next;
        });
      }
      console.log('WebSocket desconectado');

      // Tentar reconectar após 3 segundos
      setTimeout(() => {
        if (user) {
          connectWebSocket();
        }
      }, 3000);
    };

    ws.onerror = (error) => {
      if (wsRef.current !== ws) return;
      console.error('WebSocket error:', error);
      setConnected(false);
      setStreaming(false);
      setStreamStatusText('');
    };
  };

  const sendMessage = () => {
    if (!input.trim() || streaming || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    const now = Date.now();
    const userMessage = {
      role: 'user',
      content: input.trim(),
      id: `${now}-${Math.random().toString(16).slice(2)}`
    };

    setStreaming(true);

    setMessages(prev => [
      ...prev,
      userMessage,
      {
        role: 'assistant',
        content: '',
        streaming: true,
        id: `${now + 1}-${Math.random().toString(16).slice(2)}`
      }
    ]);
    setInput('');

    // Include active skill id and expert override
    const activeSkill = (skills || []).find((s) => s.id === selectedSkillId) || null;
    const agentPrompt = forceExpertId ? String(agentConfigs?.[forceExpertId]?.prompt || '').trim() : '';
    wsRef.current.send(JSON.stringify({
      type: 'chat',
      content: input.trim(),
      internal_prompt: agentPrompt || null,
      skill_id: activeSkill?.id || null,
      skill_web_search: activeSkill?.content?.web_search === true,
      force_expert_id: forceExpertId || null
    }));
  };

  const goHome = () => {
    setMessages([]);
    setCurrentConversation(null);
    setCurrentKind('conversation');
    hasHttpHydratedRef.current = false;
    setCenterView('chat');
    setChatSearch('');
    setConversationSearch('');
    setTasksSearch('');
    if (wsRef.current) {
      wsRef.current.close();
    }
    sessionId.current = `session_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
    connectWebSocket();
  };

  const createNewConversation = async () => {
    try {
      const headers = getAuthHeaders();
      headers['Content-Type'] = 'application/json';
      const title = `Chat ${new Date().toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })}`;

      const response = await fetch('/api/conversations', {
        method: 'POST',
        headers,
        body: JSON.stringify({ title })
      });

      const data = await response.json();

      setMessages([]);
      setCurrentConversation(data.conversation_id);
      setCurrentKind('conversation');
      hasHttpHydratedRef.current = false;
      setCenterView('chat');
      setChatSearch('');
      if (wsRef.current) {
        wsRef.current.close();
      }
      sessionId.current = data.session_id;
      connectWebSocket();
      // Carregar listas em segundo plano para evitar atraso na abertura do chat
      loadConversations().catch(() => {});
      loadTasks().catch(() => {});

    } catch (error) {
      console.error('Error creating conversation:', error);
    }
  };

  const startNewConversationWithPrompt = async (prompt, opts = {}) => {
    if (autoStartRef.current || streaming) return;
    autoStartRef.current = true;
    try {
      const content = String(prompt || '').trim();
      const skillId = String(opts.skillId || '').trim();
      const internalPrompt = String(opts.internalPrompt || '').trim();
      const forceExpertIdOverride = String(opts.forceExpertId || '').trim();
      let prevSkill = '';
      if (skillId) {
        prevSkill = selectedSkillId;
        setSelectedSkillId(skillId);
      }
      if (content) {
        if (internalPrompt || forceExpertIdOverride) {
          pendingAutoSendRef.current = {
            content,
            internalPrompt,
            forceExpertId: forceExpertIdOverride
          };
        } else {
          pendingAutoSendRef.current = content;
        }
      }
      await createNewConversation();
      if (skillId) {
        if (tempSkillResetTimerRef.current) {
          clearTimeout(tempSkillResetTimerRef.current);
        }
        tempSkillResetTimerRef.current = setTimeout(() => {
          setSelectedSkillId(prevSkill || '');
          tempSkillResetTimerRef.current = null;
        }, 1500);
      }
    } finally {
      autoStartRef.current = false;
    }
  };

  const parseAssistantDirectivesFromText = (text) => {
    const actions = [];
    const parts = [];
    const inputText = (text || '').toString();
    const splitRegex = /\[\[assistant_split(?::(\d{1,5}))?\]\]/gi;
    let cursor = 0;
    let nextDelay = 1200;
    let cumulativeDelay = 0;
    let match = null;
    while ((match = splitRegex.exec(inputText)) !== null) {
      const chunk = inputText.slice(cursor, match.index);
      parts.push({ text: chunk, delayMs: cumulativeDelay });
      cursor = match.index + match[0].length;
      const parsedDelay = match[1] ? Number(match[1]) : NaN;
      nextDelay = Number.isFinite(parsedDelay) ? Math.max(0, parsedDelay) : 1200;
      cumulativeDelay += nextDelay;
    }
    parts.push({ text: inputText.slice(cursor), delayMs: cumulativeDelay });

    const cleanPart = (raw) => {
      let cleaned = (raw || '').toString();
      cleaned = cleaned.replace(/\[\[open_settings:([a-z0-9_-]+)\]\]/gi, (_m, target) => {
        actions.push({ type: 'open_settings', target: String(target || '').toLowerCase() });
        return '';
      });
      cleaned = cleaned.replace(/\[\[(?:set_expert|force_expert):([a-z0-9_-]+)\]\]/gi, (_m, expertId) => {
        actions.push({ type: 'set_expert', expertId: String(expertId || '').toLowerCase() });
        return '';
      });
      cleaned = cleaned.replace(/\[\[clear_expert\]\]/gi, () => {
        actions.push({ type: 'clear_expert' });
        return '';
      });
      cleaned = cleaned.replace(/\n{3,}/g, '\n\n').trim();
      return cleaned;
    };

    const cleanedParts = (parts || [])
      .map((p) => ({ ...p, text: cleanPart(p.text) }))
      .filter((p, idx) => idx === 0 || Boolean(p.text));

    const primary = cleanedParts[0]?.text || '';
    return { cleaned: primary, actions, parts: cleanedParts };
  };

  const runUiActions = (actions) => {
    if (!actions?.length) return;
    for (const a of actions) {
      if (a?.type === 'open_settings' && a?.target === 'llm_api_key') {
        pendingSettingsActionRef.current = 'llm_api_key';
        setCenterView('settings');
      }
      if (a?.type === 'set_expert') {
        setForceExpertId(String(a.expertId || ''));
      }
      if (a?.type === 'clear_expert') {
        setForceExpertId('');
      }
    }
  };

  const buildAgentsHelpPrompt = () => {
    const expertLines = (experts || [])
      .map((e) => `- ${e.icon} ${getExpertDisplayName(e)} (id: ${e.id}) — ${getExpertDisplayDescription(e) || ''}`.trim())
      .filter(Boolean)
      .join('\n');
    const coreSkillIds = new Set([
      'cto',
      'cfo',
      'coo',
      'project-manager',
      'systems-architect',
      'backend-dev',
      'frontend-dev',
      'devops',
      'security',
      'data-scientist',
      'code-review',
      'tests',
    ]);
    const skillLines = (skills || [])
      .filter((s) => coreSkillIds.has(s.id))
      .map((s) => `- ${getSkillDisplayName(s)} (skill_id: ${s.id}) — ${getSkillDisplayDescription(s) || ''}`.trim())
      .filter(Boolean)
      .join('\n');
    return (
      (lang === 'pt'
        ? (
          'Quero ver os agentes disponíveis e como usar cada um.\n\n' +
          'Você é Sabrina e deve responder com orientação prática para desenvolvimento de projetos e código.\n\n' +
          'Agentes (Experts) disponíveis no sistema:\n' +
          (expertLines || '- (nenhum carregado)') +
          '\n\n' +
          'Skills relevantes para projetos/código:\n' +
          (skillLines || '- (nenhuma carregada)') +
          '\n\n' +
          'Entregue:\n' +
          '- Uma tabela (Agente/Skill | Quando usar | Exemplos de comandos)\n' +
          '- Um fluxo recomendado para criar um projeto de software (da ideia ao deploy)\n' +
          '- 3 perguntas rápidas para você adaptar a orientação ao meu caso'
        )
        : (
          'I want to see the available agents and how to use each one.\n\n' +
          'You are Sabrina and must respond with practical guidance for software projects and code.\n\n' +
          'Agents (Experts) available in the system:\n' +
          (expertLines || '- (none loaded)') +
          '\n\n' +
          'Relevant skills for projects/code:\n' +
          (skillLines || '- (none loaded)') +
          '\n\n' +
          'Deliver:\n' +
          '- A table (Agent/Skill | When to use | Command examples)\n' +
          '- A recommended flow to build a software project (idea → deploy)\n' +
          '- 3 quick questions so you can adapt the guidance to my case'
        ))
    );
  };

  const buildHelpHowItWorksPrompt = () => (
    'Explique como o Open Slap funciona, de forma acessível para iniciantes:\n' +
    '- O que faz e o que não faz\n' +
    '- O que são credenciais, permissões e onde configurar\n' +
    '- Como obter chaves de API gratuitas (Gemini, Groq)\n' +
    '- Como a Sabrina orquestra a interação com os especialistas\n' +
    '- Boas práticas de privacidade e limites\n' +
    'Use uma linguagem simples, com passos e exemplos.'
  );

  const buildHelpSettingsPrompt = () => (
    'Guie a configuração do sistema (Settings) passo a passo:\n' +
    '- Onde inserir chaves de API (ex.: Gemini, Groq)\n' +
    '- Regra: nunca cole chaves no chat; use somente o campo de Settings\n' +
    '- Como testar conexões\n' +
    '- Como ajustar preferências principais\n' +
    '- Checklist final de verificação\n' +
    'Faça bullets curtos, com instruções claras.'
  );

  const buildHelpProjectsPrompt = () => (
    'Explique como usar o sistema para criar projetos de software:\n' +
    '- Coleta de requisitos rápida (perguntas essenciais)\n' +
    '- Estrutura de projeto (backlog, milestones, critérios)\n' +
    '- Como a Sabrina delega o projeto ao CTO e à equipe (Plan → Build)\n' +
    '- Do plano ao código: iteração e validação\n' +
    'No final, proponha um esqueleto de plano inicial em bloco ```plan``` com tasks e skill_id.'
  );

  const buildStartProjectPrompt = () => (
    'Você é a Sabrina.\n\n' +
    'WIZARD_ID: start_project_v1\n\n' +
    'Objetivo: conduzir um onboarding de projeto com calma e sem intimidar o usuário.\n' +
    'Regras:\n' +
    '- Sempre pergunte UMA coisa de cada vez.\n' +
    '- Para cada pergunta, aguarde uma resposta do usuário (qualquer resposta).\n' +
    '- Antes de fazer a próxima pergunta, verifique se a resposta do usuário contém uma dúvida/pergunta. Se contiver, responda primeiro e só depois avance.\n' +
    '- Se a resposta do usuário já trouxer informações que responderiam alguma pergunta futura, registre internamente essa resposta e pule a pergunta correspondente.\n' +
    '- Nunca peça chaves de API/secrets no chat.\n' +
    '- Para separar mensagens, use o token [[assistant_split:1200]] (a próxima mensagem deve vir em outra entrada, com ~1–2s de intervalo).\n\n' +
    'Fluxo:\n' +
    '1) Primeiro, confirme se o usuário está realmente iniciando um projeto de tecnologia (TI/software) ou se é outro tipo de projeto. Faça isso com 1 pergunta objetiva.\n' +
    '2) Se NÃO for TI, redirecione para o tipo certo (CFO/COO/PM/etc.) e pare.\n' +
    '3) Se for TI, siga as perguntas abaixo (uma por vez), no máximo 5, pulando as que já foram respondidas:\n' +
    '   - Pergunta 1: objetivo principal\n' +
    '   - Pergunta 2: público-alvo\n' +
    '   - Pergunta 3: prazo\n' +
    '   - Pergunta 4: restrições (técnicas/orçamentárias/recursos)\n' +
    '   - Pergunta 5: integrações ou dados sensíveis\n' +
    '4) Ao concluir, liste as especificações coletadas (bullets) e peça confirmação do usuário.\n' +
    '5) Se confirmado que é TI e que o resumo está correto: diga que está delegando ao CTO e em seguida sinalize a troca para CTO com [[set_expert:cto]].\n\n' +
    'Agora, entregue APENAS:\n' +
    '- A abordagem inicial exatamente neste texto:\n' +
    '  "Para entender melhor o projeto, preciso te fazer algumas perguntas. Quanto mais detalhadas as respostas, melhor. Mas caso não saiba o que responder (e isso é normal, não fique intimidado), apenas diga que não sabe. Responda a seu tempo. Quando terminarmos, terei informações suficientes para organizar os grupos de trabalho."\n' +
    '  [[assistant_split:1200]]\n' +
    '- A primeira pergunta (de confirmação se é TI ou não), em outra entrada.\n'
  );

  const buildHelpFAQPrompt = () => (
    'Crie uma FAQ detalhada para o usuário:\n' +
    '- Como começar?\n' +
    '- Preciso de chaves de API? Como obter?\n' +
    '- O que a Sabrina faz? E os especialistas?\n' +
    '- Como criar e gerenciar tarefas e projetos?\n' +
    '- Limitações, privacidade e segurança\n' +
    'Responda com perguntas e respostas objetivas.'
  );

  const createNewTask = async () => {
    try {
      const headers = getAuthHeaders();
      headers['Content-Type'] = 'application/json';
      const title = `Task ${new Date().toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })}`;

      const response = await fetch('/api/conversations?kind=task', {
        method: 'POST',
        headers,
        body: JSON.stringify({ title })
      });

      const data = await response.json();

      setMessages([]);
      setCurrentConversation(data.conversation_id);
      setCurrentKind('task');
      hasHttpHydratedRef.current = false;
      setCenterView('chat');
      setChatSearch('');

      // Pre-load CTO skill prompt so the user can describe the project immediately
      const ctoSkill = (skills || []).find((s) => s.id === 'cto');
      if (ctoSkill) {
        const ctoPrompt =
          typeof ctoSkill.content === 'object' && ctoSkill.content?.prompt
            ? ctoSkill.content.prompt
            : typeof ctoSkill.content === 'string'
            ? ctoSkill.content
            : '';
        if (ctoPrompt) setInput(ctoPrompt);
      }

      await loadConversations();
      await loadTasks();
      await loadGlobalTodos();

      if (wsRef.current) {
        wsRef.current.close();
      }
      sessionId.current = data.session_id;
      connectWebSocket();
    } catch (error) {
      console.error('Error creating task:', error);
    }
  };

  const loadConversation = async (conversationId, conversationSessionId, kindOverride) => {
    try {
      if (kindOverride === 'task' || kindOverride === 'conversation') {
        setCurrentKind(kindOverride);
      }
      const headers = getAuthHeaders();
      const response = await fetch(`/api/conversations/${conversationId}`, { headers });
      const data = await response.json();

      setMessages((data.messages || []).map((m, i) => ({
        ...m,
        id: m.id ?? `${conversationId}-${i}`
      })));
      setCurrentConversation(conversationId);
      hasHttpHydratedRef.current = !!((data.messages || []).length);
      setCenterView('chat');
      setChatSearch('');
      if (kindOverride === 'task') {
        await loadTaskTodos(conversationId);
      } else {
        setTaskTodos([]);
      }
      const loadedPlanTasks = await loadPlanTasks(conversationId);
      if (loadedPlanTasks?.length) {
        setShowExecutionPanel(true);
      } else if (!loadedPlanTasks?.length) {
        setOrchRunId(null);
        setOrchStatus('');
        setOrchLog([]);
      }

      if (wsRef.current) {
        wsRef.current.close();
      }
      sessionId.current = conversationSessionId || `session_${conversationId}`;
      connectWebSocket();

    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  useEffect(() => {
    if (loading) {
      document.body.classList.remove('loaded');
    } else {
      document.body.classList.add('loaded');
    }
  }, [loading]);

  // Loading screen
  if (loading) {
    return null;
  }

  const DonateContent = () => {
    const [donateText, setDonateText] = useState('');
    const [donateTextLoading, setDonateTextLoading] = useState(true);

    useEffect(() => {
      let alive = true;
      setDonateTextLoading(true);
      fetch('/media/doacoes.txt', { cache: 'no-store' })
        .then((r) => r.text())
        .then((txt) => {
          if (!alive) return;
          setDonateText(String(txt || ''));
        })
        .catch(() => {
          if (!alive) return;
          setDonateText('');
        })
        .finally(() => {
          if (!alive) return;
          setDonateTextLoading(false);
        });
      return () => {
        alive = false;
      };
    }, []);

    const paragraphs = donateText
      .replace(/\r/g, '')
      .split(/\n\s*\n/g)
      .map((p) => p.trim())
      .filter(Boolean);

    const renderInlineLinks = (text) => {
      const parts = String(text || '').split(/(https?:\/\/[^\s]+)/g);
      return parts.map((part, idx) => {
        const isUrl = /^https?:\/\//.test(part);
        if (!isUrl) return <span key={idx}>{part}</span>;
        return (
          <a
            key={idx}
            href={part}
            target="_blank"
            rel="noreferrer"
            style={{ color: 'var(--blue)', textDecoration: 'underline' }}
          >
            {part}
          </a>
        );
      });
    };

    return (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(220px, 360px) minmax(0, 1fr)',
          columnGap: '36px',
          rowGap: '24px',
          alignItems: 'start',
          marginTop: '16px'
        }}
      >
        <div style={{ minWidth: 0 }}>
            <img
              src="/media/pemartins.jpg"
              alt="Pê Martins"
              style={{
              width: '100%',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.10)',
              display: 'block'
            }}
          />
          <div style={{ marginTop: '14px', display: 'grid', gap: '10px', justifyItems: 'start' }}>
            <form action="https://www.paypal.com/donate" method="post" target="_top">
              <input type="hidden" name="business" value="MP75HDT3F2W9J" />
              <input type="hidden" name="no_recurring" value="0" />
              <input type="hidden" name="currency_code" value="BRL" />
              <input
                  type="image"
                  src="/media/btn_donateCC_LG.gif"
                  border="0"
                name="submit"
                title="PayPal - The safer, easier way to pay online!"
                alt="Donate with PayPal button"
              />
              <img
                alt=""
                border="0"
                src="https://www.paypal.com/en_BR/i/scr/pixel.gif"
                width="1"
                height="1"
              />
            </form>
            <a
              href="https://www.paypal.com/donate/?business=MP75HDT3F2W9J&no_recurring=0&currency_code=BRL"
              target="_blank"
              rel="noreferrer"
              style={{
                fontSize: '12px',
                color: 'var(--blue)',
                fontFamily: 'var(--mono)',
                textDecoration: 'underline',
                display: 'block',
                maxWidth: '100%',
                overflowWrap: 'anywhere',
                wordBreak: 'break-word'
              }}
            >
              https://www.paypal.com/donate/?business=MP75HDT3F2W9J&amp;no_recurring=0&amp;currency_code=BRL
            </a>
          </div>
        </div>

        <div style={{ minWidth: 0 }}>
          {donateTextLoading ? (
            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>{t('loading')}</div>
          ) : paragraphs.length ? (
            <div style={{ display: 'grid', gap: '12px' }}>
              {paragraphs.map((p, idx) => (
                <div
                  key={idx}
                  style={{
                    fontSize: '13px',
                    color: 'var(--text)',
                    fontFamily: 'var(--sans)',
                    lineHeight: 1.6,
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  {renderInlineLinks(p)}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
              Could not load donation text.
            </div>
          )}
        </div>
      </div>
    );
  };

  // Render dentro de um único Router
  return (
    <Router>
      <Routes>
        <Route path="/login" element={
          isAuthenticated ? <Navigate to="/" replace /> : <Login onLogin={login} onRegister={register} onPasswordResetRequest={requestPasswordReset} onPasswordResetConfirm={confirmPasswordReset} />
        } />
        <Route path="/donate" element={
          !isAuthenticated ? <Navigate to="/login" replace /> : (
            <div style={styles.app} className="slap-layout">
              <div style={styles.header}>
                <div style={styles.headerTitle} className="slap-header-title">{t('app_title')}</div>
                <div style={styles.headerRight}>
                  <button
                    className="slap-sidebar-toggle"
                    style={{ display: 'none', background: 'none', border: '1px solid var(--border)',
                             borderRadius: '6px', padding: '6px 10px', color: 'var(--text)',
                             cursor: 'pointer', fontSize: '16px' }}
                    onClick={() => setMobileSidebarOpen(v => !v)}
                    title="Toggle menu"
                  >
                    {mobileSidebarOpen ? '✕' : '☰'}
                  </button>
                  <button style={styles.userButton} onClick={() => (window.location.href = '/')}>
                    ← {t('back')}
                  </button>
                  <button style={styles.userButton} onClick={logout}>
                    {user?.email} → {t('sign_out')}
                  </button>
                </div>
              </div>
              <div style={styles.main}>
                <div style={styles.centerPanel}>
                  <div style={styles.centerPanelTitle}>{t('donate_page_title')}</div>
                  <DonateContent />
                </div>
              </div>
            </div>
          )
        } />
        <Route path="/*" element={
          !isAuthenticated ? <Navigate to="/login" replace /> : (
            <div style={styles.app}>
              {commandModal ? (
                <div style={styles.modalOverlay} onClick={() => setCommandModal(null)}>
                  <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
                    <div style={styles.modalHeader}>
                      <div style={styles.modalTitle}>{t('command_confirm_title')}</div>
                      <button style={styles.iconButton} onClick={() => setCommandModal(null)}>✕</button>
                    </div>
                    <div style={styles.modalBody}>
                      {commandModal?.title ? `${commandModal.title}\n\n` : ''}
                      {commandModal?.intent ? `Motivo: ${commandModal.intent}\n` : ''}
                      {`Risco: ${riskLabel(commandModal?.risk_level)}\n`}
                      {commandModal?.cwd ? `CWD: ${commandModal.cwd}\n` : ''}
                      {`\nComando:\n${commandModal?.command || ''}\n`}
                    </div>
                    <div style={{ ...styles.commandActions, justifyContent: 'flex-end' }}>
                      <button style={styles.settingsSecondaryButton} onClick={() => setCommandModal(null)}>
                        {t('cancel')}
                      </button>
                      <button
                        style={styles.settingsPrimaryButton}
                        onClick={() => executePendingCommand(commandModal)}
                        disabled={executingCommandId === commandModal?.id}
                      >
                        {executingCommandId === commandModal?.id ? t('executing') : t('execute')}
                      </button>
                    </div>
                  </div>
                </div>
              ) : null}
              {connectorModal ? (
                <div style={styles.modalOverlay} onClick={() => setConnectorModal(null)}>
                  <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
                    <div style={styles.modalHeader}>
                      <div style={styles.modalTitle}>{connectorModal?.title || t('connect')}</div>
                      <button style={styles.iconButton} onClick={() => setConnectorModal(null)} title="Fechar">×</button>
                    </div>
                    <div style={styles.modalBody}>
                      <div style={{ display: 'grid', gap: '10px' }}>
                        {connectorModal?.help ? (
                          <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                            {connectorModal.help}
                          </div>
                        ) : null}
                        <div style={{ display: 'grid', gap: '6px' }}>
                          <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--mono)' }}>
                            {t('connector_token_label')}
                          </div>
                          <input
                            style={styles.settingsInput}
                            value={connectorModal?.token || ''}
                            type="password"
                            onChange={(e) => setConnectorModal((prev) => ({ ...(prev || {}), token: e.target.value }))}
                            placeholder={t('connector_token_placeholder')}
                          />
                        </div>
                      </div>
                    </div>
                    <div style={{ ...styles.commandActions, justifyContent: 'flex-end' }}>
                      <button style={styles.settingsSecondaryButton} onClick={() => setConnectorModal(null)}>
                        {t('cancel')}
                      </button>
                      <button
                        style={styles.settingsPrimaryButton}
                        onClick={async () => {
                          const key = connectorModal?.key;
                          const value = connectorModal?.token;
                          const ok = await saveConnector(key, value);
                          if (ok) setConnectorModal(null);
                        }}
                      >
                        {t('save')}
                      </button>
                    </div>
                  </div>
                </div>
              ) : null}
              {/* Onboarding welcome modal */}
              {showOnboarding && (
                <div style={styles.modalOverlay} onClick={() => setShowOnboarding(false)}>
                  <div style={{ ...styles.modal, maxWidth: '520px' }} onClick={e => e.stopPropagation()}>
                    <div style={styles.modalHeader}>
                      <div style={styles.modalTitle}>{t('onboarding_title')}</div>
                      <button style={styles.iconButton} onClick={() => setShowOnboarding(false)}>×</button>
                    </div>
                    <div style={styles.modalBody}>
                      <div style={{ marginBottom: '16px', fontSize: '13px', color: 'var(--text)', lineHeight: 1.7 }}>
                        {t('onboarding_intro')}
                      </div>
                      {[
                        [t('onboarding_step_task_title'), t('onboarding_step_task_desc')],
                        [t('onboarding_step_skills_title'), t('onboarding_step_skills_desc')],
                        [t('onboarding_step_connectors_title'), t('onboarding_step_connectors_desc')],
                        [t('onboarding_step_feedback_title'), t('onboarding_step_feedback_desc')],
                        [t('onboarding_step_projects_title'), t('onboarding_step_projects_desc')],
                      ].map(([title, desc]) => (
                        <div key={title} style={{ marginBottom: '12px' }}>
                          <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--accent)', fontFamily: 'var(--sans)', marginBottom: '3px' }}>{title}</div>
                          <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--sans)', lineHeight: 1.5 }}>{desc}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ ...styles.commandActions, justifyContent: 'flex-end' }}>
                      <button style={styles.settingsPrimaryButton} onClick={() => { setShowOnboarding(false); createNewTask(); }}>
                        {t('onboarding_start_first_task')}
                      </button>
                      <button style={styles.settingsSecondaryButton} onClick={() => setShowOnboarding(false)}>
                        {t('onboarding_explore')}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {renameModal ? (
                <div style={styles.modalOverlay} onClick={() => setRenameModal(null)}>
                  <div style={{ ...styles.modal, maxWidth: '520px' }} onClick={e => e.stopPropagation()}>
                    <div style={styles.modalHeader}>
                      <div style={styles.modalTitle}>{t('rename_title')}</div>
                      <button style={styles.iconButton} onClick={() => setRenameModal(null)} title={t('close')}>×</button>
                    </div>
                    <div style={styles.modalBody}>
                      <input
                        style={styles.settingsInput}
                        value={renameDraft}
                        onChange={(e) => setRenameDraft(e.target.value)}
                        autoFocus
                      />
                    </div>
                    <div style={{ ...styles.commandActions, justifyContent: 'flex-end' }}>
                      <button style={styles.settingsSecondaryButton} onClick={() => setRenameModal(null)}>
                        {t('cancel')}
                      </button>
                      <button
                        style={styles.settingsPrimaryButton}
                        onClick={submitRename}
                        disabled={!String(renameDraft || '').trim()}
                      >
                        {t('save')}
                      </button>
                    </div>
                  </div>
                </div>
              ) : null}

              {genericModal ? (
                <div style={styles.modalOverlay} onClick={() => setGenericModal(null)}>
                  <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
                    <div style={styles.modalHeader}>
                      <div style={styles.modalTitle}>{genericModal?.title || t('confirm')}</div>
                      <button style={styles.iconButton} onClick={() => setGenericModal(null)} title={t('close')}>×</button>
                    </div>
                    <div style={styles.modalBody}>{genericModal?.body || ''}</div>
                    <div style={{ ...styles.commandActions, justifyContent: 'flex-end' }}>
                      <button style={styles.settingsSecondaryButton} onClick={() => setGenericModal(null)}>
                        {t('cancel')}
                      </button>
                      <button
                        style={styles.settingsPrimaryButton}
                        onClick={() => {
                          const action = genericModal?.onConfirm;
                          setGenericModal(null);
                          if (typeof action === 'function') action();
                        }}
                      >
                        {t('confirm')}
                      </button>
                    </div>
                  </div>
                </div>
              ) : null}

              {agentConfigModal && settingsTab !== 'agent_config' ? (
                <div style={styles.modalOverlay} onClick={() => setAgentConfigModal(null)}>
                  <div style={{ ...styles.modal, maxWidth: '760px' }} onClick={(e) => e.stopPropagation()}>
                    <div style={styles.modalHeader}>
                      <div style={styles.modalTitle}>
                        {`${t('configure')}: ${agentConfigModal?.expertName || agentConfigModal?.expertId || ''}`}
                      </div>
                      <button style={styles.iconButton} onClick={() => setAgentConfigModal(null)} title={t('close')}>×</button>
                    </div>
                    <div style={styles.modalBody}>
                      <div style={{ display: 'grid', gap: '12px' }}>
                        <div style={styles.settingsField}>
                          <div style={styles.settingsLabel}>{t('agent_prompt')}</div>
                          <textarea
                            style={{ ...styles.settingsTextarea, minHeight: '140px' }}
                            value={String(agentConfigModal?.prompt || '')}
                            onChange={(e) => setAgentConfigModal((prev) => ({ ...(prev || {}), prompt: e.target.value }))}
                            placeholder={t('agent_prompt_placeholder')}
                          />
                        </div>

                        <div style={{ ...styles.settingsGrid, gridTemplateColumns: '1fr' }}>
                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>{t('default_skill')}</div>
                            <select
                              style={styles.settingsInput}
                              value={String(agentConfigModal?.defaultSkillId || '')}
                              onChange={(e) => setAgentConfigModal((prev) => ({ ...(prev || {}), defaultSkillId: e.target.value }))}
                            >
                              <option value="">{t('none')}</option>
                              {(skills || []).map((s) => (
                                <option key={s.id} value={s.id}>{getSkillDisplayName(s)}</option>
                              ))}
                            </select>
                          </div>
                        </div>

                        <div style={styles.settingsField}>
                          <div style={styles.settingsLabel}>{t('agent_skills')}</div>
                          <div style={{ display: 'grid', gap: '12px' }}>
                            {(() => {
                              const current = new Set(Array.isArray(agentConfigModal?.skillIds) ? agentConfigModal.skillIds : []);
                              const grouped = groupBySegment(skills || [], getSkillSegmentId);
                              const labelMap = {
                                system: t('segment_system'),
                                admin: t('segment_admin'),
                                finance: t('segment_finance'),
                                marketing: t('segment_marketing'),
                                it_devops: t('segment_it_devops'),
                                other: t('segment_other'),
                              };
                              return segmentOrder.map((seg) => {
                                const list = sortSkillsForSegment((grouped?.[seg] || []), seg);
                                if (!list.length) return null;
                                return (
                                  <div key={`agent-skill-seg-${seg}`} style={{ display: 'grid', gap: '8px' }}>
                                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                      {labelMap[seg] || seg}
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
                                      {list.map((s) => {
                                        const checked = current.has(s.id);
                                        return (
                                          <label
                                            key={s.id}
                                            style={{
                                              display: 'flex',
                                              alignItems: 'flex-start',
                                              gap: '8px',
                                              padding: '8px 10px',
                                              borderRadius: '10px',
                                              border: '1px solid var(--border)',
                                              background: 'var(--bg3)',
                                              cursor: 'pointer',
                                              userSelect: 'none'
                                            }}
                                          >
                                            <input
                                              type="checkbox"
                                              checked={checked}
                                              onChange={(e) => {
                                                const next = new Set(Array.isArray(agentConfigModal?.skillIds) ? agentConfigModal.skillIds : []);
                                                if (e.target.checked) next.add(s.id);
                                                else next.delete(s.id);
                                                setAgentConfigModal((prev) => ({ ...(prev || {}), skillIds: Array.from(next) }));
                                              }}
                                              style={{ marginTop: '2px' }}
                                            />
                                            <div style={{ minWidth: 0 }}>
                                              <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600 }}>
                                                {getSkillDisplayName(s)}
                                              </div>
                                              {s.description ? (
                                                <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginTop: '4px' }}>
                                                  {getSkillDisplayDescription(s)}
                                                </div>
                                              ) : null}
                                            </div>
                                          </label>
                                        );
                                      })}
                                    </div>
                                  </div>
                                );
                              });
                            })()}
                          </div>
                          <div style={{ marginTop: '10px', display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                            <button
                              style={styles.settingsSecondaryButton}
                              onClick={() => {
                                setAgentConfigModal(null);
                                setCenterView('settings');
                                setSettingsTab('skills');
                              }}
                            >
                              {t('skills_center')}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div style={{ ...styles.commandActions, justifyContent: 'space-between' }}>
                      <button
                        style={styles.settingsSecondaryButton}
                        onClick={() => {
                          const expertId = String(agentConfigModal?.expertId || '').trim();
                          if (!expertId) {
                            setAgentConfigModal(null);
                            return;
                          }
                          setAgentConfigs((prev) => {
                            const next = { ...(prev || {}) };
                            delete next[expertId];
                            return next;
                          });
                          setAgentConfigModal(null);
                        }}
                      >
                        {t('reset')}
                      </button>
                      <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                        <button style={styles.settingsSecondaryButton} onClick={() => setAgentConfigModal(null)}>
                          {t('cancel')}
                        </button>
                        <button
                          style={styles.settingsPrimaryButton}
                          onClick={() => {
                            const expertId = String(agentConfigModal?.expertId || '').trim();
                            if (!expertId) {
                              setAgentConfigModal(null);
                              return;
                            }
                            const prompt = String(agentConfigModal?.prompt || '').trim();
                            const defaultSkillId = String(agentConfigModal?.defaultSkillId || '').trim();
                            const skillIds = Array.isArray(agentConfigModal?.skillIds) ? agentConfigModal.skillIds : [];
                            setAgentConfigs((prev) => ({
                              ...(prev || {}),
                              [expertId]: {
                                prompt,
                                default_skill_id: defaultSkillId,
                                skill_ids: skillIds
                              }
                            }));
                            setAgentConfigModal(null);
                          }}
                        >
                          {t('save')}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}
              <div style={styles.header}>
                <div style={styles.headerTitle} className="slap-header-title">{t('app_title')}</div>
                <div style={styles.headerRight}>
                  <button
                    className="slap-sidebar-toggle"
                    style={{
                      background: 'none',
                      border: '1px solid var(--border)',
                      borderRadius: '6px',
                      padding: '6px 10px',
                      color: 'var(--text)',
                      cursor: 'pointer',
                      fontSize: '16px',
                      display: isMobile ? 'inline-flex' : 'none',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                    onClick={() => setMobileSidebarOpen(v => !v)}
                    title="Menu"
                  >
                    {mobileSidebarOpen ? '✕' : '☰'}
                  </button>
                  <div style={{ ...styles.connectionStatus, display: isMobile ? 'none' : styles.connectionStatus.display }} className="slap-conn-status">
                    <div style={styles.connectionDot}></div>
                    {connected ? `${t('connected')}${runtimeLlmLabel ? ` — ${runtimeLlmLabel}` : ''}` : t('disconnected')}
                  </div>
                  {doctorReport && doctorReport.ok === false ? (
                    isMobile ? (
                      <button
                        style={{ ...styles.iconButton, color: 'var(--amber)' }}
                        onClick={() => setCenterView('settings')}
                        title="Há itens de diagnóstico pendentes"
                      >
                        ⚠
                      </button>
                    ) : (
                      <button
                        style={{ ...styles.userButton, borderColor: 'var(--amber)', color: 'var(--amber)' }}
                        onClick={() => setCenterView('settings')}
                        title="Há itens de diagnóstico pendentes"
                      >
                        Doctor ⚠
                      </button>
                    )
                  ) : null}
                  <button style={styles.iconButton} onClick={() => setCenterView('settings')}>
                    ⚙️
                  </button>
                  {isMobile ? (
                    <button style={styles.iconButton} onClick={logout} title={t('sign_out')}>
                      ⎋
                    </button>
                  ) : (
                    <button style={styles.userButton} onClick={logout}>
                      {user?.email} → {t('sign_out')}
                    </button>
                  )}
                </div>
              </div>

              <div style={styles.main}>
                {isMobile && mobileSidebarOpen ? (
                  <div
                    onClick={() => setMobileSidebarOpen(false)}
                    style={{
                      position: 'fixed',
                      inset: 0,
                      background: 'rgba(0,0,0,0.55)',
                      zIndex: 9998
                    }}
                  />
                ) : null}
                <div
                  style={{
                    ...styles.sidebar,
                    width: isMobile ? '280px' : (sidebarCollapsed ? '72px' : styles.sidebar.width),
                    ...(isMobile
                      ? {
                        position: 'fixed',
                        top: 0,
                        left: mobileSidebarOpen ? 0 : '-320px',
                        height: '100vh',
                        zIndex: 9999,
                        transition: 'left 0.18s ease-out',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.45)'
                      }
                      : {})
                  }}
                  className={`slap-sidebar${mobileSidebarOpen ? ' expanded' : ''}`}
                  onMouseLeave={() => setSidebarHoverKey('')}
                >
                  <div style={styles.sidebarContent}>
                    <div style={styles.sidebarSection}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
                        {!sidebarCollapsed ? <div style={styles.sidebarTitle}>{t('menu')}</div> : <div />}
                        <button
                          style={styles.iconButton}
                          onClick={() => {
                            if (isMobile) {
                              setMobileSidebarOpen(false);
                              return;
                            }
                            setSidebarCollapsed((v) => !v);
                          }}
                          title={sidebarCollapsed ? t('menu_expand') : t('menu_collapse')}
                          className="slap-collapse-toggle"
                          hidden={isMobile}
                        >
                          {sidebarCollapsed ? '»' : '«'}
                        </button>
                      </div>
                      <div style={{ height: '12px' }} />
                      <button
                        style={{
                          ...styles.sidebarButton,
                          ...(centerView === 'conversations' ? styles.sidebarButtonActive : {}),
                          ...(sidebarHoverKey === 'conversations' ? styles.sidebarButtonHover : {}),
                          textAlign: sidebarCollapsed ? 'center' : 'left',
                          padding: sidebarCollapsed ? '10px' : styles.sidebarButton.padding,
                          justifyContent: sidebarCollapsed ? 'center' : 'flex-start'
                        }}
                        onMouseEnter={() => setSidebarHoverKey('conversations')}
                        onMouseLeave={() => setSidebarHoverKey('')}
                        onClick={() => setCenterView('conversations')}
                        title={t('conversations')}
                      >
                        💬{sidebarCollapsed ? '' : ` ${t('conversations')}`}
                      </button>
                      <button
                        style={{
                          ...styles.sidebarButton,
                          ...(sidebarHoverKey === 'call-sabrina' ? styles.sidebarButtonHover : {}),
                          textAlign: sidebarCollapsed ? 'center' : 'left',
                          padding: sidebarCollapsed ? '10px' : styles.sidebarButton.padding,
                          justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                          marginTop: '8px'
                        }}
                        onMouseEnter={() => setSidebarHoverKey('call-sabrina')}
                        onMouseLeave={() => setSidebarHoverKey('')}
                        onClick={() => startNewConversationWithPrompt(buildSabrinaBellPrompt())}
                        title={t('ask_sabrina')}
                      >
                        👩‍💼{sidebarCollapsed ? '' : ` ${t('ask_sabrina')}`}
                      </button>
                      <button
                        style={{
                          ...styles.sidebarButton,
                          ...(sidebarHoverKey === 'start-project' ? styles.sidebarButtonHover : {}),
                          textAlign: sidebarCollapsed ? 'center' : 'left',
                          padding: sidebarCollapsed ? '10px' : styles.sidebarButton.padding,
                          justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                          marginTop: '8px'
                        }}
                        onMouseEnter={() => setSidebarHoverKey('start-project')}
                        onMouseLeave={() => setSidebarHoverKey('')}
                        onClick={() => startNewConversationWithPrompt(
                          lang === 'pt' ? 'Quero iniciar um novo projeto.' : 'I want to start a new project.',
                          { internalPrompt: buildStartProjectPrompt(), forceExpertId: 'general' }
                        )}
                        title={t('start_project')}
                      >
                        🧠{sidebarCollapsed ? '' : ` ${t('start_project')}`}
                      </button>
                      <button
                        style={{
                          ...styles.sidebarButton,
                          ...(centerView === 'tasks' ? styles.sidebarButtonActive : {}),
                          ...(sidebarHoverKey === 'tasks' ? styles.sidebarButtonHover : {}),
                          textAlign: sidebarCollapsed ? 'center' : 'left',
                          padding: sidebarCollapsed ? '10px' : styles.sidebarButton.padding,
                          justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                          marginTop: '8px'
                        }}
                        onMouseEnter={() => setSidebarHoverKey('tasks')}
                        onMouseLeave={() => setSidebarHoverKey('')}
                        onClick={() => setCenterView('tasks')}
                        title={t('tasks')}
                      >
                        ✅{sidebarCollapsed ? '' : ` ${t('tasks')}`}
                      </button>
                    </div>
                  </div>

                  <div style={styles.sidebarBottom}>
                    <div style={styles.sidebarDonateArea}>
                      <button
                        style={{
                          ...styles.sidebarButton,
                          ...(sidebarHoverKey === 'donate' ? styles.sidebarButtonHover : {}),
                          textAlign: sidebarCollapsed ? 'center' : 'left',
                          padding: sidebarCollapsed ? '10px' : styles.sidebarButton.padding,
                          justifyContent: sidebarCollapsed ? 'center' : 'flex-start'
                        }}
                        onMouseEnter={() => setSidebarHoverKey('donate')}
                        onMouseLeave={() => setSidebarHoverKey('')}
                        onClick={() => {
                          window.location.href = '/donate';
                        }}
                        title={t('donate')}
                      >
                        🤝{sidebarCollapsed ? '' : ` ${t('donate')}`}
                      </button>
                    </div>

                    <div style={styles.sidebarFooter}>
                      <button
                        type="button"
                        onClick={goHome}
                        style={{ background: 'transparent', border: 'none', padding: 0, cursor: 'pointer' }}
                        title="Tela inicial"
                      >
                        <img
                          src={OPEN_SLAP_LOGO_SRC}
                          alt="Open Slap!"
                          onError={(e) => {
                            const img = e.currentTarget;
                            img.src = `/agent/slap.png?v=1`;
                          }}
                          style={{
                            ...styles.sidebarLogo,
                            width: sidebarCollapsed ? '44px' : '100%',
                            height: 'auto',
                            maxHeight: '160px',
                            maxWidth: '300px'
                          }}
                        />
                      </button>
                    </div>
                  </div>
                </div>

                <div style={styles.chatArea}>
                  {centerView === 'conversations' ? (
                    <div style={styles.centerPanel}>
                      <div style={styles.centerPanelTitle}>{t('conversations')}</div>
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '12px' }}>
                        <input
                          style={{ ...styles.chatSearchInput, width: '100%' }}
                          value={conversationSearch}
                          onChange={(e) => setConversationSearch(e.target.value)}
                          placeholder={t('search_conversations_placeholder')}
                        />
                        {conversationSearch.trim() ? (
                          <button style={styles.chatSearchClear} onClick={() => setConversationSearch('')}>
                            {t('clear')}
                          </button>
                        ) : null}
                        <button style={styles.settingsPrimaryButton} onClick={createNewConversation}>
                          {t('new_conversation')}
                        </button>
                      </div>
                      {conversations.length === 0 ? (
                        <div style={{ maxWidth: '920px', width: '100%', margin: '0 auto' }}>
                          <div style={{ ...styles.lightCard, border: '1px solid rgba(255,255,255,0.10)' }}>
                            <pre
                              style={{
                                fontFamily: OPEN_SLAP_ASCII_FONT,
                                fontSize: isMobile ? '10px' : '12px',
                                lineHeight: 1.35,
                                whiteSpace: 'pre',
                                fontVariantLigatures: 'none',
                                letterSpacing: '0',
                                color: 'var(--text)',
                                opacity: 0.95,
                                overflowX: 'auto',
                                maxWidth: '100%',
                                width: '100%',
                                margin: 0
                              }}
                            >
                              {OPEN_SLAP_ASCII}
                            </pre>
                            <div style={{ marginTop: '12px', fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
                              Open Slap! é um core agêntico open source e gratuito para organizar tarefas, planejar projetos e executar fluxos com múltiplos agentes.
                            </div>
                            <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                              Exemplos práticos (clique para preencher):
                            </div>
                            <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={() => setInput('Quero que você organize minhas tarefas pendentes. Vou listar agora e você transforma em um TODO com prioridades.')}
                              >
                                Assistente pessoal (tarefas)
                              </button>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={() => setInput('Preciso planejar um projeto web do zero. Faça perguntas para entender escopo, prazo e restrições.')}
                              >
                                Planejar projeto web
                              </button>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={() => setInput('Quero organizar minhas finanças do mês. Me guie com um passo a passo e um checklist.')}
                              >
                                Organizar finanças
                              </button>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={() => {
                                  setCenterView('settings');
                                  setSettingsTab('team');
                                }}
                              >
                                {t('open_agents_in_settings')}
                              </button>
                            </div>
                            <div style={{ marginTop: '12px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                              <button style={styles.settingsPrimaryButton} onClick={createNewConversation}>
                                {t('new_conversation')}
                              </button>
                              <button
                                style={{
                                  ...styles.settingsSecondaryButton,
                                  background: '#ffffff',
                                  color: '#000000',
                                  border: '1px solid rgba(0,0,0,0.15)'
                                }}
                                onClick={() => window.open(OPEN_SLAP_REPO_URL, '_blank')}
                              >
                                GitHub — conheça o projeto
                              </button>
                            </div>
                          </div>
                        </div>
                      ) : (
                        conversationSearch.trim() ? (
                          <div style={{ display: 'grid', gap: '10px' }}>
                            <div style={styles.lightCard}>
                              <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                {t('history_results')}
                              </div>
                              {conversationSearchResults.length ? (
                                <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
                                  {conversationSearchResults.map((r) => (
                                    <div
                                      key={r.message_id}
                                      style={{
                                        ...styles.conversationItem,
                                        ...(currentConversation === r.conversation_id ? styles.conversationItemActive : {})
                                      }}
                                      onClick={() => loadConversation(r.conversation_id, r.session_id, 'conversation')}
                                    >
                                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                                        <div style={{ ...styles.conversationTitle, marginBottom: 0, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                          {r.conversation_title}
                                        </div>
                                        <button
                                          style={styles.smallIconButton}
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            openRename('conversation', { id: r.conversation_id, title: r.conversation_title });
                                          }}
                                          title="Renomear"
                                        >
                                          ✎
                                        </button>
                                      </div>
                                      <div style={styles.conversationMeta}>
                                        {r.snippet || ''} • {formatCompactDateTime(r.message_created_at)}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                  {t('no_history_results')}
                                </div>
                              )}
                            </div>

                            <div style={styles.lightCard}>
                              <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                {t('by_title')}
                              </div>
                              <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
                                {conversations
                                  .filter((c) => {
                                    const q = conversationSearch.trim().toLowerCase();
                                    if (!q) return true;
                                    return (c.title || '').toLowerCase().includes(q) || (c.session_id || '').toLowerCase().includes(q);
                                  })
                                  .map(conv => (
                                  <div
                                    key={conv.id}
                                    style={{
                                      ...styles.conversationItem,
                                      ...(currentConversation === conv.id ? styles.conversationItemActive : {})
                                    }}
                                    onClick={() => loadConversation(conv.id, conv.session_id, conv.kind === 'task' ? 'task' : 'conversation')}
                                  >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                                      <div style={{ ...styles.conversationTitle, marginBottom: 0, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {conv.title}
                                      </div>
                                      <button
                                        style={styles.smallIconButton}
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          openRename(conv.kind === 'task' ? 'task' : 'conversation', conv);
                                        }}
                                        title="Renomear"
                                      >
                                        ✎
                                      </button>
                                    </div>
                                    <div style={styles.conversationMeta}>
                                      {conv.message_count || 0} mensagens • Abertura: {formatCompactDateTime(conv.created_at)} • Última: {formatCompactDateTime(conv.updated_at || conv.created_at)}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div>
                            {conversations.map(conv => (
                              <div
                                key={conv.id}
                                style={{
                                  ...styles.conversationItem,
                                  ...(currentConversation === conv.id ? styles.conversationItemActive : {})
                                }}
                                onClick={() => loadConversation(conv.id, conv.session_id, conv.kind === 'task' ? 'task' : 'conversation')}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                                  <div style={{ ...styles.conversationTitle, marginBottom: 0, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {conv.title}
                                  </div>
                                  <button
                                    style={styles.smallIconButton}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      openRename(conv.kind === 'task' ? 'task' : 'conversation', conv);
                                    }}
                                    title="Renomear"
                                  >
                                    ✎
                                  </button>
                                </div>
                                <div style={styles.conversationMeta}>
                                  {conv.message_count || 0} mensagens • Abertura: {formatCompactDateTime(conv.created_at)} • Última: {formatCompactDateTime(conv.updated_at || conv.created_at)}
                                </div>
                              </div>
                            ))}
                          </div>
                        )
                      )}
                    </div>
                  ) : centerView === 'tasks' ? (
                    <div style={styles.centerPanel}>
                      <div style={styles.centerPanelTitle}>{t('tasks')}</div>
                      <div style={{ display: 'flex', gap: '2px', borderBottom: '1px solid var(--border)', marginBottom: '16px', flexWrap: 'wrap' }}>
                        {[
                          { id: 'project', label: lang === 'pt' ? 'Projeto' : (lang === 'es' ? 'Proyecto' : 'Project') },
                          { id: 'tasks', label: t('tasks') },
                          { id: 'todo', label: t('global_todo') },
                        ].map((tab) => (
                          <button
                            key={tab.id}
                            onClick={() => setTasksTab(tab.id)}
                            style={{
                              ...styles.sidebarButton,
                              width: 'auto',
                              padding: '8px 14px',
                              borderRadius: '6px 6px 0 0',
                              borderBottom: tasksTab === tab.id ? '2px solid var(--amber)' : '2px solid transparent',
                              color: tasksTab === tab.id ? 'var(--text-bright)' : 'var(--text-dim)',
                              fontSize: '12px',
                              fontFamily: 'var(--mono)',
                            }}
                          >
                            {tab.label}
                          </button>
                        ))}
                      </div>

                      {tasksTab === 'project' ? (
                        <div style={styles.lightCard}>
                          <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                            {lang === 'pt' ? 'PROJETO (KICKOFF)' : 'PROJECT (KICKOFF)'}
                          </div>
                          <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--sans)' }}>
                            {lang === 'pt'
                              ? 'Este é o artefato global de kickoff: um contexto por projeto (Markdown). A Sabrina pode gerar/atualizar esse conteúdo durante o processo de criação do projeto.'
                              : 'This is the global kickoff artifact: one Markdown context per project. Sabrina can generate/update this content during project kickoff.'}
                          </div>

                          <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
                            {projects.map((proj) => (
                              <div
                                key={proj.id}
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '10px',
                                  padding: '8px 12px',
                                  background: 'var(--bg3)',
                                  borderRadius: '8px',
                                  border: activeProjectId === proj.id ? '1px solid var(--accent)' : '1px solid var(--border)'
                                }}
                              >
                                <div style={{ flex: 1, fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
                                  📁 {proj.name}
                                </div>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => {
                                    setActiveProjectId(proj.id);
                                    setProjectContextDraft(String(proj?.context_md || ''));
                                    if (currentConversation) assignConversationProject(currentConversation, proj.id);
                                  }}
                                >
                                  {activeProjectId === proj.id ? (lang === 'pt' ? 'Ativo' : 'Active') : (lang === 'pt' ? 'Ativar' : 'Set active')}
                                </button>
                              </div>
                            ))}
                            {projects.length === 0 ? (
                              <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                {lang === 'pt' ? 'Nenhum projeto ainda.' : 'No projects yet.'}
                              </div>
                            ) : null}
                          </div>

                          <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                            <input
                              id="new-project-name-task"
                              style={{ ...styles.settingsInput, flex: 1 }}
                              placeholder={lang === 'pt' ? 'Nome do novo projeto…' : 'New project name…'}
                            />
                            <button
                              style={styles.settingsPrimaryButton}
                              onClick={async () => {
                                const el = document.getElementById('new-project-name-task');
                                const name = (el?.value || '').trim();
                                if (!name) return;
                                const pid = await createProject(name);
                                if (pid) {
                                  setActiveProjectId(pid);
                                  if (currentConversation) assignConversationProject(currentConversation, pid);
                                }
                                if (el) el.value = '';
                              }}
                            >
                              {lang === 'pt' ? 'Criar' : 'Create'}
                            </button>
                          </div>

                          {activeProjectId ? (
                            <div style={{ marginTop: '12px' }}>
                              <div style={styles.settingsLabel}>
                                {lang === 'pt' ? 'Contexto do projeto (Markdown)' : 'Project context (Markdown)'}
                              </div>
                              <textarea
                                style={{ ...styles.settingsTextarea, minHeight: '150px', marginTop: '6px' }}
                                value={projectContextDraft}
                                onChange={(e) => setProjectContextDraft(e.target.value)}
                                disabled={settingsLoading || projectContextSaving}
                                placeholder={lang === 'pt'
                                  ? 'Kickoff, escopo, stack, restrições, links, credenciais (nunca o valor), etc.'
                                  : 'Kickoff, scope, stack, constraints, links, credentials (never the secret value), etc.'}
                              />
                              <div style={styles.settingsActions}>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => setProjectContextDraft('')}
                                  disabled={settingsLoading || projectContextSaving}
                                >
                                  {lang === 'pt' ? 'Limpar' : 'Clear'}
                                </button>
                                <button
                                  style={styles.settingsPrimaryButton}
                                  onClick={async () => {
                                    const ok = await updateProjectContext(activeProjectId, projectContextDraft);
                                    if (ok) {
                                      setGenericModal({
                                        title: t('success'),
                                        body: lang === 'pt' ? 'Contexto do projeto salvo.' : 'Project context saved.'
                                      });
                                    }
                                  }}
                                  disabled={settingsLoading || projectContextSaving}
                                >
                                  {projectContextSaving
                                    ? (lang === 'pt' ? 'Salvando...' : 'Saving...')
                                    : (lang === 'pt' ? 'Salvar' : 'Save')}
                                </button>
                              </div>
                            </div>
                          ) : null}
                        </div>
                      ) : tasksTab === 'tasks' ? (
                        <>
                          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '12px' }}>
                            <input
                              style={{ ...styles.chatSearchInput, width: '100%' }}
                              value={tasksSearch}
                              onChange={(e) => setTasksSearch(e.target.value)}
                              placeholder={t('search_tasks_placeholder')}
                            />
                            {tasksSearch.trim() ? (
                              <button style={styles.chatSearchClear} onClick={() => setTasksSearch('')}>
                                {t('clear')}
                              </button>
                            ) : null}
                            <button
                              style={styles.smallIconButton}
                              onClick={() => setChatFontScale((v) => clamp(Number(v || 1) - 0.1, 0.8, 1.5))}
                              title={t('decrease_font')}
                            >
                              -
                            </button>
                            <button
                              style={styles.smallIconButton}
                              onClick={() => setChatFontScale((v) => clamp(Number(v || 1) + 0.1, 0.8, 1.5))}
                              title={t('increase_font')}
                            >
                              +
                            </button>
                          </div>

                          {tasks.length === 0 ? (
                            <div style={styles.emptyState}>{t('no_tasks')}</div>
                          ) : (
                            <div style={{ display: 'grid', gap: '10px' }}>
                              {tasksSearch.trim() ? (
                                <div style={styles.lightCard}>
                                  <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                    {t('history_results')}
                                  </div>
                                  {tasksSearchResults.length ? (
                                    <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
                                      {tasksSearchResults.map((r) => (
                                        <div
                                          key={r.message_id}
                                          style={{
                                            ...styles.conversationItem,
                                            ...(currentConversation === r.conversation_id ? styles.conversationItemActive : {})
                                          }}
                                          onClick={() => loadConversation(r.conversation_id, r.session_id, 'task')}
                                        >
                                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                                            <div style={{ ...styles.conversationTitle, marginBottom: 0, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                              {r.conversation_title}
                                            </div>
                                            <button
                                              style={styles.smallIconButton}
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                openRename('task', { id: r.conversation_id, title: r.conversation_title });
                                              }}
                                              title="Renomear"
                                            >
                                              ✎
                                            </button>
                                          </div>
                                          <div style={styles.conversationMeta}>
                                            {r.snippet || ''} • {formatCompactDateTime(r.message_created_at)}
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  ) : (
                                    <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                      {t('no_history_results')}
                                    </div>
                                  )}
                                </div>
                              ) : null}

                              <div style={styles.lightCard}>
                                <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                  {t('list_label')}
                                </div>
                                <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
                                  {tasks
                                    .filter((c) => {
                                      const q = tasksSearch.trim().toLowerCase();
                                      if (!q) return true;
                                      return (c.title || '').toLowerCase().includes(q) || (c.session_id || '').toLowerCase().includes(q);
                                    })
                                    .map((task) => {
                                      const pending = Number(task.pending_todo_count || 0);
                                      const done = Number(task.done_todo_count || 0);
                                      const statusLabel = pending > 0 ? t('in_progress') : t('completed');
                                      const countsLabel = (pending || done) ? ` • ${pending} ${t('pending_items')} • ${done} ${t('done_items')}` : '';
                                      return (
                                        <div
                                          key={task.id}
                                          style={{
                                            ...styles.conversationItem,
                                            ...(currentConversation === task.id ? styles.conversationItemActive : {})
                                          }}
                                          onClick={() => loadConversation(task.id, task.session_id, 'task')}
                                        >
                                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                                            <div style={{ ...styles.conversationTitle, marginBottom: 0, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                              {task.title}
                                            </div>
                                            <button
                                              style={styles.smallIconButton}
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                openRename('task', task);
                                              }}
                                              title="Renomear"
                                            >
                                              ✎
                                            </button>
                                          </div>
                                          <div style={styles.conversationMeta}>
                                            {statusLabel}{countsLabel} • {t('last')}: {formatCompactDateTime(task.updated_at || task.created_at)}
                                          </div>
                                        </div>
                                      );
                                    })}
                                </div>
                              </div>
                            </div>
                          )}
                        </>
                      ) : (
                        <div style={styles.lightCard}>
                          <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                            {t('global_todo')}
                          </div>
                          {globalTodos.length ? (
                            <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
                              {(() => {
                                const groups = {};
                                for (const td of (globalTodos || [])) {
                                  const cid = String(td?.conversation_id ?? '');
                                  if (!cid) continue;
                                  if (!groups[cid]) groups[cid] = [];
                                  groups[cid].push(td);
                                }
                                const convIds = Object.keys(groups);
                                convIds.sort((a, b) => {
                                  const ta = Math.max(...(groups[a] || []).map(x => (x?.created_at ? Date.parse(x.created_at) : 0) || 0));
                                  const tb = Math.max(...(groups[b] || []).map(x => (x?.created_at ? Date.parse(x.created_at) : 0) || 0));
                                  return tb - ta;
                                });

                                const renderNode = (node, depth, ctx) => {
                                  const artifacts = getTodoArtifacts(node);
                                  const deliveryPath = String(node.delivery_path || '').trim();
                                  const originConversationId = node?.source_conversation_id;
                                  const originSessionId = node?.source_session_id;
                                  const originConversationKind = String(node?.source_conversation_kind || '').trim();
                                  const originConversationTitle = String(node?.source_conversation_title || '').trim();
                                  const originCreatedAt = node?.source_message_created_at || null;
                                  const hasOrigin = Boolean(originConversationId) && String(originConversationId) !== String(ctx.conversationId);
                                  return (
                                    <div key={`gtd-${node.id}`} style={{ display: 'grid', gap: '6px' }}>
                                      <div style={{ ...styles.todoItem, marginLeft: `${Math.min(6, Math.max(0, depth)) * 14}px` }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                                          <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', minWidth: 0 }}>
                                            <div style={styles.todoCheck}>☐</div>
                                            <div style={{ minWidth: 0 }}>
                                              <div style={{ ...styles.conversationTitle, marginBottom: '2px' }}>{node.text}</div>
                                              {(deliveryPath || (artifacts && artifacts.length)) ? (
                                                <div style={{ margin: '6px 0 2px 0', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                                  {deliveryPath ? (
                                                    <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: 'rgba(245,166,35,0.10)', color: 'var(--amber)', fontFamily: 'var(--mono)' }} title={deliveryPath}>
                                                      {truncatePath(deliveryPath)}
                                                    </span>
                                                  ) : null}
                                                  {(artifacts || []).slice(0, 4).map((a, i) => {
                                                    const url = String(a?.url || '').trim();
                                                    const name = String(a?.name || a?.id || `artifact-${i}`);
                                                    if (!url) {
                                                      return (
                                                        <span key={`${name}-${i}`} style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: 'rgba(127,119,221,0.12)', color: '#7F77DD', fontFamily: 'var(--mono)' }}>
                                                          {name}
                                                        </span>
                                                      );
                                                    }
                                                    return (
                                                      <button
                                                        key={`${name}-${i}`}
                                                        style={{ ...styles.settingsSecondaryButton, padding: '3px 8px', fontSize: '10px', fontFamily: 'var(--mono)' }}
                                                        onClick={() => window.open(url, '_blank')}
                                                        title={name}
                                                      >
                                                        {name}
                                                      </button>
                                                    );
                                                  })}
                                                </div>
                                              ) : null}
                                              <div style={styles.conversationMeta}>
                                                {ctx.taskTitle} • {formatCompactDateTime(node.created_at)}
                                              </div>
                                              {hasOrigin ? (
                                                <div style={{ ...styles.conversationMeta, marginTop: '2px' }}>
                                                  {(lang === 'pt' ? 'Origem' : 'Source')}: {originConversationTitle || `${lang === 'pt' ? 'Chat' : 'Chat'} #${originConversationId}`}
                                                  {originCreatedAt ? ` • ${formatCompactDateTime(originCreatedAt)}` : ''}
                                                </div>
                                              ) : null}
                                            </div>
                                          </div>
                                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flex: '0 0 auto' }}>
                                            <button
                                              style={styles.smallIconButton}
                                              onClick={() => loadConversation(ctx.conversationId, ctx.sessionId, 'task')}
                                              title={t('open')}
                                            >
                                              ↗
                                            </button>
                                            {hasOrigin ? (
                                              <button
                                                style={styles.smallIconButton}
                                                onClick={() => loadConversation(originConversationId, originSessionId, originConversationKind === 'task' ? 'task' : 'conversation')}
                                                title={lang === 'pt' ? 'Abrir origem' : 'Open source'}
                                              >
                                                ⤴
                                              </button>
                                            ) : null}
                                            <button
                                              style={styles.smallIconButton}
                                              onClick={() => markTodoDone(node.id)}
                                              title={t('complete')}
                                            >
                                              ✓
                                            </button>
                                          </div>
                                        </div>
                                      </div>
                                      {(node.children || []).map((ch) => renderNode(ch, depth + 1, ctx))}
                                    </div>
                                  );
                                };

                                return convIds.map((cid) => {
                                  const items = groups[cid] || [];
                                  const roots = buildTodoTree(items);
                                  const ctx = {
                                    conversationId: items[0]?.conversation_id,
                                    sessionId: items[0]?.session_id,
                                    taskTitle: items[0]?.task_title || `Task #${cid}`,
                                  };
                                  return (
                                    <div key={`todo-group-${cid}`} style={{ display: 'grid', gap: '8px' }}>
                                      {roots.map((r) => renderNode(r, 0, ctx))}
                                    </div>
                                  );
                                });
                              })()}
                            </div>
                          ) : (
                            <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                              {t('no_pending')}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : centerView === 'team' ? (
                    <div style={styles.centerPanel}>
                      <div style={styles.centerPanelTitle}>{t('my_team')}</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                        <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                          {t('available_agents')}
                        </div>
                        <button
                          style={styles.settingsPrimaryButton}
                          onClick={async () => {
                            await createNewConversation();
                            setInput('');
                            const now = Date.now();
                            setMessages(prev => [
                              ...prev,
                              {
                                role: 'assistant',
                                content: 'Ok, vou te ajudar a criar um novo agente. Me explique o que você quer que ele faça.',
                                id: `${now}-${Math.random().toString(16).slice(2)}`
                              }
                            ]);
                            setCenterView('chat');
                          }}
                        >
                          {t('create_new_agent')}
                        </button>
                      </div>
                      {experts.length === 0 ? (
                        <div style={styles.emptyState}>{t('no_agents')}</div>
                      ) : (
                        <div style={{ display: 'grid', gap: '10px' }}>
                          {experts.map((e) => (
                            <div key={e.id} style={{ ...styles.doctorCard, borderColor: 'rgba(255,255,255,0.08)' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                  <div style={{ fontSize: '18px' }}>{e.icon}</div>
                                  <div>
                                    <div style={{ fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600 }}>
                                      {getExpertDisplayName(e)}
                                    </div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginTop: '4px' }}>
                                      {getExpertDisplayDescription(e) || e.id}
                                      {e.id === 'general' ? (lang === 'pt' ? ' • Orquestradora (padrão)' : ' • Orchestrator (default)') : ''}
                                    </div>
                                  </div>
                                </div>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => {
                                    setCenterView('chat');
                                    setInput(lang === 'pt' ? `Quero falar com o agente ${getExpertDisplayName(e)}.` : `I want to talk to agent ${getExpertDisplayName(e)}.`);
                                  }}
                                >
                                  {t('open_in_chat')}
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : centerView === 'customize' ? (
                    <div style={styles.centerPanel}>
                      {customizeView === 'skill' ? (
                        (() => {
                          const selected = (skills || []).find((s) => s.id === selectedSkillId) || null;
                          const prompt = (() => {
                            if (!selected) return '';
                            const c = selected.content;
                            if (c && typeof c === 'object' && typeof c.prompt === 'string') return c.prompt;
                            if (typeof c === 'string') {
                              const t = c.trim();
                              if (t.startsWith('{') || t.startsWith('[')) {
                                try {
                                  const parsed = JSON.parse(t);
                                  if (parsed && typeof parsed === 'object' && typeof parsed.prompt === 'string') return parsed.prompt;
                                } catch {}
                              }
                            }
                            return '';
                          })();
                          const readText = selected
                            ? (typeof selected.content === 'string'
                              ? selected.content
                              : JSON.stringify(selected.content ?? {}, null, 2))
                            : '';

                          return (
                            <div style={{ display: 'grid', gap: '12px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => {
                                    setCustomizeView('home');
                                    setSelectedSkillId('');
                                    setSkillDraft('');
                                    setSkillEditMode(false);
                                  }}
                                >
                                  ← Customize
                                </button>
                                {!skillEditMode ? (
                                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                    <button
                                      style={styles.settingsSecondaryButton}
                                      onClick={() => {
                                        if (!prompt) return;
                                        createTaskWithPrefill(prompt);
                                        setCenterView('chat');
                                      }}
                                      disabled={!selected || !prompt}
                                      title={!prompt ? 'Esta skill não tem prompt de execução.' : 'Executar skill'}
                                    >
                                      Executar
                                    </button>
                                    <button
                                      style={styles.settingsPrimaryButton}
                                      onClick={() => {
                                        setSkillDraft(readText);
                                        setSkillEditMode(true);
                                      }}
                                      disabled={!selected}
                                    >
                                      Editar
                                    </button>
                                  </div>
                                ) : (
                                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                    <button
                                      style={styles.settingsSecondaryButton}
                                      onClick={() => {
                                        setSkillDraft(readText);
                                        setSkillEditMode(false);
                                      }}
                                    >
                                      Cancelar
                                    </button>
                                    <button
                                      style={styles.settingsPrimaryButton}
                                      onClick={() => {
                                        if (!selected) return;
                                        const raw = String(skillDraft || '').trim();
                                        let parsed = null;
                                        try {
                                          parsed = raw ? JSON.parse(raw) : {};
                                        } catch {
                                          setGenericModal({
                                            title: t('invalid_json_title'),
                                            body: t('invalid_json_body')
                                          });
                                          return;
                                        }
                                        const nextSkills = (skills || []).map((s) => (
                                          s.id === selected.id
                                            ? { ...s, content: parsed }
                                            : s
                                        ));
                                        setSkills(nextSkills);
                                        saveSkillsToBackend(nextSkills);
                                        setSkillEditMode(false);
                                      }}
                                      disabled={!selected}
                                    >
                                      Salvar
                                    </button>
                                  </div>
                                )}
                              </div>
                              {skillsSaveStatus ? (
                                <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                  {skillsSaveStatus}
                                </div>
                              ) : null}

                              <div style={{ ...styles.lightCard, padding: '14px' }}>
                                <div style={styles.skillName}>{selected ? getSkillDisplayName(selected) : 'Habilidade'}</div>
                                {selected?.description ? (
                                  <div style={styles.skillDesc}>{getSkillDisplayDescription(selected)}</div>
                                ) : null}
                                <div style={{ marginTop: '12px' }}>
                                  <textarea
                                    style={styles.monoTextarea}
                                    value={skillEditMode ? skillDraft : readText}
                                    onChange={(e) => setSkillDraft(e.target.value)}
                                    readOnly={!skillEditMode}
                                  />
                                </div>
                              </div>
                            </div>
                          );
                        })()
                      ) : (
                        <>
                          <div style={styles.centerPanelTitle}>{t('customize')}</div>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
                            <div style={styles.lightCard}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                                <div style={{ fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600 }}>
                                  Skills
                                </div>
                                <button
                                  style={styles.settingsPrimaryButton}        
                                  onClick={() => {
                                    createTaskWithPrefill(
                                      'Crie uma nova skill. Faça perguntas para coletar os dados necessários (nome, propósito, entradas/saídas, exemplos) e gere a implementação. Ao final, valide com um checklist e sugira testes.'     
                                    );
                                  }}
                                >
                                  + {t('create_new_skill') || 'Create new skill'}
                                </button>
                              </div>
                              <div style={{ marginTop: '10px' }}>
                                <div style={styles.skillGrid}>
                                  {(skills || []).map((s) => (
                                    <div
                                      key={s.id}
                                      style={styles.skillCard}
                                      onClick={() => {
                                        setSelectedSkillId(s.id);
                                        setCustomizeView('skill');
                                        const t = typeof s.content === 'string' ? s.content : JSON.stringify(s.content ?? {}, null, 2);
                                        setSkillDraft(t);
                                        setSkillEditMode(false);
                                      }}
                                      title="Abrir habilidade"
                                    >
                                      <div style={styles.skillName}>{getSkillDisplayName(s)}</div>
                                      <div style={styles.skillDesc}>{getSkillDisplayDescription(s)}</div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                              <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                {t('skills_hint_open')}
                              </div>
                            </div>

                            <div style={styles.lightCard}>
                              <div style={{ fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600 }}>
                                Execução e transparência
                              </div>
                              <div style={{ marginTop: '10px', display: 'grid', gap: '10px' }}>
                                <label style={{ display: 'flex', gap: '10px', alignItems: 'center', fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
                                  <input
                                    type="checkbox"
                                    checked={showExecutionPanel}
                                    onChange={(e) => setShowExecutionPanel(Boolean(e.target.checked))}
                                  />
                                  Mostrar painel de execução no chat
                                </label>
                                <label style={{ display: 'flex', gap: '10px', alignItems: 'center', fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
                                  <input
                                    type="checkbox"
                                    checked={showRoutingDebug}
                                    onChange={(e) => setShowRoutingDebug(Boolean(e.target.checked))}
                                  />
                                  Mostrar detalhes de roteamento (debug)
                                </label>
                                <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                  Por padrão, o chat mostra só o agente e o modelo. O modo debug exibe o motivo do roteamento.
                                </div>
                              </div>
                            </div>

                            <div style={styles.lightCard}>
                              <div style={{ fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600 }}>
                                {t('connectors')}
                              </div>
                              {connectorsLoading ? (
                                <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                  {t('loading')}
                                </div>
                              ) : null}
                              <div style={styles.connectorGrid}>
                                {[
                                  { key: 'github', name: 'GitHub' },
                                  { key: 'google_drive', name: 'Google Drive' },
                                  { key: 'google_calendar', name: 'Google Calendar' },
                                  { key: 'gmail', name: 'Gmail' },
                                  { key: 'telegram', name: 'Telegram' },
                                  { key: 'tera', name: 'Tera' }
                                ].map((c) => {
                                  const isConnected = Boolean(connectors?.[c.key]?.connected);
                                  const dotStyle = { ...styles.connectorDot, background: isConnected ? 'var(--green)' : 'var(--red)' };
                                  return (
                                    <div key={c.key} style={styles.connectorCard}>
                                      <div style={styles.connectorRow}>
                                        <div style={styles.connectorTitle}>
                                          <div style={dotStyle}></div>
                                          <div style={{ minWidth: 0 }}>
                                            <div style={{ fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600 }}>
                                              {c.name}
                                            </div>
                                            <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginTop: '4px' }}>
                                              {isConnected ? t('connected_ok') : t('not_connected')}
                                            </div>
                                          </div>
                                        </div>
                                      </div>
                                      <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                                        {!isConnected ? (
                                          <button
                                            style={styles.settingsPrimaryButton}
                                            onClick={() => openConnectorModal(c.key)}
                                          >
                                            {t('connect')}
                                          </button>
                                        ) : (
                                          <>
                                            {c.key === 'telegram' ? (
                                              <button
                                                style={styles.settingsSecondaryButton}
                                                onClick={createTelegramLinkCode}
                                              >
                                                {t('generate_code')}
                                              </button>
                                            ) : null}
                                            <button
                                              style={styles.settingsSecondaryButton}
                                              onClick={() => testConnector(c.key)}
                                            >
                                              {t('test')}
                                            </button>
                                            <button
                                              style={styles.settingsSecondaryButton}
                                              onClick={() => disconnectConnector(c.key)}
                                            >
                                              {t('disconnect')}
                                            </button>
                                          </>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  ) : centerView === 'settings' ? (
                    <div style={styles.centerPanel}>
                      <div style={styles.centerPanelTitle}>{t('settings')}</div>
                      <div style={{ display: 'flex', gap: '2px', borderBottom: '1px solid var(--border)', marginBottom: '20px', flexWrap: 'wrap' }}>
                        {[
                          { id: 'appearance', label: t('theme') },
                          { id: 'llm', label: t('llm_providers') },
                          { id: 'security', label: t('security') },
                          { id: 'connectors', label: t('connectors') || 'Conectores' },
                          { id: 'memory', label: t('memory') },
                          { id: 'skills', label: t('skills_center') },
                          { id: 'team', label: t('my_team') },
                        ].map((tab) => (
                          <button
                            key={tab.id}
                            onClick={() => setSettingsTab(tab.id)}
                            style={{
                              ...styles.sidebarButton,
                              width: 'auto',
                              padding: '8px 14px',
                              borderRadius: '6px 6px 0 0',
                              borderBottom: settingsTab === tab.id ? '2px solid var(--amber)' : '2px solid transparent',
                              color: settingsTab === tab.id ? 'var(--text-bright)' : 'var(--text-dim)',
                              fontSize: '12px',
                              fontFamily: 'var(--mono)',
                            }}
                          >
                            {tab.label}
                          </button>
                        ))}
                      </div>
                      {settingsError ? (
                        <div style={styles.settingsError}>{settingsError}</div>
                      ) : null}

                      {settingsTab === 'appearance' ? (
                        <>
                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{t('theme')}</div>
                            <div style={{
                              display: 'grid',
                              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                              gap: '12px',
                              marginTop: '8px'
                            }}>
                              {[
                                { id: 'deep-space',    label: t('theme_deep_space'),    preview: ['#080c0f','#0e1318','#f5a623'] },
                                { id: 'midnight-blue', label: t('theme_midnight_blue'),  preview: ['#07080f','#0d1020','#4a9eff'] },
                                { id: 'forest',        label: t('theme_forest'),         preview: ['#080f09','#0d1710','#4ade80'] },
                                { id: 'crimson',       label: t('theme_crimson'),        preview: ['#0f0808','#1a0d0d','#f87171'] },
                                { id: 'slate',         label: t('theme_slate'),          preview: ['#0c0e12','#13161e','#9b8cff'] },
                                { id: 'solarized',     label: t('theme_solarized'),      preview: ['#001b24','#00262f','#2aa198'] },
                                { id: 'light',         label: t('theme_light'),          preview: ['#f5f5f5','#ffffff','#d97706'] },
                                { id: 'paper',         label: t('theme_paper'),          preview: ['#f0ebe0','#faf5ea','#8b4513'] },
                              ].map((th) => {
                                const isActive = theme === th.id;
                                return (
                                  <button
                                    key={th.id}
                                    onClick={() => setTheme(th.id)}
                                    style={{
                                      background: th.preview[0],
                                      border: isActive
                                        ? `2px solid ${th.preview[2]}`
                                        : '2px solid transparent',
                                      borderRadius: '8px',
                                      padding: '8px',
                                      cursor: 'pointer',
                                      textAlign: 'left',
                                      outline: 'none',
                                      transition: 'border-color 0.15s',
                                      boxShadow: isActive ? `0 0 0 1px ${th.preview[2]}40` : 'none',
                                      width: '100%',
                                      minHeight: '74px',
                                      display: 'flex',
                                      flexDirection: 'column',
                                      justifyContent: 'space-between',
                                    }}
                                  >
                                    <div style={{ display: 'flex', gap: '5px', marginBottom: '8px' }}>
                                      {th.preview.map((c, i) => (
                                        <div key={i} style={{
                                          width: '12px', height: '12px',
                                          borderRadius: '50%',
                                          background: c,
                                          border: '1px solid rgba(255,255,255,0.15)'
                                        }} />
                                      ))}
                                    </div>
                                    <div style={{
                                      fontSize: '10px',
                                      fontFamily: 'var(--mono)',
                                      color: th.preview[2],
                                      fontWeight: isActive ? 600 : 400,
                                      letterSpacing: '0.02em',
                                    }}>
                                      {th.label}
                                    </div>
                                  </button>
                                );
                              })}
                            </div>
                          </div>

                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{t('language')}</div>
                            <div style={{ ...styles.settingsGrid, gridTemplateColumns: '1fr' }}>
                              <div style={styles.settingsField}>
                                <div style={styles.settingsLabel}>{t('language')}</div>
                                <select
                                  style={styles.settingsInput}
                                  value={lang}
                                  onChange={(e) => {
                                    const next = e.target.value;
                                    setLang(next);
                                    saveLanguageSettings(next);
                                  }}
                                  disabled={settingsLoading}
                                >
                                  <option value="pt">Português</option>
                                  <option value="en">English</option>
                                  <option value="es">Español</option>
                                  <option value="ar">العربية</option>
                                  <option value="zh">中文</option>
                                </select>
                              </div>
                            </div>
                          </div>

                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{t('doctor_diagnostics')}</div>
                            {doctorError ? (
                              <div style={styles.settingsError}>{doctorError}</div>
                            ) : null}

                            <div style={styles.doctorCard}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                                <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
                                  {doctorReport
                                    ? (doctorReport.ok ? t('doctor_all_ok') : t('doctor_some_attention'))
                                    : t('doctor_click_run')}
                                </div>
                                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                  <button
                                    style={styles.settingsSecondaryButton}
                                    onClick={() => {
                                      refreshSystemProfile().finally(() => fetchDoctorReport({ silent: true }));
                                    }}
                                    disabled={settingsLoading || doctorLoading}
                                  >
                                    {t('update_profile')}
                                  </button>
                                  <button
                                    style={styles.settingsPrimaryButton}
                                    onClick={() => fetchDoctorReport({ silent: false })}
                                    disabled={settingsLoading || doctorLoading}
                                  >
                                    {doctorLoading ? t('running') : t('run_diagnostics')}
                                  </button>
                                </div>
                              </div>

                              {doctorReport?.checks?.length ? (
                                <div style={{ marginTop: '10px' }}>
                                  {doctorReport.checks.map((c, idx) => {
                                    const ok = Boolean(c.ok);
                                    const isLast = idx === doctorReport.checks.length - 1;
                                    const statusStyle = {
                                      ...styles.doctorStatus,
                                      borderColor: ok ? 'rgba(34, 197, 94, 0.45)' : 'rgba(248, 113, 113, 0.45)',
                                      color: ok ? 'var(--green)' : 'var(--red)',
                                      background: ok ? 'rgba(34, 197, 94, 0.10)' : 'rgba(248, 113, 113, 0.10)'
                                    };
                                    return (
                                      <div
                                        key={c.id || idx}
                                        style={{ ...styles.doctorRow, ...(isLast ? styles.doctorRowLast : {}) }}
                                      >
                                        <div style={{ flex: 1 }}>
                                          <div style={styles.doctorLabel}>{c.label || c.id}</div>
                                          {c.detail ? <div style={styles.doctorDetail}>{c.detail}</div> : null}
                                        </div>
                                        <div style={statusStyle}>{ok ? 'OK' : t('status_failed')}</div>
                                      </div>
                                    );
                                  })}
                                </div>
                              ) : null}

                              {doctorReport?.recommendations?.length ? (
                                <div style={{ marginTop: '12px' }}>
                                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginBottom: '8px' }}>
                                    {t('recommendations')}
                                  </div>
                                  <div style={{ display: 'grid', gap: '6px' }}>
                                    {doctorReport.recommendations.map((r, i) => (
                                      <div key={i} style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
                                        {r}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              ) : null}
                            </div>
                          </div>
                        </>
                      ) : null}

                      {settingsTab === 'llm' ? (
                        <>
                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{t('llm_free_keys_title')}</div>
                            <div style={styles.settingsHint}>{t('llm_free_keys_body')}</div>
                            <div style={{ marginTop: '10px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                              <button
                                style={{ ...styles.settingsSecondaryButton, background: '#fff', color: '#000', border: '1px solid rgba(0,0,0,0.15)' }}
                                onClick={() => window.open('https://aistudio.google.com/app/apikey', '_blank')}
                              >
                                {t('llm_free_keys_gemini')}
                              </button>
                              <button
                                style={{ ...styles.settingsSecondaryButton, background: '#fff', color: '#000', border: '1px solid rgba(0,0,0,0.15)' }}
                                onClick={() => window.open('https://console.groq.com/keys', '_blank')}
                              >
                                {t('llm_free_keys_groq')}
                              </button>
                              <button
                                style={{ ...styles.settingsSecondaryButton, background: '#fff', color: '#000', border: '1px solid rgba(0,0,0,0.15)' }}
                                onClick={() => window.open('https://openrouter.ai/keys', '_blank')}
                              >
                                {t('llm_free_keys_openrouter')}
                              </button>
                            </div>
                          </div>

                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{t('llm_settings_title')}</div>

                            <div style={styles.settingsGrid}>
                              <div style={styles.settingsField}>
                                <div style={styles.settingsLabel}>{t('mode')}</div>
                                <select
                                  style={styles.settingsInput}
                                  value={llmMode}
                                  onChange={(e) => setLlmMode(e.target.value)}
                                  disabled={settingsLoading}
                                >
                                  <option value="env">{t('server_default')}</option>
                                  <option value="api">{t('api_cloud')}</option>
                                  <option value="local">{t('local_ollama')}</option>
                                </select>
                              </div>

                              <div style={styles.settingsField}>
                                <div style={styles.settingsLabel}>{t('provider')}</div>
                                <select
                                  style={styles.settingsInput}
                                  value={llmProvider}
                                  onChange={(e) => setLlmProvider(e.target.value)}
                                  disabled={settingsLoading}
                                >
                                  {llmMode === 'local' ? (
                                    <option value="ollama">Ollama</option>
                                  ) : (
                                    <>
                                      <option value="openai">OpenAI</option>
                                      <option value="groq">Groq</option>
                                      <option value="gemini">Gemini</option>
                                    </>
                                  )}
                                </select>
                              </div>

                              <div style={styles.settingsField}>
                                <div style={styles.settingsLabel}>{t('model')}</div>
                                <input
                                  style={styles.settingsInput}
                                  value={llmModel}
                                  onChange={(e) => setLlmModel(e.target.value)}
                                  placeholder={llmMode === 'local' ? 'ex.: llama3.2' : 'ex.: gpt-4o-mini'}
                                  disabled={settingsLoading}
                                />
                              </div>

                              <div style={styles.settingsField}>
                                <div style={styles.settingsLabel}>{t('base_url')}</div>
                                <input
                                  style={styles.settingsInput}
                                  value={llmBaseUrl}
                                  onChange={(e) => setLlmBaseUrl(e.target.value)}
                                  placeholder={llmMode === 'local' ? 'http://localhost:11434' : 'opcional'}
                                  disabled={settingsLoading}
                                />
                              </div>

                              {llmMode === 'api' ? (
                                <div style={{ ...styles.settingsField, gridColumn: '1 / -1' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                                    <div style={styles.settingsLabel}>{t('api_key')}</div>
                                    <button
                                      style={styles.settingsSecondaryButton}
                                      onClick={() => {
                                        setLlmApiKeyOpen((v) => {
                                          const next = !v;
                                          if (!v && next) {
                                            setTimeout(() => {
                                              if (llmApiKeyInputRef.current) {
                                                try {
                                                  llmApiKeyInputRef.current.focus();
                                                } catch {}
                                              }
                                            }, 50);
                                          }
                                          return next;
                                        });
                                      }}
                                      disabled={settingsLoading}
                                    >
                                      {llmApiKeyOpen ? t('api_key_close') : (llmHasApiKey ? t('api_key_switch') : t('api_key_register'))}
                                    </button>
                                  </div>

                                  {llmApiKeyOpen ? (
                                    <input
                                      ref={llmApiKeyInputRef}
                                      style={styles.settingsInput}
                                      value={llmApiKey}
                                      onChange={(e) => setLlmApiKey(e.target.value)}
                                      placeholder={t('api_key_placeholder')}
                                      disabled={settingsLoading}
                                    />
                                  ) : (
                                    <div style={styles.settingsHint}>
                                      {llmHasApiKey
                                        ? (
                                          llmApiKeySource === 'env'
                                            ? t('llm_api_key_hint_env')
                                            : t('llm_api_key_hint_saved')
                                        )
                                        : t('llm_api_key_hint_none')}
                                    </div>
                                  )}
                                  <div style={styles.settingsHint}>
                                    {t('llm_api_key_hint_storage')}
                                  </div>
                                  <div style={styles.settingsHint}>
                                    {t('llm_api_key_warning_shared')}
                                  </div>
                                </div>
                              ) : null}
                            </div>

                            <div style={styles.settingsActions}>
                              {llmMode === 'api' ? (
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => {
                                    removeLlmApiKey();
                                  }}
                                  disabled={settingsLoading || (!llmHasStoredApiKey && llmHasEnvApiKey)}
                                >
                                  {(!llmHasStoredApiKey && llmHasEnvApiKey) ? t('llm_key_from_env') : t('llm_remove_key')}
                                </button>
                              ) : null}
                              <button
                                style={styles.settingsPrimaryButton}
                                onClick={saveLlmSettings}
                                disabled={settingsLoading}
                              >
                                {settingsLoading ? t('llm_saving') : t('save_llm')}
                              </button>
                            </div>
                          </div>

                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{t('configured_providers')}</div>
                            {providerStatusError ? (
                              <div style={styles.settingsError}>{providerStatusError}</div>
                            ) : null}
                            <div style={{ display: 'grid', gap: '6px', marginTop: '8px' }}>
                              {(providerStatusList || []).map((p) => {
                                const online = Boolean(p.online);
                                const enabled = Boolean(p.enabled);
                                const dotColor = enabled ? (online ? 'var(--green)' : 'var(--red)') : 'rgba(212,212,212,0.35)';
                                return (
                                  <div
                                    key={p.id || p.name}
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '10px',
                                      padding: '8px 0',
                                      borderBottom: '1px solid var(--border)',
                                      fontSize: '13px',
                                      fontFamily: 'var(--mono)'
                                    }}
                                  >
                                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: dotColor, flexShrink: 0 }} />
                                    <span>{p.name || p.id}</span>
                                    <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: enabled ? 'rgba(245,166,35,0.12)' : 'rgba(212,212,212,0.10)', color: enabled ? 'var(--amber)' : 'var(--text-dim)' }}>
                                      {enabled ? t('provider_enabled') : t('provider_disabled')}
                                    </span>
                                    <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: 'rgba(127,119,221,0.12)', color: '#7F77DD' }}>
                                      {t('provider_keys')}: {Number(p.keys_count) || 0}
                                    </span>
                                    <span style={{ marginLeft: 'auto', color: 'var(--text-dim)', fontSize: '11px' }}>
                                      {p.model || ''}
                                    </span>
                                  </div>
                                );
                              })}
                              {!providerStatusLoading && (!providerStatusList || providerStatusList.length === 0) ? (
                                <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                  {t('no_provider_status')}
                                </div>
                              ) : null}
                            </div>
                            <div style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={loadProviderStatus}
                                disabled={providerStatusLoading}
                              >
                                {providerStatusLoading ? 'Testando...' : 'Testar conexão'}
                              </button>
                            </div>
                          </div>
                        </>
                      ) : null}

                      {settingsTab === 'security' ? (
                        <div style={styles.settingsSection}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                            <div style={styles.settingsSectionTitle}>{t('agent_security')}</div>
                            <button
                              style={{
                                ...styles.smallIconButton,
                                width: '26px',
                                height: '26px',
                                borderRadius: '8px',
                                fontFamily: 'var(--mono)',
                                fontSize: '14px',
                                fontWeight: 700,
                                background: 'rgba(245,166,35,0.12)',
                                border: '1px solid rgba(245,166,35,0.35)',
                                color: 'var(--amber)'
                              }}
                              title={t('sandbox_help_tooltip')}
                              onClick={() => setGenericModal({
                                title: t('sandbox_help_title'),
                                body: [
                                  t('sandbox_help_line_1'),
                                  '',
                                  t('sandbox_help_body_off_title'),
                                  `- ${t('sandbox_help_off_1')}`,
                                  `- ${t('sandbox_help_off_2')}`,
                                  `- ${t('sandbox_help_off_3')}`,
                                  `- ${t('sandbox_help_off_4')}`,
                                  '',
                                  t('sandbox_help_body_on_title'),
                                  `- ${t('sandbox_help_on_1')}`,
                                  `- ${t('sandbox_help_on_2')}`,
                                  `- ${t('sandbox_help_on_3')}`,
                                  '',
                                  t('sandbox_help_privacy_title'),
                                  `- ${t('sandbox_help_privacy_1')}`,
                                  `- ${t('sandbox_help_privacy_2')}`,
                                ].join('\n')
                              })}
                            >
                              ?
                            </button>
                          </div>
                          <div style={styles.settingsHint}>{t('security_caps_warning')}</div>
                          <div style={styles.settingsGrid}>
                          <div style={styles.settingsField}>
                            <div style={{ ...styles.settingsLabel, display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span>{t('sandbox_mode')}</span>
                              <button
                                style={{
                                  ...styles.smallIconButton,
                                  width: '22px',
                                  height: '22px',
                                  borderRadius: '7px',
                                  fontFamily: 'var(--mono)',
                                  fontSize: '13px',
                                  fontWeight: 700,
                                  background: 'rgba(245,166,35,0.12)',
                                  border: '1px solid rgba(245,166,35,0.35)',
                                  color: 'var(--amber)'
                                }}
                                title={t('sandbox_help_tooltip')}
                                onClick={() => setGenericModal({
                                  title: t('sandbox_help_title'),
                                  body: [
                                    t('sandbox_help_line_1'),
                                    '',
                                    t('sandbox_help_body_off_title'),
                                    `- ${t('sandbox_help_off_1')}`,
                                    `- ${t('sandbox_help_off_2')}`,
                                    `- ${t('sandbox_help_off_3')}`,
                                    `- ${t('sandbox_help_off_4')}`,
                                    '',
                                    t('sandbox_help_body_on_title'),
                                    `- ${t('sandbox_help_on_1')}`,
                                    `- ${t('sandbox_help_on_2')}`,
                                    `- ${t('sandbox_help_on_3')}`,
                                    '',
                                    t('sandbox_help_privacy_title'),
                                    `- ${t('sandbox_help_privacy_1')}`,
                                    `- ${t('sandbox_help_privacy_2')}`,
                                  ].join('\n')
                                })}
                              >
                                ?
                              </button>
                            </div>
                            <select
                              style={styles.settingsInput}
                              value={securitySettings?.sandbox ? 'on' : 'off'}
                              onChange={(e) => {
                                const next = e.target.value === 'on';
                                applySecuritySettingChange({ sandbox: next }, { needsConfirm: next });
                              }}
                              disabled={settingsLoading}
                            >
                              <option value="off">{t('off')}</option>
                              <option value="on">{t('on')}</option>
                            </select>
                          </div>

                          {[
                            { key: 'allow_os_commands', label: t('allow_os_commands') },
                            { key: 'allow_file_write', label: t('allow_file_write') },
                            { key: 'allow_web_retrieval', label: t('allow_web_retrieval') },
                            { key: 'allow_connectors', label: t('allow_connectors') },
                            { key: 'allow_system_profile', label: t('allow_system_profile') }
                          ].map((row) => {
                            const isDisabled = Boolean(securitySettings?.sandbox) && row.key !== 'allow_system_profile';
                            const value = Boolean(securitySettings?.[row.key]) ? 'on' : 'off';
                            return (
                              <div key={row.key} style={styles.settingsField}>
                                <div style={styles.settingsLabel}>{row.label}</div>
                                <select
                                  style={styles.settingsInput}
                                  value={value}
                                  onChange={(e) => {
                                    const v = e.target.value === 'on';
                                    const needsConfirm = row.key === 'allow_file_write' && !v;
                                    applySecuritySettingChange({ [row.key]: v }, { needsConfirm });
                                  }}
                                  disabled={settingsLoading || isDisabled}
                                >
                                  <option value="off">{t('off')}</option>
                                  <option value="on">{t('on')}</option>
                                </select>
                              </div>
                            );
                          })}
                        </div>
                        <div style={styles.settingsHint}>
                          {t('last_updated')}: {securitySettingsUpdatedAt || '—'}
                        </div>
                        </div>
                      ) : null}

                      {settingsTab === 'connectors' ? (
                        <>
                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{t('connectors') || 'Conectores'}</div>
                            {connectorsLoading ? (
                              <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                {t('loading')}
                              </div>
                            ) : null}
                            <div style={styles.connectorGrid}>
                              {[
                                { key: 'github', name: 'GitHub' },
                                { key: 'google_drive', name: 'Google Drive' },
                                { key: 'google_calendar', name: 'Google Calendar' },
                                { key: 'gmail', name: 'Gmail' },
                                { key: 'telegram', name: 'Telegram' },
                                { key: 'tera', name: 'Tera' }
                              ].map((c) => {
                                const isConnected = Boolean(connectors?.[c.key]?.connected);
                                const dotStyle = { ...styles.connectorDot, background: isConnected ? 'var(--green)' : 'var(--red)' };
                                return (
                                  <div key={c.key} style={styles.connectorCard}>
                                    <div style={styles.connectorRow}>
                                      <div style={styles.connectorTitle}>
                                        <div style={dotStyle}></div>
                                        <div style={{ minWidth: 0 }}>
                                          <div style={{ fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600 }}>
                                            {c.name}
                                          </div>
                                          <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginTop: '4px' }}>
                                            {isConnected ? t('connected_ok') : t('not_connected')}
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                                      {!isConnected ? (
                                        <button
                                          style={styles.settingsPrimaryButton}
                                          onClick={() => openConnectorModal(c.key)}
                                        >
                                          {t('connect')}
                                        </button>
                                      ) : (
                                        <>
                                          {c.key === 'telegram' ? (
                                            <button
                                              style={styles.settingsSecondaryButton}
                                              onClick={createTelegramLinkCode}
                                            >
                                              {t('generate_code')}
                                            </button>
                                          ) : null}
                                          <button
                                            style={styles.settingsSecondaryButton}
                                            onClick={() => testConnector(c.key)}
                                          >
                                            {t('test')}
                                          </button>
                                          <button
                                            style={styles.settingsSecondaryButton}
                                            onClick={() => disconnectConnector(c.key)}
                                          >
                                            {t('disconnect')}
                                          </button>
                                        </>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>

                          <div style={styles.settingsSection}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                              <div style={styles.settingsSectionTitle}>{t('automation_client_external')}</div>
                              <button
                                style={{
                                  ...styles.smallIconButton,
                                  width: '26px',
                                  height: '26px',
                                  borderRadius: '8px',
                                  fontFamily: 'var(--mono)',
                                  fontSize: '14px',
                                  fontWeight: 700,
                                  background: 'rgba(245,166,35,0.12)',
                                  border: '1px solid rgba(245,166,35,0.35)',
                                  color: 'var(--amber)'
                                }}
                                title={t('automation_client_help_tooltip')}
                                onClick={() => setGenericModal({
                                  title: t('automation_client_help_title'),
                                  body: [
                                    t('automation_client_help_body_1'),
                                    t('automation_client_help_body_2'),
                                    '',
                                    t('automation_client_help_body_3')
                                  ].join('\n')
                                })}
                              >
                                ?
                              </button>
                            </div>
                            <div style={styles.settingsHint}>
                              {t('automation_client_hint')}
                            </div>
                            <div style={styles.settingsGrid}>
                              <div style={styles.settingsField}>
                                <div style={styles.settingsLabel}>{t('base_url')}</div>
                                <input
                                  style={styles.settingsInput}
                                  value={automationClientBaseUrl}
                                  onChange={(e) => setAutomationClientBaseUrl(e.target.value)}
                                  placeholder="https://example.com"
                                  disabled={settingsLoading}
                                />
                              </div>
                              <div style={styles.settingsField}>
                                <div style={styles.settingsLabel}>{t('api_key')}</div>
                                <input
                                  style={styles.settingsInput}
                                  value={automationClientApiKey}
                                  onChange={(e) => setAutomationClientApiKey(e.target.value)}
                                  placeholder={automationClientHasApiKey ? t('saved_keep') : t('paste_here')}
                                  type="password"
                                  disabled={settingsLoading}
                                />
                              </div>
                            </div>
                            <div style={styles.settingsActions}>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={() => {
                                  setGenericModal({
                                    title: t('automation_client_external'),
                                    body: t('remove_credential_question'),
                                    onConfirm: deleteAutomationClientSettings
                                  });
                                }}
                                disabled={settingsLoading}
                              >
                                {t('remove')}
                              </button>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={testAutomationClientSettings}
                                disabled={settingsLoading}
                              >
                                {t('test')}
                              </button>
                              <button
                                style={styles.settingsPrimaryButton}
                                onClick={() => saveAutomationClientSettings()}
                                disabled={settingsLoading || !String(automationClientBaseUrl || '').trim()}
                              >
                                {t('save')}
                              </button>
                            </div>
                          </div>
                        </>
                      ) : null}

                      {settingsTab === 'memory' ? (
                        <>
                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{t('system_profile_local')}</div>
                            <div style={styles.settingsHint}>
                              {t('system_profile_hint_1')}
                            </div>
                            <div style={styles.settingsHint}>
                              {t('system_profile_hint_2')}
                            </div>
                            {!systemProfileEnabled ? (
                              <div style={styles.settingsHint}>
                                {t('system_profile_feature_disabled')}
                              </div>
                            ) : null}
                            {!securitySettings?.allow_system_profile ? (
                              <div style={styles.settingsHint}>
                                {t('system_profile_disabled_by_security')}
                              </div>
                            ) : null}
                            {systemProfileError ? (
                              <div style={styles.settingsError}>{systemProfileError}</div>
                            ) : null}
                            <div style={styles.settingsActions}>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={deleteSystemProfile}
                                disabled={settingsLoading || !securitySettings?.allow_system_profile}
                              >
                                {t('remove')}
                              </button>
                              <button
                                style={styles.settingsPrimaryButton}
                                onClick={refreshSystemProfile}
                                disabled={settingsLoading || !systemProfileEnabled || !securitySettings?.allow_system_profile}
                              >
                                {settingsLoading ? t('updating') : t('update_profile')}
                              </button>
                            </div>
                            <div style={styles.settingsHint}>
                              {t('last_updated')}: {systemProfileUpdatedAt || '—'}
                            </div>
                            <textarea
                              style={{ ...styles.settingsTextarea, minHeight: '180px' }}
                              value={systemProfileMarkdown}
                              readOnly
                            />
                          </div>

                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{t('soul_user_profile')}</div>

                        <div style={styles.settingsGrid}>
                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>{t('name_label')}</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.name}
                              onChange={(e) => setSoulData(prev => ({ ...prev, name: e.target.value }))}
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>{t('age_range_label')}</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.age_range}
                              onChange={(e) => setSoulData(prev => ({ ...prev, age_range: e.target.value }))}
                              placeholder="e.g. 10–12, 13–15"
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Gender</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.gender}
                              onChange={(e) => setSoulData(prev => ({ ...prev, gender: e.target.value }))}
                              placeholder="e.g. female, male, prefer not to say"
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Education</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.education}
                              onChange={(e) => setSoulData(prev => ({ ...prev, education: e.target.value }))}
                              placeholder="e.g. primary, secondary, university"
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Interests</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.interests}
                              onChange={(e) => setSoulData(prev => ({ ...prev, interests: e.target.value }))}
                              placeholder="e.g. gaming, reading, science"
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Goals</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.goals}
                              onChange={(e) => setSoulData(prev => ({ ...prev, goals: e.target.value }))}
                              placeholder="e.g. learn maths, write better"
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>{t('learning_style_label')}</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.learning_style}
                              onChange={(e) => setSoulData(prev => ({ ...prev, learning_style: e.target.value }))}
                              placeholder="e.g. visual, examples, step-by-step"
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>{t('profile_language_label')}</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.language}
                              onChange={(e) => setSoulData(prev => ({ ...prev, language: e.target.value }))}
                              placeholder="en"
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>{t('audience_label')}</div>
                            <select
                              style={styles.settingsInput}
                              value={soulData.audience}
                              onChange={(e) => setSoulData(prev => ({ ...prev, audience: e.target.value }))}
                              disabled={settingsLoading}
                            >
                              <option value="">{t('not_set')}</option>
                              <option value="youth">{t('audience_youth')}</option>
                              <option value="adult">{t('audience_adult')}</option>
                              <option value="mixed">{t('audience_mixed')}</option>
                            </select>
                          </div>

                          <div style={{ ...styles.settingsField, gridColumn: '1 / -1' }}>
                            <div style={styles.settingsLabel}>{t('notes_label')}</div>
                            <textarea
                              style={styles.settingsTextarea}
                              value={soulData.notes}
                              onChange={(e) => setSoulData(prev => ({ ...prev, notes: e.target.value }))}
                              placeholder="Useful info for personalisation, tone of voice, limits, etc."
                              disabled={settingsLoading}
                            />
                          </div>
                        </div>

                        <div style={styles.settingsActions}>
                          <button
                            style={styles.settingsPrimaryButton}
                            onClick={saveSoul}
                            disabled={settingsLoading}
                          >
                            {settingsLoading ? t('llm_saving') : t('save_soul')}
                          </button>
                        </div>

                        <div style={{ height: '12px' }} />

                        <div style={styles.settingsSectionTitle}>{t('soul_updates')}</div>
                        <div style={styles.settingsField}>
                          <textarea
                            style={styles.settingsTextarea}
                            value={soulUpdate}
                            onChange={(e) => setSoulUpdate(e.target.value)}
                            placeholder="E.g. Prefers explanations with game examples. Currently studying for a science exam."
                            disabled={settingsLoading}
                          />
                          <div style={styles.settingsActions}>
                            <button
                              style={styles.settingsPrimaryButton}
                              onClick={appendSoulUpdate}
                              disabled={settingsLoading || !soulUpdate.trim()}
                            >
                              {settingsLoading ? t('llm_saving') : t('add_update')}
                            </button>
                          </div>
                        </div>

                        <div style={{ height: '12px' }} />

                        <div style={styles.settingsSectionTitle}>{t('soul_md_preview')}</div>
                        <textarea
                          style={{ ...styles.settingsTextarea, minHeight: '180px' }}
                          value={soulMarkdown}
                          readOnly
                        />
                          </div>
                        </>
                      ) : null}

                      {settingsTab === 'skills' ? (
                        <>
                          {customizeView === 'skill' ? (
                            (() => {
                              const selected = (skills || []).find((s) => s.id === selectedSkillId) || null;
                              const prompt = (() => {
                                if (!selected) return '';
                                const c = selected.content;
                                if (c && typeof c === 'object' && typeof c.prompt === 'string') return c.prompt;
                                if (typeof c === 'string') {
                                  const tt = c.trim();
                                  if (tt.startsWith('{') || tt.startsWith('[')) {
                                    try {
                                      const parsed = JSON.parse(tt);
                                      if (parsed && typeof parsed === 'object' && typeof parsed.prompt === 'string') return parsed.prompt;
                                    } catch {}
                                  }
                                }
                                return '';
                              })();
                              const readText = selected
                                ? (typeof selected.content === 'string'
                                  ? selected.content
                                  : JSON.stringify(selected.content ?? {}, null, 2))
                                : '';
                              return (
                                <div style={{ display: 'grid', gap: '12px' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                                    <button
                                      style={styles.settingsSecondaryButton}
                                      onClick={() => {
                                        setCustomizeView('home');
                                        setSelectedSkillId('');
                                        setSkillDraft('');
                                        setSkillEditMode(false);
                                      }}
                                    >
                                      ← {t('skills_center')}
                                    </button>
                                    {!skillEditMode ? (
                                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                        <button
                                          style={styles.settingsSecondaryButton}
                                          onClick={() => {
                                            if (!prompt) return;
                                            createTaskWithPrefill(prompt);
                                            setCenterView('chat');
                                          }}
                                          disabled={!selected || !prompt}
                                          title={!prompt ? (lang === 'pt' ? 'Esta skill não tem prompt de execução.' : 'This skill has no execution prompt.') : t('run_skill')}
                                        >
                                          {t('run_skill')}
                                        </button>
                                        <button
                                          style={styles.settingsPrimaryButton}
                                          onClick={() => {
                                            setSkillDraft(readText);
                                            setSkillEditMode(true);
                                          }}
                                          disabled={!selected}
                                        >
                                          {t('edit')}
                                        </button>
                                      </div>
                                    ) : (
                                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                        <button
                                          style={styles.settingsSecondaryButton}
                                          onClick={() => {
                                            setSkillDraft(readText);
                                            setSkillEditMode(false);
                                          }}
                                        >
                                          {t('cancel')}
                                        </button>
                                        <button
                                          style={styles.settingsPrimaryButton}
                                          onClick={() => {
                                            if (!selected) return;
                                            const raw = String(skillDraft || '').trim();
                                            let parsed = null;
                                            try {
                                              parsed = raw ? JSON.parse(raw) : {};
                                            } catch {
                                              setGenericModal({
                                                title: t('invalid_json_title'),
                                                body: t('invalid_json_body')
                                              });
                                              return;
                                            }
                                            const nextSkills = (skills || []).map((s) => (
                                              s.id === selected.id
                                                ? { ...s, content: parsed }
                                                : s
                                            ));
                                            setSkills(nextSkills);
                                            saveSkillsToBackend(nextSkills);
                                            setSkillEditMode(false);
                                          }}
                                          disabled={!selected}
                                        >
                                          {t('save')}
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                  {skillsSaveStatus ? (
                                    <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                      {skillsSaveStatus}
                                    </div>
                                  ) : null}
                                  <div style={{ ...styles.lightCard, padding: '14px' }}>
                                    <div style={styles.skillName}>{selected ? getSkillDisplayName(selected) : t('skills')}</div>
                                    {selected?.description ? (
                                      <div style={styles.skillDesc}>{getSkillDisplayDescription(selected)}</div>
                                    ) : null}
                                    <div style={{ marginTop: '12px' }}>
                                      <textarea
                                        style={styles.monoTextarea}
                                        value={skillEditMode ? skillDraft : readText}
                                        onChange={(e) => setSkillDraft(e.target.value)}
                                        readOnly={!skillEditMode}
                                      />
                                    </div>
                                  </div>
                                </div>
                              );
                            })()
                          ) : (
                            <div style={styles.settingsSection}>
                              <div style={styles.settingsSectionTitle}>{t('skills_center')}</div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                                <div style={styles.settingsHint}>
                                  {t('skills_hint_open')}
                                </div>
                                <button
                                  style={styles.settingsPrimaryButton}
                                  onClick={() => {
                                    createTaskWithPrefill(
                                      lang === 'pt'
                                        ? 'Crie uma nova skill. Faça perguntas para coletar os dados necessários (nome, propósito, entradas/saídas, exemplos) e gere a implementação. Ao final, valide com um checklist e sugira testes.'
                                        : 'Create a new skill. Ask questions to collect the needed data (name, purpose, inputs/outputs, examples) and generate an implementation. At the end, validate with a checklist and suggest tests.'
                                    );
                                  }}
                                >
                                  + {t('create_new_skill')}
                                </button>
                              </div>
                              <div style={{ marginTop: '12px', display: 'grid', gap: '14px' }}>
                                {(() => {
                                  const grouped = groupBySegment(skills || [], getSkillSegmentId);
                                  const labelMap = {
                                    system: t('segment_system'),
                                    admin: t('segment_admin'),
                                    finance: t('segment_finance'),
                                    marketing: t('segment_marketing'),
                                    it_devops: t('segment_it_devops'),
                                    other: t('segment_other'),
                                  };
                                  return segmentOrder
                                    .filter((seg) => (grouped?.[seg] || []).length)
                                    .map((seg) => (
                                      <div key={`skill-seg-${seg}`} style={{ display: 'grid', gap: '10px' }}>
                                        <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                          {labelMap[seg] || seg}
                                        </div>
                                        <div style={styles.skillGrid}>
                                          {sortSkillsForSegment((grouped?.[seg] || []), seg).map((s) => (
                                            <div
                                              key={s.id}
                                              style={styles.skillCard}
                                              onClick={() => {
                                                setSelectedSkillId(s.id);
                                                setCustomizeView('skill');
                                                const tt = typeof s.content === 'string' ? s.content : JSON.stringify(s.content ?? {}, null, 2);
                                                setSkillDraft(tt);
                                                setSkillEditMode(false);
                                              }}
                                              title={t('open_skill')}
                                            >
                                              <div style={styles.skillName}>{getSkillDisplayName(s)}</div>
                                              <div style={styles.skillDesc}>{getSkillDisplayDescription(s)}</div>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    ));
                                })()}
                              </div>
                            </div>
                          )}
                        </>
                      ) : null}

                      {settingsTab === 'team' ? (
                        <div style={styles.settingsSection}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                            <div style={styles.settingsSectionTitle}>{t('my_team')}</div>
                            <button
                              style={styles.settingsPrimaryButton}
                              onClick={async () => {
                                await createNewConversation();
                                setInput('');
                                const now = Date.now();
                                setMessages(prev => [
                                  ...prev,
                                  {
                                    role: 'assistant',
                                    content: t('create_agent_assistant_message'),
                                    id: `${now}-${Math.random().toString(16).slice(2)}`
                                  }
                                ]);
                                setCenterView('chat');
                              }}
                            >
                              {t('create_new_agent')}
                            </button>
                          </div>
                          <div style={styles.settingsHint}>{t('available_agents')}</div>
                          {experts.length === 0 ? (
                            <div style={styles.emptyState}>{t('no_agents')}</div>
                          ) : (
                            <div style={{ marginTop: '12px', display: 'grid', gap: '14px' }}>
                              {(() => {
                                const grouped = groupBySegment(experts || [], getExpertSegmentId);
                                const labelMap = {
                                  system: t('segment_system'),
                                  admin: t('segment_admin'),
                                  finance: t('segment_finance'),
                                  marketing: t('segment_marketing'),
                                  it_devops: t('segment_it_devops'),
                                  other: t('segment_other'),
                                };
                                return segmentOrder
                                  .filter((seg) => (grouped?.[seg] || []).length)
                                  .map((seg) => (
                                    <div key={`expert-seg-${seg}`} style={{ display: 'grid', gap: '10px' }}>
                                      <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                        {labelMap[seg] || seg}
                                      </div>
                                      <div style={{ display: 'grid', gap: '10px' }}>
                                        {sortExpertsForSegment((grouped?.[seg] || []), seg).map((e) => (
                                          <div key={e.id} style={{ ...styles.doctorCard, borderColor: 'rgba(255,255,255,0.08)' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                                              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                <div style={{ fontSize: '18px' }}>{e.icon}</div>
                                                <div>
                                                  <div style={{ fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600 }}>
                                                    {getExpertDisplayName(e)}
                                                  </div>
                                                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginTop: '4px' }}>
                                                    {getExpertDisplayDescription(e) || e.id}
                                                    {e.id === 'general' ? (lang === 'pt' ? ' • Orquestradora (padrão)' : ' • Orchestrator (default)') : ''}
                                                  </div>
                                                </div>
                                              </div>
                                              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                                <button
                                                  style={styles.settingsSecondaryButton}
                                                  onClick={() => {
                                                    const current = agentConfigs?.[e.id] || {};
                                                    setAgentConfigModal({
                                                      expertId: e.id,
                                                      expertName: getExpertDisplayName(e),
                                                      prompt: String(current?.prompt || '').trim(),
                                                      defaultSkillId: String(current?.default_skill_id || '').trim(),
                                                      skillIds: Array.isArray(current?.skill_ids) ? current.skill_ids : [],
                                                    });
                                                    setSettingsTab('agent_config');
                                                  }}
                                                >
                                                  {t('configure')}
                                                </button>
                                                <button
                                                  style={styles.settingsPrimaryButton}
                                                  onClick={() => {
                                                    setForceExpertId(e.id);
                                                    const defSkill = String(agentConfigs?.[e.id]?.default_skill_id || '').trim();
                                                    if (defSkill) setSelectedSkillId(defSkill);
                                                    setCenterView('chat');
                                                    setInput(lang === 'pt' ? `Quero falar com o agente ${getExpertDisplayName(e)}.` : `I want to talk to agent ${getExpertDisplayName(e)}.`);
                                                  }}
                                                >
                                                  {t('open_in_chat')}
                                                </button>
                                              </div>
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  ));
                              })()}
                            </div>
                          )}
                        </div>
                      ) : null}

                      {settingsTab === 'agent_config' ? (
                        <div style={styles.settingsSection}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                            <div style={styles.settingsSectionTitle}>
                              {`${t('configure')}: ${agentConfigModal?.expertName || agentConfigModal?.expertId || ''}`}
                            </div>
                            <button
                              style={styles.settingsSecondaryButton}
                              onClick={() => {
                                setAgentConfigModal(null);
                                setSettingsTab('team');
                              }}
                            >
                              ← {t('back')}
                            </button>
                          </div>

                          <div style={{ marginTop: '12px', display: 'grid', gap: '12px' }}>
                            <div style={styles.settingsField}>
                              <div style={styles.settingsLabel}>{t('agent_prompt')}</div>
                              <textarea
                                style={{ ...styles.settingsTextarea, minHeight: '180px' }}
                                value={String(agentConfigModal?.prompt || '')}
                                onChange={(e) => setAgentConfigModal((prev) => ({ ...(prev || {}), prompt: e.target.value }))}
                                placeholder={t('agent_prompt_placeholder')}
                              />
                            </div>

                            <div style={{ ...styles.settingsGrid, gridTemplateColumns: '1fr' }}>
                              <div style={styles.settingsField}>
                                <div style={styles.settingsLabel}>{t('default_skill')}</div>
                                <select
                                  style={styles.settingsInput}
                                  value={String(agentConfigModal?.defaultSkillId || '')}
                                  onChange={(e) => setAgentConfigModal((prev) => ({ ...(prev || {}), defaultSkillId: e.target.value }))}
                                >
                                  <option value="">{t('none')}</option>
                                  {(skills || []).map((s) => (
                                    <option key={s.id} value={s.id}>{getSkillDisplayName(s)}</option>
                                  ))}
                                </select>
                              </div>
                            </div>

                            <div style={styles.settingsField}>
                              <div style={styles.settingsLabel}>{t('agent_skills')}</div>
                              <div style={{ display: 'grid', gap: '12px' }}>
                                {(() => {
                                  const current = new Set(Array.isArray(agentConfigModal?.skillIds) ? agentConfigModal.skillIds : []);
                                  const grouped = groupBySegment(skills || [], getSkillSegmentId);
                                  const labelMap = {
                                    system: t('segment_system'),
                                    admin: t('segment_admin'),
                                    finance: t('segment_finance'),
                                    marketing: t('segment_marketing'),
                                    it_devops: t('segment_it_devops'),
                                    other: t('segment_other'),
                                  };
                                  return segmentOrder.map((seg) => {
                                    const list = sortSkillsForSegment((grouped?.[seg] || []), seg);
                                    if (!list.length) return null;
                                    return (
                                      <div key={`agent-tab-skill-seg-${seg}`} style={{ display: 'grid', gap: '8px' }}>
                                        <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                          {labelMap[seg] || seg}
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px' }}>
                                          {list.map((s) => {
                                            const checked = current.has(s.id);
                                            return (
                                              <label
                                                key={s.id}
                                                style={{
                                                  display: 'flex',
                                                  alignItems: 'flex-start',
                                                  gap: '8px',
                                                  padding: '10px 12px',
                                                  borderRadius: '10px',
                                                  border: '1px solid var(--border)',
                                                  background: 'var(--bg3)',
                                                  cursor: 'pointer',
                                                  userSelect: 'none'
                                                }}
                                              >
                                                <input
                                                  type="checkbox"
                                                  checked={checked}
                                                  onChange={(e) => {
                                                    const next = new Set(Array.isArray(agentConfigModal?.skillIds) ? agentConfigModal.skillIds : []);
                                                    if (e.target.checked) next.add(s.id);
                                                    else next.delete(s.id);
                                                    setAgentConfigModal((prev) => ({ ...(prev || {}), skillIds: Array.from(next) }));
                                                  }}
                                                  style={{ marginTop: '2px' }}
                                                />
                                                <div style={{ minWidth: 0 }}>
                                                  <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600 }}>
                                                    {getSkillDisplayName(s)}
                                                  </div>
                                                  {s.description ? (
                                                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginTop: '4px' }}>
                                                      {getSkillDisplayDescription(s)}
                                                    </div>
                                                  ) : null}
                                                </div>
                                              </label>
                                            );
                                          })}
                                        </div>
                                      </div>
                                    );
                                  });
                                })()}
                              </div>
                            </div>

                            <div style={{ ...styles.commandActions, justifyContent: 'space-between' }}>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={() => {
                                  const expertId = String(agentConfigModal?.expertId || '').trim();
                                  if (!expertId) {
                                    setAgentConfigModal(null);
                                    setSettingsTab('team');
                                    return;
                                  }
                                  setAgentConfigs((prev) => {
                                    const next = { ...(prev || {}) };
                                    delete next[expertId];
                                    return next;
                                  });
                                  setAgentConfigModal(null);
                                  setSettingsTab('team');
                                }}
                              >
                                {t('reset')}
                              </button>
                              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => {
                                    setAgentConfigModal(null);
                                    setSettingsTab('team');
                                  }}
                                >
                                  {t('cancel')}
                                </button>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => {
                                    setSettingsTab('skills');
                                  }}
                                >
                                  {t('skills_center')}
                                </button>
                                <button
                                  style={styles.settingsPrimaryButton}
                                  onClick={() => {
                                    const expertId = String(agentConfigModal?.expertId || '').trim();
                                    if (!expertId) {
                                      setAgentConfigModal(null);
                                      setSettingsTab('team');
                                      return;
                                    }
                                    const prompt = String(agentConfigModal?.prompt || '').trim();
                                    const defaultSkillId = String(agentConfigModal?.defaultSkillId || '').trim();
                                    const skillIds = Array.isArray(agentConfigModal?.skillIds) ? agentConfigModal.skillIds : [];
                                    setAgentConfigs((prev) => ({
                                      ...(prev || {}),
                                      [expertId]: {
                                        prompt,
                                        default_skill_id: defaultSkillId,
                                        skill_ids: skillIds,
                                      }
                                    }));
                                    setAgentConfigModal(null);
                                    setSettingsTab('team');
                                  }}
                                >
                                  {t('save')}
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : (
                    <>
                      <div style={styles.chatToolbar}>
                        <div style={styles.toolbarTitleRow}>
                          <div style={styles.toolbarTitleText}>
                            {currentConversation ? `${currentKind === 'task' ? t('task_label') : t('conversation_label')} #${currentConversation}` : t('chat')}
                          </div>
                        </div>
                        {currentConversation ? (
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <button
                              style={styles.smallIconButton}
                              onClick={() => setChatFontScale((v) => clamp(Number(v || 1) - 0.1, 0.8, 1.5))}
                              title={t('decrease_font')}
                            >
                              -
                            </button>
                            <button
                              style={styles.smallIconButton}
                              onClick={() => setChatFontScale((v) => clamp(Number(v || 1) + 0.1, 0.8, 1.5))}
                              title={t('increase_font')}
                            >
                              +
                            </button>
                            <input
                              style={styles.chatSearchInput}
                              value={chatSearch}
                              onChange={(e) => setChatSearch(e.target.value)}
                              placeholder={t('search_chat_placeholder')}
                            />
                            {chatSearch.trim() ? (
                              <button style={styles.chatSearchClear} onClick={() => setChatSearch('')}>
                                {t('clear')}
                              </button>
                            ) : null}
                          </div>
                        ) : null}
                      </div>
                      <div style={styles.messagesContainer}>
                        {currentConversation && currentKind === 'task' ? (
                          <div style={{ maxWidth: '920px', width: '100%', margin: '0 auto 12px auto' }}>
                            <div style={{ ...styles.lightCard, border: '1px solid rgba(255,255,255,0.10)' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                                <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                  {t('todos')}
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                  <button
                                    style={styles.settingsSecondaryButton}
                                    onClick={() => setShowTaskDoneTodos((v) => !v)}
                                  >
                                    {showTaskDoneTodos ? t('hide_done') : t('show_done')}
                                  </button>
                                  <button
                                    style={styles.settingsSecondaryButton}
                                    onClick={() => loadTaskTodos(currentConversation)}
                                    disabled={taskTodosLoading}
                                  >
                                    {taskTodosLoading ? '...' : t('refresh')}
                                  </button>
                                </div>
                              </div>

                              <div style={{ marginTop: '10px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                <input
                                  style={{ ...styles.settingsInput, flex: 1, minWidth: '200px' }}
                                  value={taskTodoDraft}
                                  onChange={(e) => setTaskTodoDraft(e.target.value)}
                                  placeholder={t('todo_placeholder')}
                                  disabled={taskTodosLoading}
                                />
                                <button
                                  style={styles.settingsPrimaryButton}
                                  disabled={taskTodosLoading || !taskTodoDraft.trim()}
                                  onClick={async () => {
                                    const ok = await addTaskTodo(currentConversation, taskTodoDraft);
                                    if (ok) setTaskTodoDraft('');
                                  }}
                                >
                                  {t('add_todo')}
                                </button>
                              </div>

                              <div style={{ marginTop: '10px', display: 'grid', gap: '8px' }}>
                                {(() => {
                                  const filtered = (taskTodos || [])
                                    .filter((td) => showTaskDoneTodos ? true : String(td.status || '').toLowerCase() !== 'done');
                                  const roots = buildTodoTree(filtered);
                                  const renderNode = (node, depth) => {
                                    const isDone = String(node.status || '').toLowerCase() === 'done';
                                    const artifacts = getTodoArtifacts(node);
                                    const deliveryPath = String(node.delivery_path || '').trim();
                                    return (
                                      <div key={node.id} style={{ display: 'grid', gap: '6px' }}>
                                        <div
                                          style={{
                                            display: 'flex',
                                            gap: '10px',
                                            alignItems: 'flex-start',
                                            padding: '8px 10px',
                                            borderRadius: '10px',
                                            border: '1px solid var(--border)',
                                            background: 'var(--bg3)',
                                            marginLeft: `${Math.min(6, Math.max(0, depth)) * 14}px`
                                          }}
                                        >
                                          <button
                                            style={{
                                              ...styles.smallIconButton,
                                              opacity: isDone ? 0.4 : 1
                                            }}
                                            disabled={isDone}
                                            onClick={() => markTaskTodoDone(currentConversation, node.id)}
                                            title={t('completed')}
                                          >
                                            ✓
                                          </button>
                                          <div style={{ flex: 1, minWidth: 0 }}>
                                            <div
                                              style={{
                                                fontSize: '13px',
                                                color: 'var(--text)',
                                                fontFamily: 'var(--sans)',
                                                textDecoration: isDone ? 'line-through' : 'none',
                                                opacity: isDone ? 0.7 : 1,
                                                wordBreak: 'break-word'
                                              }}
                                            >
                                              {node.text || ''}
                                            </div>
                                            {(deliveryPath || (artifacts && artifacts.length)) ? (
                                              <div style={{ marginTop: '6px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                                {deliveryPath ? (
                                                  <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: 'rgba(245,166,35,0.10)', color: 'var(--amber)', fontFamily: 'var(--mono)' }} title={deliveryPath}>
                                                    {truncatePath(deliveryPath)}
                                                  </span>
                                                ) : null}
                                                {(artifacts || []).slice(0, 6).map((a, i) => {
                                                  const url = String(a?.url || '').trim();
                                                  const name = String(a?.name || a?.id || `artifact-${i}`);
                                                  if (!url) {
                                                    return (
                                                      <span key={`${name}-${i}`} style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: 'rgba(127,119,221,0.12)', color: '#7F77DD', fontFamily: 'var(--mono)' }}>
                                                        {name}
                                                      </span>
                                                    );
                                                  }
                                                  return (
                                                    <button
                                                      key={`${name}-${i}`}
                                                      style={{ ...styles.settingsSecondaryButton, padding: '3px 8px', fontSize: '10px', fontFamily: 'var(--mono)' }}
                                                      onClick={() => window.open(url, '_blank')}
                                                      title={name}
                                                    >
                                                      {name}
                                                    </button>
                                                  );
                                                })}
                                              </div>
                                            ) : null}
                                            <div style={{ marginTop: '2px', fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                              {node.created_at ? formatCompactDateTime(node.created_at) : ''}
                                            </div>
                                          </div>
                                        </div>
                                        {(node.children || []).map((ch) => renderNode(ch, depth + 1))}
                                      </div>
                                    );
                                  };
                                  return roots.map((r) => renderNode(r, 0));
                                })()}
                                {(!taskTodos || taskTodos.length === 0) ? (
                                  <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                    {t('no_todos')}
                                  </div>
                                ) : null}
                              </div>
                            </div>
                          </div>
                        ) : null}
                        {!currentConversation && !chatSearch.trim() && messages.length === 0 && !streaming ? (
                          <div style={{ maxWidth: '920px', width: '100%', margin: '0 auto' }}>
                            <div style={{ ...styles.lightCard, border: '1px solid rgba(255,255,255,0.10)' }}>
                              <pre
                                style={{
                                  fontFamily: OPEN_SLAP_ASCII_FONT,
                                    fontSize: isMobile ? '10px' : '12px',
                                  lineHeight: 1.35,
                                  whiteSpace: 'pre',
                                  fontVariantLigatures: 'none',
                                  letterSpacing: '0',
                                  color: 'var(--text)',
                                  opacity: 0.95,
                                  overflowX: 'auto',
                                  maxWidth: '100%',
                                    width: '100%',
                                  margin: 0
                                }}
                              >
                                {OPEN_SLAP_ASCII}
                              </pre>
                              <div style={{ marginTop: '12px', fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
                                Open Slap! é um core agêntico open source e gratuito para organizar tarefas, planejar projetos e executar fluxos com múltiplos agentes.
                              </div>
                              <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                Exemplos práticos (clique para preencher):
                              </div>
                              <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => startNewConversationWithPrompt('Quero que você organize minhas tarefas pendentes. Vou listar agora e você transforma em um TODO com prioridades.')}
                                >
                                  Assistente pessoal (tarefas)
                                </button>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => startNewConversationWithPrompt(buildAgentsHelpPrompt())}
                                >
                                  Ver agentes disponíveis
                                </button>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => startNewConversationWithPrompt(buildHelpHowItWorksPrompt())}
                                >
                                  Como o sistema funciona
                                </button>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => startNewConversationWithPrompt(buildHelpSettingsPrompt())}
                                >
                                  Configurar o sistema (Settings)
                                </button>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => startNewConversationWithPrompt(buildHelpProjectsPrompt())}
                                >
                                  Criar projetos no sistema
                                </button>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => startNewConversationWithPrompt(buildHelpFAQPrompt())}
                                >
                                  Dúvidas gerais (FAQ)
                                </button>
                                <button
                                  style={{ ...styles.settingsSecondaryButton, background: '#fff', color: '#000', border: '1px solid rgba(0,0,0,0.15)' }}
                                  onClick={() => window.open('https://aistudio.google.com/app/apikey', '_blank')}
                                >
                                  Obter chave Gemini
                                </button>
                                <button
                                  style={{ ...styles.settingsSecondaryButton, background: '#fff', color: '#000', border: '1px solid rgba(0,0,0,0.15)' }}
                                  onClick={() => window.open('https://console.groq.com/keys', '_blank')}
                                >
                                  Obter chave Groq
                                </button>
                              </div>
                              <div style={{ marginTop: '12px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                <button
                                  style={styles.settingsPrimaryButton}
                                  onClick={() => startNewConversationWithPrompt('Quero começar. Me faça perguntas rápidas e organize o que for necessário.')}
                                >
                                  {t('new_conversation')}
                                </button>
                                <button
                                  style={{
                                    ...styles.settingsSecondaryButton,
                                    background: '#ffffff',
                                    color: '#000000',
                                    border: '1px solid rgba(0,0,0,0.15)'
                                  }}
                                  onClick={() => window.open(OPEN_SLAP_REPO_URL, '_blank')}
                                >
                                  GitHub — conheça o projeto
                                </button>
                              </div>
                            </div>
                          </div>
                        ) : null}
                        {(chatSearch.trim()
                          ? messages.filter((m) => (m.content || '').toLowerCase().includes(chatSearch.trim().toLowerCase()))
                          : messages
                        ).map(message => (
                          <div
                            key={message.id}
                            style={{
                              ...styles.message,
                              ...(message.role === 'user' ? styles.messageUser : {})
                            }}
                          >
                            <div
                              style={{
                                ...styles.messageAvatar,
                                background: message.role === 'user' ? 'var(--amber)' : 'var(--bg3)',
                                color: message.role === 'user' ? 'var(--bg)' : 'var(--text)'
                              }}
                            >
                              {message.role === 'user' ? '👤' : (
                                <img
                                  src={AGENT_AVATAR_SRC}
                                  alt="Agente"
                                  style={styles.messageAvatarImg}
                                />
                              )}
                            </div>
                            <div style={styles.messageContent}>
                              <div
                                style={{
                                  ...styles.messageBubble,
                                  fontSize: `${Math.round(14 * chatFontScale)}px`,
                                  ...(message.role === 'user' ? styles.messageBubbleUser : {})
                                }}
                              >
                                {message.role === 'assistant' && !message.streaming ? (
                                  (() => {
                                    const parsed = parseCommandRequestsFromContent(message.content || '');
                                    const blocks = parseMessageBlocks(parsed.text || '');
                                    const cliBlocks = [];
                                    if (message?.cli) cliBlocks.push(message.cli);
                                    if (message?.cli_runs && typeof message.cli_runs === 'object') {
                                      try {
                                        for (const v of Object.values(message.cli_runs || {})) {
                                          if (v && typeof v === 'object') cliBlocks.push(v);
                                        }
                                      } catch {}
                                    }
                                    return (
                                      <>
                                        {blocks?.length ? (
                                          <div style={{ display: 'grid', gap: '8px' }}>
                                            {blocks.map((b, idx) => (
                                              <MessageBlock
                                                key={`${b.type || 'text'}-${idx}`}
                                                block={b}
                                                onApprovePlan={(tasks) => {
                                                  if (!currentConversation) return;
                                                  const passed = Array.isArray(tasks) ? tasks : [];
                                                  const fallback = (pendingPlanTasksRef.current || {})[String(currentConversation)] || [];
                                                  const tlist = passed.length ? passed : (Array.isArray(fallback) ? fallback : []);
                                                  if (!tlist.length) return;
                                                  setShowExecutionPanel(true);
                                                  setActivePlanMessageId(message.message_id || null);
                                                  setActivePlanLocalMsgId(message.id || null);
                                                  approvePlan(currentConversation, tlist).then((ok) => {
                                                    if (!ok) return;
                                                    const hasExecutable = tlist.some(t => String(t?.skill_id || '').trim());
                                                    if (hasExecutable && orchStatus !== 'running') startOrchestration(currentConversation);
                                                  }).catch(() => {});
                                                }}
                                              />
                                            ))}
                                          </div>
                                        ) : null}
                                        {parsed.requests?.length ? (
                                          <div>
                                            {parsed.requests.map((req, i) => {
                                              const rid = req?.id || `noid-${i}`;
                                              const isExecuting = Boolean(executingCommandId && executingCommandId === rid);
                                              const isExecuted = Boolean(executedCommandIds[rid]);
                                              const disabled = isExecuted || isExecuting;
                                              return (
                                                <div key={rid} style={styles.commandCard}>
                                                  <div style={styles.commandTitle}>
                                                    {req.title || 'Solicitação de comando'} • {riskLabel(req.risk_level)}
                                                  </div>
                                                  <div style={styles.commandMeta}>
                                                    {req.intent ? `Motivo: ${req.intent}\n` : ''}
                                                    {req.cwd ? `CWD: ${req.cwd}\n` : ''}
                                                    {req.command ? `\n${req.command}` : ''}
                                                  </div>
                                                  {req.id ? (
                                                    <div style={styles.commandActions}>
                                                      <button
                                                        style={styles.settingsPrimaryButton}
                                                        onClick={() => openCommandModal(req)}
                                                        disabled={disabled}
                                                      >
                                                        {isExecuted ? 'Executado' : 'Executar'}
                                                      </button>
                                                      <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                                        {req.requires_confirmation ? 'Requer confirmação' : 'Livre'}
                                                      </div>
                                                    </div>
                                                  ) : (
                                                    <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                                      Aguardando o servidor gerar uma solicitação pendente.
                                                    </div>
                                                  )}
                                                </div>
                                              );
                                            })}
                                          </div>
                                        ) : null}
                                        {cliBlocks.length ? (
                                          <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                            {cliBlocks.map((cli, i) => (
                                              <CLIDisplay key={`cli-${i}-${cli?.command_executed || cli?.command || ''}`} payload={cli} />
                                            ))}
                                          </div>
                                        ) : null}
                                      </>
                                    );
                                  })()
                                ) : (
                                  (() => {
                                    if (message.role !== 'assistant' || !message.streaming) return message.content;
                                    const base = (message.content || '').trim();
                                    if (base) return message.content;
                                    const dots = '.'.repeat((loadingTick % 4) + 1);
                                    const status = (streamStatusText || 'Processando').trim();
                                    return `${status}${dots}`;
                                  })()
                                )}
                                {message.expert && !message.streaming && (
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                                    <div style={styles.expertTag} title={showRoutingDebug ? (message?.expert_reason || '') : ''}>
                                      <span style={styles.expertIcon}>{message.expert.icon}</span>
                                      <span>{message.expert.name}</span>
                                      {message.provider && (
                                        <span style={{ marginLeft: '8px', fontSize: '10px' }}>
                                          {message.provider} • {message.model}
                                        </span>
                                      )}
                                      {showRoutingDebug && message?.expert_reason && (
                                        <span style={{ marginLeft: '6px', fontSize: '10px', opacity: 0.6 }}>
                                          · {message.expert_reason}
                                        </span>
                                      )}
                                    </div>
                                    {message.message_id && (
                                      <div style={{ display: 'flex', gap: '4px' }}>
                                        {[1, -1].map(rating => {
                                          const current = messageFeedback[message.message_id];
                                          const isActive = current === rating;
                                          return (
                                            <button
                                              key={rating}
                                              onClick={() => postFeedback(message.message_id, rating)}
                                              style={{
                                                background: isActive
                                                  ? (rating === 1 ? 'rgba(74,222,128,0.2)' : 'rgba(248,113,113,0.2)')
                                                  : 'transparent',
                                                border: `1px solid ${isActive
                                                  ? (rating === 1 ? 'var(--green)' : 'var(--red)')
                                                  : 'var(--border)'}`,
                                                borderRadius: '6px',
                                                padding: '2px 7px',
                                                cursor: 'pointer',
                                                fontSize: '13px',
                                                color: isActive
                                                  ? (rating === 1 ? 'var(--green)' : 'var(--red)')
                                                  : 'var(--text-dim)',
                                                transition: 'all 0.15s',
                                              }}
                                              title={rating === 1 ? 'Helpful' : 'Not helpful'}
                                            >
                                              {rating === 1 ? '👍' : '👎'}
                                            </button>
                                          );
                                        })}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                              {(centerView === 'chat'
                                && planTasks.length > 0
                                && currentConversation
                                && activePlanConvId
                                && Number(currentConversation) === Number(activePlanConvId)
                                && message.role === 'assistant'
                                && !message.streaming
                                && (
                                  (activePlanMessageId && Number(message.message_id) === Number(activePlanMessageId))
                                  || (activePlanLocalMsgId && String(message.id) === String(activePlanLocalMsgId))
                                )
                              ) ? (
                                showExecutionPanel ? (
                                  <div style={{
                                    margin: '10px 0 0 0',
                                    padding: '10px 12px',
                                    background: 'var(--bg3)',
                                    border: orchStatus === 'running' ? '1px solid var(--accent)' : '1px solid var(--border)',
                                    borderRadius: '10px'
                                  }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                                      <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text-dim)', letterSpacing: '0.04em' }}>
                                        EXECUÇÃO • {orchStatus === 'running' ? 'em andamento' : orchStatus === 'completed' ? 'concluída' : orchStatus === 'failed' ? 'falhou' : 'pendente'}
                                      </div>
                                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                        {orchLog.length > 0 ? (
                                          <button
                                            style={{ ...styles.settingsSecondaryButton, padding: '6px 10px', fontSize: '11px' }}
                                            onClick={() => setGenericModal({
                                              title: 'Log de orquestração',
                                              body: orchLog.map(l => `[${l.status}] ${l.msg}`).join('\n')
                                            })}
                                          >
                                            Ver log
                                          </button>
                                        ) : null}
                                        <button
                                          style={{ ...styles.settingsSecondaryButton, padding: '6px 10px', fontSize: '11px' }}
                                          onClick={() => setShowExecutionPanel(false)}
                                        >
                                          Ocultar
                                        </button>
                                      </div>
                                    </div>
                                    <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                      {planTasks.map((task) => {
                                        const isRunningNow = orchStatus === 'running' && orchLog.some(l => l.task_id === task.id && l.status === 'active');
                                        return (
                                          <div key={`exec-${task.id}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <div style={{ width: '18px', textAlign: 'center', fontFamily: 'var(--mono)', color: isRunningNow ? 'var(--accent)' : task.status === 'done' ? 'var(--green)' : 'var(--text-dim)' }}>
                                              {task.status === 'done' ? '✓' : isRunningNow ? '⚙' : '○'}
                                            </div>
                                            <div style={{ flex: 1, fontSize: '12px', color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={task.title}>
                                              {task.title}
                                            </div>
                                            {task.skill_id ? (
                                              <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', color: 'var(--accent)', opacity: 0.75 }}>
                                                {String(task.skill_id).split('-')[0]}
                                              </div>
                                            ) : null}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </div>
                                ) : (
                                  <div style={{ margin: '10px 0 0 0', display: 'flex', justifyContent: 'flex-end' }}>
                                    <button
                                      style={{ ...styles.settingsSecondaryButton, padding: '6px 10px', fontSize: '11px' }}
                                      onClick={() => setShowExecutionPanel(true)}
                                    >
                                      Mostrar execução
                                    </button>
                                  </div>
                                )
                              ) : null}
                              {(() => {
                                const ts = getMessageTimestamp(message);
                                const label = formatCompactDateTime(ts);
                                if (!label || message.streaming) return null;
                                return (
                                  <div
                                    style={{
                                      ...styles.messageTimestamp,
                                      textAlign: message.role === 'user' ? 'right' : 'left'
                                    }}
                                  >
                                    {label}
                                  </div>
                                );
                              })()}
                            </div>
                          </div>
                        ))}
                        <div ref={messagesEndRef} />
                      </div>

                      {currentConversation ? (
                        <div style={styles.inputArea}>
                          <div style={styles.inputContainer}>
                            <div style={styles.inputWrapper}>
                              <textarea
                                style={{ ...styles.input, fontSize: `${Math.round(14 * chatFontScale)}px` }}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={t('search_chat_placeholder') || "Type your message…"}
                            disabled={!connected}
                              />
                            </div>
                            <button
                              style={{
                                ...styles.sendButton,
                                ...(streaming || !connected ? styles.sendButtonDisabled : {})
                              }}
                              onClick={sendMessage}
                              disabled={streaming || !connected}
                            >
                              {streaming ? '⏳' : `🚀 ${t('send') || 'Send'}`}
                            </button>
                          </div>
                        </div>
                      ) : null}
                    </>
                  )}
                </div>
              </div>
            </div>
          )
        } />
      </Routes>
    </Router>
  );
};

export default App;
