"""
Referral Service - Sistema de rastreamento de acessos externos
Adiciona ?referrer=Open+Slap! em todos os links externos e rastreia acessos
"""

import logging
import urllib.parse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sqlite3
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ReferralService:
    """Serviço de rastreamento de referrals para links externos"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(Path(__file__).resolve().parents[2] / "data" / "referrals.db")
        self._ensure_database()
    
    def _ensure_database(self):
        """Garante que o banco de dados de referrals exista"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS referral_clicks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    referrer TEXT DEFAULT 'Open Slap!',
                    user_id INTEGER,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_type TEXT,  -- 'web_search', 'agent_link', 'tool_call', 'user_message'
                    metadata TEXT       -- JSON com dados adicionais
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_timestamp 
                ON referral_clicks(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_domain 
                ON referral_clicks(domain)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_user 
                ON referral_clicks(user_id)
            """)
            
            conn.commit()
    
    def add_referral_param(self, url: str, referrer: str = "Open Slap!") -> str:
        """Adiciona parâmetro de referral a uma URL"""
        if not url or not url.strip():
            return url
        
        try:
            parsed = urllib.parse.urlparse(url.strip())
            
            # Verificar se já tem parâmetros
            query_params = urllib.parse.parse_qsl(parsed.query)
            
            # Adicionar ou substituir referrer
            query_params = [(k, v) for k, v in query_params if k != 'referrer']
            query_params.append(('referrer', referrer))
            
            # Reconstruir a URL
            new_query = urllib.parse.urlencode(query_params)
            new_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
            
            return new_url
            
        except Exception as e:
            logger.error(f"Erro ao adicionar referral à URL {url}: {e}")
            return url
    
    def track_click(self, url: str, user_id: Optional[int] = None, 
                   session_id: Optional[str] = None, ip_address: Optional[str] = None,
                   user_agent: Optional[str] = None, source_type: str = "unknown",
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Registra um clique em link externo"""
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO referral_clicks 
                    (url, domain, referrer, user_id, session_id, ip_address, user_agent, source_type, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    url,
                    domain,
                    "Open Slap!",
                    user_id,
                    session_id,
                    ip_address,
                    user_agent,
                    source_type,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Erro ao registrar clique: {e}")
    
    def get_referral_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Obtém analytics de referrals"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Período
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Total de cliques
                total_clicks = conn.execute("""
                    SELECT COUNT(*) as count FROM referral_clicks 
                    WHERE timestamp >= ?
                """, (since_date,)).fetchone()['count']
                
                # Cliques por domínio
                domain_stats = conn.execute("""
                    SELECT domain, COUNT(*) as clicks 
                    FROM referral_clicks 
                    WHERE timestamp >= ?
                    GROUP BY domain 
                    ORDER BY clicks DESC
                    LIMIT 20
                """, (since_date,)).fetchall()
                
                # Cliques por tipo de source
                source_stats = conn.execute("""
                    SELECT source_type, COUNT(*) as clicks 
                    FROM referral_clicks 
                    WHERE timestamp >= ?
                    GROUP BY source_type 
                    ORDER BY clicks DESC
                """, (since_date,)).fetchall()
                
                # Cliques por dia
                daily_stats = conn.execute("""
                    SELECT DATE(timestamp) as date, COUNT(*) as clicks 
                    FROM referral_clicks 
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """, (since_date,)).fetchall()
                
                # Top URLs
                top_urls = conn.execute("""
                    SELECT url, COUNT(*) as clicks 
                    FROM referral_clicks 
                    WHERE timestamp >= ?
                    GROUP BY url 
                    ORDER BY clicks DESC
                    LIMIT 10
                """, (since_date,)).fetchall()
                
                return {
                    "period_days": days,
                    "total_clicks": total_clicks,
                    "domain_stats": [dict(row) for row in domain_stats],
                    "source_stats": [dict(row) for row in source_stats],
                    "daily_stats": [dict(row) for row in daily_stats],
                    "top_urls": [dict(row) for row in top_urls],
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erro ao gerar analytics: {e}")
            return {"error": str(e)}
    
    def get_domain_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """Análise detalhada por domínio"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Categorias de domínios
                categories = {
                    "search_engines": ["google.com", "duckduckgo.com", "bing.com", "yahoo.com"],
                    "social_media": ["twitter.com", "facebook.com", "linkedin.com", "instagram.com"],
                    "development": ["github.com", "stackoverflow.com", "gitlab.com", "bitbucket.org"],
                    "documentation": ["docs.python.org", "developer.mozilla.org", "readthedocs.io"],
                    "ai_ml": ["openai.com", "anthropic.com", "huggingface.co", "tensorflow.org"],
                    "news": ["news.ycombinator.com", "reddit.com", "medium.com"],
                    "other": []
                }
                
                domain_stats = conn.execute("""
                    SELECT domain, COUNT(*) as clicks 
                    FROM referral_clicks 
                    WHERE timestamp >= ?
                    GROUP BY domain 
                    ORDER BY clicks DESC
                """, (since_date,)).fetchall()
                
                categorized = {}
                uncategorized = []
                
                for row in domain_stats:
                    domain = row['domain']
                    clicks = row['clicks']
                    
                    categorized_domain = None
                    for category, domains in categories.items():
                        if category == "other":
                            continue
                        if any(d in domain for d in domains):
                            categorized_domain = category
                            break
                    
                    if categorized_domain:
                        if categorized_domain not in categorized:
                            categorized[categorized_domain] = {"domains": [], "total_clicks": 0}
                        categorized[categorized_domain]["domains"].append({"domain": domain, "clicks": clicks})
                        categorized[categorized_domain]["total_clicks"] += clicks
                    else:
                        uncategorized.append({"domain": domain, "clicks": clicks})
                
                categorized["other"] = {"domains": uncategorized, "total_clicks": sum(d["clicks"] for d in uncategorized)}
                
                return {
                    "period_days": days,
                    "categorized_domains": categorized,
                    "total_domains": len(domain_stats),
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erro ao analisar domínios: {e}")
            return {"error": str(e)}
    
    def get_user_engagement(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Engajamento de usuário específico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Estatísticas do usuário
                user_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_clicks,
                        COUNT(DISTINCT domain) as unique_domains,
                        COUNT(DISTINCT source_type) as source_types,
                        MIN(timestamp) as first_click,
                        MAX(timestamp) as last_click
                    FROM referral_clicks 
                    WHERE user_id = ? AND timestamp >= ?
                """, (user_id, since_date)).fetchone()
                
                # Domínios mais acessados
                top_domains = conn.execute("""
                    SELECT domain, COUNT(*) as clicks 
                    FROM referral_clicks 
                    WHERE user_id = ? AND timestamp >= ?
                    GROUP BY domain 
                    ORDER BY clicks DESC
                    LIMIT 10
                """, (user_id, since_date)).fetchall()
                
                # Fontes de acesso
                sources = conn.execute("""
                    SELECT source_type, COUNT(*) as clicks 
                    FROM referral_clicks 
                    WHERE user_id = ? AND timestamp >= ?
                    GROUP BY source_type 
                    ORDER BY clicks DESC
                """, (user_id, since_date)).fetchall()
                
                return {
                    "user_id": user_id,
                    "period_days": days,
                    "stats": dict(user_stats) if user_stats else {},
                    "top_domains": [dict(row) for row in top_domains],
                    "sources": [dict(row) for row in sources],
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erro ao obter engajamento do usuário: {e}")
            return {"error": str(e)}

# Instância global
referral_service = ReferralService()

def add_referral_tracking(url: str, referrer: str = "Open Slap!") -> str:
    """Função de conveniência para adicionar tracking"""
    return referral_service.add_referral_param(url, referrer)

def track_external_click(url: str, user_id: Optional[int] = None, 
                         session_id: Optional[str] = None, ip_address: Optional[str] = None,
                         user_agent: Optional[str] = None, source_type: str = "unknown",
                         metadata: Optional[Dict[str, Any]] = None) -> None:
    """Função de conveniência para tracking de cliques"""
    referral_service.track_click(url, user_id, session_id, ip_address, user_agent, source_type, metadata)
