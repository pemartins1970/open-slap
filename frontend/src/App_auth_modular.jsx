/**
 * App_auth_modular - Versão modularizada do App_auth.jsx
 * 
 * Esta é a nova versão do App_auth.jsx usando componentes modularizados
 * 
 * @version 2.0.0
 * @author Claude AI Assistant
 */

import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';

// Hooks existentes (mantidos)
import useAuth from './hooks/useAuth';
import useChatSocket from './hooks/useChatSocket';

// Hooks novos (da modularização)
import { 
  useLocalStorage,
  useDebounce,
  useModals,
  useConversations,
  useMessages,
  useSettings,
  useLLMConfig,
  useSoul,
  useSkills,
  useDoctor
} from './hooks';

// Utilitários (da modularização)
import {
  formatCompactDateTime,
  generateSessionId,
  getSkillDisplayName,
  getExpertDisplayName,
  getConversationTitle,
  clamp,
  debounce
} from './lib/utils';

// Componentes UI (da modularização)
import {
  Button,
  Input,
  Textarea,
  Select,
  Checkbox,
  Toggle,
  Badge,
  Alert,
  Tooltip,
  Loading
} from './components/ui';

// Componentes de Layout (da modularização)
import {
  AppLayout,
  Header,
  MainContent,
  LeftSidebar,
  RightSidebar
} from './components/layout';

// Componentes de Painéis (da modularização)
import {
  DoctorPanel,
  SkillsPanel,
  ExpertsPanel,
  SettingsPanel,
  LLMConfigPanel,
  ExecutionPanel,
  LogPanel
} from './components/panels';

// Imports existentes (mantidos)
import { buildSysGlobalKernelPrompt } from './lib/kernelPrompt';
import { maybeRepoDisambiguationInternalPrompt } from './lib/repoDisambiguation';
import { translations } from './i18n/translations_auth';
import { buildAppAuthStyles } from './styles/appAuthStyles';
import { buildDefaultSkills } from './data/defaultSkills';
import SystemSettingsPanel from './components/settings/SystemSettingsPanel';
import LlmSettingsPanel from './components/settings/LlmSettingsPanel';
import SecuritySettingsPanel from './components/settings/SecuritySettingsPanel';
import { OnboardingModal } from './components/onboarding';

// Constantes (mantidas)
const OPEN_SLAP_LOGO_SRC = '/open_slap.png';
const AGENT_AVATAR_SRC = '/agent/slap.png';
const OPEN_SLAP_REPO_URL = 'https://github.com/pemartins1970/slap-ecosystem';
const OPEN_SLAP_VERSION = 'v2.1';
const OPEN_SLAP_ASCII_FONT =
  '"Cascadia Mono", Consolas, "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, "Liberation Mono", "Courier New", monospace';

const OPEN_SLAP_ASCII = `open_slap > boot
---------------------------------------------------------

    (ASCII art mantido do original)
---------------------------------------------------------`;

