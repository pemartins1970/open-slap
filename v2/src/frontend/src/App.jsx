/**
 * 🚀 APP AUTH - Aplicação Principal com Autenticação
 * Versão completa segundo WINDSURF_AGENT.md - AUTH-02
 */

import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import useAuth from './hooks/useAuth';

const OPEN_SLAP_LOGO_SRC = '/media/open_slap.png';

const App = () => {
  const { user, loading, login, register, logout, getAuthHeaders, isAuthenticated, token, requestPasswordReset, confirmPasswordReset } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [experts, setExperts] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [centerView, setCenterView] = useState('chat');
  const [chatSearch, setChatSearch] = useState('');
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const hasHttpHydratedRef = useRef(false);
  const sessionId = useRef(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

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
      width: '280px',
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
      border: '1px solid var(--border)',
      borderRadius: '6px',
      padding: '10px 12px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      cursor: 'pointer',
      transition: 'all 0.15s',
      width: '100%',
      textAlign: 'left'
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
    }
  };

  // Carregar especialistas
  useEffect(() => {
    if (user && token) {
      fetch('/api/experts')
        .then(res => res.json())
        .then(data => setExperts(data.experts || []))
        .catch(err => console.error('Erro ao carregar especialistas:', err));
    }
  }, [user, token]);

  // Carregar conversas
  useEffect(() => {
    if (user && token) {
      loadConversations();
    }
  }, [user, token]);

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
      const response = await fetch('/api/conversations', { headers });
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error('Erro ao carregar conversas:', error);
    }
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
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage && lastMessage.role === 'assistant') {
              newMessages[newMessages.length - 1] = {
                ...lastMessage,
                streaming: false,
                expert: data.expert,
                provider: data.provider,
                model: data.model
              };
            }
            return newMessages;
          });
          setStreaming(false);
        } else if (data.type === 'status') {
          console.log('Status:', data.content);
        } else if (data.type === 'error') {
          console.error('Erro WebSocket:', data.content);
          setStreaming(false);
        }
      } catch (error) {
        console.error('Erro ao processar mensagem WebSocket:', error);
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
      console.error('Erro WebSocket:', error);
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

    wsRef.current.send(JSON.stringify({
      type: 'chat',
      content: input.trim()
    }));
  };

  const createNewConversation = async () => {
    try {
      const headers = getAuthHeaders();
      const title = `Conversa ${new Date().toLocaleString('pt-BR', { 
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
      
      // Limpar mensagens atuais
      setMessages([]);
      hasHttpHydratedRef.current = false;
      setCurrentConversation(data.conversation_id);
      setCenterView('chat');
      setChatSearch('');
      
      // Recarregar lista de conversas
      await loadConversations();
      
      // Reconectar WebSocket com nova session
      if (wsRef.current) {
        wsRef.current.close();
      }
      sessionId.current = data.session_id;
      connectWebSocket();
      
    } catch (error) {
      console.error('Erro ao criar conversa:', error);
    }
  };

  const loadConversation = async (conversationId, conversationSessionId) => {
    try {
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
      
      // Reconectar WebSocket
      if (wsRef.current) {
        wsRef.current.close();
      }
      sessionId.current = conversationSessionId || `session_${conversationId}`;
      connectWebSocket();
      
    } catch (error) {
      console.error('Erro ao carregar conversa:', error);
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

  // Loading screen
  if (loading) {
    return (
      <div style={styles.loadingScreen}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
          <img src={OPEN_SLAP_LOGO_SRC} alt="Open Slap" style={{ width: '84px', height: '84px', objectFit: 'contain' }} />
          <div>loading Open Slap!...</div>
        </div>
      </div>
    );
  }

  // Componente principal do chat
  const MainApp = () => (
    <div style={styles.app}>
      <div style={styles.header}>
        <div style={styles.headerTitle}>Open Slap! Agentic engine for makers</div>
        <div style={styles.headerRight}>
          <div style={styles.connectionStatus}>
            <div style={styles.connectionDot}></div>
            {connected ? 'Conectado' : 'Desconectado'}
          </div>
          <button style={styles.iconButton} onClick={() => setCenterView('settings')}>
            ⚙️
          </button>
          <button style={styles.userButton} onClick={logout}>
            {user?.email} → Sair
          </button>
        </div>
      </div>

      <div style={styles.main}>
        <div style={styles.sidebar}>
          <div style={styles.sidebarSection}>
            <div style={styles.sidebarTitle}>MENU</div>
            <button style={styles.sidebarButton} onClick={() => setCenterView('conversations')}>
              💬 Conversas
            </button>
            <div style={{ height: '10px' }} />
            <button style={styles.newConversationButton} onClick={createNewConversation}>
              + Nova Conversa
            </button>
          </div>

          <div style={styles.sidebarSection}>
            <div style={styles.sidebarTitle}>ESPECIALISTAS</div>
            {experts.map(expert => (
              <div key={expert.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span>{expert.icon}</span>
                <span style={{ fontSize: '12px', color: expert.color }}>{expert.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={styles.chatArea}>
          {centerView === 'conversations' ? (
            <div style={styles.centerPanel}>
              <div style={styles.centerPanelTitle}>Conversas</div>
              {conversations.length === 0 ? (
                <div style={styles.emptyState}>Nenhuma conversa ainda.</div>
              ) : (
                <div>
                  {conversations.map(conv => (
                    <div
                      key={conv.id}
                      style={{
                        ...styles.conversationItem,
                        ...(currentConversation === conv.id ? styles.conversationItemActive : {})
                      }}
                      onClick={() => loadConversation(conv.id, conv.session_id)}
                    >
                      <div style={styles.conversationTitle}>{conv.title}</div>
                      <div style={styles.conversationMeta}>
                        {conv.message_count || 0} mensagens • {new Date(conv.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : centerView === 'settings' ? (
            <div style={styles.centerPanel}>
              <div style={styles.centerPanelTitle}>Configurações</div>
              <div style={styles.emptyState}>Em breve.</div>
            </div>
          ) : (
            <>
              <div style={styles.chatToolbar}>
                <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-dim)' }}>
                  {currentConversation ? `Conversa #${currentConversation}` : 'Chat'}
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input
                    style={styles.chatSearchInput}
                    value={chatSearch}
                    onChange={(e) => setChatSearch(e.target.value)}
                    placeholder="Buscar no chat..."
                  />
                  {chatSearch.trim() ? (
                    <button style={styles.chatSearchClear} onClick={() => setChatSearch('')}>
                      Limpar
                    </button>
                  ) : null}
                </div>
              </div>
              <div style={styles.messagesContainer}>
                {(chatSearch.trim()
                  ? messages.filter((m) => (m.content || '').toLowerCase().includes(chatSearch.trim().toLowerCase()))
                  : messages
                ).map((msg) => (
                  <div
                    key={msg.id}
                    style={{
                      ...styles.message,
                      ...(msg.role === 'user' ? styles.messageUser : {})
                    }}
                  >
                    <div
                      style={{
                        ...styles.messageAvatar,
                        background: msg.role === 'user' ? 'var(--amber)' : 'var(--bg3)',
                        color: msg.role === 'user' ? 'var(--bg)' : 'var(--text)'
                      }}
                    >
                      {msg.role === 'user' ? '👤' : '🤖'}
                    </div>
                    <div style={styles.messageContent}>
                      <div
                        style={{
                          ...styles.messageBubble,
                          ...(msg.role === 'user' ? styles.messageBubbleUser : {})
                        }}
                      >
                        {msg.content}
                      </div>
                      {msg.expert && msg.role === 'assistant' && (
                        <div style={styles.expertTag}>
                          <span style={styles.expertIcon}>{msg.expert.icon}</span>
                          <span>{msg.expert.name}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              <div style={styles.inputArea}>
                <div style={styles.inputContainer}>
                  <div style={styles.inputWrapper}>
                    <textarea
                      style={styles.input}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Digite sua mensagem..."
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
                    {streaming ? '⏳' : '🚀 Enviar'}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );

  // UM único Router, sempre. Routing interno por estado.
  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated
              ? <Navigate to="/" replace />
              : <Login onLogin={login} onRegister={register} onPasswordResetRequest={requestPasswordReset} onPasswordResetConfirm={confirmPasswordReset} />
          }
        />
        <Route
          path="/*"
          element={
            isAuthenticated
              ? <MainApp />
              : <Navigate to="/login" replace />
          }
        />
      </Routes>
    </Router>
  );
};

export default App;
