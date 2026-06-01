from backend.utils.vault import SecureVault
from backend.llm.providers import ProviderConfig
from backend.llm.universal_client import UniversalLLMClient
import asyncio

async def configure_gemini():
    # 1. Armazena a chave no cofre do sistema
    # Substitua 'SUA_CHAVE_GEMINI_AQUI' pela sua chave real do Google AI Studio
    api_key = "AIzaSyAuAYUBlQJmJD42W8pcsf0OcgIr1FT3C5Q"
    SecureVault.store_secret("GEMINI_API_KEY", api_key)
    print("Chave Gemini salva no cofre com sucesso.")

    # 2. Testa a conexão (sem retentativas automáticas)
    provider = ProviderConfig(
        provider_id="gemini",
        model="gemini-2.5-flash", # Modelo rápido e ideal para o nosso motor
        base_url="https://generativelanguage.googleapis.com/v1beta"
    )
    
    client = UniversalLLMClient(provider)
    print("Testando conexão...")
    if await client.test_connection():
        print("✅ Conexão com Gemini estabelecida com sucesso!")
    else:
        print("❌ Falha na conexão. Verifique sua chave.")

if __name__ == "__main__":
    asyncio.run(configure_gemini())
