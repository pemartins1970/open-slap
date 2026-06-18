import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './i18n';
import Login from './pages/Login';
import { useAuthContext } from './hooks/AuthContext';
import useChatSocket from './hooks/useChatSocket';
import { useConversations } from './hooks';
import { useDoctor } from './hooks';
import { useSkills } from './hooks';
import { useSettings } from './hooks';
import { useSoul } from './hooks';
import { useLLMConfig } from './hooks';
import { buildSysGlobalKernelPrompt } from './lib/kernelPrompt';
import { maybeRepoDisambiguationInternalPrompt } from './lib/repoDisambiguation';
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
import AppLayout from './components/layout/AppLayout';
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
--------------------------------------------------------`;

const AppContent = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;

  const { user, loading, login, register, logout, getAuthHeaders, isAuthenticated, token, requestPasswordReset, confirmPasswordReset } = useAuthContext();

  const { conversations, currentConversation, setCurrentConversation, createConversation, deleteConversation, loadConversations, conversationsLoading } = useConversations(getAuthHeaders);
  const { doctorReport, isChecking, runCheck, loadSystemMap } = useDoctor(getAuthHeaders);
  const { skills, experts, toggleSkill, updateSkill, getSkillsBySegment, skillsLoading } = useSkills(getAuthHeaders, t);
  const settingsHook = useSettings(getAuthHeaders, t);
  const {
    lang: settingsLang, theme, settingsTab: settingsTabHook, settingsLoading, settingsError,
    providerStatusList, providerStatusLoading, providerStatusError,
    activeProvider, activeProviderLoading, fetchActiveProvider,
    setLang: setSettingsLang, setTheme, setSettingsTab: setSettingsTabHook,
    saveLanguageSettings, saveThemeSettings, loadProviderStatus,
    reloadSettings, resetSettings
  } = settingsHook;
  const { soulData, updateSoulData, loadSoul } = useSoul(getAuthHeaders);
  const llmConfigHook = useLLMConfig(getAuthHeaders, t);
  const {
    llmMode, llmProvider, llmModel, llmBaseUrl, llmApiKey,
    llmHasApiKey, llmApiKeySource, llmHasStoredApiKey, llmHasEnvApiKey, llmApiKeyOpen,
    llmProviderKeys, llmProviderKeysLoading, llmProviderKeysError,
    llmLoading: settingsLoadingLLM, llmError,
    llmApiKeyInputRef,
    setLlmMode, setLlmProvider, setLlmModel, setLlmBaseUrl, setLlmApiKey, setLlmApiKeyOpen,
    loadProviderKeys, saveLlmSettings, removeLlmApiKey, loadLlmSettings,
    getStoredLlmPrefs, setStoredLlmPrefs
  } = llmConfigHook;

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [bootInput, setBootInput] = useState('');

  const [connected, setConnected] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamStatusText, setStreamStatusText] = useState('');
  const [runtimeLlmLabel, setRuntimeLlmLabel] = useState('');
  const [lastExpertReason, setLastExpertReason] = useState('');
  const [lastExpertKeywords, setLastExpertKeywords] = useState([]);
  const [loadingTick, setLoadingTick] = useState(0);

  const [centerView, setCenterView] = useState('chat');
  const [settingsTab, setSettingsTab] = useState('general');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [showExecutionPanel, setShowExecutionPanel] = useState(false);
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = useState(false);
  const [showConversationList, setShowConversationList] = useState(false);

  const [approvedPlanLocalMsgIds, setApprovedPlanLocalMsgIds] = useState({});
  const [activePlanMessageId, setActivePlanMessageId] = useState(null);
  const [activePlanLocalMsgId, setActivePlanLocalMsgId] = useState(null);
  const [orchStatus, setOrchStatus] = useState('');
  const [orchLog, setOrchLog] = useState([]);
  const orchPollRef = useRef(null);

  const [commandModal, setCommandModal] = useState(null);
  const [executingCommandId, setExecutingCommandId] = useState('');
  const [executedCommandIds, setExecutedCommandIds] = useState({});

  const [selectedSkillId, setSelectedSkillId] = useState('');
  const [forceExpertId, setForceExpertId] = useState('');
  const [agentConfigs, setAgentConfigs] = useState({});
  const [showRoutingDebug, setShowRoutingDebug] = useState(false);
  const [chatFontScale, setChatFontScale] = useState(1);
  const [chatSearchQuery, setChatSearchQuery] = useState('');
  const [isMobile, setIsMobile] = useState(false);
  const [currentKind, setCurrentKind] = useState('conversation');
  const [chatSearch, setChatSearch] = useState('');
  const [messageFeedback, setMessageFeedback] = useState({});

  const setActiveLlmProviderKey = useCallback(async (providerId, keyId) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      const res = await fetch(`/api/settings/llm/keys/${encodeURIComponent(String(providerId || ''))}/active`, {
        method: 'POST', headers, body: JSON.stringify({ key_id: Number(keyId) })
      });
      if (!res.ok) throw new Error('Error selecting key.');
      if (typeof loadProviderKeys === 'function') loadProviderKeys();
    } catch (e) { console.error('Error selecting key:', e); }
  }, [getAuthHeaders, loadProviderKeys]);

  const deleteLlmProviderKey = useCallback(async (providerId, keyId) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      const res = await fetch(`/api/settings/llm/keys/${encodeURIComponent(String(providerId || ''))}/${encodeURIComponent(String(keyId))}`, {
        method: 'DELETE', headers
      });
      if (!res.ok) throw new Error('Error deleting key.');
      if (typeof loadProviderKeys === 'function') loadProviderKeys();
    } catch (e) { console.error('Error deleting key:', e); }
  }, [getAuthHeaders, loadProviderKeys]);

  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const hasHttpHydratedRef = useRef(false);
  const pendingAutoSendRef = useRef(null);
  const sessionIdRef = useRef(generateSessionId());
  const pendingPlanTasksRef = useRef({});

  useEffect(() => {
    if (!streaming) return;
    const id = setInterval(() => setLoadingTick(v => v + 1), 250);
    return () => clearInterval(id);
  }, [streaming]);

  useEffect(() => {
    document.body.classList.toggle('loaded', !loading);
  }, [loading]);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    loadConversations();
    if (typeof loadSoul === 'function') loadSoul();
  }, [isAuthenticated]);

  useEffect(() => {
    const path = location.pathname;
    if (path.startsWith('/skills')) setCenterView('skills');
    else if (path.startsWith('/doctor')) setCenterView('doctor');
    else if (path.startsWith('/conversations')) setCenterView('conversations');
    else setCenterView('chat');
  }, [location.pathname]);

  useEffect(() => {
    const pathParts = location.pathname.split('/');
    if (pathParts[1] === 'chat' && pathParts[2]) {
      setCurrentConversation(pathParts[2]);
    }
  }, [location.pathname]);

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

  const { sendMessage } = useChatSocket({
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

  const styles = buildAppAuthStyles({ connected });

  const handleSendMessage = () => sendMessage();

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
        method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' }, body: JSON.stringify({ tasks }),
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

  const handleNavigate = (view) => {
    setCenterView(view);
    navigate(`/${view}`);
  };

  const renderBootScreen = () => {
    console.log('[Boot] renderBootScreen called, centerView=%s messages.length=%s bootInput="%s"', centerView, messages.length, bootInput);
    const greeting = getBootGreeting(t, soulData, user);
    const asciiWithVersion = OPEN_SLAP_ASCII.replace('open_slap > boot', `open_slap > boot #${OPEN_SLAP_VERSION}#`);
    return (
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', overflow: 'auto' }}>
        <div style={{ maxWidth: '920px', width: '100%', padding: '20px' }}>
          <div style={{ ...styles.lightCard, border: '1px solid rgba(255,255,255,0.10)' }}>
            <pre style={{ fontFamily: OPEN_SLAP_ASCII_FONT, fontSize: isMobile ? '10px' : '12px', lineHeight: 1.2, color: 'var(--text-dim)', textAlign: 'center' }}>
              {asciiWithVersion}
            </pre>
          </div>
          <div style={{ marginTop: '20px', color: 'var(--text)', fontSize: '16px', textAlign: 'center' }}>{greeting}</div>
          <form onSubmit={e => { e.preventDefault(); const v = bootInput.trim(); if (!v) return; console.log('[Boot] Submit, sending:', v); setBootInput(''); setInput(v); setCenterView('chat'); navigate('/chat'); const sent = sendMessage(v); console.log('[Boot] sendMessage result:', sent); if (!sent) { pendingAutoSendRef.current = v; console.log('[Boot] fallback to pendingAutoSendRef'); } }} style={{ marginTop: '30px', display: 'flex', justifyContent: 'center' }}>
            <input value={bootInput} onChange={e => setBootInput(e.target.value)}
              placeholder={t('boot_input_placeholder')} style={{ maxWidth: '500px', width: '100%', textAlign: 'center', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', padding: '10px 14px', fontSize: '14px', color: 'var(--text)', fontFamily: 'var(--sans)', outline: 'none' }} autoFocus />
          </form>
        </div>
      </div>
    );
  };

  const renderChatView = () => (
    <>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ ...styles.messagesContainer, fontSize: `${chatFontScale}em`, flex: 1, overflowY: 'auto' }}>
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
                  return `${(streamStatusText || t('processing')).trim()}${'.'.repeat((loadingTick % 4) + 1)}`;
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
                          borderRadius: '6px', padding: '2px 7px', cursor: 'pointer', fontSize: '13px',
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

        <div style={styles.inputArea}>
          <textarea value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }}
            placeholder={t('boot_input_placeholder')} style={styles.input} rows={2} />
          <button onClick={handleSendMessage} disabled={!input.trim() || streaming}
            style={{ ...styles.settingsPrimaryButton, padding: '8px 16px' }}>{t('send')}</button>
        </div>
      </div>

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
  );

  const handleCreateConversation = () => {
    const now = new Date().toISOString();
    const newConv = createConversation({ title: t('new_conversation'), created_at: now });
    setCenterView('chat');
    navigate('/chat');
  };

  const handleSelectConversation = (convId) => {
    setCurrentConversation(convId);
    setCenterView('chat');
    navigate(`/chat/${convId}`);
  };

  return (
    <>
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

      <OnboardingModal />

      <AppLayout
        styles={styles}
        user={user}
        leftSidebarCollapsed={leftSidebarCollapsed}
        setLeftSidebarCollapsed={setLeftSidebarCollapsed}
        connected={connected}
        runtimeLlmLabel={runtimeLlmLabel}
        onSettingsClick={() => setSettingsOpen(true)}
        onLogout={logout}
        conversations={conversations}
        currentConversation={currentConversation}
        onSelectConversation={handleSelectConversation}
        onCreateConversation={handleCreateConversation}
        centerView={centerView}
        onNavigate={handleNavigate}
      >
        {!messages.length && centerView === 'chat' ? renderBootScreen()
        : centerView === 'chat' ? renderChatView()
        : centerView === 'conversations' ? (
          <div style={{ ...styles.centerPanel, display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={styles.centerPanelTitle}>{t('conversations')}</div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0' }}>
              {conversations.length === 0 ? (
                <div style={{ fontSize: '13px', color: 'var(--text-dim)', textAlign: 'center', padding: '40px 0' }}>
                  {t('no_conversations')}
                </div>
              ) : (
                conversations.map((conv) => (
                  <button
                    key={conv.id}
                    type="button"
                    onClick={() => handleSelectConversation(conv.id)}
                    style={{
                      display: 'block',
                      width: '100%',
                      background: currentConversation === conv.id ? 'var(--accent-bg)' : 'transparent',
                      border: 'none',
                      borderBottom: '1px solid var(--border)',
                      padding: '12px 16px',
                      cursor: 'pointer',
                      fontSize: '13px',
                      color: 'var(--text)',
                      textAlign: 'left'
                    }}
                  >
                    <div style={{ fontWeight: 500 }}>{conv.title || t('new_conversation')}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
                      {formatCompactDateTime(conv.created_at || conv.createdAt || '')}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        ) : centerView === 'skills' ? (
          <SkillsPanel styles={styles} skills={skills} loading={skillsLoading} onRefresh={() => {}}
            onToggleSkill={toggleSkill} onUpdateSkill={updateSkill} />
        ) : centerView === 'doctor' ? (
          <DoctorPanel styles={styles} doctorReport={doctorReport} loading={isChecking}
            onRefresh={runCheck} onRunCheck={runCheck} onLoadSystemMap={loadSystemMap} />
        ) : renderBootScreen()}
      </AppLayout>

      {settingsOpen && (
        <div style={styles.modalOverlay} onClick={() => setSettingsOpen(false)}>
          <div style={{ ...styles.modal, width: '640px', maxHeight: '80vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <div style={{ fontSize: '18px', fontWeight: 600 }}>{t('settings')}</div>
              <button style={styles.modalClose} onClick={() => setSettingsOpen(false)}>✕</button>
            </div>
            <div style={{ marginBottom: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap', padding: '0 16px' }}>
              {[['general', t('general')], ['system', t('system')], ['llm', t('llm')], ['security', t('security')]].map(([key, label]) => (
                <button key={key} onClick={() => setSettingsTab(key)}
                  style={{ ...styles.settingsTab, background: settingsTab === key ? 'var(--accent-bg)' : 'transparent' }}>{label}</button>
              ))}
            </div>
            <div style={{ padding: '0 16px 16px' }}>
              {settingsTab === 'system' && <SystemSettingsPanel styles={styles} settingsLoading={settingsLoadingLLM} />}
              {settingsTab === 'llm' && <LlmSettingsPanel
                styles={styles}
                settingsLoading={settingsLoadingLLM}
                llmMode={llmMode} setLlmMode={setLlmMode}
                llmProvider={llmProvider} setLlmProvider={setLlmProvider}
                llmModel={llmModel} setLlmModel={setLlmModel}
                llmBaseUrl={llmBaseUrl} setLlmBaseUrl={setLlmBaseUrl}
                llmApiKey={llmApiKey} setLlmApiKey={setLlmApiKey}
                llmHasApiKey={llmHasApiKey}
                llmApiKeySource={llmApiKeySource}
                llmApiKeyOpen={llmApiKeyOpen} setLlmApiKeyOpen={setLlmApiKeyOpen}
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
                activeProvider={activeProvider}
                activeProviderLoading={activeProviderLoading}
                fetchActiveProvider={fetchActiveProvider}
                runtimeLlmLabel={runtimeLlmLabel}
              />}
              {settingsTab === 'security' && <SecuritySettingsPanel styles={styles} />}
              {settingsTab === 'general' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '400px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>{t('language')}</label>
                    <select value={lang} onChange={e => i18n.changeLanguage(e.target.value)} style={styles.input}>
                      <option value="pt">Português</option><option value="en">English</option><option value="es">Español</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

const App = () => {
  const { isAuthenticated, loading, login, register, logout, requestPasswordReset, confirmPasswordReset } = useAuthContext();

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)', color: 'var(--text-dim)', fontFamily: 'var(--sans)' }}>
        <div>{'Carregando Open Slap!...'}</div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route path="/login" element={
          <Login onLogin={login} onRegister={register}
            onPasswordResetRequest={requestPasswordReset} onPasswordResetConfirm={confirmPasswordReset} />
        } />
        <Route path="/chat" element={
          isAuthenticated ? <AppContent /> : <Navigate to="/login" replace />
        } />
        <Route path="/chat/:convId" element={
          isAuthenticated ? <AppContent /> : <Navigate to="/login" replace />
        } />
        <Route path="/conversations" element={
          isAuthenticated ? <AppContent /> : <Navigate to="/login" replace />
        } />
        <Route path="/skills" element={
          isAuthenticated ? <AppContent /> : <Navigate to="/login" replace />
        } />
        <Route path="/doctor" element={
          isAuthenticated ? <AppContent /> : <Navigate to="/login" replace />
        } />
        <Route path="/*" element={
          isAuthenticated ? <Navigate to="/chat" replace /> : <Navigate to="/login" replace />
        } />
      </Routes>
    </Router>
  );
};

export default App;
