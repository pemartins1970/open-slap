# Documentação da Interface Web e Componentes

## Visão Geral

Interface web moderna e responsiva construída com React 18+, TypeScript e Tailwind CSS, oferecendo uma experiência completa para interação com o sistema agêntico.

## Arquitetura da Interface

### Stack Tecnológico
- **Frontend:** React 18+ com TypeScript
- **State Management:** Zustand / Redux Toolkit
- **Styling:** Tailwind CSS + Headless UI
- **Routing:** React Router v6
- **HTTP Client:** Axios + React Query
- **Real-time:** Socket.IO Client
- **UI Components:** Radix UI + Lucide Icons
- **Charts:** Recharts / Chart.js
- **Forms:** React Hook Form + Zod
- **Testing:** Jest + React Testing Library + Playwright

### Estrutura de Diretórios
```
src/frontend/
├── components/          # Componentes reutilizáveis
│   ├── ui/             # Componentes base (Button, Input, etc)
│   ├── layout/         # Layout components
│   ├── chat/           # Chat components
│   ├── sidebar/        # Sidebar components
│   └── dashboard/      # Dashboard components
├── pages/              # Páginas principais
├── hooks/              # Custom hooks
├── stores/             # State management
├── services/           # API services
├── utils/              # Utilitários
├── types/              # TypeScript types
└── styles/             # Estilos globais
```

## Layout Principal

### Header Component
```typescript
interface HeaderProps {
  user: User;
  notifications: Notification[];
  onMenuToggle: () => void;
}

const Header: React.FC<HeaderProps> = ({ user, notifications, onMenuToggle }) => {
  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-4">
      <div className="flex items-center space-x-4">
        <button onClick={onMenuToggle} className="p-2 rounded-md hover:bg-gray-100">
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="text-xl font-semibold text-gray-900">Agentic System</h1>
      </div>
      
      <div className="flex items-center space-x-4">
        <NotificationDropdown notifications={notifications} />
        <UserMenu user={user} />
      </div>
    </header>
  );
};
```

### Sidebar Component
```typescript
interface SidebarProps {
  isOpen: boolean;
  activeSection: string;
  onSectionChange: (section: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, activeSection, onSectionChange }) => {
  const menuItems = [
    { id: 'tasks', icon: ListTodo, label: 'Todas as tarefas', badge: 12 },
    { id: 'new-task', icon: Plus, label: 'Nova tarefa' },
    { id: 'projects', icon: Folder, label: 'Projetos', badge: 5 },
    { id: 'new-project', icon: FolderPlus, label: 'Novo Projeto' },
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'reports', icon: BarChart3, label: 'Relatórios' },
    { id: 'skills', icon: Brain, label: 'Central de skills' },
    { id: 'agents', icon: Users, label: 'Central de agentes' },
    { id: 'ml', icon: Cpu, label: 'Machine Learning' },
    { id: 'rag', icon: Database, label: 'RAG' },
  ];

  return (
    <aside className={`bg-gray-50 border-r border-gray-200 transition-all duration-300 ${
      isOpen ? 'w-64' : 'w-0 overflow-hidden'
    }`}>
      <nav className="p-4 space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onSectionChange(item.id)}
            className={`w-full flex items-center justify-between p-3 rounded-lg transition-colors ${
              activeSection === item.id
                ? 'bg-blue-100 text-blue-700'
                : 'hover:bg-gray-100 text-gray-700'
            }`}
          >
            <div className="flex items-center space-x-3">
              <item.icon className="h-5 w-5" />
              <span className="font-medium">{item.label}</span>
            </div>
            {item.badge && (
              <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </nav>
    </aside>
  );
};
```

## Componentes Principais

### Chat Interface
```typescript
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  agent?: string;
  attachments?: Attachment[];
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { selectedAgent } = useAgentStore();

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatService.sendMessage({
        message: input,
        agent: selectedAgent,
        context: messages.slice(-5), // Last 5 messages for context
      });

      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        agent: response.agent,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && <TypingIndicator />}
      </div>
      
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Digite sua mensagem..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};
```

