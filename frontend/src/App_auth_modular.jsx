import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import useAuth from './hooks/useAuth';
import useChatSocket from './hooks/useChatSocket';
import { useConversations } from './hooks';
import { useDoctor } from './hooks';
import { useSkills } from './hooks';
import { useSettings } from './hooks';
import { useSoul } from './hooks';
import { useLLMConfig } from './hooks';
import { buildSysGlobalKernelPrompt } from './lib/kernelPrompt';
import { maybeRepoDisambiguationInternalPrompt } from './lib/repoDisambiguation';
import { translations } from './i18n/translations_auth';
import { buildAppAuthStyles } from './styles/appAuthStyles';
import { BUILTIN_SKILL_I18N, BUILTIN_EXPERT_I18N } from './data/skillI18n';
import SystemSettingsPanel from './components/settings/SystemSettingsPanel';
import LlmSettingsPanel from './components/settings/LlmSettingsPanel';
import SecuritySettingsPanel from './components/settings/SecuritySettingsPanel';
import { OnboardingModal } from './components/onboarding';
import { DoctorPanel } from './components/panels';
import { SkillsPanel } from './components/panels';
import CLIDisplay from './components/CLIDisplay';
import MessageBlock from './components/MessageBlock';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  formatCompactDateTime,
  generateSessionId,
  parseMessageBlocks,
  parsePlanTasksFromText,
  extractTaggedJsonBlocks,
  parseCommandRequestsFromContent,
  getBuiltinMeta,
  getBootGreeting,
} from './lib/utils';

const OPEN_SLAP_ASCII_FONT =
  '"Cascadia Mono", Consolas, "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, "Liberation Mono", "Courier New", monospace';
const OPEN_SLAP_VERSION = 'v2.1';
const OPEN_SLAP_ASCII = `open_slap > boot
---------------------------------------------------------
    (ASCII art mantido do original)
---------------------------------------------------------`;

