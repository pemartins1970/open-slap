"""
Referral Routes - Endpoints para analytics e tracking de referrals
Dashboard de percepção e reconhecimento de uso do Open Slap!
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials

from ..auth import get_current_user
from ..services.referral_service import referral_service
from ..deps import security

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/referrals", tags=["Referral Analytics"])

@router.get("/analytics")
async def get_referral_analytics(
    days: int = Query(30, ge=1, le=365, description="Período em dias"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtém analytics de referrals do sistema"""
    try:
        analytics = referral_service.get_referral_analytics(days)
        return {
            "success": True,
            "data": analytics
        }
    except Exception as e:
        logger.error(f"Erro ao obter analytics: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter analytics")

@router.get("/domains")
async def get_domain_breakdown(
    days: int = Query(30, ge=1, le=365, description="Período em dias"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtém análise detalhada por domínio"""
    try:
        breakdown = referral_service.get_domain_breakdown(days)
        return {
            "success": True,
            "data": breakdown
        }
    except Exception as e:
        logger.error(f"Erro ao obter breakdown de domínios: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter breakdown de domínios")

@router.get("/user/{user_id}")
async def get_user_engagement(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Período em dias"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtém engajamento de usuário específico"""
    try:
        # Verificar permissão (só admin ou próprio usuário)
        if current_user.get("id") != user_id and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        engagement = referral_service.get_user_engagement(user_id, days)
        return {
            "success": True,
            "data": engagement
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter engajamento do usuário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter engajamento do usuário")

@router.get("/summary")
async def get_referral_summary(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtém resumo geral de referrals"""
    try:
        # Analytics de 7 dias
        week_analytics = referral_service.get_referral_analytics(7)
        
        # Analytics de 30 dias
        month_analytics = referral_service.get_referral_analytics(30)
        
        # Breakdown de domínios
        domain_breakdown = referral_service.get_domain_breakdown(30)
        
        # Engajamento do usuário atual
        user_engagement = referral_service.get_user_engagement(current_user.get("id"), 30)
        
        return {
            "success": True,
            "data": {
                "week_summary": {
                    "total_clicks": week_analytics.get("total_clicks", 0),
                    "top_domains": week_analytics.get("domain_stats", [])[:5],
                    "period_days": 7
                },
                "month_summary": {
                    "total_clicks": month_analytics.get("total_clicks", 0),
                    "top_domains": month_analytics.get("domain_stats", [])[:10],
                    "source_breakdown": month_analytics.get("source_stats", []),
                    "period_days": 30
                },
                "domain_categories": domain_breakdown.get("categorized_domains", {}),
                "user_engagement": user_engagement.get("stats", {}),
                "generated_at": month_analytics.get("generated_at")
            }
        }
    except Exception as e:
        logger.error(f"Erro ao obter resumo: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter resumo")

@router.get("/dashboard")
async def get_dashboard_data(
    days: int = Query(30, ge=1, le=365, description="Período em dias"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtém dados completos para dashboard"""
    try:
        # Analytics geral
        analytics = referral_service.get_referral_analytics(days)
        
        # Breakdown por domínio
        domain_breakdown = referral_service.get_domain_breakdown(days)
        
        # Engajamento do usuário
        user_engagement = referral_service.get_user_engagement(current_user.get("id"), days)
        
        # Métricas de percepção
        perception_metrics = _calculate_perception_metrics(analytics, domain_breakdown)
        
        return {
            "success": True,
            "data": {
                "analytics": analytics,
                "domain_breakdown": domain_breakdown,
                "user_engagement": user_engagement,
                "perception_metrics": perception_metrics,
                "period_days": days
            }
        }
    except Exception as e:
        logger.error(f"Erro ao obter dashboard: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter dashboard")

def _calculate_perception_metrics(analytics: Dict[str, Any], domain_breakdown: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula métricas de percepção e reconhecimento"""
    try:
        total_clicks = analytics.get("total_clicks", 0)
        domain_stats = analytics.get("domain_stats", [])
        categorized = domain_breakdown.get("categorized_domains", {})
        
        # Métricas de diversidade
        unique_domains = len(domain_stats)
        domain_diversity = min(100, (unique_domains / max(1, total_clicks)) * 100)
        
        # Score de presença em diferentes categorias
        category_presence = 0
        total_categories = len(categorized)
        
        for category, data in categorized.items():
            if data.get("total_clicks", 0) > 0:
                category_presence += 1
        
        presence_score = (category_presence / max(1, total_categories)) * 100
        
        # Score de engajamento (baseado em fontes variadas)
        source_stats = analytics.get("source_stats", [])
        engagement_diversity = min(100, (len(source_stats) / 5) * 100)  # 5 tipos de fonte ideais
        
        # Score de reconhecimento (peso maior para search engines e dev tools)
        recognition_score = 0
        high_value_categories = ["search_engines", "development", "ai_ml"]
        
        for category in high_value_categories:
            if category in categorized:
                clicks = categorized[category].get("total_clicks", 0)
                recognition_score += min(30, (clicks / max(1, total_clicks)) * 100)
        
        # Score geral de percepção
        perception_score = (
            domain_diversity * 0.3 +
            presence_score * 0.3 +
            engagement_diversity * 0.2 +
            recognition_score * 0.2
        )
        
        return {
            "domain_diversity_score": round(domain_diversity, 2),
            "category_presence_score": round(presence_score, 2),
            "engagement_diversity_score": round(engagement_diversity, 2),
            "recognition_score": round(recognition_score, 2),
            "overall_perception_score": round(perception_score, 2),
            "total_domains_tracked": unique_domains,
            "categories_reached": category_presence,
            "engagement_sources": len(source_stats)
        }
    except Exception as e:
        logger.error(f"Erro ao calcular métricas: {e}")
        return {
            "domain_diversity_score": 0,
            "category_presence_score": 0,
            "engagement_diversity_score": 0,
            "recognition_score": 0,
            "overall_perception_score": 0,
            "error": str(e)
        }

# Exportar router para import
referral_router = router
