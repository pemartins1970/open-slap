import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  ExternalLink, 
  TrendingUp, 
  Users, 
  Globe, 
  Search,
  Code,
  Brain,
  MessageSquare,
  BarChart3,
  Activity
} from 'lucide-react';

interface ReferralAnalytics {
  period_days: number;
  total_clicks: number;
  domain_stats: Array<{ domain: string; clicks: number }>;
  source_stats: Array<{ source_type: string; clicks: number }>;
  daily_stats: Array<{ date: string; clicks: number }>;
  top_urls: Array<{ url: string; clicks: number }>;
  generated_at: string;
}

interface DomainBreakdown {
  period_days: number;
  categorized_domains: {
    [key: string]: {
      domains: Array<{ domain: string; clicks: number }>;
      total_clicks: number;
    };
  };
  total_domains: number;
  generated_at: string;
}

interface PerceptionMetrics {
  domain_diversity_score: number;
  category_presence_score: number;
  engagement_diversity_score: number;
  recognition_score: number;
  overall_perception_score: number;
  total_domains_tracked: number;
  categories_reached: number;
  engagement_sources: number;
}

interface ReferralDashboardProps {
  className?: string;
}

export function ReferralDashboard({ className }: ReferralDashboardProps) {
  const [analytics, setAnalytics] = useState<ReferralAnalytics | null>(null);
  const [domainBreakdown, setDomainBreakdown] = useState<DomainBreakdown | null>(null);
  const [perceptionMetrics, setPerceptionMetrics] = useState<PerceptionMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  useEffect(() => {
    fetchDashboardData();
  }, [selectedPeriod]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Token de autenticação não encontrado');
      }

      const response = await fetch(`/api/referrals/dashboard?days=${selectedPeriod}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Erro ao carregar dados do dashboard');
      }

      const data = await response.json();
      
      if (data.success) {
        setAnalytics(data.data.analytics);
        setDomainBreakdown(data.data.domain_breakdown);
        setPerceptionMetrics(data.data.perception_metrics);
      } else {
        throw new Error(data.message || 'Erro desconhecido');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category: string) => {
    const icons: { [key: string]: React.ReactNode } = {
      search_engines: <Search className="h-4 w-4" />,
      development: <Code className="h-4 w-4" />,
      ai_ml: <Brain className="h-4 w-4" />,
      social_media: <Users className="h-4 w-4" />,
      documentation: <MessageSquare className="h-4 w-4" />,
      news: <TrendingUp className="h-4 w-4" />,
      other: <Globe className="h-4 w-4" />,
    };
    return icons[category] || icons.other;
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      search_engines: 'bg-blue-100 text-blue-800',
      development: 'bg-green-100 text-green-800',
      ai_ml: 'bg-purple-100 text-purple-800',
      social_media: 'bg-pink-100 text-pink-800',
      documentation: 'bg-yellow-100 text-yellow-800',
      news: 'bg-orange-100 text-orange-800',
      other: 'bg-gray-100 text-gray-800',
    };
    return colors[category] || colors.other;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <div className="text-center text-red-600">
            <Activity className="h-8 w-8 mx-auto mb-2" />
            <p>Erro ao carregar dados: {error}</p>
            <Button onClick={fetchDashboardData} className="mt-2">
              Tentar novamente
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!analytics || !domainBreakdown || !perceptionMetrics) {
    return null;
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Dashboard de Referrals</h2>
          <p className="text-gray-600">Percepção e reconhecimento de uso do Open Slap!</p>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map((days) => (
            <Button
              key={days}
              variant={selectedPeriod === days ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedPeriod(days)}
            >
              {days === 7 ? '7 dias' : days === 30 ? '30 dias' : '90 dias'}
            </Button>
          ))}
        </div>
      </div>

      {/* Métricas Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Cliques</CardTitle>
            <ExternalLink className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_clicks.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Últimos {selectedPeriod} dias
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Domínios Únicos</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{perceptionMetrics.total_domains_tracked}</div>
            <p className="text-xs text-muted-foreground">
              Sites diferentes acessados
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Score de Percepção</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getScoreColor(perceptionMetrics.overall_perception_score)}`}>
              {perceptionMetrics.overall_perception_score.toFixed(1)}
            </div>
            <Progress value={perceptionMetrics.overall_perception_score} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Categorias Alcançadas</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{perceptionMetrics.categories_reached}</div>
            <p className="text-xs text-muted-foreground">
              de {Object.keys(domainBreakdown.categorized_domains).length} categorias
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs Detalhadas */}
      <Tabs defaultValue="domains" className="space-y-4">
        <TabsList>
          <TabsTrigger value="domains">Domínios</TabsTrigger>
          <TabsTrigger value="metrics">Métricas</TabsTrigger>
          <TabsTrigger value="sources">Fontes</TabsTrigger>
        </TabsList>

        <TabsContent value="domains" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Domínios por Categoria</CardTitle>
              <CardDescription>
                Distribuição de acessos por tipo de site
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(domainBreakdown.categorized_domains).map(([category, data]) => (
                  <div key={category} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getCategoryIcon(category)}
                        <span className="font-medium capitalize">
                          {category.replace('_', ' ')}
                        </span>
                        <Badge variant="secondary" className={getCategoryColor(category)}>
                          {data.total_clicks} cliques
                        </Badge>
                      </div>
                      <span className="text-sm text-gray-500">
                        {data.domains.length} domínios
                      </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                      {data.domains.slice(0, 6).map((domain) => (
                        <div key={domain.domain} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <span className="text-sm truncate">{domain.domain}</span>
                          <span className="text-xs text-gray-500">{domain.clicks}</span>
                        </div>
                      ))}
                      {data.domains.length > 6 && (
                        <div className="text-sm text-gray-500 p-2 text-center">
                          +{data.domains.length - 6} mais
                        </div>
                      )}
                    </div>
                    <Separator />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Métricas de Percepção</CardTitle>
                <CardDescription>
                  Indicadores de reconhecimento e alcance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm">Diversidade de Domínios</span>
                    <span className={`text-sm font-medium ${getScoreColor(perceptionMetrics.domain_diversity_score)}`}>
                      {perceptionMetrics.domain_diversity_score.toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={perceptionMetrics.domain_diversity_score} />
                </div>
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm">Presença em Categorias</span>
                    <span className={`text-sm font-medium ${getScoreColor(perceptionMetrics.category_presence_score)}`}>
                      {perceptionMetrics.category_presence_score.toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={perceptionMetrics.category_presence_score} />
                </div>
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm">Diversidade de Engajamento</span>
                    <span className={`text-sm font-medium ${getScoreColor(perceptionMetrics.engagement_diversity_score)}`}>
                      {perceptionMetrics.engagement_diversity_score.toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={perceptionMetrics.engagement_diversity_score} />
                </div>
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm">Score de Reconhecimento</span>
                    <span className={`text-sm font-medium ${getScoreColor(perceptionMetrics.recognition_score)}`}>
                      {perceptionMetrics.recognition_score.toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={perceptionMetrics.recognition_score} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Domínios</CardTitle>
                <CardDescription>
                  Sites mais acessados
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analytics.domain_stats.slice(0, 10).map((domain, index) => (
                    <div key={domain.domain} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
                        <span className="text-sm">{domain.domain}</span>
                      </div>
                      <Badge variant="outline">{domain.clicks}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="sources" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Fontes de Acesso</CardTitle>
              <CardDescription>
                Como os usuários acessam os links externos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.source_stats.map((source) => (
                  <div key={source.source_type} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span className="font-medium capitalize">
                        {source.source_type.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">
                        {((source.clicks / analytics.total_clicks) * 100).toFixed(1)}%
                      </span>
                      <Badge>{source.clicks}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
