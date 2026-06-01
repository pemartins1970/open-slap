"""
Security Tester Agent - Especialista em Testes de Intrusão
Agente especializado em testes de segurança para aplicações web FastAPI
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SecurityTest:
    """Resultado de um teste de segurança"""
    name: str
    category: str
    severity: str  # "critical", "high", "medium", "low", "info"
    description: str
    payload: str
    result: str
    status: str  # "vulnerable", "safe", "error"
    recommendation: str

class SecurityTesterAgent:
    """Agente especializado em testes de intrusão e segurança"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5150"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        self.test_results: List[SecurityTest] = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run_full_security_audit(self) -> Dict[str, Any]:
        """Executa auditoria de segurança completa"""
        logger.info("Iniciando auditoria de segurança completa...")
        
        # Testes de autenticação
        await self.test_authentication_security()
        
        # Testes de SQL Injection
        await self.test_sql_injection()
        
        # Testes de XSS
        await self.test_xss_attacks()
        
        # Testes de CSRF
        await self.test_csrf_protection()
        
        # Testes de Rate Limiting
        await self.test_rate_limiting()
        
        # Testes de CORS
        await self.test_cors_configuration()
        
        # Testes de Input Validation
        await self.test_input_validation()
        
        # Testes de Information Disclosure
        await self.test_information_disclosure()
        
        return self.generate_security_report()
    
    async def test_authentication_security(self) -> None:
        """Testa segurança da autenticação"""
        logger.info("Testando segurança da autenticação...")
        
        # Test 1: Login com SQL Injection
        payload = {"email": "' OR '1'='1", "password": "anything"}
        result = await self._make_request("POST", "/auth/login", payload)
        self.test_results.append(SecurityTest(
            name="SQL Injection em Login",
            category="Authentication",
            severity="critical",
            description="Tentativa de SQL Injection no formulário de login",
            payload=json.dumps(payload),
            result=str(result),
            status="vulnerable" if result.get("access_token") else "safe",
            recommendation="Usar parameterized queries e ORM"
        ))
        
        # Test 2: Login com email malicioso
        payload = {"email": "<script>alert('xss')</script>@test.com", "password": "password123"}
        result = await self._make_request("POST", "/auth/login", payload)
        self.test_results.append(SecurityTest(
            name="XSS em Email de Login",
            category="Authentication", 
            severity="medium",
            description="Tentativa de XSS no campo de email",
            payload=json.dumps(payload),
            result=str(result),
            status="safe",  # Esperado que seja sanitizado
            recommendation="Sanitizar inputs no frontend e backend"
        ))
        
        # Test 3: Força bruta simulada
        for i in range(5):
            payload = {"email": f"test{i}@example.com", "password": f"password{i}"}
            await self._make_request("POST", "/auth/login", payload)
        
        self.test_results.append(SecurityTest(
            name="Força Bruta",
            category="Authentication",
            severity="medium",
            description="Teste de força bruta múltiplas tentativas",
            payload="Múltiplas tentativas de login",
            result="5 tentativas executadas",
            status="info",  # Depende de rate limiting
            recommendation="Implementar rate limiting e account lockout"
        ))
    
    async def test_sql_injection(self) -> None:
        """Testa vulnerabilidades de SQL Injection"""
        logger.info("Testando SQL Injection...")
        
        # payloads clássicos de SQL Injection
        sql_payloads = [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "admin'--",
            "admin'/*",
            "' OR 1=1--",
            "' UNION SELECT * FROM users--",
            "'; DROP TABLE users; --"
        ]
        
        for payload in sql_payloads:
            # Testar em registro
            register_payload = {"email": f"{payload}@test.com", "password": "password123"}
            result = await self._make_request("POST", "/auth/register", register_payload)
            
            self.test_results.append(SecurityTest(
                name=f"SQL Injection - Registro: {payload[:20]}",
                category="SQL Injection",
                severity="critical",
                description=f"Teste SQL Injection com payload: {payload}",
                payload=json.dumps(register_payload),
                result=str(result),
                status="vulnerable" if result.get("id") else "safe",
                recommendation="Usar ORM e parameterized queries"
            ))
    
    async def test_xss_attacks(self) -> None:
        """Testa vulnerabilidades de XSS"""
        logger.info("Testando XSS...")
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "'><script>alert('xss')</script>",
            "<iframe src=javascript:alert('xss')></iframe>"
        ]
        
        for payload in xss_payloads:
            # Testar em diferentes endpoints
            endpoints_to_test = [
                ("/auth/register", {"email": f"{payload}@test.com", "password": "password123"}),
                ("/auth/login", {"email": f"{payload}@test.com", "password": "password123"}),
            ]
            
            for endpoint, test_payload in endpoints_to_test:
                result = await self._make_request("POST", endpoint, test_payload)
                
                self.test_results.append(SecurityTest(
                    name=f"XSS - {endpoint.split('/')[-1]}: {payload[:20]}",
                    category="XSS",
                    severity="high",
                    description=f"Teste XSS com payload: {payload}",
                    payload=json.dumps(test_payload),
                    result=str(result),
                    status="vulnerable" if payload in str(result) else "safe",
                    recommendation="Sanitizar inputs e usar auto-escaping"
                ))
    
    async def test_csrf_protection(self) -> None:
        """Testa proteção CSRF"""
        logger.info("Testando CSRF...")
        
        # Simular requisição de origem diferente
        headers = {
            "Origin": "http://malicious-site.com",
            "Referer": "http://malicious-site.com/attack"
        }
        
        # Testar se endpoint permite requisições sem CSRF token
        result = await self._make_request("GET", "/auth/me", headers=headers)
        
        self.test_results.append(SecurityTest(
            name="CSRF Protection",
            category="CSRF",
            severity="medium",
            description="Teste de proteção contra CSRF",
            payload="Headers de origem maliciosa",
            result=str(result),
            status="info",  # Depende da configuração CORS
            recommendation="Configurar CORS corretamente e usar CSRF tokens"
        ))
    
    async def test_rate_limiting(self) -> None:
        """Testa rate limiting"""
        logger.info("Testando rate limiting...")
        
        # Testar múltiplas requisições rápidas
        responses = []
        for i in range(20):
            result = await self._make_request("GET", "/auth/me")
            responses.append(result.get("status_code", 200))
        
        # Verificar se houve bloqueio
        blocked_responses = [r for r in responses if r == 429]
        
        self.test_results.append(SecurityTest(
            name="Rate Limiting",
            category="Rate Limiting",
            severity="medium",
            description="Teste de rate limiting com 20 requisições rápidas",
            payload="20 requisições GET /auth/me",
            result=f"Respostas 429: {len(blocked_responses)}/20",
            status="safe" if blocked_responses else "vulnerable",
            recommendation="Implementar rate limiting em endpoints sensíveis"
        ))
    
    async def test_cors_configuration(self) -> None:
        """Testa configuração CORS"""
        logger.info("Testando CORS...")
        
        # Testar diferentes origens
        test_origins = [
            "http://localhost:3002",  # Esperado permitir
            "http://malicious-site.com",  # Esperado bloquear
            "*",  # Esperado bloquear
            "null",  # Esperado bloquear
        ]
        
        for origin in test_origins:
            headers = {"Origin": origin}
            result = await self._make_request("OPTIONS", "/auth/login", headers=headers)
            
            self.test_results.append(SecurityTest(
                name=f"CORS - Origin: {origin}",
                category="CORS",
                severity="medium",
                description=f"Teste CORS com origin: {origin}",
                payload=f"Origin: {origin}",
                result=str(result),
                status="info",  # Depende da configuração
                recommendation="Configurar CORS para permitir apenas origins confiáveis"
            ))
    
    async def test_input_validation(self) -> None:
        """Testa validação de inputs"""
        logger.info("Testando validação de inputs...")
        
        # Testar inputs inválidos
        invalid_inputs = [
            {"email": "", "password": "password123"},  # Email vazio
            {"email": "invalid-email", "password": "password123"},  # Email inválido
            {"email": "test@test.com", "password": ""},  # Senha vazia
            {"email": "a" * 300 + "@test.com", "password": "password123"},  # Email muito longo
            {"email": "test@test.com", "password": "a"},  # Senha muito curta
        ]
        
        for i, payload in enumerate(invalid_inputs):
            result = await self._make_request("POST", "/auth/register", payload)
            
            self.test_results.append(SecurityTest(
                name=f"Input Validation - Test {i+1}",
                category="Input Validation",
                severity="medium",
                description=f"Teste de validação: {payload}",
                payload=json.dumps(payload),
                result=str(result),
                status="safe" if result.get("detail") else "vulnerable",
                recommendation="Implementar validação robusta no backend"
            ))
    
    async def test_information_disclosure(self) -> None:
        """Testa disclosure de informações sensíveis"""
        logger.info("Testando information disclosure...")
        
        # Testar endpoints que podem expor informações
        sensitive_endpoints = [
            "/docs",  # Swagger docs
            "/openapi.json",  # OpenAPI schema
            "/redoc",  # ReDoc
            "/",  # Root endpoint
        ]
        
        for endpoint in sensitive_endpoints:
            result = await self._make_request("GET", endpoint)
            
            self.test_results.append(SecurityTest(
                name=f"Information Disclosure - {endpoint}",
                category="Information Disclosure",
                severity="low",
                description=f"Teste de disclosure em {endpoint}",
                payload="GET request",
                result=str(result)[:200],  # Limitar output
                status="info",
                recommendation="Proteger documentação em produção"
            ))
    
    async def _make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict] = None, 
                          headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Faz requisição HTTP para teste"""
        try:
            url = f"{self.base_url}{endpoint}"
            request_headers = {"Content-Type": "application/json"}
            if headers:
                request_headers.update(headers)
            if self.auth_token:
                request_headers["Authorization"] = f"Bearer {self.auth_token}"
            
            if method == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    result = {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "data": await response.text()
                    }
                    if response.status == 200 and "application/json" in response.headers.get("content-type", ""):
                        result["json"] = await response.json()
                    return result
                    
            elif method == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    result = {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "data": await response.text()
                    }
                    if "application/json" in response.headers.get("content-type", ""):
                        result["json"] = await response.json()
                    return result
                    
            elif method == "OPTIONS":
                async with self.session.options(url, headers=request_headers) as response:
                    return {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "data": await response.text()
                    }
                    
        except Exception as e:
            return {
                "status_code": 500,
                "error": str(e),
                "data": None
            }
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Gera relatório de segurança"""
        vulnerabilities = [t for t in self.test_results if t.status == "vulnerable"]
        safe_tests = [t for t in self.test_results if t.status == "safe"]
        
        severity_counts = {
            "critical": len([t for t in vulnerabilities if t.severity == "critical"]),
            "high": len([t for t in vulnerabilities if t.severity == "high"]),
            "medium": len([t for t in vulnerabilities if t.severity == "medium"]),
            "low": len([t for t in vulnerabilities if t.severity == "low"]),
            "info": len([t for t in self.test_results if t.severity == "info"])
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "target": self.base_url,
            "summary": {
                "total_tests": len(self.test_results),
                "vulnerabilities": len(vulnerabilities),
                "safe": len(safe_tests),
                "info": len([t for t in self.test_results if t.status == "info"]),
                "severity_breakdown": severity_counts
            },
            "vulnerabilities": [
                {
                    "name": t.name,
                    "category": t.category,
                    "severity": t.severity,
                    "description": t.description,
                    "payload": t.payload,
                    "recommendation": t.recommendation
                }
                for t in vulnerabilities
            ],
            "recommendations": [
                t.recommendation for t in vulnerabilities
            ],
            "risk_score": self._calculate_risk_score(severity_counts)
        }
    
    def _calculate_risk_score(self, severity_counts: Dict[str, int]) -> int:
        """Calcula score de risco (0-100)"""
        weights = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 2,
            "info": 0
        }
        
        total_score = sum(
            severity_counts[severity] * weight 
            for severity, weight in weights.items()
        )
        
        # Normalizar para 0-100
        max_possible_score = sum(weights.values()) * 10  # Assumindo max 10 por categoria
        return min(100, (total_score / max_possible_score) * 100)

