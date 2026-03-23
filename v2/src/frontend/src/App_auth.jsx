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
  const sessionId = useRef(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [centerView, setCenterView] = useState('chat');
  const [chatSearch, setChatSearch] = useState('');
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsError, setSettingsError] = useState('');
  const [llmMode, setLlmMode] = useState('env');
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [llmModel, setLlmModel] = useState('');
  const [llmBaseUrl, setLlmBaseUrl] = useState('');
  const [llmApiKey, setLlmApiKey] = useState('');
  const [llmHasApiKey, setLlmHasApiKey] = useState(false);
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
  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 640;
  const [conversationSearch, setConversationSearch] = useState('');
  const [tasksSearch, setTasksSearch] = useState('');
  const [conversationSearchResults, setConversationSearchResults] = useState([]);
  const [tasksSearchResults, setTasksSearchResults] = useState([]);
  const [globalTodos, setGlobalTodos] = useState([]);
  const [renameModal, setRenameModal] = useState(null);
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
  // Plan→build
  const [planTasks, setPlanTasks] = useState([]);       // [{id, title, skill_id, status}]
  const [activePlanConvId, setActivePlanConvId] = useState(null);
  // Message feedback
  const [messageFeedback, setMessageFeedback] = useState({}); // {message_id: 1|-1}
  // MoE expert override
  const [forceExpertId, setForceExpertId] = useState('');
  const [lastExpertReason, setLastExpertReason] = useState('');
  const [lastExpertKeywords, setLastExpertKeywords] = useState([]);
  // Onboarding
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  // Projects
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(null);
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
      cancel: 'Cancelar',
      confirm: 'Confirmar',
      language: 'Idioma',
      connector_token_label: 'Token',
      connector_token_placeholder: 'Cole aqui o token',
      github_token_help: 'Personal access token do GitHub (classic ou fine-grained).',
      google_token_help: 'Access token OAuth do Google (Bearer).',
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
      create_new_skill: 'Criar nova skill'
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
      cancel: 'Cancel',
      confirm: 'Confirm',
      language: 'Language',
      connector_token_label: 'Token',
      connector_token_placeholder: 'Paste the token here',
      github_token_help: 'GitHub personal access token (classic or fine-grained).',
      google_token_help: 'Google OAuth access token (Bearer).',
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
      create_new_skill: 'Create new skill'
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
      create_new_skill: 'Crear nueva skill'
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
  const t = (key) => {
    const table = translations[lang] || translations.pt;
    return table[key] || translations.pt[key] || key;
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
      flexDirection: 'column'
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
      background: 'rgba(255,255,255,0.04)',
      borderColor: 'rgba(255,255,255,0.08)'
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
    sidebarDonateArea: {
      marginTop: 'auto',
      padding: '16px',
      display: 'grid',
      gap: '10px'
    },
    sidebarLogo: {
      width: '100%',
      maxWidth: '160px',
      height: 'auto',
      display: 'block',
      objectFit: 'contain'
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
      fetch('/api/experts')
        .then(res => res.json())
        .then(data => setExperts(data.experts || []))
        .catch(err => console.error('Error loading agents:', err));
    }
  }, [user, token]);

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
      localStorage.setItem('open_slap_lang_v1', String(lang || 'pt'));
    } catch {}
    try {
      document.documentElement.lang = lang === 'pt' ? 'pt-BR' : lang;
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    } catch {}
  }, [lang]);

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
            'You are acting as CTO. When the user describes a project or challenge:\n' +
            '1. PLAN: ask clarifying questions, map requirements, constraints and risks.\n' +
            '   When you have enough information, output the structured plan followed IMMEDIATELY by a task breakdown in this exact format:\n' +
            '   ```plan\n' +
            '   Task title | skill_id\n' +
            '   Task title | skill_id\n' +
            '   ```\n' +
            '   Valid skill_ids: cto, project-manager, systems-architect, backend-dev, frontend-dev, devops, security, code-review, tests, excel-expert, seo, marketing, chat-assistant\n' +
            '   Omit skill_id column if no specific skill applies.\n' +
            '2. BUILD: after the plan is approved by the user, orchestrate execution — track progress, flag blockers, coordinate between skills.\n' +
            'Always reason out loud before deciding. Prefer incremental delivery. Flag security and scalability concerns early.'
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
            'You are acting as Backend Developer.\n' +
            'Ask for: language/framework, DB, auth method, scale expectations.\n' +
            'Deliver: working code with error handling, input validation, tests and a brief explanation of design decisions.\n' +
            'Flag security concerns (injection, secrets exposure, auth bypass) before finalising.'
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
            'You are acting as Frontend Developer.\n' +
            'Ask for: target browsers, design system, accessibility requirements, state complexity.\n' +
            'Deliver: component code, styling approach, responsive behaviour and a11y notes.\n' +
            'Prefer semantic HTML and progressively enhanced interactions.'
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
            'You are acting as DevOps Engineer.\n' +
            'Ask for: cloud/on-prem, current stack, team size, compliance needs.\n' +
            'Deliver: pipeline config, Dockerfile or compose, monitoring strategy and rollback plan.\n' +
            'Always separate secrets from code. Prefer immutable artefacts.'
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
            'You are acting as Security Reviewer.\n' +
            'For the system or code described: identify threats (STRIDE), classify by severity (Critical/High/Medium/Low), and propose mitigations with effort estimate.\n' +
            'Check: auth flows, input validation, secrets handling, dependency risk, logging of sensitive data.'
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
            '4. Suggest 2–3 test prompts to validate the skill before saving.'
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

      await fetchDoctorReport({ silent: true });
    } catch (error) {
      setSettingsError('Could not load settings.');
    } finally {
      setSettingsLoading(false);
    }
  };

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
      setLlmHasApiKey(Boolean(json?.has_api_key));
    } catch (e) {
      setSettingsError('Could not remove the key.');
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
      }
      setLlmHasApiKey(Boolean(json?.has_api_key));
      setStoredLlmPrefs({
        mode: payload.mode,
        provider: payload.provider,
        model: payload.model,
        base_url: payload.base_url
      });
      setLlmProvider(payload.provider);
      setLlmBaseUrl(payload.base_url || '');
    } catch (error) {
      setSettingsError('Could not save LLM settings.');
    } finally {
      setSettingsLoading(false);
    }
  };

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
      setSettingsError('Could not save SOUL information.');
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
      setSettingsError('Could not add update to SOUL.');
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
      const response = await fetch('/api/conversations?kind=conversation', { headers });
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
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
          setSkillsSaveStatus('Saved.');
          skillsSaveStatusTimeoutRef.current = setTimeout(() => {
            setSkillsSaveStatus('');
            skillsSaveStatusTimeoutRef.current = null;
          }, 2200);
        } else {
          setSkillsSaveStatus('Failed to save.');
          skillsSaveStatusTimeoutRef.current = setTimeout(() => {
            setSkillsSaveStatus('');
            skillsSaveStatusTimeoutRef.current = null;
          }, 3500);
          setGenericModal({
            title: 'Save error',
            body: 'Could not save skills. Please try again.'
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
        setSkillsSaveStatus('Failed to save.');
        skillsSaveStatusTimeoutRef.current = setTimeout(() => {
          setSkillsSaveStatus('');
          skillsSaveStatusTimeoutRef.current = null;
        }, 3500);
        setGenericModal({
          title: 'Save error',
          body: 'Could not save skills. Check your connection and try again.'
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
      tera: 'Tera'
    };
    const helpMap = {
      github: t('github_token_help'),
      google_drive: t('google_token_help'),
      google_calendar: t('google_token_help'),
      gmail: t('google_token_help'),
      tera: ''
    };
    setConnectorModal({
      key,
      title: `${t('connect')} — ${labelMap[key] || key}`,
      help: helpMap[key] || '',
      token: ''
    });
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
      if (!headers.Authorization) return;
      headers['Content-Type'] = 'application/json';
      const res = await fetch('/api/plan/approve', {
        method: 'POST', headers,
        body: JSON.stringify({ conversation_id: convId, tasks })
      });
      const json = await res.json().catch(() => ({}));
      if (res.ok) {
        setActivePlanConvId(convId);
        // Reload plan tasks
        const tr = await fetch(`/api/plan/tasks/${convId}`, { headers: getAuthHeaders() });
        const td = await tr.json().catch(() => ({}));
        setPlanTasks(Array.isArray(td?.tasks) ? td.tasks : []);
      }
    } catch {}
  };

  const loadPlanTasks = async (convId) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      const res = await fetch(`/api/plan/tasks/${convId}`, { headers });
      const json = await res.json().catch(() => ({}));
      setPlanTasks(Array.isArray(json?.tasks) ? json.tasks : []);
      if (json?.tasks?.length) setActivePlanConvId(convId);
    } catch {}
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

  const connectWebSocket = () => {
    const tokenValue = token || localStorage.getItem('agentic_token');
    if (!tokenValue) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${wsProtocol}://${window.location.host}/ws/${sessionId.current}?token=${tokenValue}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log('WebSocket conectado');
      fetchRuntimeLlmLabel();

      if (pendingAutoSendRef.current) {
        const content = pendingAutoSendRef.current;
        pendingAutoSendRef.current = null;

        const now = Date.now();
        const userMessage = {
          role: 'user',
          content: content,
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
          content: content,
          skill_id: activeSkill?.id || null,
          skill_web_search: activeSkill?.content?.web_search === true,
          force_expert_id: forceExpertId || null
        }));
      }
    };

    ws.onmessage = (event) => {
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
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage && lastMessage.role === 'assistant' && lastMessage.streaming) {
              newMessages[newMessages.length - 1] = {
                ...lastMessage,
                content: `${lastMessage.content}${data.content}`
              };
            } else {
              newMessages.push({
                role: 'assistant',
                content: data.content,
                streaming: true,
                id: `chunk-${Date.now()}-${Math.random().toString(16).slice(2)}`
              });
            }
            return newMessages;
          });
        } else if (data.type === 'done') {
          // Expert selection transparency
          if (data.selection_reason) setLastExpertReason(data.selection_reason);
          if (data.matched_keywords) setLastExpertKeywords(data.matched_keywords || []);
          // Auto-approve plan if backend detected a plan block
          if (data.plan_detected && data.plan_tasks?.length && currentConversation) {
            approvePlan(currentConversation, data.plan_tasks);
          }
          const _doneMessageId = data.message_id || null;
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage && lastMessage.role === 'assistant') {
              newMessages[newMessages.length - 1] = {
                ...lastMessage,
                streaming: false,
                expert: data.expert,
                provider: data.provider,
                model: data.model,
                message_id: _doneMessageId,
              };
            }
            return newMessages;
          });
          if (data.provider || data.model) {
            const label = formatRuntimeLlmLabel(data.provider, data.model, llmMode);
            if (label) {
              setRuntimeLlmLabel(label);
            }
          }
          setStreaming(false);
          setStreamStatusText('');
        } else if (data.type === 'status') {
          const txt = String(data.content || '').trim();
          if (txt) setStreamStatusText(txt);
        } else if (data.type === 'error') {
          console.error('WebSocket error:', data.content);
          setStreaming(false);
          setStreamStatusText('');
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('WebSocket desconectado');

      // Tentar reconectar após 3 segundos
      setTimeout(() => {
        if (user) {
          connectWebSocket();
        }
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
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
    wsRef.current.send(JSON.stringify({
      type: 'chat',
      content: input.trim(),
      skill_id: activeSkill?.id || null,
      skill_web_search: activeSkill?.content?.web_search === true,
      force_expert_id: forceExpertId || null
    }));
  };

  const createNewConversation = async () => {
    try {
      const headers = getAuthHeaders();
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

      await loadConversations();
      await loadTasks();

      if (wsRef.current) {
        wsRef.current.close();
      }
      sessionId.current = data.session_id;
      connectWebSocket();

    } catch (error) {
      console.error('Error creating conversation:', error);
    }
  };

  const createNewTask = async () => {
    try {
      const headers = getAuthHeaders();
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
      hasHttpHydratedRef.current = true;
      setCenterView('chat');
      setChatSearch('');

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
      fetch('/doacoes.txt', { cache: 'no-store' })
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
              src="/pemartins.jpg"
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
                  src="/btn_donateCC_LG.gif"
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
                      <div style={styles.modalTitle}>👋 Welcome to Open Slap!</div>
                      <button style={styles.iconButton} onClick={() => setShowOnboarding(false)}>×</button>
                    </div>
                    <div style={styles.modalBody}>
                      <div style={{ marginBottom: '16px', fontSize: '13px', color: 'var(--text)', lineHeight: 1.7 }}>
                        Open Slap! is an agentic workspace. Here's how to get started quickly:
                      </div>
                      {[
                        ['➕ New Task', 'Click "New Task" in the sidebar. The CTO skill loads automatically — describe your project and it will create a structured plan.'],
                        ['🧠 Skills', 'Go to Customize → Skills to see all built-in skills (CTO, Architect, Backend, Frontend, SEO…). Click any skill to run it.'],
                        ['🔌 Connectors', 'Go to Customize → Connectors to link GitHub, Google Calendar or Gmail. The agent will use your live data automatically.'],
                        ['👍 Feedback', "Rate any assistant reply with 👍/👎. This helps the system learn what's useful."],
                        ['🗂️ Projects', 'Create a project in Settings → Projects to share context across multiple tasks.'],
                      ].map(([title, desc]) => (
                        <div key={title} style={{ marginBottom: '12px' }}>
                          <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--accent)', fontFamily: 'var(--sans)', marginBottom: '3px' }}>{title}</div>
                          <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--sans)', lineHeight: 1.5 }}>{desc}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ ...styles.commandActions, justifyContent: 'flex-end' }}>
                      <button style={styles.settingsPrimaryButton} onClick={() => { setShowOnboarding(false); createNewTask(); }}>
                        🚀 Start my first task
                      </button>
                      <button style={styles.settingsSecondaryButton} onClick={() => setShowOnboarding(false)}>
                        Explore on my own
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {genericModal ? (
                <div style={styles.modalOverlay} onClick={() => setGenericModal(null)}>
                  <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
                    <div style={styles.modalHeader}>
                      <div style={styles.modalTitle}>{genericModal?.title || 'Confirmar'}</div>
                      <button style={styles.iconButton} onClick={() => setGenericModal(null)} title="Fechar">×</button>
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
              <div style={styles.header}>
                <div style={styles.headerTitle}>{t('app_title')}</div>
                <div style={styles.headerRight}>
                  <div style={styles.connectionStatus} className="slap-conn-status">
                    <div style={styles.connectionDot}></div>
                    {connected ? `${t('connected')}${runtimeLlmLabel ? ` — ${runtimeLlmLabel}` : ''}` : t('disconnected')}
                  </div>
                  {doctorReport && doctorReport.ok === false ? (
                    <button
                      style={{ ...styles.userButton, borderColor: 'var(--amber)', color: 'var(--amber)' }}
                      onClick={() => setCenterView('settings')}
                      title="Há itens de diagnóstico pendentes"
                    >
                      Doctor ⚠
                    </button>
                  ) : null}
                  <button style={styles.iconButton} onClick={() => setCenterView('settings')}>
                    ⚙️
                  </button>
                  <button style={styles.userButton} onClick={logout}>
                    {user?.email} → {t('sign_out')}
                  </button>
                </div>
              </div>

              <div style={styles.main}>
                <div style={{ ...styles.sidebar, width: sidebarCollapsed ? '72px' : styles.sidebar.width }} className={`slap-sidebar${mobileSidebarOpen ? ' expanded' : ''}`}>
                  <div style={styles.sidebarSection}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
                      {!sidebarCollapsed ? <div style={styles.sidebarTitle}>{t('menu')}</div> : <div />}
                      <button
                        style={styles.iconButton}
                        onClick={() => setSidebarCollapsed((v) => !v)}
                        title={sidebarCollapsed ? t('menu_expand') : t('menu_collapse')}
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
                    <button
                        style={{
                          ...styles.sidebarButton,
                          ...(sidebarHoverKey === 'tasks_new' ? styles.sidebarButtonHover : {}),
                          textAlign: sidebarCollapsed ? 'center' : 'left',
                          padding: sidebarCollapsed ? '10px' : styles.sidebarButton.padding,
                          justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                          marginTop: '8px'
                        }}
                        onMouseEnter={() => setSidebarHoverKey('tasks_new')}
                        onMouseLeave={() => setSidebarHoverKey('')}
                        onClick={createNewTask}
                        title={t('new_task')}
                      >
                        {sidebarCollapsed ? '➕' : ` ${t('new_task')}`}
                      </button>
                    {/* Plan tasks panel + orchestration */}
                    {!sidebarCollapsed && planTasks.length > 0 && (
                      <div style={{
                        margin: '10px 0', padding: '10px',
                        background: 'var(--bg3)', borderRadius: '8px',
                        border: orchStatus === 'running'
                          ? '1px solid var(--accent)'
                          : '1px solid var(--border)',
                        transition: 'border-color 0.3s'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <div style={{ fontSize: '10px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', letterSpacing: '0.05em' }}>
                            PLAN TASKS
                          </div>
                          {orchStatus !== 'running' && planTasks.some(t => t.status !== 'done') && (
                            <button
                              onClick={() => activePlanConvId && startOrchestration(activePlanConvId)}
                              style={{
                                background: 'var(--accent)', border: 'none',
                                borderRadius: '5px', padding: '3px 8px',
                                fontSize: '10px', color: 'var(--bg)',
                                fontFamily: 'var(--mono)', cursor: 'pointer',
                                fontWeight: 600, letterSpacing: '0.03em'
                              }}
                              title="Run all pending tasks automatically"
                            >
                              ▶ Run all
                            </button>
                          )}
                          {orchStatus === 'running' && (
                            <div style={{ fontSize: '10px', color: 'var(--accent)', fontFamily: 'var(--mono)', animation: 'pulse 1.2s infinite' }}>
                              ⚙ Running…
                            </div>
                          )}
                          {orchStatus === 'completed' && (
                            <div style={{ fontSize: '10px', color: 'var(--green)', fontFamily: 'var(--mono)' }}>✓ Done</div>
                          )}
                          {orchStatus === 'failed' && (
                            <div style={{ fontSize: '10px', color: 'var(--red)', fontFamily: 'var(--mono)' }}>✗ Failed</div>
                          )}
                        </div>

                        {planTasks.map(task => {
                          const isRunningNow = orchStatus === 'running' &&
                            orchLog.some(l => l.task_id === task.id && l.status === 'active');
                          return (
                            <div key={task.id} style={{
                              display: 'flex', alignItems: 'center', gap: '6px',
                              padding: '4px 0', borderBottom: '1px solid var(--border)'
                            }}>
                              <button
                                onClick={() => !orchStatus || orchStatus !== 'running'
                                  ? updatePlanTaskStatus(task.id, task.status === 'done' ? 'pending' : 'done')
                                  : null}
                                style={{
                                  background: 'none', border: 'none', cursor: 'pointer',
                                  fontSize: '14px', padding: 0, lineHeight: 1,
                                  color: task.status === 'done'
                                    ? 'var(--green)'
                                    : isRunningNow ? 'var(--accent)' : 'var(--text-dim)'
                                }}
                              >
                                {task.status === 'done' ? '✓' : isRunningNow ? '⚙' : task.status === 'active' ? '▶' : '○'}
                              </button>
                              <div
                                onClick={() => task.conversation_id && loadConversation(task.conversation_id, null, 'task')}
                                style={{
                                  flex: 1, fontSize: '11px', fontFamily: 'var(--sans)',
                                  color: task.status === 'done' ? 'var(--text-dim)' : 'var(--text)',
                                  textDecoration: task.status === 'done' ? 'line-through' : 'none',
                                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                  cursor: task.conversation_id ? 'pointer' : 'default',
                                }} title={task.title}
                              >
                                {task.title}
                              </div>
                              {task.skill_id && (
                                <div style={{ fontSize: '9px', color: 'var(--accent)', fontFamily: 'var(--mono)', opacity: 0.7 }}>
                                  {task.skill_id.split('-')[0]}
                                </div>
                              )}
                            </div>
                          );
                        })}

                        <div style={{ marginTop: '6px', fontSize: '10px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', display: 'flex', justifyContent: 'space-between' }}>
                          <span>{planTasks.filter(t => t.status === 'done').length}/{planTasks.length} done</span>
                          {orchLog.length > 0 && (
                            <span
                              style={{ cursor: 'pointer', color: 'var(--accent)', textDecoration: 'underline' }}
                              onClick={() => setGenericModal({
                                title: 'Orchestration log',
                                body: orchLog.map(l => `[${l.status}] ${l.msg}`).join('\n')
                              })}
                            >
                              view log
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                    <button
                      style={{
                        ...styles.sidebarButton,
                        ...(centerView === 'team' ? styles.sidebarButtonActive : {}),
                        ...(sidebarHoverKey === 'team' ? styles.sidebarButtonHover : {}),
                        textAlign: sidebarCollapsed ? 'center' : 'left',
                        padding: sidebarCollapsed ? '10px' : styles.sidebarButton.padding,
                        justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                        marginTop: '8px'
                      }}
                      onMouseEnter={() => setSidebarHoverKey('team')}
                      onMouseLeave={() => setSidebarHoverKey('')}
                      onClick={() => setCenterView('team')}
                      title={t('my_team')}
                    >
                      👥{sidebarCollapsed ? '' : ` ${t('my_team')}`}
                    </button>
                    <button
                      style={{
                        ...styles.sidebarButton,
                        ...(centerView === 'customize' ? styles.sidebarButtonActive : {}),
                        ...(sidebarHoverKey === 'customize' ? styles.sidebarButtonHover : {}),
                        textAlign: sidebarCollapsed ? 'center' : 'left',
                        padding: sidebarCollapsed ? '10px' : styles.sidebarButton.padding,
                        justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                        marginTop: '8px'
                      }}
                      onMouseEnter={() => setSidebarHoverKey('customize')}
                      onMouseLeave={() => setSidebarHoverKey('')}
                      onClick={() => setCenterView('customize')}
                      title={t('customize')}
                    >
                      🧩{sidebarCollapsed ? '' : ` ${t('customize')}`}
                    </button>
                  </div>

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
                    <img
                      src={OPEN_SLAP_LOGO_SRC}
                      alt="Open Slap!"
                      style={{
                        ...styles.sidebarLogo,
                        maxWidth: sidebarCollapsed ? '44px' : styles.sidebarLogo.maxWidth
                      }}
                    />
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
                        <div style={styles.emptyState}>{t('no_conversations')}</div>
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
                                      <div style={styles.conversationTitle}>{r.conversation_title}</div>
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
                                    onClick={() => loadConversation(conv.id, conv.session_id, 'conversation')}
                                  >
                                    <div style={styles.conversationTitle}>{conv.title}</div>
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
                                onClick={() => loadConversation(conv.id, conv.session_id, 'conversation')}
                              >
                                <div style={styles.conversationTitle}>{conv.title}</div>
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
                        <button style={styles.settingsPrimaryButton} onClick={createNewTask}>
                          + {t('new_task')}
                        </button>
                      </div>
                      {tasks.length === 0 ? (
                        <div style={styles.emptyState}>{t('no_tasks')}</div>
                      ) : (
                        <div style={styles.listTwoCols}>
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
                                        <div style={styles.conversationTitle}>{r.conversation_title}</div>
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
                                        <div style={styles.conversationTitle}>{task.title}</div>
                                        <div style={styles.conversationMeta}>
                                          {statusLabel}{countsLabel} • {t('last')}: {formatCompactDateTime(task.updated_at || task.created_at)}
                                        </div>
                                      </div>
                                    );
                                  })}
                              </div>
                            </div>
                          </div>

                          <div style={styles.lightCard}>
                            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                              {t('global_todo')}
                            </div>
                            {globalTodos.length ? (
                              <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
                                {globalTodos.map((t) => (
                                  <div key={t.id} style={{ ...styles.conversationItem, borderColor: 'rgba(255,255,255,0.08)' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                                      <div style={{ minWidth: 0 }}>
                                        <div style={styles.conversationTitle}>{t.text}</div>
                                        <div style={styles.conversationMeta}>
                                          {t.task_title} • {formatCompactDateTime(t.created_at)}
                                        </div>
                                      </div>
                                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                        <button
                                          style={styles.settingsSecondaryButton}
                                          onClick={() => loadConversation(t.conversation_id, t.session_id, 'task')}
                                        >
                                          {t('open')}
                                        </button>
                                        <button
                                          style={styles.settingsPrimaryButton}
                                          onClick={() => markTodoDone(t.id)}
                                        >
                                          {t('complete')}
                                        </button>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                {t('no_pending')}
                              </div>
                            )}
                          </div>
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
                          onClick={() => {
                            createTaskWithPrefill(
                              t('create_new_agent_prompt') || 'Crie um novo agente. Faça perguntas para coletar os dados necessários (nome, objetivo, habilidades, limites) e no final gere o pacote do agente.',
                              true
                            );
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
                                      {e.name}
                                    </div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginTop: '4px' }}>
                                      {e.description || e.id}
                                    </div>
                                  </div>
                                </div>
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => {
                                    setCenterView('chat');
                                    setInput(`Quero falar com o agente ${e.name}.`);
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
                                            title: 'Invalid JSON',
                                            body: 'Could not save. Fix the JSON and try again.'
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
                                <div style={styles.skillName}>{selected?.name || 'Habilidade'}</div>
                                {selected?.description ? (
                                  <div style={styles.skillDesc}>{selected.description}</div>
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
                                      <div style={styles.skillName}>{s.name}</div>
                                      <div style={styles.skillDesc}>{s.description}</div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                              <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                Click a skill to open in read mode.
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
                      {settingsError ? (
                        <div style={styles.settingsError}>{settingsError}</div>
                      ) : null}

                      <div style={styles.settingsSection}>
                        <div style={styles.settingsSectionTitle}>{t('theme')}</div>
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
                          gap: '10px',
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
                                  borderRadius: '10px',
                                  padding: '10px',
                                  cursor: 'pointer',
                                  textAlign: 'left',
                                  outline: 'none',
                                  transition: 'border-color 0.15s',
                                  boxShadow: isActive ? `0 0 0 1px ${th.preview[2]}40` : 'none',
                                }}
                              >
                                <div style={{ display: 'flex', gap: '5px', marginBottom: '8px' }}>
                                  {th.preview.map((c, i) => (
                                    <div key={i} style={{
                                      width: '16px', height: '16px',
                                      borderRadius: '50%',
                                      background: c,
                                      border: '1px solid rgba(255,255,255,0.15)'
                                    }} />
                                  ))}
                                </div>
                                <div style={{
                                  fontSize: '11px',
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
                        <div style={styles.settingsGrid}>
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
                        <div style={styles.settingsSectionTitle}>Doctor (diagnostics)</div>
                        {doctorError ? (
                          <div style={styles.settingsError}>{doctorError}</div>
                        ) : null}

                        <div style={styles.doctorCard}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                            <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
                              {doctorReport
                                ? (doctorReport.ok ? 'All systems OK.' : 'Some items need attention.')
                                : 'Clique em “Rodar diagnóstico”.'}
                            </div>
                            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={() => {
                                  refreshSystemProfile().finally(() => fetchDoctorReport({ silent: true }));
                                }}
                                disabled={settingsLoading || doctorLoading}
                              >
                                Atualizar perfil
                              </button>
                              <button
                                style={styles.settingsPrimaryButton}
                                onClick={() => fetchDoctorReport({ silent: false })}
                                disabled={settingsLoading || doctorLoading}
                              >
                                {doctorLoading ? 'Running...' : 'Run diagnostics'}
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
                                    <div style={statusStyle}>{ok ? 'OK' : 'FALHOU'}</div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : null}

                          {doctorReport?.recommendations?.length ? (
                            <div style={{ marginTop: '12px' }}>
                              <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginBottom: '8px' }}>
                                Recommendations
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

                      <div style={styles.settingsSection}>
                        <div style={styles.settingsSectionTitle}>LLM (API key or local)</div>

                        <div style={styles.settingsGrid}>
                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Mode</div>
                            <select
                              style={styles.settingsInput}
                              value={llmMode}
                              onChange={(e) => setLlmMode(e.target.value)}
                              disabled={settingsLoading}
                            >
                              <option value="env">Server default</option>
                              <option value="api">API (cloud)</option>
                              <option value="local">Local (Ollama)</option>
                            </select>
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Provider</div>
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
                            <div style={styles.settingsLabel}>Modelo</div>
                            <input
                              style={styles.settingsInput}
                              value={llmModel}
                              onChange={(e) => setLlmModel(e.target.value)}
                              placeholder={llmMode === 'local' ? 'ex.: llama3.2' : 'ex.: gpt-4o-mini'}
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Base URL</div>
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
                              <div style={styles.settingsLabel}>Chave API</div>
                              <input
                                style={styles.settingsInput}
                                value={llmApiKey}
                                onChange={(e) => setLlmApiKey(e.target.value)}
                                placeholder={llmHasApiKey ? 'Chave já cadastrada (opcional trocar)' : 'Cole sua chave aqui'}
                                disabled={settingsLoading}
                              />
                              <div style={styles.settingsHint}>
                                A chave fica salva de forma protegida no servidor local deste computador. Não aparece novamente depois de salvar.
                              </div>
                              <div style={styles.settingsHint}>
                                Warning: on a shared computer, others with access to the same Windows user may use this local server and consume your credentials. Use separate OS profiles.
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
                              disabled={settingsLoading}
                            >
                              Remover chave
                            </button>
                          ) : null}
                          <button
                            style={styles.settingsPrimaryButton}
                            onClick={saveLlmSettings}
                            disabled={settingsLoading}
                          >
                            {settingsLoading ? 'Saving...' : 'Save LLM'}
                          </button>
                        </div>
                      </div>

                      <div style={styles.settingsSection}>
                        <div style={styles.settingsSectionTitle}>System profile (local)</div>
                        <div style={styles.settingsHint}>
                          Esse perfil é coletado pelo servidor local (Windows) e fica disponível para evitar perguntas recorrentes do tipo “qual versão do seu sistema?”.
                        </div>
                        <div style={styles.settingsHint}>
                          Atenção: pode conter informações sensíveis (nome do computador, rede, etc.). Use “Remover” se preferir não armazenar.
                        </div>
                        {!systemProfileEnabled ? (
                          <div style={styles.settingsHint}>
                            Feature disabled on server (OPENSLAP_SYSTEM_PROFILE=0).
                          </div>
                        ) : null}
                        {systemProfileError ? (
                          <div style={styles.settingsError}>{systemProfileError}</div>
                        ) : null}
                        <div style={styles.settingsActions}>
                          <button
                            style={styles.settingsSecondaryButton}
                            onClick={deleteSystemProfile}
                            disabled={settingsLoading}
                          >
                            Remover
                          </button>
                          <button
                            style={styles.settingsPrimaryButton}
                            onClick={refreshSystemProfile}
                            disabled={settingsLoading || !systemProfileEnabled}
                          >
                            {settingsLoading ? 'Updating...' : 'Update profile'}
                          </button>
                        </div>
                        <div style={styles.settingsHint}>
                          Last updated: {systemProfileUpdatedAt || '—'}
                        </div>
                        <textarea
                          style={{ ...styles.settingsTextarea, minHeight: '180px' }}
                          value={systemProfileMarkdown}
                          readOnly
                        />
                      </div>

                      <div style={styles.settingsSection}>
                        <div style={styles.settingsSectionTitle}>SOUL (user profile)</div>

                        <div style={styles.settingsGrid}>
                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Name</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.name}
                              onChange={(e) => setSoulData(prev => ({ ...prev, name: e.target.value }))}
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Age range</div>
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
                            <div style={styles.settingsLabel}>Learning style</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.learning_style}
                              onChange={(e) => setSoulData(prev => ({ ...prev, learning_style: e.target.value }))}
                              placeholder="e.g. visual, examples, step-by-step"
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Language</div>
                            <input
                              style={styles.settingsInput}
                              value={soulData.language}
                              onChange={(e) => setSoulData(prev => ({ ...prev, language: e.target.value }))}
                              placeholder="en"
                              disabled={settingsLoading}
                            />
                          </div>

                          <div style={styles.settingsField}>
                            <div style={styles.settingsLabel}>Audience</div>
                            <select
                              style={styles.settingsInput}
                              value={soulData.audience}
                              onChange={(e) => setSoulData(prev => ({ ...prev, audience: e.target.value }))}
                              disabled={settingsLoading}
                            >
                              <option value="">Not set</option>
                              <option value="youth">Youth</option>
                              <option value="adult">Adult</option>
                              <option value="mixed">Mixed</option>
                            </select>
                          </div>

                          <div style={{ ...styles.settingsField, gridColumn: '1 / -1' }}>
                            <div style={styles.settingsLabel}>Notes</div>
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
                            {settingsLoading ? 'Saving...' : 'Save SOUL'}
                          </button>
                        </div>

                        <div style={{ height: '12px' }} />

                        <div style={styles.settingsSectionTitle}>SOUL updates</div>
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
                              {settingsLoading ? 'Saving...' : 'Add update'}
                            </button>
                          </div>
                        </div>

                        <div style={{ height: '12px' }} />

                        <div style={styles.settingsSectionTitle}>SOUL.md preview</div>
                        <textarea
                          style={{ ...styles.settingsTextarea, minHeight: '180px' }}
                          value={soulMarkdown}
                          readOnly
                        />
                      </div>

                      <div style={styles.settingsSection}>
                        <div style={styles.settingsSectionTitle}>Projects</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--sans)', marginBottom: '10px' }}>
                          Projects share a context document across tasks. The agent always has this context available.
                        </div>
                        <div style={{ display: 'grid', gap: '8px', marginBottom: '10px' }}>
                          {projects.map(proj => (
                            <div key={proj.id} style={{
                              display: 'flex', alignItems: 'center', gap: '10px',
                              padding: '8px 12px', background: 'var(--bg3)',
                              borderRadius: '8px',
                              border: activeProjectId === proj.id ? '1px solid var(--accent)' : '1px solid var(--border)'
                            }}>
                              <div style={{ flex: 1, fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>📁 {proj.name}</div>
                              <button style={styles.settingsSecondaryButton} onClick={() => {
                                setActiveProjectId(proj.id);
                                if (currentConversation) assignConversationProject(currentConversation, proj.id);
                              }}>{activeProjectId === proj.id ? 'Active' : 'Set active'}</button>
                            </div>
                          ))}
                          {projects.length === 0 && (
                            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>No projects yet.</div>
                          )}
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <input id='new-project-name' style={{ ...styles.settingsInput, flex: 1 }} placeholder='New project name…' />
                          <button style={styles.settingsPrimaryButton} onClick={async () => {
                            const el = document.getElementById('new-project-name');
                            const name = (el?.value || '').trim();
                            if (!name) return;
                            const pid = await createProject(name);
                            if (pid && currentConversation) { setActiveProjectId(pid); assignConversationProject(currentConversation, pid); }
                            if (el) el.value = '';
                          }}>Create</button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div style={styles.chatToolbar}>
                        <div style={styles.toolbarTitleRow}>
                          <div style={styles.toolbarTitleText}>
                            {currentConversation ? `${currentKind === 'task' ? t('task_label') : t('conversation_label')} #${currentConversation}` : t('chat')}
                          </div>
                        </div>
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
                      </div>
                      <div style={styles.messagesContainer}>
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
                                    return (
                                      <>
                                        {parsed.text ? <div>{parsed.text}</div> : null}
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
                                    <div style={styles.expertTag} title={lastExpertReason || ''}>
                                      <span style={styles.expertIcon}>{message.expert.icon}</span>
                                      <span>{message.expert.name}</span>
                                      {message.provider && (
                                        <span style={{ marginLeft: '8px', fontSize: '10px' }}>
                                          {message.provider} • {message.model}
                                        </span>
                                      )}
                                      {lastExpertReason && (
                                        <span style={{ marginLeft: '6px', fontSize: '10px', opacity: 0.6 }}>
                                          · {lastExpertReason}
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

                      <div style={styles.inputArea}>
                        {/* Expert override + project selector row */}
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
                          <select
                            value={forceExpertId}
                            onChange={e => setForceExpertId(e.target.value)}
                            style={{
                              background: 'var(--bg3)', border: '1px solid var(--border)',
                              borderRadius: '6px', padding: '4px 8px', fontSize: '11px',
                              color: forceExpertId ? 'var(--accent)' : 'var(--text-dim)',
                              fontFamily: 'var(--mono)', cursor: 'pointer', outline: 'none'
                            }}
                            title="Force a specific expert (overrides auto-selection)"
                          >
                            <option value="">Auto expert</option>
                            {experts.map(e => (
                              <option key={e.id} value={e.id}>{e.icon} {e.name}</option>
                            ))}
                          </select>
                          {activeProjectId && projects.length > 0 && (
                            <div style={{ fontSize: '11px', fontFamily: 'var(--mono)', color: 'var(--accent)', opacity: 0.8 }}>
                              📁 {(projects.find(p => p.id === activeProjectId) || {}).name || 'Project'}
                            </div>
                          )}
                          {lastExpertReason && !streaming && (
                            <div style={{ fontSize: '10px', fontFamily: 'var(--mono)', color: 'var(--text-dim)', marginLeft: 'auto' }}>
                              {lastExpertReason}
                              {lastExpertKeywords.length > 0 && ` · ${lastExpertKeywords.slice(0,3).join(', ')}`}
                            </div>
                          )}
                        </div>
                        <div style={styles.inputContainer}>
                          <div style={styles.inputWrapper}>
                            <textarea
                              style={{ ...styles.input, fontSize: `${Math.round(14 * chatFontScale)}px` }}
                              value={input}
                              onChange={(e) => setInput(e.target.value)}      
                              onKeyPress={handleKeyPress}
                              placeholder={t('search_chat_placeholder') || "Type your message…"}
                              disabled={streaming || !connected}
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
