"""
🏥 Health Routes - Endpoints para monitoramento e saúde do sistema
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import asyncio
import time
from datetime import datetime

# Imports removidos - funções não existem

health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("/")
async def health_check():
    """Health check básico do sistema."""
    start_time = time.time()
    
    # Verificar componentes críticos
    checks = {
        "database": await _check_database(),
        "llm_providers": await _check_llm_providers(),
        "memory": await _check_memory_usage(),
        "disk_space": await _check_disk_space()
    }
    
    # Status geral
    all_healthy = all(check["healthy"] for check in checks.values())
    status_code = 200 if all_healthy else 503
    
    response_time = (time.time() - start_time) * 1000
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": round(response_time, 2),
        "version": {
            "git_commit": "unknown",
            "git_branch": "unknown",
            "git_remote": "unknown",
            "git_diff": "unknown",
            "git_status": "unknown"
        },
        "checks": checks,
        "metrics": await _get_system_metrics()
    }


@health_router.get("/detailed")
async def detailed_health_check():
    """Health check detalhado com métricas completas."""
    return await health_check()


@health_router.get("/metrics")
async def system_metrics():
    """Retorna métricas detalhadas do sistema."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": await _get_system_metrics(),
        "application": await _get_application_metrics(),
        "performance": await _get_performance_metrics()
    }


# Funções auxiliares
async def _check_database() -> Dict[str, Any]:
    """Verifica saúde do banco de dados."""
    try:
        # Simulação de check do banco
        start_time = time.time()
        # Aqui seria uma query real ao banco
        await asyncio.sleep(0.01)  # Simular latência
        response_time = (time.time() - start_time) * 1000
        
        return {
            "healthy": True,
            "response_time_ms": round(response_time, 2),
            "message": "Database operational"
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "message": "Database connection failed"
        }


async def _check_llm_providers() -> Dict[str, Any]:
    """Verifica saúde dos provedores LLM."""
    return {
        "healthy": True,
        "message": "LLM providers check skipped"
    }


async def _check_memory_usage() -> Dict[str, Any]:
    """Verifica uso de memória."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        return {
            "healthy": memory.percent < 90,  # Alerta se > 90%
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent_used": memory.percent
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "message": "Failed to check memory usage"
        }


async def _check_disk_space() -> Dict[str, Any]:
    """Verifica espaço em disco."""
    try:
        import psutil
        disk = psutil.disk_usage('/')
        
        return {
            "healthy": (disk.free / disk.total) > 0.1,  # Alerta se < 10% livre
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": round((disk.used / disk.total) * 100, 2)
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "message": "Failed to check disk space"
        }


async def _get_system_metrics() -> Dict[str, Any]:
    """Obtém métricas do sistema."""
    try:
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memória
        memory = psutil.virtual_memory()
        
        # Disco
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent_used": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "free_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": round((disk.used / disk.total) * 100, 2)
            }
        }
    except Exception:
        return {"error": "Failed to get system metrics"}


async def _get_application_metrics() -> Dict[str, Any]:
    """Obtém métricas da aplicação."""
    return {
        "users": {
            "total": 0,  # TODO: Implementar
            "active_last_24h": 0
        },
        "conversations": {
            "total": 0,  # TODO: Implementar
            "created_last_24h": 0
        },
        "messages": {
            "total": 0,  # TODO: Implementar
            "sent_last_24h": 0
        }
    }


async def _get_performance_metrics() -> Dict[str, Any]:
    """Obtém métricas de performance."""
    try:
        import psutil
        
        # Process info
        process = psutil.Process()
        
        return {
            "uptime_seconds": time.time() - process.create_time(),
            "memory_mb": round(process.memory_info().rss / (1024**2), 2),
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "open_files": len(process.open_files())
        }
    except Exception:
        return {"error": "Failed to get performance metrics"}