### Dashboard Component
```typescript
interface DashboardMetrics {
  totalProjects: number;
  activeTasks: number;
  completedTasks: number;
  activeAgents: number;
  systemHealth: 'healthy' | 'warning' | 'critical';
  resourceUsage: {
    cpu: number;
    memory: number;
    disk: number;
  };
}

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await dashboardService.getMetrics(timeRange);
        setMetrics(data);
      } catch (error) {
        console.error('Error fetching metrics:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, [timeRange]);

  if (!metrics) return <div>Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value as any)}
          className="px-3 py-2 border border-gray-300 rounded-lg"
        >
          <option value="24h">Últimas 24 horas</option>
          <option value="7d">Últimos 7 dias</option>
          <option value="30d">Últimos 30 dias</option>
        </select>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Projetos Totais"
          value={metrics.totalProjects}
          icon={Folder}
          trend={{ value: 12, isPositive: true }}
        />
        <MetricCard
          title="Tarefas Ativas"
          value={metrics.activeTasks}
          icon={ListTodo}
          trend={{ value: 8, isPositive: true }}
        />
        <MetricCard
          title="Tarefas Concluídas"
          value={metrics.completedTasks}
          icon={CheckCircle}
          trend={{ value: 15, isPositive: true }}
        />
        <MetricCard
          title="Agentes Ativos"
          value={metrics.activeAgents}
          icon={Users}
          trend={{ value: 2, isPositive: false }}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Uso de Recursos</h3>
          <ResourceUsageChart data={metrics.resourceUsage} />
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Atividade de Agentes</h3>
          <AgentActivityChart timeRange={timeRange} />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold">Atividade Recente</h3>
        </div>
        <RecentActivityList />
      </div>
    </div>
  );
};
```

### Task Management Component
```typescript
interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high';
  assignedAgent?: string;
  createdAt: Date;
  updatedAt: Date;
  deadline?: Date;
  tags: string[];
}

const TaskManagement: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<TaskFilter>({});
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Gerenciamento de Tarefas</h2>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
        >
          <Plus className="h-5 w-5" />
          <span>Nova Tarefa</span>
        </button>
      </div>

      {/* Filters */}
      <TaskFilters filter={filter} onFilterChange={setFilter} />

      {/* Task List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tasks
          .filter(task => applyFilters(task, filter))
          .map(task => (
            <TaskCard
              key={task.id}
              task={task}
              onEdit={(task) => {/* Handle edit */}}
              onDelete={(id) => {/* Handle delete */}}
              onStatusChange={(id, status) => {/* Handle status change */}}
            />
          ))}
      </div>

      {/* Create Task Modal */}
      {isCreateModalOpen && (
        <CreateTaskModal
          onClose={() => setIsCreateModalOpen(false)}
          onSubmit={(task) => {
            setTasks(prev => [...prev, task]);
            setIsCreateModalOpen(false);
          }}
        />
      )}
    </div>
  );
};
```

### Agent Management Component
```typescript
interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'idle' | 'busy' | 'offline' | 'error';
  currentTask?: string;
  performance: {
    tasksCompleted: number;
    averageResponseTime: number;
    successRate: number;
  };
  capabilities: string[];
  lastActive: Date;
}

const AgentManagement: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Central de Agentes</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent List */}
        <div className="lg:col-span-2 space-y-4">
          {agents.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onSelect={() => setSelectedAgent(agent)}
              isSelected={selectedAgent?.id === agent.id}
            />
          ))}
        </div>

        {/* Agent Details */}
        {selectedAgent && (
          <div className="bg-white rounded-lg shadow p-6">
            <AgentDetails agent={selectedAgent} />
          </div>
        )}
      </div>
    </div>
  );
};
```

## Componentes UI Reutilizáveis

