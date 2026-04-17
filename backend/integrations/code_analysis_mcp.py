"""
Code Analysis MCP Integration
Análise de código, code review e análise estática para OpenSlap
"""

from typing import Dict, Any, List, Optional, Tuple
import aiohttp
import re
import json

class CodeAnalysisMCP:
    """
    Code Analysis MCP - Análise e Revisão de Código
    
    Funcionalidades:
    - Análise de arquivos
    - Code review (bugs, performance, security)
    - Detecção de code smells
    - Análise de complexidade
    - Security scanning
    - Style checking
    - Geração de testes
    """
    
    def __init__(self, openai_api_key: str = None, anthropic_api_key: str = None):
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.supported_languages = [
            "python", "javascript", "typescript", "java", "cpp", "c",
            "csharp", "go", "rust", "ruby", "php", "swift", "kotlin",
            "scala", "r", "matlab", "sql", "bash", "yaml", "json"
        ]
    
    def _detect_language(self, code: str, filename: str = None) -> str:
        """Detecta linguagem de programação"""
        if filename:
            extension_map = {
                ".py": "python", ".js": "javascript", ".ts": "typescript",
                ".java": "java", ".cpp": "cpp", ".c": "c", ".cs": "csharp",
                ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
                ".swift": "swift", ".kt": "kotlin", ".scala": "scala",
                ".r": "r", ".m": "matlab", ".sql": "sql", ".sh": "bash",
                ".yml": "yaml", ".yaml": "yaml", ".json": "json"
            }
            ext = filename[filename.rfind("."):].lower() if "." in filename else ""
            if ext in extension_map:
                return extension_map[ext]
        
        # Detect por padrões
        if "def " in code or "import " in code or "class " in code:
            return "python"
        elif "function" in code or "const " in code or "let " in code:
            return "javascript"
        elif "public class" in code or "private class" in code:
            return "java"
        elif "#include" in code:
            return "cpp"
        
        return "unknown"
    
    async def _call_llm(self, prompt: str, provider: str = "openai") -> str:
        """Chama LLM para análise"""
        if provider == "openai" and self.openai_api_key:
            return await self._call_openai(prompt)
        elif provider == "anthropic" and self.anthropic_api_key:
            return await self._call_anthropic(prompt)
        else:
            return "LLM não configurado. Análise local apenas."
    
    async def _call_openai(self, prompt: str) -> str:
        """Chama OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "Você é um especialista em análise de código."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error = await response.text()
                    raise Exception(f"OpenAI API Error: {error}")
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Chama Anthropic API"""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 4000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["content"][0]["text"]
                else:
                    error = await response.text()
                    raise Exception(f"Anthropic API Error: {error}")
    
    # ========== ANÁLISE DE ARQUIVOS ==========
    
    async def analyze_file(self, code: str, filename: str = None,
                          language: str = None) -> Dict[str, Any]:
        """
        Análise completa de arquivo
        
        Args:
            code: Conteúdo do arquivo
            filename: Nome do arquivo (para detectar linguagem)
            language: Linguagem (opcional, auto-detect se não fornecido)
        """
        lang = language or self._detect_language(code, filename)
        
        analysis = {
            "filename": filename,
            "language": lang,
            "metrics": self._calculate_metrics(code),
            "structure": self._analyze_structure(code, lang),
            "complexity": self._analyze_complexity(code, lang),
            "issues": self._detect_issues(code, lang),
            "dependencies": self._extract_dependencies(code, lang)
        }
        
        return analysis
    
    async def review_code(self, code: str, filename: str = None,
                         focus_areas: List[str] = None) -> Dict[str, Any]:
        """
        Code review completo
        
        Args:
            focus_areas: bugs, performance, security, maintainability
        """
        lang = self._detect_language(code, filename)
        areas = focus_areas or ["bugs", "performance", "security", "maintainability"]
        
        prompt = f"""Realize um code review do seguinte código {lang}:

```
{code}
```

Foque nestas áreas: {', '.join(areas)}

Forneça:
1. Severidade (crítica, alta, média, baixa) para cada problema
2. Linha/coluna onde ocorre
3. Descrição do problema
4. Sugestão de correção
5. Código corrigido quando aplicável

Formato JSON:
{{
  "issues": [
    {{
      "severity": "...",
      "location": "linha X",
      "description": "...",
      "suggestion": "...",
      "fixed_code": "..."
    }}
  ],
  "summary": "..."
}}"""
        
        try:
            llm_response = await self._call_llm(prompt)
            # Tenta extrair JSON da resposta
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                review_data = json.loads(json_match.group())
                return review_data
        except:
            pass
        
        # Fallback: análise local
        return {
            "issues": self._detect_issues(code, lang),
            "summary": f"Code review {lang} - Análise local (LLM não disponível)"
        }
    
    async def analyze_code_with_context(self, code: str, context: str = None,
                                       filename: str = None) -> Dict[str, Any]:
        """Análise com contexto adicional"""
        lang = self._detect_language(code, filename)
        
        prompt = f"""Analise este código {lang}:

```
{code}
```

Contexto adicional: {context or 'Nenhum'}

Forneça:
1. Funcionalidade principal
2. Padrões de design utilizados
3. Potenciais problemas
4. Sugestões de melhoria
5. Documentação necessária"""
        
        try:
            analysis = await self._call_llm(prompt)
            return {
                "filename": filename,
                "language": lang,
                "analysis": analysis
            }
        except:
            return await self.analyze_file(code, filename, lang)
    
    # ========== ANÁLISE LOCAL ==========
    
    def _calculate_metrics(self, code: str) -> Dict[str, Any]:
        """Calcula métricas básicas"""
        lines = code.split("\n")
        non_empty = [l for l in lines if l.strip()]
        
        return {
            "total_lines": len(lines),
            "code_lines": len(non_empty),
            "blank_lines": len(lines) - len(non_empty),
            "avg_line_length": sum(len(l) for l in lines) / len(lines) if lines else 0
        }
    
    def _analyze_structure(self, code: str, language: str) -> Dict[str, Any]:
        """Analisa estrutura do código"""
        structure = {
            "functions": [],
            "classes": [],
            "imports": [],
            "comments": []
        }
        
        if language == "python":
            # Detectar funções
            func_pattern = r'def\s+(\w+)\s*\('
            structure["functions"] = re.findall(func_pattern, code)
            
            # Detectar classes
            class_pattern = r'class\s+(\w+)'
            structure["classes"] = re.findall(class_pattern, code)
            
            # Detectar imports
            import_pattern = r'(?:from\s+(\S+)\s+import|import\s+(\S+))'
            imports = re.findall(import_pattern, code)
            structure["imports"] = [i[0] or i[1] for i in imports]
            
            # Detectar comentários
            comment_pattern = r'#\s*(.*)'
            structure["comments"] = re.findall(comment_pattern, code)
        
        elif language in ["javascript", "typescript"]:
            func_pattern = r'function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\('
            matches = re.findall(func_pattern, code)
            structure["functions"] = [m[0] or m[1] for m in matches if m[0] or m[1]]
            
            class_pattern = r'class\s+(\w+)'
            structure["classes"] = re.findall(class_pattern, code)
        
        return structure
    
    def _analyze_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """Analisa complexidade do código"""
        # Contar estruturas de controle
        control_patterns = [
            r'\bif\b', r'\belse\b', r'\belif\b', r'\bfor\b',
            r'\bwhile\b', r'\bswitch\b', r'\bcase\b',
            r'\btry\b', r'\bcatch\b', r'\bexcept\b',
            r'\band\b', r'\bor\b'
        ]
        
        complexity = 1  # Base complexity
        for pattern in control_patterns:
            complexity += len(re.findall(pattern, code, re.IGNORECASE))
        
        # Classificar complexidade
        level = "low"
        if complexity > 20:
            level = "very_high"
        elif complexity > 15:
            level = "high"
        elif complexity > 10:
            level = "medium"
        
        return {
            "cyclomatic_complexity": complexity,
            "level": level,
            "control_structures": complexity - 1
        }
    
    def _detect_issues(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Detecta problemas comuns no código"""
        issues = []
        lines = code.split("\n")
        
        # Problemas comuns por linguagem
        if language == "python":
            # Bare except
            for i, line in enumerate(lines, 1):
                if re.search(r'except\s*:', line):
                    issues.append({
                        "severity": "medium",
                        "line": i,
                        "description": "Bare except - captura exceções genéricas",
                        "suggestion": "Use 'except Exception:' ou exceções específicas"
                    })
                
                # Mutable default arguments
                if re.search(r'def.*\(.*=\s*\[', line):
                    issues.append({
                        "severity": "high",
                        "line": i,
                        "description": "Argumento padrão mutável (lista)",
                        "suggestion": "Use None como default e inicialize dentro da função"
                    })
                
                # print statements (deveria ser logging)
                if re.search(r'^\s*print\s*\(', line) and "print(" not in line.split("#")[0]:
                    issues.append({
                        "severity": "low",
                        "line": i,
                        "description": "Uso de print - considere usar logging",
                        "suggestion": "Use logging.info(), logging.debug(), etc."
                    })
        
        elif language in ["javascript", "typescript"]:
            for i, line in enumerate(lines, 1):
                # var (deveria ser let/const)
                if re.search(r'^\s*var\s+', line):
                    issues.append({
                        "severity": "low",
                        "line": i,
                        "description": "Uso de 'var' - prefira 'let' ou 'const'",
                        "suggestion": "Substitua 'var' por 'const' ou 'let'"
                    })
                
                # == vs ===
                if re.search(r'[^=!]\s*=\s*=\s*[^=]', line):
                    issues.append({
                        "severity": "medium",
                        "line": i,
                        "description": "Uso de '==' - prefira '===' para comparação estrita",
                        "suggestion": "Use '===' em vez de '=='"
                    })
        
        # Problemas genéricos
        for i, line in enumerate(lines, 1):
            # Linhas muito longas
            if len(line) > 120:
                issues.append({
                    "severity": "low",
                    "line": i,
                    "description": f"Linha muito longa ({len(line)} caracteres)",
                    "suggestion": "Quebre em múltiplas linhas (máx 120 chars)"
                })
            
            # Trailing whitespace
            if line.rstrip() != line:
                issues.append({
                    "severity": "info",
                    "line": i,
                    "description": "Espaços em branco no final da linha",
                    "suggestion": "Remova espaços trailing"
                })
        
        return issues
    
    def _extract_dependencies(self, code: str, language: str) -> List[str]:
        """Extrai dependências do código"""
        deps = []
        
        if language == "python":
            # Imports
            import_pattern = r'(?:from\s+(\S+)\s+import|import\s+(\S+))'
            matches = re.findall(import_pattern, code)
            deps = [m[0] or m[1] for m in matches]
        
        elif language in ["javascript", "typescript"]:
            # require
            require_pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
            deps = re.findall(require_pattern, code)
            
            # import
            import_pattern = r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]"
            deps += re.findall(import_pattern, code)
        
        return list(set(deps))
    
    # ========== SECURITY SCANNING ==========
    
    async def security_scan(self, code: str, filename: str = None) -> Dict[str, Any]:
        """Escaneia vulnerabilidades de segurança"""
        lang = self._detect_language(code, filename)
        
        security_issues = []
        lines = code.split("\n")
        
        # Padrões de segurança comuns
        patterns = {
            "python": [
                (r'eval\s*\(', "Uso de eval() - risco de injeção de código", "critical"),
                (r'exec\s*\(', "Uso de exec() - risco de injeção de código", "critical"),
                (r'subprocess\.call.*shell\s*=\s*True', "Shell=True - risco de command injection", "high"),
                (r'input\s*\(', "Uso de input() - considere validação", "medium"),
                (r'pickle\.loads', "pickle.loads - risco de deserialization", "high"),
                (r'yaml\.load\s*\([^)]*\)', "yaml.load sem Loader seguro", "high"),
                (r'PASSWORD\s*=\s*["\'][^"\']+["\']', "Senha hardcoded", "critical"),
                (r'API_KEY\s*=\s*["\'][^"\']+["\']', "API key hardcoded", "critical"),
                (r'SECRET\s*=\s*["\'][^"\']+["\']', "Secret hardcoded", "critical"),
            ],
            "javascript": [
                (r'eval\s*\(', "Uso de eval() - risco de injeção", "critical"),
                (r'Function\s*\(', "Uso de Function() constructor", "high"),
                (r'document\.write\s*\(', "document.write() - XSS potencial", "high"),
                (r'innerHTML\s*=', "innerHTML - XSS potencial", "medium"),
                (r'location\.href\s*=.*\+', "Open redirect potencial", "medium"),
                (r'localStorage\.[gs]etItem.*password', "Senha em localStorage", "high"),
            ]
        }
        
        lang_patterns = patterns.get(lang, [])
        
        for i, line in enumerate(lines, 1):
            for pattern, description, severity in lang_patterns:
                if re.search(pattern, line):
                    security_issues.append({
                        "severity": severity,
                        "line": i,
                        "description": description,
                        "code_snippet": line.strip()[:100]
                    })
        
        return {
            "filename": filename,
            "language": lang,
            "vulnerabilities_found": len(security_issues),
            "vulnerabilities": security_issues,
            "risk_level": self._calculate_risk_level(security_issues)
        }
    
    def _calculate_risk_level(self, issues: List[Dict]) -> str:
        """Calcula nível de risco baseado em vulnerabilidades"""
        critical = sum(1 for i in issues if i["severity"] == "critical")
        high = sum(1 for i in issues if i["severity"] == "high")
        
        if critical > 0:
            return "critical"
        elif high > 2:
            return "high"
        elif high > 0:
            return "medium"
        elif len(issues) > 0:
            return "low"
        return "none"
    
    # ========== STYLE CHECKING ==========
    
    async def check_style(self, code: str, filename: str = None,
                         standard: str = "pep8") -> Dict[str, Any]:
        """Verifica conformidade de estilo de código"""
        lang = self._detect_language(code, filename)
        
        style_issues = []
        lines = code.split("\n")
        
        # Verificações básicas de estilo
        for i, line in enumerate(lines, 1):
            # Comprimento da linha
            if len(line) > 100:
                style_issues.append({
                    "rule": "line-too-long",
                    "line": i,
                    "message": f"Linha muito longa ({len(line)} > 100 caracteres)"
                })
            
            # Trailing whitespace
            if line != line.rstrip():
                style_issues.append({
                    "rule": "trailing-whitespace",
                    "line": i,
                    "message": "Espaços em branco no final da linha"
                })
            
            if lang == "python":
                # Indentação (deve ser 4 espaços)
                stripped = line.lstrip()
                if stripped:
                    indent = len(line) - len(stripped)
                    if indent % 4 != 0:
                        style_issues.append({
                            "rule": "bad-indentation",
                            "line": i,
                            "message": f"Indentação não é múltiplo de 4 ({indent} espaços)"
                        })
        
        return {
            "filename": filename,
            "standard": standard,
            "total_issues": len(style_issues),
            "issues": style_issues,
            "compliance_rate": max(0, 100 - (len(style_issues) / len(lines) * 100)) if lines else 100
        }
    
    # ========== TEST GENERATION ==========
    
    async def generate_tests(self, code: str, filename: str = None,
                            test_framework: str = "pytest") -> Dict[str, Any]:
        """Gera casos de teste para o código"""
        lang = self._detect_language(code, filename)
        
        prompt = f"""Gere testes unitários para o seguinte código {lang} usando {test_framework}:

```
{code}
```

Inclua:
1. Testes para casos normais
2. Testes para edge cases
3. Testes para erros/exceções
4. Mocks quando necessário

Retorne apenas o código de teste."""
        
        try:
            test_code = await self._call_llm(prompt)
            return {
                "filename": filename,
                "language": lang,
                "framework": test_framework,
                "test_code": test_code
            }
        except:
            return {
                "filename": filename,
                "language": lang,
                "framework": test_framework,
                "test_code": "# Geração de testes requer LLM configurado",
                "note": "Configure OPENAI_API_KEY ou ANTHROPIC_API_KEY"
            }
    
    async def test_connection(self) -> bool:
        """Testa conexão (sempre retorna True - análise local)"""
        return True


code_analysis_mcp = None

def init_code_analysis_mcp(openai_api_key: str = None, anthropic_api_key: str = None):
    global code_analysis_mcp
    code_analysis_mcp = CodeAnalysisMCP(openai_api_key, anthropic_api_key)
    return code_analysis_mcp
