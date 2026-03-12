import React, { useState, useEffect } from 'react';
import {
  Activity,
  Bot,
  Users,
  Globe,
  Cpu,
  Database,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  RefreshCw,
  BarChart3,
  PieChart,
  Zap,
  Shield,
  Code,
  Palette,
  Eye
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

interface DashboardProps {
  systemStatus: SystemStatus | null;
  expertStatus: ExpertStatus | null;
  onRefresh: () => void;
  isDarkMode: boolean;
}

const Dashboard: React.FC<DashboardProps> = ({
  systemStatus,
  expertStatus,
  onRefresh,
  isDarkMode
}) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1h' | '24h' | '7d'>('1h');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await onRefresh();
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'idle':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'busy':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'offline':
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  const getLoadPercentage = (current: number, max: number) => {
    return Math.round((current / max) * 100);
  };

  const getLoadColor = (percentage: number) => {
    if (percentage < 50) return 'text-green-600';
    if (percentage < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getExpertIcon = (expertName: string) => {
    if (expertName.toLowerCase().includes('architect')) return <Palette className="w-4 h-4" />;
    if (expertName.toLowerCase().includes('backend')) return <Database className="w-4 h-4" />;
    if (expertName.toLowerCase().includes('frontend')) return <Eye className="w-4 h-4" />;
    if (expertName.toLowerCase().includes('security')) return <Shield className="w-4 h-4" />;
    return <Bot className="w-4 h-4" />;
  };

  return (
    <div className={`p-6 h-full overflow-y-auto custom-scrollbar ${isDarkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Dashboard
          </h1>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Visão geral do sistema agêntico
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Time Range Selector */}
          <div className={`flex rounded-lg border ${isDarkMode ? 'border-gray-700' : 'border-gray-300'}`}>
            {(['1h', '24h', '7d'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setSelectedTimeRange(range)}
                className={`px-3 py-1 text-sm font-medium transition-colors ${
                  selectedTimeRange === range
                    ? isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
                    : isDarkMode ? 'text-gray-400 hover:bg-gray-800' : 'text-gray-600 hover:bg-gray-100'
                } ${range === '1h' ? 'rounded-l-lg' : ''} ${range === '7d' ? 'rounded-r-lg' : ''}`}
              >
                {range}
              </button>
            ))}
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={`p-2 rounded-lg transition-colors ${
              isRefreshing
                ? 'opacity-50 cursor-not-allowed'
                : isDarkMode ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-100 text-gray-600'
            }`}
          >
            <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* System Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Server Status */}
        <div className={`p-6 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-blue-900' : 'bg-blue-100'}`}>
              <Globe className="w-6 h-6 text-blue-500" />
            </div>
            {systemStatus && getStatusIcon(systemStatus.server)}
          </div>
          <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Servidor
          </h3>
          <p className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            {systemStatus?.server || 'Desconhecido'}
          </p>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} mt-1`}>
            Status do MCP Server
          </p>
        </div>

        {/* Active Sessions */}
        <div className={`p-6 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-green-900' : 'bg-green-100'}`}>
              <Users className="w-6 h-6 text-green-500" />
            </div>
            <div className={`text-xs px-2 py-1 rounded-full bg-green-100 text-green-800`}>
              Ativo
            </div>
          </div>
          <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Sessões
          </h3>
          <p className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            {systemStatus?.active_sessions || 0}
          </p>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} mt-1`}>
            Sessões ativas
          </p>
        </div>

        {/* MoE Experts */}
        <div className={`p-6 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-purple-900' : 'bg-purple-100'}`}>
              <Bot className="w-6 h-6 text-purple-500" />
            </div>
            <div className={`text-xs px-2 py-1 rounded-full ${isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-800'}`}>
              {expertStatus?.available_experts || 0}/{expertStatus?.total_experts || 0}
            </div>
          </div>
          <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Especialistas
          </h3>
          <p className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            {expertStatus?.total_experts || 0}
          </p>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} mt-1`}>
            Especialistas MoE
          </p>
        </div>

        {/* LLM Providers */}
        <div className={`p-6 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-orange-900' : 'bg-orange-100'}`}>
              <Cpu className="w-6 h-6 text-orange-500" />
            </div>
            <div className={`text-xs px-2 py-1 rounded-full bg-orange-100 text-orange-800`}>
              Online
            </div>
          </div>
          <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            LLMs
          </h3>
          <p className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            {systemStatus?.llm_providers.length || 0}
          </p>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} mt-1`}>
            Providers ativos
          </p>
        </div>
      </div>

      {/* Expert Status Grid */}
      {expertStatus && (
        <div className={`mb-8`}>
          <h2 className={`text-xl font-bold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Status dos Especialistas
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(expertStatus.experts).map(([id, expert]) => {
              const loadPercentage = getLoadPercentage(expert.current_load, expert.max_concurrent_tasks);
              const Icon = getExpertIcon(expert.name);
              
              return (
                <div
                  key={id}
                  className={`p-4 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <div className={`p-2 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
                        <Icon className={`w-4 h-4 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`} />
                      </div>
                      <div>
                        <h3 className={`font-medium text-sm ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                          {expert.name}
                        </h3>
                        <p className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                          {expert.status}
                        </p>
                      </div>
                    </div>
                    {getStatusIcon(expert.status)}
                  </div>

                  {/* Load Bar */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                        Carga
                      </span>
                      <span className={`text-xs font-medium ${getLoadColor(loadPercentage)}`}>
                        {loadPercentage}%
                      </span>
                    </div>
                    <div className={`h-2 rounded-full ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          loadPercentage < 50 ? 'bg-green-500' :
                          loadPercentage < 80 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${loadPercentage}%` }}
                      />
                    </div>
                    <div className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      {expert.current_load}/{expert.max_concurrent_tasks} tarefas
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Activity Chart Placeholder */}
      <div className={`p-6 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Atividade do Sistema
          </h2>
          <div className="flex items-center space-x-2">
            <BarChart3 className={`w-5 h-5 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
            <PieChart className={`w-5 h-5 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
          </div>
        </div>

        {/* Chart Placeholder */}
        <div className={`h-64 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'} flex items-center justify-center`}>
          <div className="text-center">
            <TrendingUp className={`w-12 h-12 mx-auto mb-2 ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`} />
            <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Gráficos de atividade em desenvolvimento
            </p>
            <p className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-500'} mt-1`}>
              Métricas de performance e uso dos especialistas
            </p>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className={`mt-8`}>
        <h2 className={`text-xl font-bold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
          Atividade Recente
        </h2>
        <div className={`rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="p-4">
            <div className="space-y-3">
              {expertStatus?.active_tasks && Object.keys(expertStatus.active_tasks).length > 0 ? (
                Object.entries(expertStatus.active_tasks).slice(0, 5).map(([taskId, task]) => (
                  <div
                    key={taskId}
                    className={`flex items-center justify-between p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}
                  >
                    <div className="flex items-center space-x-3">
                      <Clock className={`w-4 h-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
                      <div>
                        <p className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                          {task.description || `Tarefa ${taskId}`}
                        </p>
                        <p className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                          {task.assigned_expert || 'Não atribuída'}
                        </p>
                      </div>
                    </div>
                    <div className={`text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800`}>
                      {task.type || 'unknown'}
                    </div>
                  </div>
                ))
              ) : (
                <div className={`text-center py-8 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  <Activity className={`w-8 h-8 mx-auto mb-2 opacity-50`} />
                  <p className="text-sm">
                    Nenhuma tarefa ativa no momento
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
