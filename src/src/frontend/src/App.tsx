import React, { useState, useEffect } from 'react';
import { Socket } from 'socket.io-client';

// Components
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';
import Dashboard from './components/Dashboard';
import Header from './components/Header';
import { LemonEditorWrapper } from './components/LemonRTWE';

// Types
interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  expert?: string;
  confidence?: number;
}

interface SystemStatus {
  server: string;
  active_sessions: number;
  moe_experts: number;
  llm_providers: string[];
  timestamp: string;
}

interface ExpertStatus {
  experts: Record<string, {
    name: string;
    status: string;
    current_load: number;
    max_concurrent_tasks: number;
  }>;
  active_tasks: Record<string, any>;
  total_experts: number;
  available_experts: number;
}

interface AppProps {
  socket: Socket;
}

const App: React.FC<AppProps> = ({ socket }) => {
  const [activeView, setActiveView] = useState<'chat' | 'dashboard' | 'editor'>('chat');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [expertStatus, setExpertStatus] = useState<ExpertStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Socket event handlers
  useEffect(() => {
    // Connection events
    socket.on('connect', () => {
      console.log('Connected to MCP Server');
      setIsConnected(true);
      createSession();
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from MCP Server');
      setIsConnected(false);
    });

    // Message events
    socket.on('message', (data) => {
      const message: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: data.result?.content || data.content || 'Resposta recebida',
        timestamp: new Date(),
        expert: data.result?.expert_name,
        confidence: data.result?.confidence,
      };
      setMessages(prev => [...prev, message]);
      setIsLoading(false);
    });

    socket.on('system_status', (status: SystemStatus) => {
      setSystemStatus(status);
    });

    socket.on('expert_status', (status: ExpertStatus) => {
      setExpertStatus(status);
    });

    // Error handling
    socket.on('error', (error) => {
      console.error('Socket error:', error);
      setIsLoading(false);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'system',
        content: `Erro: ${error.message || 'Erro desconhecido'}`,
        timestamp: new Date(),
      }]);
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('message');
      socket.off('system_status');
      socket.off('expert_status');
      socket.off('error');
    };
  }, [socket]);

  // Create session
  const createSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: 'session-create',
          type: 'request',
          method: 'session/create',
          params: { user_id: 'web_user' }
        })
      });

      const data = await response.json();
      if (data.result?.session_id) {
        setSessionId(data.result.session_id);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'system',
          content: 'Sessão criada com sucesso!',
          timestamp: new Date(),
        }]);
      }
    } catch (error) {
      console.error('Session creation error:', error);
    }
  };

  // Send message
  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInputMessage('');

    try {
      // Send via WebSocket if connected
      if (isConnected && sessionId) {
        socket.emit('message', {
          id: Date.now().toString(),
          type: 'request',
          method: 'message/send',
          params: {
            session_id: sessionId,
            message: inputMessage.trim(),
            provider: 'ollama'
          }
        });
      } else {
        // Fallback to HTTP
        const response = await fetch('http://localhost:8000/mcp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            id: Date.now().toString(),
            type: 'request',
            method: 'message/send',
            params: {
              session_id: sessionId,
              message: inputMessage.trim(),
              provider: 'ollama'
            }
          })
        });

        const data = await response.json();
        if (data.result) {
          const assistantMessage: Message = {
            id: Date.now().toString(),
            type: 'assistant',
            content: data.result.content,
            timestamp: new Date(),
            expert: data.result.provider,
          };
          setMessages(prev => [...prev, assistantMessage]);
        } else {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            type: 'system',
            content: data.error || 'Erro ao processar mensagem',
            timestamp: new Date(),
          }]);
        }
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Send message error:', error);
      setIsLoading(false);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'system',
        content: 'Erro ao enviar mensagem',
        timestamp: new Date(),
      }]);
    }
  };

  // Get system status
  const getSystemStatus = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch('http://localhost:8000/mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: 'status-check',
          type: 'request',
          method: 'system/status',
          params: { session_id: sessionId }
        })
      });

      const data = await response.json();
      if (data.result) {
        setSystemStatus(data.result);
      }
    } catch (error) {
      console.error('Status check error:', error);
    }
  };

  // Get expert status
  const getExpertStatus = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch('http://localhost:8000/mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: 'expert-status-check',
          type: 'request',
          method: 'moe/expert_status',
          params: { session_id: sessionId }
        })
      });

      const data = await response.json();
      if (data.result) {
        setExpertStatus(data.result);
      }
    } catch (error) {
      console.error('Expert status check error:', error);
    }
  };

  // Route task to MoE
  const routeTask = async (taskType: string, description: string) => {
    if (!sessionId) return;

    try {
      const response = await fetch('http://localhost:8000/mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: 'moe-task',
          type: 'request',
          method: 'moe/route_task',
          params: {
            session_id: sessionId,
            task_id: `task-${Date.now()}`,
            task_type: taskType,
            description: description,
            requirements: [taskType],
            priority: 7,
            estimated_duration: 30,
            use_multiple_experts: false,
            context: { web_interface: true }
          }
        })
      });

      const data = await response.json();
      if (data.result) {
        const taskMessage: Message = {
          id: Date.now().toString(),
          type: 'system',
          content: `Tarefa "${description}" roteada para ${data.result.result?.expert_name || 'especialista'}`,
          timestamp: new Date(),
          expert: data.result.result?.expert_name,
          confidence: data.result.confidence,
        };
        setMessages(prev => [...prev, taskMessage]);
      } else {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'system',
          content: data.error || 'Erro ao rotear tarefa',
          timestamp: new Date(),
        }]);
      }
    } catch (error) {
      console.error('Task routing error:', error);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault();
        document.getElementById('chat-input')?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, []);

  return (
    <div className={`flex h-screen ${isDarkMode ? 'dark' : ''}`}>
      {/* Sidebar */}
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}
        systemStatus={systemStatus}
        expertStatus={expertStatus}
        onRouteTask={routeTask}
        onRefreshStatus={() => {
          getSystemStatus();
          getExpertStatus();
        }}
        isDarkMode={isDarkMode}
        onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <Header
          isConnected={isConnected}
          sessionId={sessionId}
          activeView={activeView}
          isDarkMode={isDarkMode}
          onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
        />

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {activeView === 'chat' ? (
            <Chat
              messages={messages}
              inputMessage={inputMessage}
              onInputChange={setInputMessage}
              onSendMessage={sendMessage}
              isLoading={isLoading}
              isDarkMode={isDarkMode}
            />
          ) : activeView === 'dashboard' ? (
            <Dashboard
              systemStatus={systemStatus}
              expertStatus={expertStatus}
              onRefresh={() => {
                getSystemStatus();
                getExpertStatus();
              }}
              isDarkMode={isDarkMode}
            />
          ) : (
            <div className="flex flex-col h-full p-6 overflow-hidden">
              <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-gray-200">Editor RTWE</h2>
              <div className="flex-1 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-white dark:bg-gray-800 shadow-lg">
                <LemonEditorWrapper 
                  content="<h1>Olá, Lemon RTWE!</h1><p>Este é o novo editor integrado.</p>" 
                  className="h-full"
                  theme={isDarkMode ? 'dark' : 'light'}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
