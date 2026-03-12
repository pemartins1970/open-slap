import React, { useState } from 'react';
import {
  MessageSquare,
  LayoutDashboard,
  FileEdit,
  Bot,
  Users,
  Settings,
  Moon,
  Sun,
  RefreshCw,
  Code,
  Palette,
  Shield,
  TrendingUp,
  Activity,
  Cpu,
  Database,
  Globe,
  Zap
} from 'lucide-react';

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

interface SidebarProps {
  activeView: 'chat' | 'dashboard' | 'editor';
  onViewChange: (view: 'chat' | 'dashboard' | 'editor') => void;
  systemStatus: SystemStatus | null;
  expertStatus: ExpertStatus | null;
  onRouteTask: (taskType: string, description: string) => void;
  onRefreshStatus: () => void;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  activeView,
  onViewChange,
  systemStatus,
  expertStatus,
  onRouteTask,
  onRefreshStatus,
  isDarkMode,
  onToggleDarkMode
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const taskTemplates = [
    {
      type: 'coding',
      icon: Code,
      label: 'Desenvolvimento',
      description: 'Criar APIs, implementar features, debug',
      color: 'blue'
    },
    {
      type: 'design',
      icon: Palette,
      label: 'Design',
      description: 'Arquitetura, UI/UX, planejamento',
      color: 'purple'
    },
    {
      type: 'security',
      icon: Shield,
      label: 'Segurança',
      description: 'Auditoria, vulnerabilidades, compliance',
      color: 'red'
    },
    {
      type: 'analysis',
      icon: TrendingUp,
      label: 'Análise',
      description: 'Performance, métricas, otimização',
      color: 'green'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return isDarkMode ? 'text-green-400' : 'text-green-600';
      case 'busy': return isDarkMode ? 'text-yellow-400' : 'text-yellow-600';
      case 'offline': return isDarkMode ? 'text-gray-400' : 'text-gray-600';
      default: return isDarkMode ? 'text-gray-400' : 'text-gray-600';
    }
  };

  const getLoadColor = (current: number, max: number) => {
    const percentage = (current / max) * 100;
    if (percentage < 50) return isDarkMode ? 'bg-green-600' : 'bg-green-500';
    if (percentage < 80) return isDarkMode ? 'bg-yellow-600' : 'bg-yellow-500';
    return isDarkMode ? 'bg-red-600' : 'bg-red-500';
  };

  return (
    <div className={`flex flex-col ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-r transition-all duration-300 ${isExpanded ? 'w-80' : 'w-16'}`}>
      {/* Header */}
      <div className={`p-4 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="flex items-center justify-between">
          {isExpanded && (
            <div className="flex items-center space-x-2">
              <Bot className={`w-6 h-6 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`} />
              <span className={`font-bold text-lg ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                Agentic System
              </span>
            </div>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={`p-2 rounded-lg transition-colors ${isDarkMode ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}
          >
            <Activity className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Navigation */}
      <div className="p-4 space-y-2">
        <button
          onClick={() => onViewChange('chat')}
          className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
            activeView === 'chat'
              ? isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
              : isDarkMode ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'
          }`}
        >
          <MessageSquare className="w-5 h-5" />
          {isExpanded && <span>Chat</span>}
        </button>

        <button
          onClick={() => onViewChange('dashboard')}
          className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
            activeView === 'dashboard'
              ? isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
              : isDarkMode ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'
          }`}
        >
          <LayoutDashboard className="w-5 h-5" />
          {isExpanded && <span>Dashboard</span>}
        </button>

        <button
          onClick={() => onViewChange('editor')}
          className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
            activeView === 'editor'
              ? isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
              : isDarkMode ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'
          }`}
        >
          <FileEdit className="w-5 h-5" />
          {isExpanded && <span>Editor</span>}
        </button>
      </div>

      {/* Quick Tasks */}
      {isExpanded && (
        <div className="px-4 pb-4">
          <h3 className={`text-sm font-medium mb-3 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Tarefas Rápidas
          </h3>
          <div className="space-y-2">
            {taskTemplates.map((template) => {
              const Icon = template.icon;
              return (
                <button
                  key={template.type}
                  onClick={() => onRouteTask(template.type, `Tarefa de ${template.label} solicitada via interface`)}
                  className={`w-full flex items-start space-x-3 p-3 rounded-lg border transition-colors ${
                    isDarkMode
                      ? 'border-gray-700 hover:bg-gray-700 text-gray-300'
                      : 'border-gray-200 hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <div className={`p-2 rounded-lg bg-${template.color}-100 text-${template.color}-600`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 text-left">
                    <div className={`font-medium text-sm ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                      {template.label}
                    </div>
                    <div className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      {template.description}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* System Status */}
      {isExpanded && systemStatus && (
        <div className="px-4 pb-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Status do Sistema
            </h3>
            <button
              onClick={onRefreshStatus}
              className={`p-1 rounded transition-colors ${isDarkMode ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-3">
            {/* Server Status */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4 text-green-500" />
                <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Servidor
                </span>
              </div>
              <span className={`text-xs px-2 py-1 rounded-full ${
                systemStatus.server === 'running'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}>
                {systemStatus.server}
              </span>
            </div>

            {/* Sessions */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-blue-500" />
                <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Sessões
                </span>
              </div>
              <span className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                {systemStatus.active_sessions}
              </span>
            </div>

            {/* Experts */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Bot className="w-4 h-4 text-purple-500" />
                <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Especialistas
                </span>
              </div>
              <span className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                {systemStatus.moe_experts}
              </span>
            </div>

            {/* LLM Providers */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Cpu className="w-4 h-4 text-orange-500" />
                <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  LLMs
                </span>
              </div>
              <span className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                {systemStatus.llm_providers.length}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Expert Status */}
      {isExpanded && expertStatus && (
        <div className="px-4 pb-4">
          <h3 className={`text-sm font-medium mb-3 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Especialistas
          </h3>
          <div className="space-y-2">
            {Object.entries(expertStatus.experts).slice(0, 3).map(([id, expert]) => (
              <div key={id} className={`p-2 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                    {expert.name}
                  </span>
                  <span className={`text-xs ${getStatusColor(expert.status)}`}>
                    {expert.status}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="flex-1">
                    <div className={`h-1 rounded-full ${isDarkMode ? 'bg-gray-600' : 'bg-gray-300'}`}>
                      <div
                        className={`h-1 rounded-full ${getLoadColor(expert.current_load, expert.max_concurrent_tasks)}`}
                        style={{
                          width: `${(expert.current_load / expert.max_concurrent_tasks) * 100}%`
                        }}
                      />
                    </div>
                  </div>
                  <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    {expert.current_load}/{expert.max_concurrent_tasks}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className={`mt-auto p-4 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="flex items-center justify-between">
          {isExpanded && (
            <div className="flex items-center space-x-2">
              <Database className={`w-4 h-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
              <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                v1.0.0
              </span>
            </div>
          )}
          <button
            onClick={onToggleDarkMode}
            className={`p-2 rounded-lg transition-colors ${isDarkMode ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}
          >
            {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
