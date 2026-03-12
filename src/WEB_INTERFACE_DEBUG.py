"""
🌐 WEB INTERFACE DEBUG - VERSÃO DEBUG COM LOGS DETALHADOS
Servidor web com debugging extensivo para identificar problemas
"""

import asyncio
import json
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import traceback
import sys

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_server_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Importar componentes
try:
    from TURBO_STANDALONE import StandaloneCascadeClient, standalone_cascade_client
    logger.info("✅ TURBO_STANDALONE importado com sucesso")
except ImportError as e:
    logger.error(f"❌ Erro ao importar TURBO_STANDALONE: {e}")
    standalone_cascade_client = None

class DebugTurboWebHandler(BaseHTTPRequestHandler):
    """Handler HTTP com debugging extensivo"""
    
    def __init__(self, *args, turbo_server=None, **kwargs):
        self.turbo_server = turbo_server
        logger.info(f"🔧 Handler inicializado - Server: {turbo_server is not None}")
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Sobrescrever para usar nosso logging"""
        logger.info(f"HTTP: {format % args}")
    
    def do_GET(self):
        """Handle GET requests com debug"""
        logger.info(f"📥 GET request: {self.path}")
        
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            logger.info(f"📍 Path parsed: {path}")
            
            if path == "/":
                logger.info("🏠 Servindo página principal")
                self._serve_html()
            elif path == "/api/status":
                logger.info("📊 Servindo status")
                self._serve_status()
            elif path == "/api/turbo/info":
                logger.info("ℹ️ Servindo turbo info")
                self._serve_turbo_info()
            elif path == "/debug":
                logger.info("🐛 Servindo página de debug")
                self._serve_debug_page()
            else:
                logger.warning(f"⚠️ Path não encontrado: {path}")
                self._serve_404()
                
        except Exception as e:
            logger.error(f"❌ Erro em do_GET: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self._serve_error(f"GET Error: {str(e)}", 500)
    
    def do_POST(self):
        """Handle POST requests com debug extensivo"""
        logger.info(f"📤 POST request: {self.path}")
        logger.info(f"📋 Headers: {dict(self.headers)}")
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            logger.info(f"📏 Content-Length: {content_length}")
            
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                logger.info(f"📦 Raw data length: {len(post_data)}")
                
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    logger.info(f"📋 JSON data: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {e}")
                    logger.error(f"❌ Raw data: {post_data}")
                    self._serve_error(f"JSON decode error: {str(e)}", 400)
                    return
            else:
                logger.warning("⚠️ POST sem dados")
                data = {}
            
            path = urlparse(self.path).path
            logger.info(f"📍 POST path: {path}")
            
            # Processar diferentes endpoints
            if path == "/api/turbo/code":
                logger.info("💻 Processando geração de código")
                self._handle_turbo_code(data)
            elif path == "/api/turbo/design":
                logger.info("🏗️ Processando análise de arquitetura")
                self._handle_turbo_design(data)
            elif path == "/api/turbo/security":
                logger.info("🔒 Processando auditoria de segurança")
                self._handle_turbo_security(data)
            elif path == "/api/turbo/analyze":
                logger.info("⚡ Processando análise de performance")
                self._handle_turbo_analyze(data)
            else:
                logger.warning(f"⚠️ Endpoint POST não encontrado: {path}")
                self._serve_error(f"Unknown endpoint: {path}", 404)
                
        except Exception as e:
            logger.error(f"❌ Erro em do_POST: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self._serve_error(f"POST Error: {str(e)}", 500)
    
    def _serve_html(self):
        """Servir HTML com debug"""
        logger.info("🏠 Construindo página HTML")
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>🚀 Cascade AI Turbo - Debug Mode</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #667eea; text-align: center; }
        .debug-info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { background: #667eea; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; }
        button:hover { background: #5a67d8; }
        .result { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #667eea; }
        .result pre { white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
        .error { color: #721c24; background: #f8d7da; border-left-color: #f5c6cb; }
        .loading { text-align: center; margin: 20px 0; }
        .hidden { display: none; }
        .debug-panel { background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; font-family: monospace; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Cascade AI Turbo - Debug Mode</h1>
        
        <div class="debug-info">
            <strong>🐛 Debug Mode Ativo</strong><br>
            Logs detalhados no console e arquivo web_server_debug.log
        </div>
        
        <div class="debug-panel" id="debug-info">
            Aguardando primeira requisição...
        </div>
        
        <div class="form-group">
            <label for="prompt">Prompt:</label>
            <input type="text" id="prompt" placeholder="Create REST API with authentication" value="Create hello world function">
        </div>
        
        <div class="form-group">
            <label for="language">Linguagem:</label>
            <select id="language">
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
            </select>
        </div>
        
        <button onclick="generateCode()">🚀 Gerar Código</button>
        
        <div class="loading hidden" id="loading">
            <p>🔄 Gerando código...</p>
        </div>
        
        <div class="result hidden" id="result"></div>
    </div>
    
    <script>
        function updateDebugInfo(message) {
            const debugDiv = document.getElementById('debug-info');
            const timestamp = new Date().toLocaleTimeString();
            debugDiv.innerHTML = `[${timestamp}] ${message}`;
        }
        
        async function generateCode() {
            const prompt = document.getElementById('prompt').value;
            const language = document.getElementById('language').value;
            
            updateDebugInfo(`Iniciando requisição - Prompt: "${prompt}"`);
            
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('result').classList.add('hidden');
            
            try {
                updateDebugInfo('Enviando requisição POST para /api/turbo/code');
                
                const response = await fetch('/api/turbo/code', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ prompt, language })
                });
                
                updateDebugInfo(`Response status: ${response.status} ${response.statusText}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                updateDebugInfo(`Response recebido: ${JSON.stringify(data).substring(0, 200)}...`);
                
                if (data.result) {
                    document.getElementById('result').innerHTML = `
                        <strong>✅ Código Gerado (Confiança: ${(data.result.confidence * 100).toFixed(1)}%)</strong>
                        <pre>${data.result.code}</pre>
                    `;
                    document.getElementById('result').classList.remove('error');
                    updateDebugInfo('✅ Sucesso! Código gerado e exibido');
                } else {
                    document.getElementById('result').innerHTML = `<strong>❌ Erro:</strong> ${data.error}`;
                    document.getElementById('result').classList.add('error');
                    updateDebugInfo(`❌ Erro no servidor: ${data.error}`);
                }
            } catch (error) {
                updateDebugInfo(`❌ Erro de conexão: ${error.message}`);
                document.getElementById('result').innerHTML = `<strong>❌ Erro de conexão:</strong> ${error.message}`;
                document.getElementById('result').classList.add('error');
            } finally {
                document.getElementById('loading').classList.add('hidden');
                document.getElementById('result').classList.remove('hidden');
            }
        }
        
        // Testar conexão ao carregar
        window.onload = function() {
            updateDebugInfo('Página carregada, testando conexão...');
            fetch('/api/status')
                .then(response => response.json())
                .then(data => updateDebugInfo('✅ Conexão OK - Server online'))
                .catch(error => updateDebugInfo(`❌ Erro no teste de conexão: ${error.message}`));
        };
    </script>
</body>
</html>
        """
        
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            logger.info("✅ HTML enviado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar HTML: {e}")
    
    def _serve_debug_page(self):
        """Servir página de debug detalhada"""
        debug_info = {
            "server_status": "running",
            "cascade_client": standalone_cascade_client is not None,
            "timestamp": datetime.now().isoformat(),
            "headers": dict(self.headers),
            "client_address": self.client_address
        }
        
        self._send_json(debug_info)
    
    def _serve_status(self):
        """Servir status"""
        status = {
            "server": "running",
            "mode": "debug",
            "cascade_available": standalone_cascade_client is not None,
            "timestamp": datetime.now().isoformat()
        }
        self._send_json(status)
    
    def _serve_turbo_info(self):
        """Servir info turbo"""
        if self.turbo_server and standalone_cascade_client:
            info = {
                "turbo_mode": True,
                "cache_size": len(standalone_cascade_client.performance_cache),
                "requests": self.turbo_server.performance_stats.get("total_requests", 0)
            }
            self._send_json(info)
        else:
            self._send_json({"error": "Turbo server or cascade client not available"})
    
    def _serve_404(self):
        """404"""
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode('utf-8'))
    
    def _serve_error(self, message, code=500):
        """Erro"""
        logger.error(f"🚨 Server Error {code}: {message}")
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))
    
    def _send_json(self, data):
        """JSON response"""
        try:
            json_str = json.dumps(data, default=str)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json_str.encode('utf-8'))
            logger.info(f"✅ JSON response enviado: {len(json_str)} bytes")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar JSON: {e}")
    
    def _handle_turbo_code(self, data):
        """Handle código com debug"""
        logger.info("💻 Iniciando _handle_turbo_code")
        
        if not standalone_cascade_client:
            logger.error("❌ Cascade client não disponível")
            self._serve_error("Cascade client not available", 503)
            return
        
        try:
            prompt = data.get("prompt", "")
            language = data.get("language", "python")
            
            logger.info(f"📝 Prompt: {prompt}")
            logger.info(f"🐍 Language: {language}")
            
            # Executar de forma síncrona para evitar problemas de event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    standalone_cascade_client.generate_code(prompt, language)
                )
                logger.info(f"✅ Código gerado com sucesso")
                
                response_data = {
                    "result": {
                        "code": result.content,
                        "confidence": result.confidence,
                        "expert": result.expert_type
                    }
                }
                
                self._send_json(response_data)
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar código: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self._serve_error(f"Code generation error: {str(e)}", 500)
    
    def _handle_turbo_design(self, data):
        """Handle design"""
        logger.info("🏗️ Iniciando _handle_turbo_design")
        self._send_json({"result": {"architecture": "Design feature em desenvolvimento", "confidence": 0.8}})
    
    def _handle_turbo_security(self, data):
        """Handle security"""
        logger.info("🔒 Iniciando _handle_turbo_security")
        self._send_json({"result": {"audit": "Security feature em desenvolvimento", "confidence": 0.8}})
    
    def _handle_turbo_analyze(self, data):
        """Handle analyze"""
        logger.info("⚡ Iniciando _handle_turbo_analyze")
        self._send_json({"result": {"analysis": "Analysis feature em desenvolvimento", "confidence": 0.8}})

