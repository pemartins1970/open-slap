import React from 'react';
import {
  Bot,
  Wifi,
  WifiOff,
  MessageSquare,
  LayoutDashboard,
  FileEdit,
  Moon,
  Sun,
  Settings,
  LogOut,
  User
} from 'lucide-react';

interface HeaderProps {
  isConnected: boolean;
  sessionId: string;
  activeView: 'chat' | 'dashboard' | 'editor';
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}

const Header: React.FC<HeaderProps> = ({
  isConnected,
  sessionId,
  activeView,
  isDarkMode,
  onToggleDarkMode
}) => {
  const formatSessionId = (id: string) => {
    return id.length > 8 ? `${id.slice(0, 8)}...` : id;
  };

  const getViewTitle = () => {
    switch (activeView) {
      case 'chat':
        return 'Chat Agêntico';
      case 'dashboard':
        return 'Dashboard';
      case 'editor':
        return 'Editor RTWE';
      default:
        return 'Agentic System';
    }
  };

  const getViewIcon = () => {
    switch (activeView) {
      case 'chat':
        return <MessageSquare className="w-5 h-5" />;
      case 'dashboard':
        return <LayoutDashboard className="w-5 h-5" />;
      case 'editor':
        return <FileEdit className="w-5 h-5" />;
      default:
        return <Bot className="w-5 h-5" />;
    }
  };

  return (
    <header className={`border-b ${isDarkMode ? 'bg-gray-900 border-gray-700' : 'bg-white border-gray-200'}`}>
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left Section - Title and Status */}
          <div className="flex items-center space-x-4">
            {/* View Icon */}
            <div className={`p-2 rounded-lg ${isDarkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
              {getViewIcon()}
            </div>

            {/* Title */}
            <div>
              <h1 className={`text-xl font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                {getViewTitle()}
              </h1>
              <div className="flex items-center space-x-3 text-sm">
                {/* Connection Status */}
                <div className="flex items-center space-x-1">
                  {isConnected ? (
                    <>
                      <Wifi className="w-4 h-4 text-green-500" />
                      <span className={isDarkMode ? 'text-green-400' : 'text-green-600'}>
                        Conectado
                      </span>
                    </>
                  ) : (
                    <>
                      <WifiOff className="w-4 h-4 text-red-500" />
                      <span className={isDarkMode ? 'text-red-400' : 'text-red-600'}>
                        Desconectado
                      </span>
                    </>
                  )}
                </div>

                {/* Session ID */}
                {sessionId && (
                  <div className="flex items-center space-x-1">
                    <User className={`w-4 h-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
                    <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                      Sessão: {formatSessionId(sessionId)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Section - Actions */}
          <div className="flex items-center space-x-3">
            {/* Theme Toggle */}
            <button
              onClick={onToggleDarkMode}
              className={`p-2 rounded-lg transition-colors ${
                isDarkMode 
                  ? 'hover:bg-gray-700 text-gray-400' 
                  : 'hover:bg-gray-100 text-gray-600'
              }`}
              title="Alternar tema"
            >
              {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {/* Settings */}
            <button
              className={`p-2 rounded-lg transition-colors ${
                isDarkMode 
                  ? 'hover:bg-gray-700 text-gray-400' 
                  : 'hover:bg-gray-100 text-gray-600'
              }`}
              title="Configurações"
            >
              <Settings className="w-5 h-5" />
            </button>

            {/* Logout */}
            <button
              className={`p-2 rounded-lg transition-colors ${
                isDarkMode 
                  ? 'hover:bg-gray-700 text-gray-400' 
                  : 'hover:bg-gray-100 text-gray-600'
              }`}
              title="Sair"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Connection Status Bar */}
      <div className={`px-6 py-2 border-t ${isDarkMode ? 'bg-gray-900 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center space-x-4">
            {/* Server Status */}
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                MCP Server: {isConnected ? 'Online' : 'Offline'}
              </span>
            </div>

            {/* Expert Status */}
            <div className="flex items-center space-x-1">
              <Bot className={`w-3 h-3 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
              <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                MoE Experts: 4 disponíveis
              </span>
            </div>

            {/* LLM Status */}
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full bg-blue-500`} />
              <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                LLM Providers: 2 ativos
              </span>
            </div>
          </div>

          {/* Timestamp */}
          <div className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
            {new Date().toLocaleString('pt-BR', {
              day: '2-digit',
              month: '2-digit',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
