"""
Motor Validation Test - B.E.N. 2.0 e TenantManager
Valida que os componentes críticos do sistema estão operacionais
"""

import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
src_dir = Path(__file__).resolve().parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from backend.tenant_manager import tenant_manager, TenantManager
from backend.security_guardrail import SecurityGuardrail


def test_tenant_manager():
    """Testa o TenantManager"""
    print("=== Teste do TenantManager ===\n")
    
    # 1. Instanciação
    print("1. Testando instanciação...")
    tm = TenantManager()
    assert tm is not None, "TenantManager não foi instanciado"
    print("   [OK] TenantManager instanciado com sucesso")
    
    # 2. Singleton global
    print("\n2. Testando singleton global...")
    assert tenant_manager is not None, "Singleton tenant_manager não existe"
    print("   [OK] Singleton global disponível")
    
    # 3. Operações básicas
    print("\n3. Testando operações básicas...")
    tm.set_tenant("test_tenant_123")
    assert tm.get_tenant() == "test_tenant_123", "set_tenant/get_tenant falhou"
    print("   [OK] set_tenant/get_tenant funcionando")
    
    tm.clear_tenant()
    assert tm.get_tenant() is None, "clear_tenant falhou"
    print("   [OK] clear_tenant funcionando")
    
    print("\n=== TenantManager: OPERACIONAL [OK] ===\n")


def test_ben_2():
    """Testa o B.E.N. 2.0 (SecurityGuardrail)"""
    print("=== Teste do B.E.N. 2.0 (SecurityGuardrail) ===\n")
    
    # 1. Instanciação
    print("1. Testando classe SecurityGuardrail...")
    assert SecurityGuardrail is not None, "Classe SecurityGuardrail não existe"
    print("   [OK] Classe SecurityGuardrail disponível")
    
    # 2. Método evaluate
    print("\n2. Testando método evaluate...")
    result = SecurityGuardrail.evaluate("Teste de mensagem normal")
    assert result is not None, "evaluate retornou None"
    assert "action" in result, "evaluate não retornou 'action'"
    print(f"   [OK] evaluate funcionando: action={result['action']}")
    
    # 3. Teste de mensagem vazia
    print("\n3. Testando mensagem vazia...")
    empty_result = SecurityGuardrail.evaluate("")
    assert empty_result["action"] == "block", "Mensagem vazia não foi bloqueada"
    print("   [OK] Mensagem vazia bloqueada corretamente")
    
    # 4. Método validate_code_execution
    print("\n4. Testando validate_code_execution...")
    code_result = SecurityGuardrail.validate_code_execution("print('test')")
    assert code_result is not None, "validate_code_execution retornou None"
    assert "action" in code_result, "validate_code_execution não retornou 'action'"
    print(f"   [OK] validate_code_execution funcionando: action={code_result['action']}")
    
    print("\n=== B.E.N. 2.0: OPERACIONAL [OK] ===\n")


def test_integration():
    """Testa integração entre componentes"""
    print("=== Teste de Integração ===\n")
    
    # 1. TenantManager + SecurityGuardrail
    print("1. Testando TenantManager + SecurityGuardrail...")
    tenant_manager.set_tenant("integration_test")
    result = SecurityGuardrail.evaluate("Mensagem de teste com tenant ativo")
    assert result["action"] == "allow", "Integração falhou"
    print("   [OK] Integração funcionando")
    
    tenant_manager.clear_tenant()
    
    print("\n=== Integração: OPERACIONAL [OK] ===\n")


if __name__ == "__main__":
    print("\n======================================================")
    print("     Motor Validation Test - B.E.N. 2.0 & Tenant")
    print("======================================================\n")
    
    try:
        test_tenant_manager()
        test_ben_2()
        test_integration()
        
        print("\n======================================================")
        print("           TODOS OS TESTES PASSARAM [OK]")
        print("======================================================\n")
        
    except AssertionError as e:
        print(f"\n[ERRO] TESTE FALHOU: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO] ERRO INESPERADO: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
