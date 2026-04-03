/**
 * 🚀 APP AUTH - Aplicação Principal com Autenticação
 * Versão completa segundo WINDSURF_AGENT.md - AUTH-02
 */

import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import useAuth from './hooks/useAuth';
import useChatSocket from './hooks/useChatSocket';
import { buildSysGlobalKernelPrompt } from './lib/kernelPrompt';
import { maybeRepoDisambiguationInternalPrompt } from './lib/repoDisambiguation';
import { translations } from './i18n/translations_auth';
import { buildAppAuthStyles } from './styles/appAuthStyles';
import { buildDefaultSkills } from './data/defaultSkills';
import SystemSettingsPanel from './components/settings/SystemSettingsPanel';
import LlmSettingsPanel from './components/settings/LlmSettingsPanel';
import SecuritySettingsPanel from './components/settings/SecuritySettingsPanel';

const OPEN_SLAP_LOGO_SRC = '/open_slap.png';
const AGENT_AVATAR_SRC = '/agent/slap.png';
const OPEN_SLAP_REPO_URL = 'https://github.com/pemartins1970/slap-ecosystem';
const OPEN_SLAP_VERSION = 'v2.1';
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
  const [bootInput, setBootInput] = useState('');
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
  const [llmProviderKeys, setLlmProviderKeys] = useState([]);
  const [llmProviderKeysLoading, setLlmProviderKeysLoading] = useState(false);
  const [llmProviderKeysError, setLlmProviderKeysError] = useState('');
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
  const [authSettings, setAuthSettings] = useState({
    jwt_expire_minutes: 120,
    default_jwt_expire_minutes: 120,
    has_override: false
  });
  const [authSettingsUpdatedAt, setAuthSettingsUpdatedAt] = useState('');
  const [jwtExpireMinutesDraft, setJwtExpireMinutesDraft] = useState(120);
  const [authSettingsSaving, setAuthSettingsSaving] = useState(false);
  const [autoApproveCommands, setAutoApproveCommands] = useState([]);
  const [autoApproveCommandsLoading, setAutoApproveCommandsLoading] = useState(false);
  const [autoApproveCommandsError, setAutoApproveCommandsError] = useState('');
  const [automationClientBaseUrl, setAutomationClientBaseUrl] = useState('');
  const [automationClientApiKey, setAutomationClientApiKey] = useState('');
  const [automationClientHasApiKey, setAutomationClientHasApiKey] = useState(false);
  const [doctorReport, setDoctorReport] = useState(null);
  const [doctorError, setDoctorError] = useState('');
  const [doctorLoading, setDoctorLoading] = useState(false);
  const [systemMapText, setSystemMapText] = useState('');
  const [systemMapUpdatedAt, setSystemMapUpdatedAt] = useState('');
  const [systemMapError, setSystemMapError] = useState('');
  const [systemMapLoading, setSystemMapLoading] = useState(false);
  const [externalMemoryProvider, setExternalMemoryProvider] = useState('');
  const [externalMemoryUploading, setExternalMemoryUploading] = useState(false);
  const [externalMemoryImports, setExternalMemoryImports] = useState([]);
  const [externalMemoryImportsLoading, setExternalMemoryImportsLoading] = useState(false);
  const [externalMemoryImportsError, setExternalMemoryImportsError] = useState('');
  const [memoryDreamLoading, setMemoryDreamLoading] = useState(false);
  const [memoryDreamDecayed, setMemoryDreamDecayed] = useState(0);
  const [memoryDreamPruned, setMemoryDreamPruned] = useState(0);
  const [memoryDreamSnapshot, setMemoryDreamSnapshot] = useState('');
  const [rawMemoryQuery, setRawMemoryQuery] = useState('');
  const [rawMemoryResults, setRawMemoryResults] = useState([]);
  const [rawMemoryLoading, setRawMemoryLoading] = useState(false);
  const [rawMemoryError, setRawMemoryError] = useState('');
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
  const [globalTodoScope, setGlobalTodoScope] = useState('project');
  const [globalTodoShowAgent, setGlobalTodoShowAgent] = useState(false);
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
  const [approvedPlanLocalMsgIds, setApprovedPlanLocalMsgIds] = useState({});
  const pendingPlanTasksRef = useRef({});
  // Message feedback
  const [messageFeedback, setMessageFeedback] = useState({}); // {message_id: 1|-1}
  const [savedInfoLocalMsgIds, setSavedInfoLocalMsgIds] = useState({}); // {local_message_id: true}
  // MoE expert override
  const [forceExpertId, setForceExpertId] = useState('');
  const [lastExpertReason, setLastExpertReason] = useState('');
  const [lastExpertKeywords, setLastExpertKeywords] = useState([]);
  const hasRestoredConversationRef = useRef(false);
  const [showRoutingDebug, setShowRoutingDebug] = useState(false);
  const [showExecutionPanel, setShowExecutionPanel] = useState(true);
  // Onboarding
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(0);
  const [onboardingSoulDraft, setOnboardingSoulDraft] = useState({ name: '', age_range: '', goals: '' });
  const [onboardingSoulSaving, setOnboardingSoulSaving] = useState(false);
  const [onboardingError, setOnboardingError] = useState('');
  const [onboardingActionLoading, setOnboardingActionLoading] = useState(false);
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
  const t = (key) => {
    const table = translations[lang] || translations.en || translations.pt;
    return table[key] || (translations.en && translations.en[key]) || translations.pt[key] || key;
  };
  const getDoctorLabel = (check) => {
    const id = String(check?.id || '').trim();
    if (!id) return check?.label || '';
    const k = `doctor_check_${id}`;
    const v = t(k);
    return v === k ? (check?.label || id) : v;
  };
  const getBootGreeting = () => {
    const h = new Date().getHours();
    const key = h < 12 ? 'boot_greeting_morning' : (h < 18 ? 'boot_greeting_afternoon' : 'boot_greeting_evening');
    const base = t(key);
    const candidates = [
      String(soulData?.name || '').trim(),
      String(soulData?.full_name || '').trim(),
      String(soulData?.user_name || '').trim(),
      (() => {
        const em = String(user?.email || '').trim();
        return em.includes('@') ? em.split('@')[0] : '';
      })()
    ].filter(Boolean);
    const name = candidates.length ? candidates[0] : '';
    return `${base}${name ? `, ${name}` : ''}.`;
  };
  const renderBootScreen = () => {
    const greeting = getBootGreeting();
    const recentConversations = (conversations || [])
      .slice()
      .sort((a, b) => {
        const ta = new Date(a?.updated_at || a?.created_at || 0).getTime();
        const tb = new Date(b?.updated_at || b?.created_at || 0).getTime();
        return tb - ta;
      })
      .slice(0, 3);
    const asciiWithVersion = (() => {
      try {
        return OPEN_SLAP_ASCII.replace('open_slap > boot', `open_slap > boot #${OPEN_SLAP_VERSION}#`);
      } catch {
        return OPEN_SLAP_ASCII;
      }
    })();
    return (
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
            {asciiWithVersion}
          </pre>
        </div>
        <div style={{ marginTop: '28px', fontSize: '18px', fontWeight: 700, color: 'var(--text)', fontFamily: 'var(--sans)' }}>
          {greeting}
        </div>
        <input
          style={{ ...styles.chatSearchInput, width: '100%', marginTop: '24px' }}
          value={bootInput}
          onChange={(e) => setBootInput(e.target.value)}
          placeholder={t('boot_input_placeholder')}
          onKeyDown={(e) => {
            if (e.key !== 'Enter') return;
            const content = String(bootInput || '').trim();
            if (!content) return;
            setBootInput('');
            startNewConversationWithPrompt(content);
          }}
        />
        {recentConversations.length ? (
          <div style={{ ...styles.lightCard, marginTop: '18px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
              {t('conversations')} • {t('last')} 3
            </div>
            <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
              {recentConversations.map((conv) => (
                <div
                  key={conv.id}
                  style={styles.conversationItem}
                  onClick={() => loadConversation(conv.id, conv.session_id, 'conversation')}
                >
                  <div style={{ ...styles.conversationTitle, marginBottom: 0 }}>
                    {String(conv?.title || '').trim() || `${t('conversation_label')} ${String(conv?.id || '').slice(0, 8)}`}
                  </div>
                  <div style={styles.conversationMeta}>
                    {formatCompactDateTime(conv.updated_at || conv.created_at)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    );
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
    const parseSqliteTimestampUtc = (raw) => {
      const s = String(raw || '').trim();
      const m = s.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?/);
      if (!m) return null;
      const year = Number(m[1]);
      const month = Number(m[2]);
      const day = Number(m[3]);
      const hour = Number(m[4]);
      const minute = Number(m[5]);
      const second = Number(m[6] || '0');
      if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day)) return null;
      return new Date(Date.UTC(year, month - 1, day, hour, minute, second));
    };
    const d =
      value && typeof value === 'string' && /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}/.test(value)
        ? parseSqliteTimestampUtc(value)
        : value
          ? new Date(value)
          : null;
    if (!d || Number.isNaN(d.getTime())) return '';
    return d.toLocaleString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  };
  const getMessageTimestamp = (message) => message?.created_at || message?.createdAt || message?.timestamp || message?.time || '';

  const styles = buildAppAuthStyles({ connected });

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

  const MessageBlock = ({ block, onApprovePlan, planUi }) => {
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
      const isRunning = Boolean(planUi?.running);
      const isApproved = Boolean(planUi?.approved);
      const approveLabel = isRunning
        ? (lang === 'pt' ? 'Executando…' : 'Running…')
        : isApproved
          ? (lang === 'pt' ? 'Aprovado' : 'Approved')
          : (lang === 'pt' ? 'Aprovar' : 'Approve');
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
                disabled={!tasks.length || isRunning || isApproved}
              >
                {approveLabel}
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

  const autoApprovePendingCommand = async (req) => {
    if (!req?.id) return false;
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      const res = await fetch(`/api/commands/pending/${encodeURIComponent(req.id)}/autoapprove`, {
        method: 'POST',
        headers
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail || 'Failed to auto-approve command.');
      }
      return true;
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ ${e?.message || String(e)}`,
          id: `${Date.now()}-${Math.random().toString(16).slice(2)}`
        }
      ]);
      return false;
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
    const defaults = buildDefaultSkills();

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

  const fetchSystemMap = async ({ silent = false, refresh = false } = {}) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    if (!silent) {
      setSystemMapLoading(true);
      setSystemMapError('');
    }
    try {
      const res = await fetch(refresh ? '/api/system_map/refresh' : '/api/system_map', {
        method: refresh ? 'POST' : 'GET',
        headers
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error loading system map.');
      }
      setSystemMapText(String(json?.ascii || ''));
      setSystemMapUpdatedAt(String(json?.generated_at || ''));
    } catch (e) {
      setSystemMapError(lang === 'pt' ? 'Não foi possível carregar o mapa do sistema.' : 'Could not load system map.');
      setSystemMapText('');
      setSystemMapUpdatedAt('');
    } finally {
      if (!silent) {
        setSystemMapLoading(false);
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
      setLlmProviderKeys([]);
      setLlmProviderKeysError('');
      if ((llm.mode || 'env') === 'api') {
        try {
          setLlmProviderKeysLoading(true);
          const providerId = (llm.provider || 'openai').toString().trim().toLowerCase();
          const keysRes = await fetch(`/api/settings/llm/keys?provider=${encodeURIComponent(providerId)}`, { headers });
          const keysJson = await keysRes.json().catch(() => ({}));
          if (keysRes.ok) {
            setLlmProviderKeys(Array.isArray(keysJson?.keys) ? keysJson.keys : []);
          } else {
            setLlmProviderKeys([]);
            setLlmProviderKeysError(keysJson?.detail || 'Could not load saved keys.');
          }
        } catch {
          setLlmProviderKeys([]);
          setLlmProviderKeysError('Could not load saved keys.');
        } finally {
          setLlmProviderKeysLoading(false);
        }
      }

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
        const authRes = await fetch('/api/settings/auth', { headers });
        const authJson = await authRes.json().catch(() => ({}));
        if (authRes.ok) {
          const effective = Number(authJson?.settings?.jwt_expire_minutes || 120) || 120;
          const def = Number(authJson?.defaults?.jwt_expire_minutes || 120) || 120;
          const hasOverride = Boolean(authJson?.has_override);
          setAuthSettings({
            jwt_expire_minutes: effective,
            default_jwt_expire_minutes: def,
            has_override: hasOverride
          });
          setAuthSettingsUpdatedAt(authJson?.updated_at || '');
          setJwtExpireMinutesDraft(effective);
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

  useEffect(() => {
    if (!user || !token) return;
    if (centerView !== 'settings') return;
    if (settingsTab !== 'security') return;
    if (autoApproveCommandsLoading) return;
    if (autoApproveCommands?.length) return;
    loadAutoApproveCommands({ silent: false });
  }, [user, token, centerView, settingsTab]);

  const loadExternalMemoryImports = async ({ silent = false } = {}) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      if (!silent) {
        setExternalMemoryImportsLoading(true);
        setExternalMemoryImportsError('');
      }
      const res = await fetch('/api/memory/imports?limit=25', { headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Failed to load imports.');
      }
      setExternalMemoryImports(Array.isArray(json?.imports) ? json.imports : []);
    } catch (e) {
      if (!silent) {
        setExternalMemoryImportsError(e?.message || 'Failed to load imports.');
      }
      setExternalMemoryImports([]);
    } finally {
      if (!silent) {
        setExternalMemoryImportsLoading(false);
      }
    }
  };

  const setExternalMemoryImportPinned = async (importId, pinned) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return false;
    const iid = String(importId || '').trim();
    if (!iid) return false;
    try {
      headers['Content-Type'] = 'application/json';
      const res = await fetch(`/api/memory/imports/${encodeURIComponent(iid)}/pin`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ pinned: Boolean(pinned) })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || 'Failed to update.');
      await loadExternalMemoryImports({ silent: true });
      return true;
    } catch {
      return false;
    }
  };

  const deleteExternalMemoryImport = async (importId) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return false;
    const iid = String(importId || '').trim();
    if (!iid) return false;
    try {
      const res = await fetch(`/api/memory/imports/${encodeURIComponent(iid)}`, {
        method: 'DELETE',
        headers
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || 'Failed to delete.');
      await loadExternalMemoryImports({ silent: true });
      return true;
    } catch {
      return false;
    }
  };

  useEffect(() => {
    if (!user || !token) return;
    if (centerView !== 'settings') return;
    if (settingsTab !== 'memory') return;
    if (externalMemoryImportsLoading) return;
    loadExternalMemoryImports({ silent: false });
  }, [user, token, centerView, settingsTab]);

  const runMemoryDream = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return false;
    try {
      setMemoryDreamLoading(true);
      setMemoryDreamSnapshot('');
      const res = await fetch('/api/memory/dream', { method: 'POST', headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(String(json?.detail || 'Failed to run Dream.'));
      }
      setMemoryDreamDecayed(Number(json?.decayed || 0));
      setMemoryDreamPruned(Number(json?.pruned || 0));
      setMemoryDreamSnapshot(String(json?.snapshot || ''));
      return true;
    } catch (e) {
      setGenericModal({ title: t('error'), body: e?.message || 'Failed to run Dream.' });
      return false;
    } finally {
      setMemoryDreamLoading(false);
    }
  };

  const searchRawMemory = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    const q = String(rawMemoryQuery || '').trim();
    if (!q) return;
    try {
      setRawMemoryLoading(true);
      setRawMemoryError('');
      setRawMemoryResults([]);
      const url = `/api/memory/search_raw?q=${encodeURIComponent(q)}&limit=50`;
      const res = await fetch(url, { headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(String(json?.detail || 'Failed to search.'));
      }
      setRawMemoryResults(Array.isArray(json?.results) ? json.results : []);
    } catch (e) {
      setRawMemoryError(e?.message || 'Failed to search.');
      setRawMemoryResults([]);
    } finally {
      setRawMemoryLoading(false);
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

  const loadAutoApproveCommands = async ({ silent = false } = {}) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      if (!silent) {
        setAutoApproveCommandsLoading(true);
        setAutoApproveCommandsError('');
      }
      const res = await fetch('/api/commands/autoapprove?limit=200', { headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Could not load auto-approvals.');
      }
      setAutoApproveCommands(Array.isArray(json?.items) ? json.items : []);
    } catch (e) {
      if (!silent) {
        setAutoApproveCommandsError(e?.message || 'Could not load auto-approvals.');
      }
      setAutoApproveCommands([]);
    } finally {
      if (!silent) {
        setAutoApproveCommandsLoading(false);
      }
    }
  };

  const deleteAutoApproveCommand = async (commandNorm) => {
    const cmd = String(commandNorm || '').trim().toLowerCase();
    if (!cmd) return false;
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      headers['Content-Type'] = 'application/json';
      const res = await fetch('/api/commands/autoapprove', {
        method: 'DELETE',
        headers,
        body: JSON.stringify({ command_norm: cmd })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Could not remove auto-approval.');
      }
      await loadAutoApproveCommands({ silent: true });
      return true;
    } catch (e) {
      setGenericModal({
        title: t('error'),
        body: e?.message || 'Could not remove auto-approval.'
      });
      return false;
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
          : rawKey.startsWith('sk-or-')
            ? 'openrouter'
            : rawKey.startsWith('sk-ant-')
              ? 'anthropic'
              : rawKey.startsWith('sk-')
                ? 'openai'
                : '';

      const providerToSave = inferredProvider || llmProvider || (rawKey ? 'openai' : '');
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
        api_key: null
      };

      if (llmMode === 'api' && rawKey) {
        if (!providerToSave) {
          throw new Error('Provider required');
        }
        const keyRes = await fetch('/api/settings/llm/keys', {
          method: 'POST',
          headers,
          body: JSON.stringify({ provider: providerToSave, api_key: rawKey })
        });
        const keyJson = await keyRes.json().catch(() => ({}));
        if (!keyRes.ok) {
          throw new Error(keyJson?.detail || 'Error saving API key.');
        }
        setLlmApiKey('');
        setLlmApiKeyOpen(false);
      }

      const res = await fetch('/api/settings/llm', {
        method: 'PUT',
        headers,
        body: JSON.stringify(payload)
      });

      const json = await res.json();
      if (!res.ok) {
        throw new Error(json?.detail || 'Error saving LLM settings.');
      }

      try {
        const refreshRes = await fetch('/api/settings/llm', { headers });
        const refreshJson = await refreshRes.json().catch(() => ({}));
        if (refreshRes.ok) {
          setLlmHasApiKey(Boolean(refreshJson?.has_api_key));
          setLlmApiKeySource((refreshJson?.api_key_source || (refreshJson?.has_api_key ? 'stored' : 'none')));
          setLlmHasStoredApiKey(Boolean(refreshJson?.has_stored_api_key));
          setLlmHasEnvApiKey(Boolean(refreshJson?.has_env_api_key));
        }
      } catch {}

      try {
        setLlmProviderKeysLoading(true);
        const keysRes = await fetch(`/api/settings/llm/keys?provider=${encodeURIComponent(providerToSave)}`, { headers });
        const keysJson = await keysRes.json().catch(() => ({}));
        if (keysRes.ok) {
          setLlmProviderKeys(Array.isArray(keysJson?.keys) ? keysJson.keys : []);
          setLlmProviderKeysError('');
        } else {
          setLlmProviderKeys([]);
          setLlmProviderKeysError(keysJson?.detail || 'Could not load saved keys.');
        }
      } catch {
        setLlmProviderKeys([]);
        setLlmProviderKeysError('Could not load saved keys.');
      } finally {
        setLlmProviderKeysLoading(false);
      }

      setStoredLlmPrefs({
        mode: payload.mode,
        provider: payload.provider,
        model: payload.model,
        base_url: payload.base_url
      });
      setLlmProvider(payload.provider);
      setLlmBaseUrl(payload.base_url || '');
    } catch (error) {
      const msg = String(error?.message || '').trim();
      setSettingsError(msg || t('llm_settings_save_error'));
    } finally {
      setSettingsLoading(false);
    }
  };

  const setActiveLlmProviderKey = async (providerId, keyId) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      setLlmProviderKeysLoading(true);
      setLlmProviderKeysError('');
      const res = await fetch(`/api/settings/llm/keys/${encodeURIComponent(String(providerId || ''))}/active`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ key_id: Number(keyId) })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || 'Error selecting key.');
      const keysRes = await fetch(`/api/settings/llm/keys?provider=${encodeURIComponent(String(providerId || ''))}`, { headers });
      const keysJson = await keysRes.json().catch(() => ({}));
      if (keysRes.ok) setLlmProviderKeys(Array.isArray(keysJson?.keys) ? keysJson.keys : []);
    } catch (e) {
      setLlmProviderKeysError('Could not select key.');
    } finally {
      setLlmProviderKeysLoading(false);
    }
  };

  const deleteLlmProviderKey = async (providerId, keyId) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      setLlmProviderKeysLoading(true);
      setLlmProviderKeysError('');
      const res = await fetch(`/api/settings/llm/keys/${encodeURIComponent(String(providerId || ''))}/${encodeURIComponent(String(keyId))}`, {
        method: 'DELETE',
        headers
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || 'Error deleting key.');
      const keysRes = await fetch(`/api/settings/llm/keys?provider=${encodeURIComponent(String(providerId || ''))}`, { headers });
      const keysJson = await keysRes.json().catch(() => ({}));
      if (keysRes.ok) setLlmProviderKeys(Array.isArray(keysJson?.keys) ? keysJson.keys : []);
    } catch (e) {
      setLlmProviderKeysError('Could not delete key.');
    } finally {
      setLlmProviderKeysLoading(false);
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

  const saveAuthSettings = async ({ jwt_expire_minutes, use_default }) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      setAuthSettingsSaving(true);
      const payload = {
        jwt_expire_minutes: use_default ? null : Number(jwt_expire_minutes || 0),
        use_default: Boolean(use_default)
      };
      const res = await fetch('/api/settings/auth', {
        method: 'PUT',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || (lang === 'pt' ? 'Não foi possível salvar.' : 'Could not save.'));
      }
      const effective = Number(json?.settings?.jwt_expire_minutes || 120) || 120;
      const def = Number(json?.defaults?.jwt_expire_minutes || 120) || 120;
      const hasOverride = Boolean(json?.has_override);
      setAuthSettings({
        jwt_expire_minutes: effective,
        default_jwt_expire_minutes: def,
        has_override: hasOverride
      });
      setAuthSettingsUpdatedAt(json?.updated_at || '');
      setJwtExpireMinutesDraft(effective);
      return true;
    } catch (e) {
      setGenericModal({ title: t('error'), body: e?.message || (lang === 'pt' ? 'Não foi possível salvar.' : 'Could not save.') });
      return false;
    } finally {
      setAuthSettingsSaving(false);
    }
  };

  const applyJwtExpiryChange = ({ use_default = false } = {}) => {
    const def = Number(authSettings?.default_jwt_expire_minutes || 120) || 120;
    const raw = Number(jwtExpireMinutesDraft || 0) || 0;
    const minutes = clamp(raw, 15, 10080);
    const next = use_default ? def : minutes;
    const risk =
      next >= 24 * 60
        ? (lang === 'pt'
          ? 'Risco alto: sessões longas aumentam a janela de abuso em caso de token vazado.'
          : 'High risk: long sessions increase the abuse window if a token leaks.')
        : next >= 4 * 60
          ? (lang === 'pt'
            ? 'Atenção: sessões mais longas aumentam a janela de abuso em caso de token vazado.'
            : 'Warning: longer sessions increase the abuse window if a token leaks.')
          : (lang === 'pt'
            ? 'Sessões curtas aumentam a segurança, mas podem exigir login mais frequente.'
            : 'Short sessions improve security but may require more frequent logins.');
    const body = [
      lang === 'pt' ? 'Alterar duração da sessão (JWT)?' : 'Change session duration (JWT)?',
      '',
      `${lang === 'pt' ? 'Novo valor' : 'New value'}: ${next} min`,
      `${lang === 'pt' ? 'Padrão' : 'Default'}: ${def} min`,
      '',
      risk,
      '',
      lang === 'pt'
        ? 'Isso vale para novos tokens (você pode precisar sair/entrar novamente).'
        : 'This applies to newly issued tokens (you may need to sign out/in again).'
    ].join('\n');
    setGenericModal({
      title: t('security'),
      body,
      onConfirm: () => saveAuthSettings({ jwt_expire_minutes: next, use_default })
    });
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

  const saveOnboardingSoulDraft = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return false;
    setOnboardingSoulSaving(true);
    setOnboardingError('');
    try {
      const currentRes = await fetch('/api/soul', { headers });
      const currentJson = await currentRes.json().catch(() => ({}));
      const base = (currentJson?.data && typeof currentJson.data === 'object') ? currentJson.data : {};
      const next = {
        ...base,
        name: String(onboardingSoulDraft?.name || '').trim(),
        age_range: String(onboardingSoulDraft?.age_range || '').trim(),
        goals: String(onboardingSoulDraft?.goals || '').trim()
      };
      const res = await fetch('/api/soul', {
        method: 'PUT',
        headers,
        body: JSON.stringify({ data: next })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || 'Error saving profile.');
      setSoulData((prev) => ({ ...(prev || {}), ...next }));
      setSoulMarkdown(json?.markdown || '');
      return true;
    } catch (e) {
      setOnboardingError(t('soul_save_error'));
      return false;
    } finally {
      setOnboardingSoulSaving(false);
    }
  };

  const completeOnboarding = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      setOnboardingActionLoading(true);
      const res = await fetch('/api/onboarding/complete', { method: 'POST', headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || 'Error completing onboarding.');
      try { localStorage.setItem('open_slap_onboarding_hide_v1', '1'); } catch {}
    } catch {
    } finally {
      setOnboardingActionLoading(false);
    }
  };

  const resetOnboarding = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      setOnboardingActionLoading(true);
      const res = await fetch('/api/onboarding/reset', { method: 'POST', headers });
      await res.json().catch(() => ({}));
      try { localStorage.removeItem('open_slap_onboarding_hide_v1'); } catch {}
    } catch {
      try { localStorage.removeItem('open_slap_onboarding_hide_v1'); } catch {}
    } finally {
      setOnboardingActionLoading(false);
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
        let hide = false;
        try {
          hide = localStorage.getItem('open_slap_onboarding_hide_v1') === '1';
        } catch {}
        if (hide) return;
        fetch('/api/onboarding/status', { headers: getAuthHeaders() })
          .then(r => r.json())
          .then(d => { if (!d.completed) setShowOnboarding(true); })
          .catch(() => {});
      }
    }
  }, [user, token]);

  useEffect(() => {
    if (!showOnboarding) return;
    setOnboardingStep(0);
    setOnboardingError('');
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    fetch('/api/soul', { headers })
      .then((r) => r.json())
      .then((d) => {
        setOnboardingSoulDraft({
          name: d?.data?.name || '',
          age_range: d?.data?.age_range || '',
          goals: d?.data?.goals || ''
        });
      })
      .catch(() => {});
  }, [showOnboarding]);

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

  // Persistir conversa ativa no storage
  useEffect(() => {
    try {
      if (currentConversation) {
        localStorage.setItem('open_slap_current_conversation', String(currentConversation));
      }
    } catch {}
  }, [currentConversation]);

  // Restaurar conversa ativa após carregar lista
  useEffect(() => {
    if (!user || !token) return;
    if (currentConversation) return;
    if (!Array.isArray(conversations) || conversations.length === 0) return;
    if (hasRestoredConversationRef.current) return;
    let stored = null;
    try {
      stored = localStorage.getItem('open_slap_current_conversation');
    } catch {}
    const storedId = stored ? Number(stored) : 0;
    if (!storedId) return;
    const found = conversations.find((c) => Number(c?.id || c?.conversation_id || 0) === storedId);
    if (!found) return;
    const sid = found.session_id || `session_${storedId}`;
    hasRestoredConversationRef.current = true;
    loadConversation(storedId, sid, 'conversation').catch(() => {});
  }, [user, token, conversations, currentConversation]);

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
          : kind === 'project'
            ? `/api/projects/${encodeURIComponent(id)}`
            : `/api/conversations/${encodeURIComponent(id)}/title`;
      const res = await fetch(url, {
        method: 'PUT',
        headers,
        body: JSON.stringify(kind === 'project' ? { name: nextTitle } : { title: nextTitle })
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
      } else if (kind === 'project') {
        setProjects((prev) => (prev || []).map((p) => (String(p.id) === String(id) ? { ...p, name: nextTitle } : p)));
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
      if (!headers.Authorization) {
        setGenericModal({ title: t('error'), body: lang === 'pt' ? 'Não autenticado.' : 'Not authenticated.' });
        return null;
      }
      headers['Content-Type'] = 'application/json';
      const res = await fetch('/api/projects', {
        method: 'POST', headers, body: JSON.stringify({ name })
      });
      const raw = await res.text().catch(() => '');
      let json = {};
      try {
        json = raw ? JSON.parse(raw) : {};
      } catch {
        json = {};
      }
      if (!res.ok) {
        const detail = String(json?.detail || '').trim();
        const rawLine = String(raw || '').trim().split('\n')[0]?.trim() || '';
        const msg =
          detail ||
          (rawLine ? `${res.status} ${res.statusText} — ${rawLine}` : `${res.status} ${res.statusText}`) ||
          (lang === 'pt' ? 'Não foi possível criar o projeto.' : 'Could not create project.');
        throw new Error(msg);
      }
      await loadProjects();
      return json.project_id;
    } catch (e) {
      const msg = String(e?.message || '').trim();
      const hint = (msg.toLowerCase().includes('econnrefused') || msg.toLowerCase().includes('failed to fetch'))
        ? (lang === 'pt'
          ? 'Parece que o backend não está acessível (porta 5150). Verifique se o backend está rodando e se o proxy do Vite está apontando para o endereço correto.'
          : 'Backend seems unreachable (port 5150). Check if backend is running and Vite proxy targets the correct address.')
        : '';
      setGenericModal({
        title: t('error'),
        body: hint ? `${msg}\n\n${hint}` : (msg || (lang === 'pt' ? 'Não foi possível criar o projeto.' : 'Could not create project.'))
      });
    }
    return null;
  };

  const deleteProject = async (projectId) => {
    const pid = Number(projectId || 0);
    if (!pid) return false;
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      const res = await fetch(`/api/projects/${pid}`, { method: 'DELETE', headers });
      if (!res.ok) return false;
      await loadProjects();
      if (Number(activeProjectId || 0) === pid) {
        setActiveProjectId(null);
        setProjectContextDraft('');
        if (currentConversation) assignConversationProject(currentConversation, null);
      }
      return true;
    } catch {
      return false;
    }
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

  const ingestKickoffFileToProjectContext = async (file) => {
    const pid = Number(activeProjectId || 0);
    if (!pid || !file) return;
    const fileName = String(file?.name || '').trim() || 'kickoff.txt';
    const ext = fileName.toLowerCase();
    if (!(ext.endsWith('.txt') || ext.endsWith('.md'))) {
      setGenericModal({
        title: t('error'),
        body: lang === 'pt' ? 'Envie um arquivo .txt ou .md.' : 'Please upload a .txt or .md file.'
      });
      return;
    }
    try {
      const content = await new Promise((resolve, reject) => {
        const r = new FileReader();
        r.onerror = () => reject(new Error('Failed to read file.'));
        r.onload = () => resolve(String(r.result || ''));
        r.readAsText(file);
      });
      const normalized = String(content || '').replace(/\r/g, '').trim();
      const header = `\n\n---\n\n# Kickoff upload: ${fileName}\n\n`;
      const base = String(projectContextDraft || '').trim();
      const merged = `${base}${base ? header : header.trimStart()}${normalized}\n`;
      setProjectContextDraft(merged);
      const ok = await updateProjectContext(pid, merged);
      if (!ok) return;
      const projectName = String(projects.find((p) => Number(p?.id || 0) === pid)?.name || `#${pid}`);
      const userPrompt =
        lang === 'pt'
          ? `Kickoff do projeto "${projectName}" atualizado com o arquivo "${fileName}". Leia o contexto do projeto (Markdown) e estruture: objetivos, escopo, entregáveis, backlog inicial, riscos e próximos passos.`
          : `Project kickoff "${projectName}" was updated with "${fileName}". Read the project Markdown and structure: goals, scope, deliverables, initial backlog, risks, and next steps.`;
      const internalPrompt =
        lang === 'pt'
          ? `Emita imediatamente um bloco de plano estruturado para aprovação:\n\`\`\`plan\nTarefa: Planejar MVP | project\nTarefa: Definir backlog inicial | project\nTarefa: Arquitetar UI mínima | project\nTarefa: Implementar CRUD de tarefas | software_operator\nTarefa: Persistência local (LocalStorage/SQLite) | software_operator\nTarefa: Testes mínimos e README | project\n\`\`\`\nDepois do bloco \`plan\`, responda com a análise do kickoff (objetivos, escopo, entregáveis, backlog inicial, riscos, próximos passos).`
          : `Immediately emit a structured plan block for approval:\n\`\`\`plan\nTask: Plan MVP | project\nTask: Define initial backlog | project\nTask: Design minimal UI | project\nTask: Implement task CRUD | software_operator\nTask: Local persistence (LocalStorage/SQLite) | software_operator\nTask: Minimal tests and README | project\n\`\`\`\nAfter the \`plan\` block, reply with the kickoff analysis (goals, scope, deliverables, initial backlog, risks, next steps).`;
      startNewConversationWithPrompt(userPrompt, { projectId: pid, internalPrompt, kind: 'task' });
    } catch (e) {
      setGenericModal({
        title: t('error'),
        body: e?.message || 'Failed to read file.'
      });
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

  const saveAssistantInfo = async (message) => {
    try {
      if (!message || message.role !== 'assistant') return false;
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      headers['Content-Type'] = 'application/json';
      const res = await fetch('/api/padxml/save_message', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          conversation_id: currentConversation ? Number(currentConversation) : null,
          local_message_id: message.id || null,
          message_id: message.message_id || null,
          content: String(message.content || '')
        })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(String(json?.detail || 'Failed to save.'));
      setSavedInfoLocalMsgIds(prev => ({ ...prev, [message.id]: true }));
      return true;
    } catch {
      return false;
    }
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
      if (String(currentKind || '') === 'task' && Number(currentConversation || 0) === Number(convId || 0)) {
        const existing = await fetch(`/api/tasks/${encodeURIComponent(convId)}/todos`, { headers: getAuthHeaders() });
        const existingJson = await existing.json().catch(() => ({}));
        const existingTodos = Array.isArray(existingJson?.todos) ? existingJson.todos : [];
        if (!existingTodos.length) {
          const rawTasks = Array.isArray(tasks) ? tasks : [];
          for (const it of rawTasks) {
            const titleRaw = String(it?.title || '').trim();
            const cleaned = titleRaw.replace(/^tarefa:\s*/i, '').replace(/^task:\s*/i, '').trim();
            if (!cleaned) continue;
            await addTaskTodo(convId, cleaned);
          }
        }
      }
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

  const getTodoScope = (td) => {
    const raw = String(td?.scope || '').trim().toLowerCase();
    if (raw) return raw;
    const title = String(td?.task_title || '').trim().toLowerCase();
    if (title === 'inbox') return 'personal';
    return 'project';
  };
  const getTodoActor = (td) => {
    const raw = String(td?.actor || '').trim().toLowerCase();
    return raw || 'human';
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

  const { connectWebSocket, sendMessage } = useChatSocket({
    user,
    token,
    lang,
    llmMode,
    skills,
    selectedSkillId,
    forceExpertId,
    agentConfigs,
    showRoutingDebug,
    currentConversation,
    currentKind,
    sessionIdRef: sessionId,
    wsRef,
    pendingAutoSendRef,
    messagesEndRef,
    setMessages,
    input,
    setInput,
    setConnected,
    setStreaming,
    setStreamStatusText,
    setRuntimeLlmLabel,
    setLastExpertReason,
    setLastExpertKeywords,
    setShowExecutionPanel,
    setActivePlanMessageId,
    setActivePlanLocalMsgId,
    pendingPlanTasksRef,
    scheduleListsRefresh,
    formatRuntimeLlmLabel,
    parseAssistantDirectivesFromText,
    runUiActions,
    loadTaskTodos,
    loadGlobalTodos,
    loadTasks,
    buildSysGlobalKernelPrompt,
    maybeRepoDisambiguationInternalPrompt,
    fetchRuntimeLlmLabel,
    streaming,
  });

  const goHome = () => {
    setMessages([]);
    setCurrentConversation(null);
    setCurrentKind('conversation');
    hasHttpHydratedRef.current = false;
    setCenterView('chat');
    setChatSearch('');
    setConversationSearch('');
    setTasksSearch('');
    try {
      localStorage.removeItem('open_slap_current_conversation');
    } catch {}
    hasRestoredConversationRef.current = true;
    if (wsRef.current) {
      wsRef.current.close();
    }
    sessionId.current = `session_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
    connectWebSocket();
  };

  const createNewConversation = async (opts = {}) => {
    try {
      const headers = getAuthHeaders();
      headers['Content-Type'] = 'application/json';
      const projectIdToLink = Number(opts.projectId || 0);
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
      if (projectIdToLink) {
        await assignConversationProject(data.conversation_id, projectIdToLink);
      }
      connectWebSocket();
      // Carregar listas em segundo plano para evitar atraso na abertura do chat
      loadConversations().catch(() => {});
      loadTasks().catch(() => {});

      return data;
    } catch (error) {
      console.error('Error creating conversation:', error);
      return null;
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
      const projectIdToLink = Number(opts.projectId || 0);
      const kind = String(opts.kind || 'conversation').trim().toLowerCase();
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
      if (kind === 'task') {
        await createNewTask(
          projectIdToLink ? { projectId: projectIdToLink, skipPrefill: true } : { skipPrefill: true }
        );
      } else {
        await createNewConversation(projectIdToLink ? { projectId: projectIdToLink } : {});
      }
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

  function parseAssistantDirectivesFromText(text) {
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
  }

  function runUiActions(actions) {
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
  }

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

  const createNewTask = async (opts = {}) => {
    try {
      const headers = getAuthHeaders();
      headers['Content-Type'] = 'application/json';
      const projectIdToLink = Number(opts.projectId || 0);
      const skipPrefill = Boolean(opts.skipPrefill);
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

      if (!skipPrefill) {
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
      }

      await loadConversations();
      await loadTasks();
      await loadGlobalTodos();

      if (wsRef.current) {
        wsRef.current.close();
      }
      sessionId.current = data.session_id;
      if (projectIdToLink) {
        await assignConversationProject(data.conversation_id, projectIdToLink);
      }
      connectWebSocket();
      return data;
    } catch (error) {
      console.error('Error creating task:', error);
      return null;
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
  if (loading) {
    return (
      <div style={{ padding: '22px', fontFamily: 'var(--mono)', color: 'var(--text-dim)', fontSize: '12px' }}>
        {t('loading')}
      </div>
    );
  }
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
                    <div style={{ ...styles.commandActions, justifyContent: 'space-between', gap: '10px', alignItems: 'center' }}>
                      <button
                        style={{ ...styles.linkButton, fontSize: '12px' }}
                        onClick={() => {
                          setGenericModal({
                            title: lang === 'pt' ? 'Permissões de comando' : 'Command permissions',
                            body: lang === 'pt'
                              ? 'Permitir apenas agora executa este comando uma única vez.\n\nPermitir automaticamente salva uma permissão para executar automaticamente este comando (idêntico) no futuro.\n\nUse “Permitir automaticamente” apenas para comandos de baixo risco e bem conhecidos.'
                              : 'Allow only now executes this command once.\n\nAllow automatically saves a permission to auto-run this exact command in the future.\n\nUse “Allow automatically” only for low-risk, well-known commands.'
                          });
                        }}
                      >
                        {lang === 'pt' ? 'O que isso significa?' : 'What does this mean?'}
                      </button>
                      <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                      <button style={styles.settingsSecondaryButton} onClick={() => setCommandModal(null)}>
                        {t('cancel')}
                      </button>
                      <button
                        style={styles.settingsPrimaryButton}
                        onClick={() => executePendingCommand(commandModal)}
                        disabled={executingCommandId === commandModal?.id}
                      >
                        {executingCommandId === commandModal?.id
                          ? t('executing')
                          : (lang === 'pt' ? 'Permitir apenas agora' : 'Allow only now')}
                      </button>
                      <button
                        style={styles.settingsSecondaryButton}
                        onClick={async () => {
                          if (executingCommandId === commandModal?.id) return;
                          const ok = await autoApprovePendingCommand(commandModal);
                          if (!ok) return;
                          await executePendingCommand(commandModal);
                        }}
                        disabled={executingCommandId === commandModal?.id}
                      >
                        {lang === 'pt' ? 'Permitir automaticamente' : 'Allow automatically'}
                      </button>
                    </div>
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
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginBottom: '14px' }}>
                        {[0, 1, 2, 3, 4, 5].map((i) => (
                          <div
                            key={i}
                            style={{
                              height: '8px',
                              flex: 1,
                              borderRadius: '999px',
                              background: i === onboardingStep ? 'var(--accent)' : 'rgba(255,255,255,0.10)'
                            }}
                          />
                        ))}
                      </div>

                      {onboardingError ? <div style={styles.settingsError}>{onboardingError}</div> : null}

                      {onboardingStep === 0 ? (
                        <div style={{ display: 'grid', gap: '10px' }}>
                          <div style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.7 }}>
                            {t('language')}
                          </div>
                          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                            {[
                              { id: 'en', label: 'English' },
                              { id: 'pt', label: 'Português' },
                              { id: 'es', label: 'Español' },
                              { id: 'ar', label: 'العربية' },
                              { id: 'zh', label: '中文' }
                            ].map((opt) => {
                              const active = String(lang) === opt.id;
                              return (
                                <button
                                  key={opt.id}
                                  style={{
                                    ...styles.settingsSecondaryButton,
                                    borderColor: active ? 'var(--accent)' : 'rgba(255,255,255,0.15)',
                                    color: active ? 'var(--accent)' : 'var(--text)'
                                  }}
                                  onClick={() => {
                                    setLang(opt.id);
                                    saveLanguageSettings(opt.id);
                                  }}
                                >
                                  {opt.label}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}

                      {onboardingStep === 1 ? (
                        <div style={{ display: 'grid', gap: '10px' }}>
                          <div style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.7 }}>
                            {t('onboarding_theme_prompt')}
                          </div>
                          <div style={{ display: 'grid', gap: '10px', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
                            {[
                              { id: 'light', label: t('theme_light'), preview: ['#f5f5f5','#ffffff','#d97706'] },
                              { id: 'deep-space', label: 'Deep Space', preview: ['#0b1220','#0e1626','#22d3ee'] },
                              { id: 'midnight', label: 'Midnight', preview: ['#0a0a0a','#111111','#60a5fa'] }
                            ].map((th) => {
                              const isActive = String(theme) === th.id;
                              return (
                                <button
                                  key={th.id}
                                  style={{
                                    ...styles.smallIconButton,
                                    width: '100%',
                                    padding: '10px',
                                    borderRadius: '10px',
                                    border: isActive ? '1px solid var(--accent)' : '1px solid rgba(255,255,255,0.15)',
                                    background: 'rgba(255,255,255,0.04)'
                                  }}
                                  onClick={() => {
                                    setTheme(th.id);
                                    try { localStorage.setItem('open_slap_theme_v1', th.id); } catch {}
                                  }}
                                >
                                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', justifyContent: 'space-between' }}>
                                    {th.preview.map((c, i) => (
                                      <div key={i} style={{ width: 12, height: 12, borderRadius: '50%', background: c, border: '1px solid rgba(255,255,255,0.15)' }} />
                                    ))}
                                    <div style={{ fontSize: '10px', fontFamily: 'var(--mono)', color: th.preview[2], fontWeight: isActive ? 600 : 400, whiteSpace: 'nowrap' }}>
                                      {th.label}
                                    </div>
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}

                      {onboardingStep === 2 ? (
                        <div style={{ display: 'grid', gap: '10px' }}>
                          <div style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.7 }}>
                            {t('onboarding_intro')}
                          </div>
                          <div style={{ fontSize: '12px', color: 'var(--text-dim)', lineHeight: 1.6 }}>
                            {t('onboarding_welcome_hint')}
                          </div>
                        </div>
                      ) : null}

                      {onboardingStep === 3 ? (
                        <div style={{ display: 'grid', gap: '10px' }}>
                          <div style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.7 }}>
                            {t('onboarding_profile_intro')}
                          </div>
                          <div style={{ display: 'grid', gap: '10px' }}>
                            <div style={{ display: 'grid', gap: '6px' }}>
                              <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--mono)' }}>{t('name_label')}</div>
                              <input
                                style={styles.settingsInput}
                                value={onboardingSoulDraft?.name || ''}
                                onChange={(e) => setOnboardingSoulDraft((prev) => ({ ...(prev || {}), name: e.target.value }))}
                              />
                            </div>
                            <div style={{ display: 'grid', gap: '6px' }}>
                              <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--mono)' }}>{t('age_range_label')}</div>
                              <input
                                style={styles.settingsInput}
                                value={onboardingSoulDraft?.age_range || ''}
                                onChange={(e) => setOnboardingSoulDraft((prev) => ({ ...(prev || {}), age_range: e.target.value }))}
                                placeholder={t('age_range_placeholder')}
                              />
                            </div>
                            <div style={{ display: 'grid', gap: '6px' }}>
                              <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--mono)' }}>{t('goals_label')}</div>
                              <textarea
                                style={{ ...styles.settingsTextarea, minHeight: '90px' }}
                                value={onboardingSoulDraft?.goals || ''}
                                onChange={(e) => setOnboardingSoulDraft((prev) => ({ ...(prev || {}), goals: e.target.value }))}
                                placeholder={t('goals_placeholder')}
                              />
                            </div>
                          </div>
                        </div>
                      ) : null}

                      {onboardingStep === 4 ? (
                        <div style={{ display: 'grid', gap: '10px' }}>
                          <div style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.7 }}>
                            {t('onboarding_llm_intro')}
                          </div>
                          <div style={{ fontSize: '12px', color: 'var(--text-dim)', lineHeight: 1.6 }}>
                            {t('onboarding_llm_hint')}
                          </div>
                          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                            <button
                              style={styles.settingsSecondaryButton}
                              onClick={() => {
                                pendingSettingsActionRef.current = 'llm_api_key';
                                setShowOnboarding(false);
                                setCenterView('settings');
                              }}
                            >
                              {t('onboarding_open_llm_settings')}
                            </button>
                          </div>
                        </div>
                      ) : null}

                      {onboardingStep === 5 ? (
                        <div style={{ display: 'grid', gap: '12px' }}>
                          <div style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.7 }}>
                            {t('onboarding_how_to_start')}
                          </div>
                          {[
                            [t('onboarding_step_task_title'), t('onboarding_step_task_desc')],
                            [t('onboarding_step_skills_title'), t('onboarding_step_skills_desc')],
                            [t('onboarding_step_connectors_title'), t('onboarding_step_connectors_desc')]
                          ].map(([title, desc]) => (
                            <div key={title} style={{ marginBottom: '8px' }}>
                              <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--accent)', fontFamily: 'var(--sans)', marginBottom: '3px' }}>{title}</div>
                              <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--sans)', lineHeight: 1.5 }}>{desc}</div>
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </div>
                    <div style={{ ...styles.commandActions, justifyContent: 'flex-end' }}>
                      <button
                        style={styles.settingsSecondaryButton}
                        onClick={() => setShowOnboarding(false)}
                        disabled={onboardingActionLoading}
                      >
                        {t('onboarding_explore')}
                      </button>
                      <button
                        style={styles.settingsSecondaryButton}
                        onClick={() => setShowOnboarding(false)}
                        disabled={onboardingActionLoading}
                      >
                        {t('onboarding_skip')}
                      </button>
                      <button
                        style={styles.settingsSecondaryButton}
                        onClick={async () => {
                          await completeOnboarding();
                          setShowOnboarding(false);
                        }}
                        disabled={onboardingActionLoading}
                      >
                        {t('onboarding_dont_show')}
                      </button>
                      {onboardingStep > 0 ? (
                        <button
                          style={styles.settingsSecondaryButton}
                          onClick={() => setOnboardingStep((s) => Math.max(0, (Number(s) || 0) - 1))}
                          disabled={onboardingActionLoading}
                        >
                          {t('onboarding_back')}
                        </button>
                      ) : null}
                      {onboardingStep < 5 ? (
                        <button
                          style={styles.settingsPrimaryButton}
                          onClick={async () => {
                            if (onboardingStep === 0) {
                              try { await saveLanguageSettings(lang); } catch {}
                            }
                            if (onboardingStep === 3) {
                              const ok = await saveOnboardingSoulDraft();
                              if (!ok) return;
                            }
                            setOnboardingStep((s) => Math.min(5, (Number(s) || 0) + 1));
                          }}
                          disabled={onboardingSoulSaving || onboardingActionLoading}
                        >
                          {onboardingSoulSaving ? t('saving') : t('onboarding_next')}
                        </button>
                      ) : (
                        <button
                          style={styles.settingsPrimaryButton}
                          onClick={() => {
                            setShowOnboarding(false);
                            startNewConversationWithPrompt(
                              lang === 'pt' ? 'Quero iniciar um novo projeto.' : 'I want to start a new project.',
                              { internalPrompt: buildStartProjectPrompt(), forceExpertId: 'general' }
                            );
                          }}
                          disabled={onboardingActionLoading}
                        >
                          {t('onboarding_start_first_task')}
                        </button>
                      )}
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
                      {conversations.length ? (
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
                      ) : null}
                      {conversations.length === 0 ? (
                        renderBootScreen()
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
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                              {lang === 'pt' ? 'PROJETO (KICKOFF)' : 'PROJECT (KICKOFF)'}
                            </div>
                            <button
                              style={styles.smallIconButton}
                              onClick={() => {
                                setGenericModal({
                                  title: lang === 'pt' ? 'Como usar o Kickoff' : 'How to use Kickoff',
                                  body:
                                    lang === 'pt'
                                      ? '1) Crie/ative um projeto\n2) Importe um arquivo .md com o contexto\n3) O sistema gera um plano (bloco ```plan)\n4) Clique Aprovar para criar o backlog (TODOs) e iniciar a execução\n\nDica: use os templates em docs/kickoff_templates/.'
                                      : '1) Create/activate a project\n2) Import a .md file with context\n3) The system emits a plan (```plan block)\n4) Click Approve to create the backlog (TODOs) and start execution\n\nTip: use templates in docs/kickoff_templates/.'
                                });
                              }}
                              title={lang === 'pt' ? 'Como usar' : 'How to use'}
                            >
                              ?
                            </button>
                          </div>
                          <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--sans)' }}>
                            {lang === 'pt'
                              ? 'Este é o artefato global de kickoff: um contexto por projeto (Markdown). A Sabrina pode gerar/atualizar esse conteúdo durante o processo de criação do projeto.'
                              : 'This is the global kickoff artifact: one Markdown context per project. Sabrina can generate/update this content during project kickoff.'}
                          </div>

                          <div style={{ marginTop: '10px', padding: '10px 12px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: '8px' }}>
                            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                              {lang === 'pt' ? 'CRIAR NOVO PROJETO' : 'CREATE NEW PROJECT'}
                            </div>
                            <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
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
                                    setTimeout(() => {
                                      const fileEl = document.getElementById('kickoff-file-input');
                                      if (fileEl && typeof fileEl.scrollIntoView === 'function') {
                                        fileEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                      }
                                    }, 0);
                                  }
                                  if (el) el.value = '';
                                }}
                              >
                                {lang === 'pt' ? 'Criar' : 'Create'}
                              </button>
                            </div>
                          </div>

                          <div style={{ marginTop: '10px', padding: '10px 12px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', borderRadius: '8px' }}>
                            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                              {lang === 'pt' ? 'MEUS PROJETOS' : 'YOUR PROJECTS'}
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
                                  <div style={{ flex: 1, fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    📁 {proj.name}
                                  </div>
                                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
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
                                    <button
                                      style={styles.smallIconButton}
                                      title={lang === 'pt' ? 'Renomear' : 'Rename'}
                                      onClick={() => openRename('project', { id: proj.id, title: proj.name })}
                                    >
                                      ✎
                                    </button>
                                    <button
                                      style={styles.smallIconButton}
                                      title={lang === 'pt' ? 'Excluir' : 'Delete'}
                                      onClick={() => {
                                        setGenericModal({
                                          title: lang === 'pt' ? 'Excluir projeto?' : 'Delete project?',
                                          body: lang === 'pt'
                                            ? `Excluir "${proj.name}"? Isso remove o projeto e desvincula conversas/tarefas associadas.`
                                            : `Delete "${proj.name}"? This removes the project and unlinks associated conversations/tasks.`,
                                          onConfirm: async () => {
                                            const ok = await deleteProject(proj.id);
                                            if (!ok) {
                                              setGenericModal({
                                                title: t('error'),
                                                body: lang === 'pt' ? 'Não foi possível excluir o projeto.' : 'Could not delete the project.'
                                              });
                                            }
                                          }
                                        });
                                      }}
                                    >
                                      🗑
                                    </button>
                                  </div>
                                </div>
                              ))}
                              {projects.length === 0 ? (
                                <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                  {lang === 'pt' ? 'Nenhum projeto ainda.' : 'No projects yet.'}
                                </div>
                              ) : null}
                            </div>
                          </div>

                          {activeProjectId ? (
                            <div style={{ marginTop: '12px' }}>
                              <div style={styles.settingsLabel}>
                                {lang === 'pt' ? 'Contexto do projeto (Markdown)' : 'Project context (Markdown)'}
                              </div>
                              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '8px', flexWrap: 'wrap' }}>
                                <input
                                  id="kickoff-file-input"
                                  type="file"
                                  accept=".txt,.md"
                                  style={{ ...styles.settingsInput, flex: 1, paddingTop: '8px', paddingBottom: '8px' }}
                                  disabled={settingsLoading || projectContextSaving || !activeProjectId}
                                  onChange={(e) => {
                                    const file = e.target.files && e.target.files[0];
                                    e.target.value = '';
                                    if (!file) return;
                                    ingestKickoffFileToProjectContext(file);
                                  }}
                                />
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
                          <div style={{ marginTop: '10px', display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                            {[
                              { id: 'project', label: t('todo_scope_project') },
                              { id: 'personal', label: t('todo_scope_personal') },
                              { id: 'all', label: t('todo_scope_all') },
                            ].map((opt) => {
                              const active = String(globalTodoScope) === opt.id;
                              return (
                                <button
                                  key={opt.id}
                                  style={{
                                    ...styles.settingsSecondaryButton,
                                    borderColor: active ? 'var(--accent)' : 'rgba(255,255,255,0.15)',
                                    color: active ? 'var(--accent)' : 'var(--text)'
                                  }}
                                  onClick={() => setGlobalTodoScope(opt.id)}
                                >
                                  {opt.label}
                                </button>
                              );
                            })}
                            <button
                              style={{
                                ...styles.settingsSecondaryButton,
                                borderColor: globalTodoShowAgent ? 'var(--accent)' : 'rgba(255,255,255,0.15)',
                                color: globalTodoShowAgent ? 'var(--accent)' : 'var(--text)'
                              }}
                              onClick={() => setGlobalTodoShowAgent((v) => !v)}
                            >
                              {t('todo_show_agent')}
                            </button>
                          </div>
                          {globalTodos.length ? (
                            <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
                              {(() => {
                                const filtered = (globalTodos || []).filter((td) => {
                                  const scope = getTodoScope(td);
                                  const actor = getTodoActor(td);
                                  if (!globalTodoShowAgent && actor === 'agent') return false;
                                  if (String(globalTodoScope) === 'all') return true;
                                  return scope === String(globalTodoScope);
                                });
                                const groups = {};
                                for (const td of filtered) {
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
                                  const scope = getTodoScope(node);
                                  const actor = getTodoActor(node);
                                  const actorLabel = actor === 'agent' ? (lang === 'pt' ? 'agente' : 'agent') : (lang === 'pt' ? 'humano' : 'human');
                                  const scopeLabel = scope === 'personal' ? t('todo_scope_personal') : t('todo_scope_project');
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
                                                {ctx.taskTitle} • {scopeLabel} • {actorLabel} • {formatCompactDateTime(node.created_at)}
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
                          { id: 'system', label: t('system') },
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
                            <div style={{ marginTop: '10px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={async () => {
                                  await resetOnboarding();
                                  setShowOnboarding(true);
                                }}
                                disabled={settingsLoading}
                              >
                                {t('reopen_onboarding')}
                              </button>
                            </div>
                          </div>

                        </>
                      ) : null}

                      {settingsTab === 'system' ? (
                        <SystemSettingsPanel
                          styles={styles}
                          t={t}
                          lang={lang}
                          settingsLoading={settingsLoading}
                          doctorError={doctorError}
                          doctorReport={doctorReport}
                          doctorLoading={doctorLoading}
                          refreshSystemProfile={refreshSystemProfile}
                          fetchDoctorReport={fetchDoctorReport}
                          getDoctorLabel={getDoctorLabel}
                          setSettingsTab={setSettingsTab}
                          systemMapLoading={systemMapLoading}
                          systemMapError={systemMapError}
                          systemMapUpdatedAt={systemMapUpdatedAt}
                          systemMapText={systemMapText}
                          fetchSystemMap={fetchSystemMap}
                        />
                      ) : null}

                      {settingsTab === 'llm' ? (
                        <LlmSettingsPanel
                          styles={styles}
                          t={t}
                          lang={lang}
                          settingsLoading={settingsLoading}
                          llmMode={llmMode}
                          setLlmMode={setLlmMode}
                          llmProvider={llmProvider}
                          setLlmProvider={setLlmProvider}
                          llmModel={llmModel}
                          setLlmModel={setLlmModel}
                          llmBaseUrl={llmBaseUrl}
                          setLlmBaseUrl={setLlmBaseUrl}
                          llmApiKey={llmApiKey}
                          setLlmApiKey={setLlmApiKey}
                          llmHasApiKey={llmHasApiKey}
                          llmApiKeySource={llmApiKeySource}
                          llmApiKeyOpen={llmApiKeyOpen}
                          setLlmApiKeyOpen={setLlmApiKeyOpen}
                          llmApiKeyInputRef={llmApiKeyInputRef}
                          llmProviderKeys={llmProviderKeys}
                          llmProviderKeysLoading={llmProviderKeysLoading}
                          llmProviderKeysError={llmProviderKeysError}
                          setActiveLlmProviderKey={setActiveLlmProviderKey}
                          deleteLlmProviderKey={deleteLlmProviderKey}
                          saveLlmSettings={saveLlmSettings}
                          removeLlmApiKey={removeLlmApiKey}
                          llmHasStoredApiKey={llmHasStoredApiKey}
                          llmHasEnvApiKey={llmHasEnvApiKey}
                          providerStatusList={providerStatusList}
                          providerStatusLoading={providerStatusLoading}
                          providerStatusError={providerStatusError}
                          loadProviderStatus={loadProviderStatus}
                        />
                      ) : null}

                      {settingsTab === 'security' ? (
                        <SecuritySettingsPanel
                          styles={styles}
                          t={t}
                          lang={lang}
                          settingsLoading={settingsLoading}
                          securitySettings={securitySettings}
                          securitySettingsUpdatedAt={securitySettingsUpdatedAt}
                          applySecuritySettingChange={applySecuritySettingChange}
                          setGenericModal={setGenericModal}
                          authSettings={authSettings}
                          authSettingsUpdatedAt={authSettingsUpdatedAt}
                          jwtExpireMinutesDraft={jwtExpireMinutesDraft}
                          setJwtExpireMinutesDraft={setJwtExpireMinutesDraft}
                          authSettingsSaving={authSettingsSaving}
                          applyJwtExpiryChange={applyJwtExpiryChange}
                          autoApproveCommands={autoApproveCommands}
                          autoApproveCommandsLoading={autoApproveCommandsLoading}
                          autoApproveCommandsError={autoApproveCommandsError}
                          loadAutoApproveCommands={loadAutoApproveCommands}
                          deleteAutoApproveCommand={deleteAutoApproveCommand}
                        />
                      ) : null}

                      {settingsTab === 'connectors' ? (
                        <>
                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{t('connectors') || 'Conectores'}</div>
                            <div style={{ marginTop: '6px', marginBottom: '8px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', lineHeight: 1.5 }}>
                              {t('connectors_oauth_hint')}
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
                            <div style={styles.settingsSectionTitle}>{lang === 'pt' ? 'Memória (Dream)' : 'Memory (Dream)'}</div>
                            <div style={styles.settingsHint}>
                              {lang === 'pt'
                                ? 'O Dream consolida memórias derivadas (snapshot) e faz higiene (decay/prune). O histórico RAW (SQL) não é apagado.'
                                : 'Dream consolidates derived memories (snapshot) and performs hygiene (decay/prune). RAW history (SQL) is never deleted.'}
                            </div>
                            <div style={styles.settingsActions}>
                              <button
                                style={styles.settingsPrimaryButton}
                                onClick={runMemoryDream}
                                disabled={settingsLoading || memoryDreamLoading}
                              >
                                {memoryDreamLoading ? (lang === 'pt' ? 'Executando…' : 'Running…') : (lang === 'pt' ? 'Rodar Dream' : 'Run Dream')}
                              </button>
                            </div>
                            {(memoryDreamSnapshot || memoryDreamDecayed || memoryDreamPruned) ? (
                              <div style={{ marginTop: '10px' }}>
                                <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                  {lang === 'pt'
                                    ? `decayed=${memoryDreamDecayed} • pruned=${memoryDreamPruned}`
                                    : `decayed=${memoryDreamDecayed} • pruned=${memoryDreamPruned}`}
                                </div>
                                <textarea
                                  style={{ ...styles.settingsTextarea, minHeight: '140px', marginTop: '8px' }}
                                  value={memoryDreamSnapshot}
                                  readOnly
                                  placeholder={lang === 'pt' ? 'Snapshot vazio.' : 'Empty snapshot.'}
                                />
                              </div>
                            ) : null}
                          </div>

                          <div style={styles.settingsSection}>
                            <div style={styles.settingsSectionTitle}>{lang === 'pt' ? 'Pesquisar memória RAW' : 'Search RAW memory'}</div>
                            <div style={styles.settingsHint}>
                              {lang === 'pt'
                                ? 'Pesquisa no histórico bruto em SQL (mensagens). Não altera nem apaga o RAW.'
                                : 'Searches the raw SQL history (messages). Does not alter or delete RAW.'}
                            </div>
                            <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
                              <input
                                style={{ ...styles.settingsInput, flex: 1, minWidth: '240px' }}
                                value={rawMemoryQuery}
                                onChange={(e) => setRawMemoryQuery(e.target.value)}
                                placeholder={lang === 'pt' ? 'Ex.: kickoff, orçamento, nome do projeto…' : 'E.g., kickoff, budget, project name…'}
                                disabled={rawMemoryLoading}
                              />
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={searchRawMemory}
                                disabled={rawMemoryLoading || !String(rawMemoryQuery || '').trim()}
                              >
                                {rawMemoryLoading ? t('loading') : t('search')}
                              </button>
                            </div>
                            {rawMemoryError ? (
                              <div style={{ ...styles.settingsError, marginTop: '8px' }}>{rawMemoryError}</div>
                            ) : null}
                            {(rawMemoryResults || []).length ? (
                              <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
                                {rawMemoryResults.slice(0, 25).map((r) => {
                                  const cid = r?.conversation_id;
                                  const sid = r?.session_id;
                                  const ckind = String(r?.conversation_kind || '').trim().toLowerCase();
                                  const kindOverride = ckind === 'task' ? 'task' : 'conversation';
                                  return (
                                    <div
                                      key={`${r?.message_id || ''}-${r?.conversation_id || ''}`}
                                      style={{ ...styles.lightCard, padding: '10px 12px' }}
                                    >
                                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                          <div style={{ fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {r?.conversation_title || `#${cid}`}
                                          </div>
                                          <div style={{ marginTop: '4px', fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                            {formatCompactDateTime(r?.message_created_at || '')}
                                          </div>
                                          <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--sans)' }}>
                                            {r?.snippet || ''}
                                          </div>
                                        </div>
                                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                          <button
                                            style={styles.settingsSecondaryButton}
                                            onClick={() => loadConversation(cid, sid, kindOverride)}
                                          >
                                            {lang === 'pt' ? 'Abrir' : 'Open'}
                                          </button>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            ) : null}
                          </div>

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
                            <div style={styles.settingsSectionTitle}>{lang === 'pt' ? 'Importar dados de memória externos' : 'Import external memory data'}</div>
                            <div style={styles.settingsHint}>
                              {lang === 'pt'
                                ? 'Use o prompt abaixo no seu outro provedor de IA para gerar um resumo em Markdown. Depois, envie o arquivo .md aqui para importar como memória com a origem “imported”.'
                                : 'Use the prompt below in your other AI provider to generate a Markdown summary. Then upload the .md file here to import it as memory with “imported” provenance.'}
                            </div>
                            <textarea
                              style={{ ...styles.settingsTextarea, minHeight: '180px', marginTop: '8px' }}
                              value={
                                `Importar dados de memória para o Open Slap\n\n## Copie este comando e cole em uma conversa com seu outro provedor de IA\n\nVocê está me ajudando a importar o contexto de um assistente de IA para outro. Seu trabalho é analisar nossas conversas anteriores e resumir o que você sabe sobre mim.\n\nNa resposta, evite usar pronomes na primeira pessoa (eu, meu, minha, me) e na segunda pessoa (você, seu, sua). Em vez disso, use \"o usuário\" ou outro termo neutro para se referir ao indivíduo com essas características.\n\nPreserve as palavras do usuário ao pé da letra sempre que possível, especialmente para instruções e preferências.\n\nCategorias (resposta nesta ordem):\n\n1. Informações demográficas: como gosto que me chamem, profissão, formação acadêmica e local onde moro.\n\n2. Interesses e preferências: coisas com que me envolvo de modo ativo e contínuo, não apenas um objeto que eu tenho ou uma compra que fiz uma vez.\n\n3. Relacionamentos: relacionamentos confirmados e de longo prazo.\n\n4. Eventos, projetos e planos: um registro de atividades recentes e significativas.\n\n5. Instruções: regras que pedi explicitamente para você seguir, como \"sempre faça X\", \"nunca faça Y\" e correções no seu comportamento. Inclua apenas regras de dados de memória armazenados, não de conversas.\n\nFormato:\n\nDivida o conteúdo em seções rotuladas usando as categorias acima. Tente incluir citações de comandos meus que justifiquem cada resposta. Estruture cada item usando este formato:\n\nO nome do usuário é <name>.\n\n– Evidência: o usuário disse \"me chame de <name>\". Data: [YYYY-MM-DD].\n\nSaída:\n\n– Formate o resumo da resposta final como um bloco de texto md.`
                              }
                              readOnly
                            />
                            <div style={{ display: 'grid', gap: '8px', marginTop: '8px' }}>
                              <div style={styles.settingsField}>
                                <div style={styles.settingsLabel}>{lang === 'pt' ? 'Provedor/Origem (opcional)' : 'Provider/Source (optional)'}</div>
                                <input
                                  style={styles.settingsInput}
                                  value={externalMemoryProvider}
                                  onChange={(e) => setExternalMemoryProvider(e.target.value)}
                                  placeholder={lang === 'pt' ? 'ex.: claude, chatgpt' : 'e.g., claude, chatgpt'}
                                  disabled={settingsLoading || externalMemoryUploading}
                                />
                              </div>
                              <input
                                type="file"
                                accept=".md"
                                style={{ ...styles.settingsInput, paddingTop: '8px', paddingBottom: '8px' }}
                                disabled={settingsLoading || externalMemoryUploading}
                                onChange={async (e) => {
                                  const file = e.target.files && e.target.files[0];
                                  e.target.value = '';
                                  if (!file) return;
                                  try {
                                    setExternalMemoryUploading(true);
                                    const md = await new Promise((resolve, reject) => {
                                      const r = new FileReader();
                                      r.onerror = () => reject(new Error('Failed to read file.'));
                                      r.onload = () => resolve(String(r.result || ''));
                                      r.readAsText(file);
                                    });
                                    const headers = getAuthHeaders();
                                    if (!headers.Authorization) return;
                                    headers['Content-Type'] = 'application/json';
                                    const res = await fetch('/api/memory/import', {
                                      method: 'POST',
                                      headers,
                                      body: JSON.stringify({
                                        markdown: String(md || ''),
                                        provider: String(externalMemoryProvider || ''),
                                        label: String(file?.name || ''),
                                        split_by_category: true
                                      })
                                    });
                                    const json = await res.json().catch(() => ({}));
                                    if (!res.ok) {
                                      throw new Error(json?.detail || 'Failed to import memory.');
                                    }
                                    loadExternalMemoryImports({ silent: true });
                                    setGenericModal({
                                      title: lang === 'pt' ? 'Importado' : 'Imported',
                                      body: lang === 'pt'
                                        ? 'Memória importada. A seção “Instruções” foi fixada automaticamente.'
                                        : 'Memory imported and recorded with “imported” provenance.'
                                    });
                                  } catch (e) {
                                    setGenericModal({
                                      title: t('error'),
                                      body: e?.message || 'Failed to import memory.'
                                    });
                                  } finally {
                                    setExternalMemoryUploading(false);
                                  }
                                }}
                              />
                            </div>
                            <div style={{ marginTop: '10px' }}>
                              <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                {lang === 'pt' ? 'Importações recentes' : 'Recent imports'}
                              </div>
                              {externalMemoryImportsError ? (
                                <div style={{ ...styles.settingsError, marginTop: '8px' }}>{externalMemoryImportsError}</div>
                              ) : null}
                              {externalMemoryImportsLoading ? (
                                <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                  {t('loading')}
                                </div>
                              ) : (
                                <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
                                  {(externalMemoryImports || []).length ? (
                                    (externalMemoryImports || []).slice(0, 12).map((imp) => {
                                      const importId = String(imp?.import_id || '').trim();
                                      const provider = String(imp?.provider || '').trim();
                                      const createdAt = String(imp?.created_at || '').trim();
                                      const firstContent = String(imp?.items?.[0]?.content || '');
                                      const labelMatch = firstContent.match(/label:\s*([^,)]+)/i);
                                      const label = String(labelMatch?.[1] || '').trim();
                                      const pinned = Boolean(imp?.pinned);
                                      const count = Number(imp?.count || 0) || (imp?.items?.length || 0);
                                      return (
                                        <div key={importId || createdAt} style={{ ...styles.lightCard, padding: '10px 12px' }}>
                                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                                            <div style={{ flex: 1, minWidth: 0 }}>
                                              <div style={{ fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', fontWeight: 600, wordBreak: 'break-word' }}>
                                                {label || (lang === 'pt' ? 'Importação de memória' : 'Memory import')}
                                              </div>
                                              <div style={{ marginTop: '4px', fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                                {(provider ? `provider=${provider} • ` : '')}{count ? `${count} ${lang === 'pt' ? 'seções' : 'sections'} • ` : ''}{formatCompactDateTime(createdAt)}
                                                {pinned ? ` • ${lang === 'pt' ? 'fixado' : 'pinned'}` : ''}
                                              </div>
                                            </div>
                                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                              <button
                                                style={styles.settingsSecondaryButton}
                                                onClick={() => setExternalMemoryImportPinned(importId, !pinned)}
                                                disabled={externalMemoryUploading || !importId}
                                              >
                                                {pinned ? (lang === 'pt' ? 'Desfixar' : 'Unpin') : (lang === 'pt' ? 'Fixar' : 'Pin')}
                                              </button>
                                              <button
                                                style={styles.settingsSecondaryButton}
                                                onClick={() => {
                                                  setGenericModal({
                                                    title: lang === 'pt' ? 'Remover importação' : 'Remove import',
                                                    body: lang === 'pt'
                                                      ? 'Remover esta importação de memória? Isto apaga os eventos importados.'
                                                      : 'Remove this memory import? This deletes the imported events.',
                                                    onConfirm: async () => {
                                                      await deleteExternalMemoryImport(importId);
                                                    }
                                                  });
                                                }}
                                                disabled={externalMemoryUploading || !importId}
                                              >
                                                {lang === 'pt' ? 'Remover' : 'Remove'}
                                              </button>
                                            </div>
                                          </div>
                                        </div>
                                      );
                                    })
                                  ) : (
                                    <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                                      {lang === 'pt' ? 'Nenhuma importação ainda.' : 'No imports yet.'}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
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
                          renderBootScreen()
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
                                                planUi={{
                                                  approved: Boolean(approvedPlanLocalMsgIds[message.id]),
                                                  running: (orchStatus === 'running' && message.id === activePlanLocalMsgId && Number(currentConversation) === Number(activePlanConvId))
                                                }}
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
                                                    setApprovedPlanLocalMsgIds(prev => ({ ...prev, [message.id]: true }));
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
                                {message.role === 'assistant' && !message.streaming ? (
                                  <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'flex-end' }}>
                                    <button
                                      style={{
                                        ...styles.settingsSecondaryButton,
                                        padding: '6px 10px',
                                        fontSize: '11px',
                                        opacity: savedInfoLocalMsgIds[message.id] ? 0.8 : 1
                                      }}
                                      onClick={() => saveAssistantInfo(message)}
                                      disabled={Boolean(savedInfoLocalMsgIds[message.id])}
                                    >
                                      {savedInfoLocalMsgIds[message.id]
                                        ? (lang === 'pt' ? 'Salvo' : 'Saved')
                                        : (lang === 'pt' ? 'Salvar informações' : 'Save info')}
                                    </button>
                                  </div>
                                ) : null}
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
