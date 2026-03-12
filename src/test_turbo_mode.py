"""
🚀 TURBO MODE TEST - CASCADE AI VALIDATION
Teste completo do modo turbo com Cascade AI
Validação de funcionalidades, performance e integração
"""

import asyncio
import json
import time
from datetime import datetime

# Importar componentes turbo
from src.core.cascade_client import CascadeClient
from src.core.moe_router_turbo import TurboMoERouter, turbo_moe_router
from src.core.mcp_server_turbo import TurboMCPServer, turbo_mcp_server

class TurboModeTester:
    """Testador do modo turbo"""
    
    def __init__(self):
        self.cascade_client = CascadeClient()
        self.moe_router = TurboMoERouter()
        self.test_results = []
        
    async def run_all_tests(self):
        """Executar todos os testes turbo"""
        print("🚀 INICIANDO TESTES DO MODO TURBO")
        print("=" * 60)
        
        # Teste 1: Inicialização
        await self.test_initialization()
        
        # Teste 2: Geração de Código
        await self.test_code_generation()
        
        # Teste 3: Análise de Arquitetura
        await self.test_architecture_analysis()
        
        # Teste 4: Auditoria de Segurança
        await self.test_security_audit()
        
        # Teste 5: Otimização de Performance
        await self.test_performance_optimization()
        
        # Teste 6: Roteamento de Tarefas
        await self.test_task_routing()
        
        # Teste 7: Performance do Sistema
        await self.test_system_performance()
        
        # Teste 8: Cache e Memória
        await self.test_caching()
        
        # Relatório final
        self.generate_final_report()
    
    async def test_initialization(self):
        """Teste 1: Inicialização do modo turbo"""
        print("\n📋 TESTE 1: INICIALIZAÇÃO")
        print("-" * 40)
        
        try:
            start_time = time.time()
            
            # Inicializar Cascade Client
            await self.cascade_client.initialize()
            
            # Inicializar MoE Router
            await self.moe_router.initialize()
            
            end_time = time.time()
            init_time = end_time - start_time
            
            print(f"✅ Cascade Client: Inicializado")
            print(f"✅ MoE Router: Inicializado")
            print(f"⚡ Tempo de inicialização: {init_time:.3f}s")
            print(f"🎯 Modo turbo: Ativado")
            
            self.test_results.append({
                "test": "initialization",
                "status": "PASS",
                "time": init_time,
                "details": "Todos os componentes inicializados com sucesso"
            })
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            self.test_results.append({
                "test": "initialization",
                "status": "FAIL",
                "error": str(e)
            })
    
    async def test_code_generation(self):
        """Teste 2: Geração de código turbo"""
        print("\n💻 TESTE 2: GERAÇÃO DE CÓDIGO")
        print("-" * 40)
        
        test_cases = [
            {
                "name": "Python API",
                "prompt": "Create FastAPI with JWT authentication",
                "language": "python"
            },
            {
                "name": "React Component",
                "prompt": "Create React component with TypeScript",
                "language": "typescript"
            },
            {
                "name": "Database Query",
                "prompt": "Optimize SQL query for performance",
                "language": "sql"
            }
        ]
        
        for case in test_cases:
            try:
                start_time = time.time()
                
                result = await self.cascade_client.generate_code(
                    case["prompt"],
                    case["language"]
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                print(f"✅ {case['name']}: {result.confidence:.2f} confiança")
                print(f"   ⚡ Tempo: {processing_time:.3f}s")
                print(f"   📏 Linhas: {len(result.content.split())}")
                
                self.test_results.append({
                    "test": f"code_generation_{case['name']}",
                    "status": "PASS",
                    "confidence": result.confidence,
                    "time": processing_time,
                    "lines": len(result.content.split())
                })
                
            except Exception as e:
                print(f"❌ {case['name']}: {e}")
                self.test_results.append({
                    "test": f"code_generation_{case['name']}",
                    "status": "FAIL",
                    "error": str(e)
                })
    
    async def test_architecture_analysis(self):
        """Teste 3: Análise de arquitetura"""
        print("\n🏗️ TESTE 3: ANÁLISE DE ARQUITETURA")
        print("-" * 40)
        
        test_cases = [
            {
                "name": "Microservices",
                "description": "Design microservices for e-commerce platform",
                "requirements": ["scalability", "docker", "kubernetes"]
            },
            {
                "name": "Monolith",
                "description": "Design monolithic application for startup",
                "requirements": ["simplicity", "fast_development"]
            }
        ]
        
        for case in test_cases:
            try:
                start_time = time.time()
                
                result = await self.cascade_client.analyze_architecture(
                    case["description"],
                    case["requirements"]
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                print(f"✅ {case['name']}: {result.confidence:.2f} confiança")
                print(f"   ⚡ Tempo: {processing_time:.3f}s")
                print(f"   🏗️ Componentes: {len(result.content.get('components', []))}")
                
                self.test_results.append({
                    "test": f"architecture_{case['name']}",
                    "status": "PASS",
                    "confidence": result.confidence,
                    "time": processing_time,
                    "components": len(result.content.get('components', []))
                })
                
            except Exception as e:
                print(f"❌ {case['name']}: {e}")
                self.test_results.append({
                    "test": f"architecture_{case['name']}",
                    "status": "FAIL",
                    "error": str(e)
                })
    
    async def test_security_audit(self):
        """Teste 4: Auditoria de segurança"""
        print("\n🔒 TESTE 4: AUDITORIA DE SEGURANÇA")
        print("-" * 40)
        
        test_code = '''
def login(username, password):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    return execute_query(query)
'''
        
        try:
            start_time = time.time()
            
            result = await self.cascade_client.audit_security(test_code)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            vulnerabilities = result.content.get('vulnerabilities', [])
            
            print(f"✅ Auditoria: {result.confidence:.2f} confiança")
            print(f"   ⚡ Tempo: {processing_time:.3f}s")
            print(f"   🔍 Vulnerabilidades: {len(vulnerabilities)}")
            
            for vuln in vulnerabilities[:3]:  # Mostrar primeiras 3
                print(f"   - {vuln.get('type', 'Unknown')}: {vuln.get('severity', 'Unknown')}")
            
            self.test_results.append({
                "test": "security_audit",
                "status": "PASS",
                "confidence": result.confidence,
                "time": processing_time,
                "vulnerabilities": len(vulnerabilities)
            })
            
        except Exception as e:
            print(f"❌ Auditoria: {e}")
            self.test_results.append({
                "test": "security_audit",
                "status": "FAIL",
                "error": str(e)
            })
    
    async def test_performance_optimization(self):
        """Teste 5: Otimização de performance"""
        print("\n⚡ TESTE 5: OTIMIZAÇÃO DE PERFORMANCE")
        print("-" * 40)
        
        test_code = '''
def process_data(data):
    result = []
    for item in data:
        for i in range(1000):
            result.append(item * i)
    return result
'''
        
        try:
            start_time = time.time()
            
            result = await self.cascade_client.optimize_performance(test_code)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            optimizations = result.content.get('optimizations', [])
            
            print(f"✅ Otimização: {result.confidence:.2f} confiança")
            print(f"   ⚡ Tempo: {processing_time:.3f}s")
            print(f"   🚀 Otimizações: {len(optimizations)}")
            
            for opt in optimizations[:2]:  # Mostrar primeiras 2
                print(f"   - {opt.get('type', 'Unknown')}: {opt.get('description', 'No description')}")
            
            self.test_results.append({
                "test": "performance_optimization",
                "status": "PASS",
                "confidence": result.confidence,
                "time": processing_time,
                "optimizations": len(optimizations)
            })
            
        except Exception as e:
            print(f"❌ Otimização: {e}")
            self.test_results.append({
                "test": "performance_optimization",
                "status": "FAIL",
                "error": str(e)
            })
    
    async def test_task_routing(self):
        """Teste 6: Roteamento de tarefas"""
        print("\n🎯 TESTE 6: ROTEAMENTO DE TAREFAS")
        print("-" * 40)
        
        from src.core.moe_router import Task, TaskType
        
        test_tasks = [
            Task(
                id="test_1",
                type=TaskType.CODING,
                description="Create REST API with authentication",
                requirements=["python", "fastapi", "jwt"],
                priority=8,
                estimated_duration=10
            ),
            Task(
                id="test_2",
                type=TaskType.DESIGN,
                description="Design scalable microservices architecture",
                requirements=["kubernetes", "docker", "redis"],
                priority=7,
                estimated_duration=15
            )
        ]
        
        for task in test_tasks:
            try:
                start_time = time.time()
                
                result = await self.moe_router.route_task(task)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                print(f"✅ Tarefa {task.id}: {result.confidence_score:.2f} confiança")
                print(f"   ⚡ Tempo: {processing_time:.3f}s")
                print(f"   🤖 Especialista: {result.expert_contributions[0][0]}")
                print(f"   📊 Método: {result.aggregation_method}")
                
                self.test_results.append({
                    "test": f"task_routing_{task.id}",
                    "status": "PASS",
                    "confidence": result.confidence_score,
                    "time": processing_time,
                    "expert": result.expert_contributions[0][0]
                })
                
            except Exception as e:
                print(f"❌ Tarefa {task.id}: {e}")
                self.test_results.append({
                    "test": f"task_routing_{task.id}",
                    "status": "FAIL",
                    "error": str(e)
                })
    
    async def test_system_performance(self):
        """Teste 7: Performance do sistema"""
        print("\n📊 TESTE 7: PERFORMANCE DO SISTEMA")
        print("-" * 40)
        
        # Teste de carga
        concurrent_tasks = 10
        start_time = time.time()
        
        tasks = []
        for i in range(concurrent_tasks):
            task = asyncio.create_task(
                self.cascade_client.generate_code(
                    f"Generate function {i}",
                    "python"
                )
            )
            tasks.append(task)
        
        # Executar todas em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Contar sucessos
        successes = sum(1 for r in results if not isinstance(r, Exception))
        failures = sum(1 for r in results if isinstance(r, Exception))
        
        print(f"✅ Teste de carga: {concurrent_tasks} tarefas")
        print(f"   ⚡ Tempo total: {total_time:.3f}s")
        print(f"   📈 Sucessos: {successes}/{concurrent_tasks}")
        print(f"   ❌ Falhas: {failures}/{concurrent_tasks}")
        print(f"   🚀 Throughput: {successes/total_time:.1f} tarefas/s")
        
        self.test_results.append({
            "test": "system_performance",
            "status": "PASS" if successes == concurrent_tasks else "FAIL",
            "total_time": total_time,
            "successes": successes,
            "failures": failures,
            "throughput": successes/total_time
        })
    
    async def test_caching(self):
        """Teste 8: Cache e memória"""
        print("\n💾 TESTE 8: CACHE E MEMÓRIA")
        print("-" * 40)
        
        # Primeira chamada (sem cache)
        start_time = time.time()
        result1 = await self.cascade_client.generate_code("Create hello world function", "python")
        first_time = time.time() - start_time
        
        # Segunda chamada (com cache)
        start_time = time.time()
        result2 = await self.cascade_client.generate_code("Create hello world function", "python")
        second_time = time.time() - start_time
        
        # Verificar se cache funcionou
        cache_improvement = ((first_time - second_time) / first_time) * 100 if first_time > 0 else 0
        
        print(f"✅ Teste de cache:")
        print(f"   🕐 Primeira chamada: {first_time:.3f}s")
        print(f"   🚀 Segunda chamada: {second_time:.3f}s")
        print(f"   💾 Melhoria: {cache_improvement:.1f}%")
        
        self.test_results.append({
            "test": "caching",
            "status": "PASS" if cache_improvement > 0 else "FAIL",
            "first_time": first_time,
            "second_time": second_time,
            "improvement": cache_improvement
        })
    
    def generate_final_report(self):
        """Gerar relatório final dos testes"""
        print("\n" + "=" * 60)
        print("📋 RELATÓRIO FINAL - MODO TURBO")
        print("=" * 60)
        
        # Estatísticas gerais
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t.get("status") == "PASS")
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total de testes: {total_tests}")
        print(f"✅ Testes passados: {passed_tests}")
        print(f"❌ Testes falhados: {failed_tests}")
        print(f"📈 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        # Performance média
        times = [t.get("time", 0) for t in self.test_results if "time" in t]
        if times:
            avg_time = sum(times) / len(times)
            print(f"⚡ Tempo médio: {avg_time:.3f}s")
        
        # Confiança média
        confidences = [t.get("confidence", 0) for t in self.test_results if "confidence" in t]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            print(f"🎯 Confiança média: {avg_confidence:.2f}")
        
        # Detalhes dos testes
        print("\n📋 DETALHES DOS TESTES:")
        print("-" * 40)
        
        for result in self.test_results:
            status_icon = "✅" if result.get("status") == "PASS" else "❌"
            print(f"{status_icon} {result.get('test', 'Unknown')}")
            
            if result.get("status") == "PASS":
                if "time" in result:
                    print(f"   ⚡ Tempo: {result['time']:.3f}s")
                if "confidence" in result:
                    print(f"   🎯 Confiança: {result['confidence']:.2f}")
            else:
                if "error" in result:
                    print(f"   ❌ Erro: {result['error']}")
        
        # Conclusão
        print("\n" + "=" * 60)
        if passed_tests == total_tests:
            print("🎉 MODO TURBO 100% FUNCIONAL!")
            print("⚡ Cascade AI está pronto para produção")
            print("🚀 Sistema operando em velocidade máxima")
        else:
            print("⚠️ MODO TURBO COM PROBLEMAS")
            print("🔧 Alguns ajustes podem ser necessários")
        
        print("=" * 60)
        
        # Salvar relatório
        self.save_report()
    
    def save_report(self):
        """Salvar relatório em arquivo"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "mode": "turbo",
            "powered_by": "Cascade AI",
            "test_results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for t in self.test_results if t.get("status") == "PASS"),
                "failed_tests": sum(1 for t in self.test_results if t.get("status") == "FAIL")
            }
        }
        
        with open("turbo_mode_test_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Relatório salvo em: turbo_mode_test_report.json")

async def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DO MODO TURBO - CASCADE AI")
    print("⚡ Zero configuração, velocidade máxima, poder total")
    print()
    
    tester = TurboModeTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