class DebugTurboWebServer:
    """Servidor web com debug"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.cascade_client = standalone_cascade_client
        self.performance_stats = {"total_requests": 0}
        self.http_server = None
    
    async def initialize(self):
        """Inicializar com debug"""
        logger.info("🚀 Inicializando Debug Turbo Web Server")
        
        if self.cascade_client:
            try:
                await self.cascade_client.initialize()
                logger.info("✅ Cascade client inicializado")
            except Exception as e:
                logger.error(f"❌ Erro ao inicializar cascade client: {e}")
        else:
            logger.warning("⚠️ Cascade client não disponível")
        
        return True
    
    def start(self):
        """Iniciar servidor com debug"""
        def handler(*args, **kwargs):
            return DebugTurboWebHandler(*args, turbo_server=self, **kwargs)
        
        self.http_server = HTTPServer((self.host, self.port), handler)
        
        logger.info(f"\n🌐 SERVIDOR WEB DEBUG INICIADO!")
        logger.info(f"📍 URL: http://{self.host}:{self.port}")
        logger.info(f"🐛 Debug mode: ATIVO")
        logger.info(f"📋 Logs: console + web_server_debug.log")
        logger.info(f"🚀 ABRA NO NAVEGADOR: http://{self.host}:{self.port}")
        
        try:
            self.http_server.serve_forever()
        except KeyboardInterrupt:
            logger.info("\n🛑 Servidor parado pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro no servidor: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Parar servidor"""
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
        logger.info("🛑 Servidor web debug parado")

async def main():
    """Main com debug"""
    logger.info("🚀 Iniciando modo DEBUG do servidor web")
    
    web_server = DebugTurboWebServer()
    await web_server.initialize()
    web_server.start()

if __name__ == "__main__":
    logger.info("🚀 Iniciando servidor web em modo DEBUG")
    
    # Iniciar sem asyncio.run() para evitar erro
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("🛑 Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
    finally:
        loop.close()
        logger.info("🏁 Servidor finalizado")