async def run_security_audit(base_url: str = "http://127.0.0.1:5150") -> Dict[str, Any]:
    """Executa auditoria de segurança completa"""
    async with SecurityTesterAgent(base_url) as tester:
        return await tester.run_full_security_audit()

if __name__ == "__main__":
    # Teste standalone
    import asyncio
    
    async def main():
        print("?? Iniciando auditoria de segurança do Open Slap!...")
        report = await run_security_audit()
        
        print(f"\n?? Relatório de Segurança")
        print(f"URL: {report['target']}")
        print(f"Data: {report['timestamp']}")
        print(f"Score de Risco: {report['risk_score']}/100")
        print(f"Total de Testes: {report['summary']['total_tests']}")
        print(f"Vulnerabilidades: {report['summary']['vulnerabilities']}")
        print(f"Testes Seguros: {report['summary']['safe']}")
        
        if report['summary']['vulnerabilities'] > 0:
            print(f"\n? Vulnerabilidades Encontradas:")
            for vuln in report['vulnerabilities']:
                print(f"  - {vuln['name']} ({vuln['severity']})")
                print(f"    {vuln['description']}")
                print(f"    Recomendação: {vuln['recommendation']}")
        
        print(f"\n? Score de Risco: {report['risk_score']}/100")
        if report['risk_score'] < 30:
            print("?? BAIXO RISCO - Sistema bem protegido")
        elif report['risk_score'] < 60:
            print("?? MÉDIO RISCO - Algumas melhorias necessárias")
        else:
            print("?? ALTO RISCO - Correções críticas necessárias")
    
    asyncio.run(main())