### Button Component
```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  className,
  disabled,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500',
    outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-blue-500',
    ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-blue-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
      {icon && !loading && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
};
```

### Modal Component
```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children, size = 'md' }) => {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black opacity-50" onClick={onClose} />
        
        <div className={`relative w-full ${sizes[size]} bg-white rounded-lg shadow-xl`}>
          {title && (
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-semibold">{title}</h3>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
          
          <div className="p-6">{children}</div>
        </div>
      </div>
    </div>
  );
};
```

## State Management

### Store Configuration
```typescript
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface AppState {
  user: User | null;
  currentProject: Project | null;
  selectedAgent: Agent | null;
  theme: 'light' | 'dark';
  notifications: Notification[];
  
  // Actions
  setUser: (user: User | null) => void;
  setCurrentProject: (project: Project | null) => void;
  setSelectedAgent: (agent: Agent | null) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  addNotification: (notification: Notification) => void;
  removeNotification: (id: string) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set, get) => ({
      user: null,
      currentProject: null,
      selectedAgent: null,
      theme: 'light',
      notifications: [],
      
      setUser: (user) => set({ user }),
      setCurrentProject: (project) => set({ currentProject: project }),
      setSelectedAgent: (agent) => set({ selectedAgent: agent }),
      setTheme: (theme) => set({ theme }),
      addNotification: (notification) =>
        set((state) => ({
          notifications: [...state.notifications, notification],
        })),
      removeNotification: (id) =>
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),
    }),
    { name: 'app-store' }
  )
);
```

## Responsividade

### Breakpoints
- **Mobile:** < 768px
- **Tablet:** 768px - 1024px
- **Desktop:** > 1024px

### Mobile Adaptations
- Sidebar colapsável em mobile
- Cards empilhados verticalmente
- Touch-friendly buttons (min 44px)
- Swipe gestures para navegação

## Performance

### Otimizações
- Code splitting por rota
- Lazy loading de componentes
- Virtual scrolling para listas longas
- Memoização de componentes pesados
- Imagens otimizadas e lazy loaded

### Métricas Alvo
- First Contentful Paint: < 1.5s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1
- First Input Delay: < 100ms

## Acessibilidade

### WCAG 2.1 Compliance
- Navegação por teclado completa
- ARIA labels apropriados
- Contraste de cores mínimo 4.5:1
- Screen reader friendly
- Focus management adequado

## Temas

### Light Theme
```css
:root {
  --background: 255 255 255;
  --foreground: 9 9 11;
  --primary: 37 99 235;
  --primary-foreground: 255 255 255;
  --secondary: 241 245 249;
  --secondary-foreground: 15 23 42;
  --muted: 241 245 249;
  --muted-foreground: 100 116 139;
  --border: 226 232 240;
  --input: 255 255 255;
  --ring: 37 99 235;
}
```

### Dark Theme
```css
:root[data-theme="dark"] {
  --background: 9 9 11;
  --foreground: 250 250 250;
  --primary: 59 130 246;
  --primary-foreground: 9 9 11;
  --secondary: 39 39 42;
  --secondary-foreground: 250 250 250;
  --muted: 39 39 42;
  --muted-foreground: 161 161 170;
  --border: 39 39 42;
  --input: 17 24 39;
  --ring: 59 130 246;
}
```

## Internacionalização

### Suporte a Idiomas
- Português (pt-BR) - Padrão
- Inglês (en-US)
- Espanhol (es-ES)

### Formatos
- Datas: DD/MM/YYYY
- Números: 1.234,56
- Moeda: R$ 1.234,56

## Testes

### Estratégia de Testes
- Unit tests: Jest + React Testing Library
- Integration tests: Cypress
- E2E tests: Playwright
- Visual regression: Chromatic
- Performance: Lighthouse CI

### Coverage Alvo
- Statements: > 90%
- Branches: > 85%
- Functions: > 90%
- Lines: > 90%
