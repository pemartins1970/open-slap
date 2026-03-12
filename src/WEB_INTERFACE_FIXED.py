"""
🌐 WEB INTERFACE FIXED - CORRIGIDO PARA asyncio
Servidor web standalone corrigido para evitar erro de event loop
"""

import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import nest_asyncio

# Aplicar nest_asyncio para permitir asyncio.run() dentro de event loop
nest_asyncio.apply()

from TURBO_STANDALONE import StandaloneCascadeClient, standalone_cascade_client

class TurboWebHandler(BaseHTTPRequestHandler):
    """Handler HTTP corrigido"""
    
    def __init__(self, *args, turbo_server=None, **kwargs):
        self.turbo_server = turbo_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/":
            self._serve_html()
        elif path == "/api/status":
            self._serve_status()
        elif path == "/api/turbo/info":
            self._serve_turbo_info()
        else:
            self._serve_404()
    
    def do_POST(self):
        """Handle POST requests corrigido"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            path = urlparse(self.path).path
            
            # Usar asyncio.create_task() em vez de asyncio.run()
            if path == "/api/turbo/code":
                asyncio.create_task(self._handle_turbo_code_async(data))
            elif path == "/api/turbo/design":
                asyncio.create_task(self._handle_turbo_design_async(data))
            elif path == "/api/turbo/security":
                asyncio.create_task(self._handle_turbo_security_async(data))
            elif path == "/api/turbo/analyze":
                asyncio.create_task(self._handle_turbo_analyze_async(data))
            else:
                self._serve_error("Unknown endpoint", 404)
        except Exception as e:
            self._serve_error(str(e), 500)
    
    def _serve_html(self):
        """Servir HTML simplificado"""
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>🚀 Cascade AI Turbo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #667eea; text-align: center; }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #667eea; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; }
        button:hover { background: #5a67d8; }
        .result { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #667eea; }
        .result pre { white-space: pre-wrap; }
        .error { color: #721c24; background: #f8d7da; border-left-color: #f5c6cb; }
        .loading { text-align: center; margin: 20px 0; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Cascade AI Turbo</h1>
        
        <div class="form-group">
            <label for="prompt">Prompt:</label>
            <input type="text" id="prompt" placeholder="Create REST API with authentication">
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
            <p>Gerando código...</p>
        </div>
        
        <div class="result hidden" id="result"></div>
    </div>
    
    <script>
        async function generateCode() {
            const prompt = document.getElementById('prompt').value;
            const language = document.getElementById('language').value;
            
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('result').classList.add('hidden');
            
            try {
                const response = await fetch('/api/turbo/code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, language })
                });
                
                const data = await response.json();
                
                if (data.result) {
                    document.getElementById('result').innerHTML = `
                        <strong>✅ Código Gerado (Confiança: ${(data.result.confidence * 100).toFixed(1)}%)</strong>
                        <pre>${data.result.code}</pre>
                    `;
                    document.getElementById('result').classList.remove('error');
                } else {
                    document.getElementById('result').innerHTML = `<strong>❌ Erro:</strong> ${data.error}`;
                    document.getElementById('result').classList.add('error');
                }
            } catch (error) {
                document.getElementById('result').innerHTML = `<strong>❌ Erro de conexão:</strong> ${error.message}`;
                document.getElementById('result').classList.add('error');
            } finally {
                document.getElementById('loading').classList.add('hidden');
                document.getElementById('result').classList.remove('hidden');
            }
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def _serve_status(self):
        """Servir status"""
        self._send_json({"server": "running", "mode": "turbo_fixed"})
    
    def _serve_turbo_info(self):
        """Servir info turbo"""
        if self.turbo_server:
            info = {
                "turbo_mode": True,
                "cache_size": len(self.turbo_server.cascade_client.performance_cache),
                "requests": self.turbo_server.performance_stats["total_requests"]
            }
            self._send_json(info)
        else:
            self._send_json({"error": "Server not initialized"})
    
    def _serve_404(self):
        """404"""
        self.send_response(404)
        self.end_headers()
    
    def _serve_error(self, message, code=500):
        """Erro"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))
    
    def _send_json(self, data):
        """JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))
    
    async def _handle_turbo_code_async(self, data):
        """Handle código async corrigido"""
        try:
            prompt = data.get("prompt", "")
            language = data.get("language", "python")
            
            result = await self.turbo_server.cascade_client.generate_code(prompt, language)
            
            response_data = {
                "result": {
                    "code": result.content,
                    "confidence": result.confidence,
                    "expert": result.expert_type
                }
            }
            
            self._send_json(response_data)
        except Exception as e:
            self._serve_error(str(e))
    
    async def _handle_turbo_design_async(self, data):
        """Handle design async"""
        try:
            description = data.get("description", "")
            requirements = data.get("requirements", [])
            
            result = await self.turbo_server.cascade_client.analyze_architecture(description, requirements)
            
            response_data = {
                "result": {
                    "architecture": result.content,
                    "confidence": result.confidence
                }
            }
            
            self._send_json(response_data)
        except Exception as e:
            self._serve_error(str(e))
    
    async def _handle_turbo_security_async(self, data):
        """Handle security async"""
        try:
            code = data.get("code", "")
            standards = data.get("standards", ["owasp"])
            
            result = await self.turbo_server.cascade_client.audit_security(code, standards)
            
            response_data = {
                "result": {
                    "audit": result.content,
                    "confidence": result.confidence
                }
            }
            
            self._send_json(response_data)
        except Exception as e:
            self._serve_error(str(e))
    
    async def _handle_turbo_analyze_async(self, data):
        """Handle analyze async"""
        try:
            code = data.get("code", "")
            metrics = data.get("metrics", {})
            
            result = await self.turbo_server.cascade_client.optimize_performance(code, metrics)
            
            response_data = {
                "result": {
                    "analysis": result.content,
                    "confidence": result.confidence
                }
            }
            
            self._send_json(response_data)
        except Exception as e:
            self._serve_error(str(e))
    
    def log_message(self, format, *args):
        """Silenciar logs"""
        pass

class TurboWebServerFixed:
    """Servidor web corrigido"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.cascade_client = standalone_cascade_client
        self.performance_stats = {"total_requests": 0}
        self.http_server = None
    
    async def initialize(self):
        """Inicializar"""
        await self.cascade_client.initialize()
        print("🚀 Turbo Web Server Fixed - Inicializado")
        return True
    
    def start(self):
        """Iniciar servidor"""
        def handler(*args, **kwargs):
            return TurboWebHandler(*args, turbo_server=self, **kwargs)
        
        self.http_server = HTTPServer((self.host, self.port), handler)
        
        print(f"\n🌐 SERVIDOR WEB CORRIGIDO INICIADO!")
        print(f"📍 URL: http://{self.host}:{self.port}")
        print(f"✅ Erro asyncio.run() corrigido")
        print(f"🚀 ABRA NO NAVEGADOR: http://{self.host}:{self.port}")
        
        try:
            self.http_server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor parado")
        finally:
            self.stop()
    
    def stop(self):
        """Parar servidor"""
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()

async def main():
    """Main corrigido"""
    web_server = TurboWebServerFixed()
    await web_server.initialize()
    web_server.start()

if __name__ == "__main__":
    # Iniciar sem asyncio.run() para evitar erro
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