const App = () => {
  // Hooks existentes (mantidos)
  const { user, loading, login, register, logout, getAuthHeaders, isAuthenticated, token, requestPasswordReset, confirmPasswordReset } = useAuth();
  
  // Hooks novos (para gerenciar estado)
  const {
    conversations,
    currentConversation,
    setCurrentConversation,
    createConversation,
    deleteConversation,
    updateConversation
  } = useConversations();
  
  const {
    messages,
    addMessage,
    updateMessage,
    deleteMessage,
    clearMessages
  } = useMessages();
  
  const {
    settings,
    updateSetting,
    resetSettings,
    isLoading: settingsLoading
  } = useSettings();
  
  const {
    llmConfig,
    updateLLMConfig,
    testConnection,
    providerStatus
  } = useLLMConfig();
  
  const {
    soulData,
    updateSoulData,
    generateSoulMarkdown
  } = useSoul();
  
  const {
    skills,
    toggleSkill,
    updateSkill,
    getSkillsBySegment
  } = useSkills();
  
  const {
    doctorReport,
    runCheck,
    loadSystemMap,
    isChecking
  } = useDoctor();
  
  const {
    modals,
    openModal,
    closeModal,
    showModal
  } = useModals();

  // Estado WebSocket (mantido)
  const [connected, setConnected] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [runtimeLlmLabel, setRuntimeLlmLabel] = useState('');
  const wsRef = useRef(null);

  // Estado UI (simplificado)
  const [input, setInput] = useState('');
  const [bootInput, setBootInput] = useState('');
  const [centerView, setCenterView] = useState('chat');
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = useState(false);
  const [rightSidebarCollapsed, setRightSidebarCollapsed] = useState(false);

  // Refs (mantidos)
  const messagesEndRef = useRef(null);
  const hasHttpHydratedRef = useRef(false);
  const pendingAutoSendRef = useRef(null);
  const autoStartRef = useRef(false);
  const sessionId = useRef(generateSessionId());

  // WebSocket Hook (mantido)
  useChatSocket({
    wsRef,
    sessionId,
    token,
    connected,
    setConnected,
    streaming,
    setStreaming,
    messages,
    addMessage,
    conversations,
    currentConversation,
    runtimeLlmLabel,
    setRuntimeLlmLabel
  });

  // Styles (mantidos)
  const styles = buildAppAuthStyles();

  // Handlers (simplificados com hooks)
  const handleSendMessage = () => {
    if (input.trim()) {
      addMessage({
        id: generateSessionId(),
        content: input,
        sender: 'user',
        timestamp: new Date().toISOString()
      });
      setInput('');
    }
  };

  const handleCreateConversation = () => {
    createConversation({
      title: getConversationTitle(input),
      createdAt: new Date().toISOString()
    });
  };

  const handleToggleSkill = (skillId) => {
    toggleSkill(skillId);
  };

  const handleUpdateSettings = (newSettings) => {
    updateSetting(newSettings);
  };

  const handleTestLLMConnection = (provider) => {
    testConnection(provider);
  };

  // Controlar loading screen no index.html
  useEffect(() => {
    if (loading) {
      document.body.classList.remove('loaded');
    } else {
      document.body.classList.add('loaded');
    }
  }, [loading]);

  // Renderização principal com layout modular
  return (
    <Router>
      {!isAuthenticated ? (
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      ) : (
        <AppLayout
          styles={styles}
          user={user}
          leftSidebarCollapsed={leftSidebarCollapsed}
          rightSidebarCollapsed={rightSidebarCollapsed}
          setLeftSidebarCollapsed={setLeftSidebarCollapsed}
          setRightSidebarCollapsed={setRightSidebarCollapsed}
          leftSidebarProps={{
            conversations,
            currentConversation,
            setCurrentConversation,
            onCreateConversation: handleCreateConversation,
            onDeleteConversation: deleteConversation,
            chatSearch: '', // TODO: implementar busca
            setChatSearch: () => {}, // TODO: implementar
            t: translations.t
          }}
          rightSidebarProps={{
            doctorProps: {
              doctorReport,
              loading: isChecking,
              onRefresh: runCheck,
              onRunCheck: runCheck,
              onLoadSystemMap: loadSystemMap,
              t: translations.t
            },
            executionProps: {
              executionState: {}, // TODO: implementar estado de execução
              commandHistory: [], // TODO: implementar histórico
              activeCommands: [], // TODO: implementar comandos ativos
              onExecuteCommand: () => {}, // TODO: implementar
              onStopCommand: () => {}, // TODO: implementar
              onClearHistory: () => {}, // TODO: implementar
              t: translations.t
            },
            logsProps: {
              logs: [], // TODO: implementar logs
              loading: false,
              realTimeMode: true,
              onRefresh: () => {}, // TODO: implementar
              onClearLogs: () => {}, // TODO: implementar
              onExportLogs: () => {}, // TODO: implementar
              onToggleRealTime: () => {}, // TODO: implementar
              t: translations.t
            },
            settingsProps: {
              settings,
              loading: settingsLoading,
              onSaveSettings: handleUpdateSettings,
              onResetSettings: resetSettings,
              t: translations.t
            }
          }}
          mainContentProps={{
            chatProps: {
              messages,
              input,
              setInput,
              onSendMessage: handleSendMessage,
              streaming,
              connected,
              currentConversation,
              t: translations.t
            },
            executionProps: {},
            panelProps: {}
          }}
          t={translations.t}
        >
          {/* Conteúdo principal renderizado pelo AppLayout */}
          <MainContent
            styles={styles}
            leftSidebarCollapsed={leftSidebarCollapsed}
            rightSidebarCollapsed={rightSidebarCollapsed}
            isMobile={false} // TODO: implementar detecção mobile
          >
            {centerView === 'chat' && (
              <div style={styles.chatContainer}>
                {/* Chat implementado com componentes modulares */}
                <div style={styles.chatMessages}>
                  {messages.map((message) => (
                    <div key={message.id} style={styles.messageBubble}>
                      <div style={styles.messageContent}>
                        {message.content}
                      </div>
                      <div style={styles.messageTimestamp}>
                        {formatCompactDateTime(message.timestamp)}
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
                
                <div style={styles.chatInput}>
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={translations.t('type_message')}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    styles={styles}
                    t={translations.t}
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!input.trim() || streaming}
                    variant="primary"
                    styles={styles}
                    t={translations.t}
                  >
                    {translations.t('send')}
                  </Button>
                </div>
              </div>
            )}

            {centerView === 'doctor' && (
              <DoctorPanel
                styles={styles}
                doctorReport={doctorReport}
                loading={isChecking}
                onRefresh={runCheck}
                onRunCheck={runCheck}
                onLoadSystemMap={loadSystemMap}
                t={translations.t}
              />
            )}

            {centerView === 'skills' && (
              <SkillsPanel
                styles={styles}
                skills={skills}
                loading={false}
                onRefresh={() => {}}
                onToggleSkill={handleToggleSkill}
                onUpdateSkill={updateSkill}
                t={translations.t}
              />
            )}

            {centerView === 'settings' && (
              <SettingsPanel
                styles={styles}
                settings={settings}
                loading={settingsLoading}
                onSaveSettings={handleUpdateSettings}
                onResetSettings={resetSettings}
                t={translations.t}
              />
            )}

            {centerView === 'llm' && (
              <LLMConfigPanel
                styles={styles}
                llmConfig={llmConfig}
                providers={providerStatus}
                models={[]} // TODO: implementar modelos
                loading={false}
                onSaveConfig={handleUpdateSettings}
                onTestConnection={handleTestLLMConnection}
                onRemoveApiKey={() => {}} // TODO: implementar
                t={translations.t}
              />
            )}
          </MainContent>
        </AppLayout>
      )}
    </Router>
  );
};

export default App;