const App = () => {
  const { user, loading, login, register, logout, getAuthHeaders, isAuthenticated, token, requestPasswordReset, confirmPasswordReset } = useAuth();

  // i18n
  const [lang, setLang] = useState('pt');
  const t = (key) => {
    const table = translations[lang] || translations.en || translations.pt;
    return table[key] || (translations.en && translations.en[key]) || translations.pt[key] || key;
  };

  // Hooks de dados
  const { conversations, currentConversation, setCurrentConversation, createConversation, deleteConversation, loadConversations, conversationsLoading } = useConversations();
  const { doctorReport, isChecking, runCheck, loadSystemMap } = useDoctor();
  const { skills, experts, toggleSkill, updateSkill, getSkillsBySegment, skillsLoading } = useSkills();
  const { settings, updateSetting, resetSettings, isLoading: settingsLoading, setLang: setSettingsLang } = useSettings();
  const { soulData, updateSoulData, loadSoul } = useSoul();
  const { llmConfig, updateLLMConfig, testConnection, providerStatus } = useLLMConfig();

  // Estado de mensagens (useState puro para compatibilidade com useChatSocket)
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [bootInput, setBootInput] = useState('');

  // Estado WebSocket
  const [connected, setConnected] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamStatusText, setStreamStatusText] = useState('');
  const [runtimeLlmLabel, setRuntimeLlmLabel] = useState('');
  const [lastExpertReason, setLastExpertReason] = useState('');
  const [lastExpertKeywords, setLastExpertKeywords] = useState([]);
  const [loadingTick, setLoadingTick] = useState(0);

  // Estado UI
  const [centerView, setCenterView] = useState('chat');
  const [settingsTab, setSettingsTab] = useState('general');
  const [showExecutionPanel, setShowExecutionPanel] = useState(false);
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = useState(false);
  const [showConversationList, setShowConversationList] = useState(false);

  // Estado de aprovação de planos
  const [approvedPlanLocalMsgIds, setApprovedPlanLocalMsgIds] = useState({});
  const [activePlanMessageId, setActivePlanMessageId] = useState(null);
  const [activePlanLocalMsgId, setActivePlanLocalMsgId] = useState(null);
  const [orchStatus, setOrchStatus] = useState('');
  const [orchLog, setOrchLog] = useState([]);
  const orchPollRef = useRef(null);

  // Estado de comandos
  const [commandModal, setCommandModal] = useState(null);
  const [executingCommandId, setExecutingCommandId] = useState('');
  const [executedCommandIds, setExecutedCommandIds] = useState({});

  // Estado misc
  const [selectedSkillId, setSelectedSkillId] = useState('');
  const [forceExpertId, setForceExpertId] = useState('');
  const [agentConfigs, setAgentConfigs] = useState({});
  const [llmMode, setLlmMode] = useState('auto');
  const [showRoutingDebug, setShowRoutingDebug] = useState(false);
  const [chatFontScale, setChatFontScale] = useState(1);
  const [chatSearchQuery, setChatSearchQuery] = useState('');
  const [isMobile, setIsMobile] = useState(false);
  const [currentKind, setCurrentKind] = useState('conversation');
  const [chatSearch, setChatSearch] = useState('');
  const [messageFeedback, setMessageFeedback] = useState({});

  // Refs
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const hasHttpHydratedRef = useRef(false);
  const pendingAutoSendRef = useRef(null);
  const autoStartRef = useRef(false);
  const sessionIdRef = useRef(generateSessionId());
  const pendingPlanTasksRef = useRef({});

  // Tick de loading para animações
  useEffect(() => {
    if (!streaming) return;
    const id = setInterval(() => setLoadingTick(v => v + 1), 250);
    return () => clearInterval(id);
  }, [streaming]);

  // Loading screen
  useEffect(() => {
    document.body.classList.toggle('loaded', !loading);
  }, [loading]);

  // Mobile detection
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  // Load initial data
  useEffect(() => {
    if (!isAuthenticated) return;
    loadConversations();
    if (typeof loadSoul === 'function') loadSoul();
  }, [isAuthenticated]);

  // Schedule helpers for useChatSocket
  const scheduleListsRefresh = useCallback(() => {}, []);

  const formatRuntimeLlmLabel = (provider, model, mode) => {
    const p = String(provider || '').trim();
    const m = String(model || '').trim();
    if (!p && !m) return '';
    return `${p}/${m}`;
  };

  const parseAssistantDirectivesFromText = (text) => ({});
  const runUiActions = (actions) => {
    if (!Array.isArray(actions)) return;
    for (const a of actions) {
      if (a?.type === 'show_execution_panel') setShowExecutionPanel(true);
    }
  };
  const loadTaskTodos = (convId) => {};
  const loadGlobalTodos = () => {};
  const loadTasks = () => {};
  const fetchRuntimeLlmLabel = () => {};

  // WebSocket Hook
  useChatSocket({
    user, token, lang, llmMode, skills, selectedSkillId, forceExpertId, agentConfigs,
    showRoutingDebug, currentConversation, currentKind, sessionIdRef, wsRef,
    pendingAutoSendRef, messagesEndRef, setMessages, input, setInput,
    setConnected, setStreaming, setStreamStatusText, setRuntimeLlmLabel,
    setLastExpertReason, setLastExpertKeywords, setShowExecutionPanel,
    setActivePlanMessageId, setActivePlanLocalMsgId, pendingPlanTasksRef,
    scheduleListsRefresh, formatRuntimeLlmLabel, parseAssistantDirectivesFromText,
    runUiActions, loadTaskTodos, loadGlobalTodos, loadTasks,
    buildSysGlobalKernelPrompt, maybeRepoDisambiguationInternalPrompt,
    fetchRuntimeLlmLabel, streaming,
  });

  // Styles
  const styles = buildAppAuthStyles({ connected });

  // Handlers
  const handleSendMessage = () => {
    if (!input.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    const now = Date.now();
    const contentRaw = input.trim();
    const extraPrompt = maybeRepoDisambiguationInternalPrompt({ lang, text: contentRaw });
    const userMessage = { role: 'user', content: contentRaw, id: `${now}-${Math.random().toString(16).slice(2)}` };
    setStreaming(true);
    setMessages(prev => [...prev, userMessage, { role: 'assistant', content: '', streaming: true, id: `${now + 1}-${Math.random().toString(16).slice(2)}` }]);
    setInput('');
    const activeSkill = (skills || []).find(s => s.id === selectedSkillId) || null;
    const agentPrompt = forceExpertId ? String(agentConfigs?.[forceExpertId]?.prompt || '').trim() : '';
    const kernelPrompt = buildSysGlobalKernelPrompt(lang);
    wsRef.current.send(JSON.stringify({
      type: 'chat', content: contentRaw,
      internal_prompt: [kernelPrompt, agentPrompt, extraPrompt].filter(Boolean).join('\n\n') || null,
      skill_id: activeSkill?.id || null, skill_web_search: activeSkill?.content?.web_search === true,
      force_expert_id: forceExpertId || null, debug_router: Boolean(showRoutingDebug),
    }));
  };

  const handleApprovePlan = (tlist) => {
    if (!currentConversation || !tlist?.length) return;
    setShowExecutionPanel(true);
    startOrchestration(currentConversation, tlist);
  };

  const startOrchestration = async (convId, tasks) => {
    setOrchStatus('running');
    try {
      const headers = getAuthHeaders();
      const res = await fetch(`/api/orchestrate/${encodeURIComponent(convId)}/start`, {
        method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ tasks }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || 'Failed');
      setOrchRunId(data.run_id);
    } catch (e) {
      setOrchStatus('failed');
      setOrchLog(prev => [...prev, `Erro: ${e.message}`]);
    }
  };

  const [orchRunId, setOrchRunId] = useState(null);

  const executePendingCommand = async (req) => {
    if (!req?.id || executingCommandId) return;
    try {
      setExecutingCommandId(req.id);
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      headers['Content-Type'] = 'application/json';
      const res = await fetch(`/api/commands/pending/${encodeURIComponent(req.id)}/execute`, {
        method: 'POST', headers, body: JSON.stringify({ confirm: true }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || 'Failed');
      setExecutedCommandIds(prev => ({ ...prev, [req.id]: true }));
      const output = data?.output || data?.stdout || '(sem saída)';
      setMessages(prev => [...prev, {
        role: 'assistant', content: `✅ Comando executado:\n${data?.command || req.command}\n\n${output}`,
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant', content: `❌ ${e.message}`,
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      }]);
    } finally {
      setExecutingCommandId('');
      setCommandModal(null);
    }
  };

  const openCliArtifact = (artifact) => {
    const url = String(artifact?.url || '').trim();
    const name = String(artifact?.name || 'artefato').trim() || 'artefato';
    if (!url) return;
    try {
      const a = document.createElement('a');
      a.href = url; a.download = name; a.target = '_blank'; a.rel = 'noopener noreferrer';
      document.body.appendChild(a); a.click(); a.remove();
    } catch (e) { console.error('Falha ao abrir artefato:', e); }
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

  const renderBootScreen = () => {
    const greeting = getBootGreeting(t, soulData, user);
    const asciiWithVersion = OPEN_SLAP_ASCII.replace('open_slap > boot', `open_slap > boot #${OPEN_SLAP_VERSION}#`);
    return (
      <div style={{ maxWidth: '920px', width: '100%', margin: '0 auto' }}>
        <div style={{ ...styles.lightCard, border: '1px solid rgba(255,255,255,0.10)' }}>
          <pre style={{ fontFamily: OPEN_SLAP_ASCII_FONT, fontSize: isMobile ? '10px' : '12px', lineHeight: 1.2, color: 'var(--text-dim)', textAlign: 'center' }}>
            {asciiWithVersion}
          </pre>
        </div>
        <div style={{ marginTop: '20px', color: 'var(--text)', fontSize: '16px', textAlign: 'center' }}>{greeting}</div>
        <div style={{ marginTop: '30px', display: 'flex', justifyContent: 'center' }}>
          <input value={bootInput} onChange={e => setBootInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && bootInput.trim()) { const v = bootInput.trim(); setBootInput(''); setInput(v); setCenterView('chat'); autoStartRef.current = true; pendingAutoSendRef.current = v; } }}
            placeholder={t('type_message')} style={{ ...styles.input, maxWidth: '500px', width: '100%', textAlign: 'center' }} autoFocus />
        </div>
      </div>
    );
  };

  return (
    <Router>
      {!isAuthenticated ? (
        <Routes>
          <Route path="/login" element={<Login onLogin={login} onRegister={register} onPasswordResetRequest={requestPasswordReset} onPasswordResetConfirm={confirmPasswordReset} t={t} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      ) : (
        <div style={styles.app}>
          {/* Command Modal */}
          {commandModal && (
            <div style={styles.modalOverlay} onClick={() => setCommandModal(null)}>
              <div style={styles.modal} onClick={e => e.stopPropagation()}>
                <div style={styles.modalHeader}>
                  <div>{t('command_approval')}</div>
                  <button style={styles.modalClose} onClick={() => setCommandModal(null)}>✕</button>
                </div>
                <div style={styles.modalBody}>
                  <div style={{ marginBottom: '12px', fontFamily: 'var(--mono)', fontSize: '12px', whiteSpace: 'pre-wrap' }}>
                    {commandModal.command}
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--text-dim)', marginBottom: '16px' }}>
                    {commandModal.intent || ''}
                  </div>
                  <button style={styles.settingsPrimaryButton} onClick={() => executePendingCommand(commandModal)}>
                    {t('execute')}
                  </button>
                </div>
              </div>
            </div>
          )}

          <OnboardingModal t={t} />

          {/* Header */}
          <div style={styles.header}>
            <button style={{ ...styles.iconButton, fontSize: '18px' }} onClick={() => setLeftSidebarCollapsed(v => !v)} title={t('menu')}>
              {leftSidebarCollapsed ? '☰' : '✕'}
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: connected ? 'var(--green)' : 'var(--red)', display: 'inline-block' }} />
              <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>{connected ? t('connected') : t('disconnected')}</span>
            </div>
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>{runtimeLlmLabel || ''}</span>
              <button onClick={() => { setCenterView('settings'); setSettingsTab('general'); }} style={styles.iconButton} title={t('settings')}>⚙️</button>
              <span style={{ fontSize: '12px', color: 'var(--text-dim)', cursor: 'pointer' }} onClick={logout}>{t('sign_out')}</span>
            </div>
          </div>

          <div style={styles.main}>
            {/* Left Sidebar */}
            <div style={{ ...styles.sidebar, width: leftSidebarCollapsed ? '0px' : '240px', overflow: 'hidden', transition: 'width 0.2s' }}>
              <div style={{ padding: '8px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '16px' }}>
                  {[
                    { key: 'chat', label: t('chat'), icon: '💬' },
                    { key: 'skills', label: t('skills'), icon: '🧠' },
                    { key: 'doctor', label: t('doctor'), icon: '🔍' },
                    { key: 'settings', label: t('settings'), icon: '⚙️' },
                  ].map(item => (
                    <button key={item.key} onClick={() => setCenterView(item.key)}
                      style={{ ...styles.sidebarButton, background: centerView === item.key ? 'var(--accent-bg)' : 'transparent' }}>
                      <span>{item.icon}</span>
                      <span>{item.label}</span>
                    </button>
                  ))}
                </div>
                {/* Conversations list */}
                <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '8px', padding: '0 8px' }}>
                  {t('conversations')}
                </div>
                {conversations?.slice(0, 10).map(conv => (
                  <button key={conv.id} onClick={() => { setCurrentConversation(conv.id); setCenterView('chat'); }}
                    style={{ ...styles.sidebarButton, fontSize: '12px', padding: '4px 8px', background: Number(currentConversation) === Number(conv.id) ? 'var(--accent-bg)' : 'transparent', textAlign: 'left', width: '100%' }}>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {conv.title || `${t('conversation_label')} ${String(conv.id).slice(0, 8)}`}
                    </span>
                  </button>
                ))}
                <button onClick={() => createConversation({ title: t('new_conversation'), created_at: new Date().toISOString() })}
                  style={{ ...styles.sidebarButton, fontSize: '12px', padding: '4px 8px', marginTop: '4px' }}>
                  + {t('new_conversation')}
                </button>
              </div>
            </div>

            {/* Main Content */}
            <div style={styles.chatArea}>
              {centerView === 'chat' && !messages.length ? renderBootScreen()
              : centerView === 'chat' ? (
                <>
                  <div style={{ ...styles.messagesContainer, fontSize: `${chatFontScale}em` }}>
                    {messages.filter(m => !chatSearchQuery || String(m.content || '').toLowerCase().includes(chatSearchQuery.toLowerCase())).map(message => (
                      <div key={message.id} style={{ ...styles.messageBubble, ...(message.role === 'user' ? styles.messageBubbleUser : {}) }}>
                        {message.role === 'assistant' && !message.streaming ? (
                          (() => {
                            const parsed = parseCommandRequestsFromContent(message.content || '');
                            const blocks = parseMessageBlocks(parsed.text || '');
                            const cliBlocks = [];
                            if (message?.cli) cliBlocks.push(message.cli);
                            if (message?.cli_runs && typeof message.cli_runs === 'object') {
                              try { for (const v of Object.values(message.cli_runs)) { if (v && typeof v === 'object') cliBlocks.push(v); } } catch {}
                            }
                            return (
                              <>
                                {blocks?.length ? (
                                  <div style={{ display: 'grid', gap: '8px' }}>
                                    {blocks.map((b, idx) => (
                                      <MessageBlock key={`${b.type || 'text'}-${idx}`} block={b} lang={lang} styles={styles}
                                        planUi={{ approved: Boolean(approvedPlanLocalMsgIds[message.id]), running: (orchStatus === 'running' && message.id === activePlanLocalMsgId) }}
                                        onApprovePlan={handleApprovePlan} />
                                    ))}
                                  </div>
                                ) : null}
                                {cliBlocks.length ? (
                                  <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                    {cliBlocks.map((cli, i) => (
                                      <CLIDisplay key={`cli-${i}`} payload={cli} loadingTick={loadingTick} onOpenArtifact={openCliArtifact} styles={styles} />
                                    ))}
                                  </div>
                                ) : null}
                                {parsed.requests?.length ? (
                                  <div>
                                    {parsed.requests.map((req, i) => {
                                      const rid = req?.id || `noid-${i}`;
                                      const isExecuting = executingCommandId === rid;
                                      const isExecuted = Boolean(executedCommandIds[rid]);
                                      return (
                                        <div key={rid} style={styles.commandCard}>
                                          <div style={styles.commandTitle}>{req.title || t('command_request')}</div>
                                          <div style={styles.commandMeta}>{req.command}</div>
                                          <button style={styles.settingsPrimaryButton} onClick={() => setCommandModal(req)}
                                            disabled={isExecuted || isExecuting}>{isExecuted ? t('executed') : t('execute')}</button>
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
                            if (message.role !== 'assistant' || !message.streaming)
                              return <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(message.content || '')}</ReactMarkdown>;
                            const base = (message.content || '').trim();
                            if (base) return <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>;
                            return `${(streamStatusText || 'Processando').trim()}${'.'.repeat((loadingTick % 4) + 1)}`;
                          })()
                        )}
                        {message.expert && !message.streaming && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginTop: '8px' }}>
                            <div style={styles.expertTag}><span>{message.expert.icon}</span><span>{message.expert.name}</span></div>
                          </div>
                        )}
                        <div style={styles.messageTimestamp}>
                          {formatCompactDateTime(message?.created_at || message?.createdAt || message?.timestamp || message?.time || '')}
                        </div>
                        {message.message_id && (
                          <div style={{ display: 'flex', gap: '4px', marginTop: '6px' }}>
                            {[1, -1].map(rating => {
                              const current = messageFeedback[message.message_id];
                              const isActive = current === rating;
                              return (
                                <button key={rating}
                                  onClick={() => postFeedback(message.message_id, rating)}
                                  style={{
                                    background: isActive ? (rating === 1 ? 'rgba(74,222,128,0.2)' : 'rgba(248,113,113,0.2)') : 'transparent',
                                    border: `1px solid ${isActive ? (rating === 1 ? 'var(--green)' : 'var(--red)') : 'var(--border)'}`,
                                    borderRadius: '6px', padding: '2px 7px', cursor: 'pointer',
                                    fontSize: '13px',
                                    color: isActive ? (rating === 1 ? 'var(--green)' : 'var(--red)') : 'var(--text-dim)',
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
                    ))}
                    <div ref={messagesEndRef} />
                  </div>

                  <div style={styles.chatInput}>
                    <textarea value={input} onChange={e => setInput(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }}
                      placeholder={t('type_message')} style={styles.input} rows={2} />
                    <button onClick={handleSendMessage} disabled={!input.trim() || streaming}
                      style={{ ...styles.settingsPrimaryButton, padding: '8px 16px' }}>{t('send')}</button>
                  </div>

                  {/* Execution Panel */}
                  {showExecutionPanel && (
                    <div style={{ width: '320px', borderLeft: '1px solid var(--border)', padding: '12px', overflowY: 'auto' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <div style={{ fontWeight: 600, fontSize: '13px' }}>{t('execution_panel')}</div>
                        <button style={styles.iconButton} onClick={() => setShowExecutionPanel(false)}>✕</button>
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                        {orchStatus === 'running' ? `${t('running')}...` : orchStatus === 'failed' ? t('failed') : t('no_active_tasks')}
                      </div>
                    </div>
                  )}
                </>
              ) : centerView === 'skills' ? (
                <SkillsPanel styles={styles} skills={skills} loading={skillsLoading} onRefresh={() => {}}
                  onToggleSkill={toggleSkill} onUpdateSkill={updateSkill} t={t} />
              ) : centerView === 'doctor' ? (
                <DoctorPanel styles={styles} doctorReport={doctorReport} loading={isChecking}
                  onRefresh={runCheck} onRunCheck={runCheck} onLoadSystemMap={loadSystemMap} t={t} />
              ) : centerView === 'settings' ? (
                <div style={{ padding: '16px' }}>
                  <div style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>{t('settings')}</div>
                  <div style={{ marginBottom: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {[['general', t('general')], ['system', t('system')], ['llm', t('llm')], ['security', t('security')]].map(([key, label]) => (
                      <button key={key} onClick={() => setSettingsTab(key)}
                        style={{ ...styles.settingsTab, background: settingsTab === key ? 'var(--accent-bg)' : 'transparent' }}>{label}</button>
                    ))}
                  </div>
                  {settingsTab === 'system' && <SystemSettingsPanel styles={styles} t={t} />}
                  {settingsTab === 'llm' && <LlmSettingsPanel styles={styles} t={t} />}
                  {settingsTab === 'security' && <SecuritySettingsPanel styles={styles} t={t} />}
                  {settingsTab === 'general' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '400px' }}>
                      <div>
                        <label style={{ fontSize: '12px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>{t('language')}</label>
                        <select value={lang} onChange={e => { setLang(e.target.value); }} style={styles.input}>
                          <option value="pt">Português</option><option value="en">English</option><option value="es">Español</option>
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                renderBootScreen()
              )}
            </div>
          </div>
        </div>
      )}
    </Router>
  );
};

export default App;
