"""
Algoritmo de Roteamento para MoE (Mixture of Experts)
"""

import re
import os
from typing import Dict, Any, List, Optional, AsyncGenerator

from .experts import Expert, ExpertRegistry


class RoutingAlgorithm:
    """Algoritmo de seleção de especialistas"""
    
    def __init__(self, experts: List[Expert]):
        self.experts = experts
        self.keyword_patterns = self._create_keyword_patterns()
    
    def _create_keyword_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Cria padrões de regex para cada especialista"""
        patterns = {}
        
        for expert in self.experts:
            expert_patterns = []
            for keyword in expert.keywords:
                # Cria pattern case-insensitive que corresponda à palavra inteira
                pattern = re.compile(
                    rf'\b{re.escape(keyword.lower())}\b',
                    re.IGNORECASE
                )
                expert_patterns.append(pattern)
            patterns[expert.id] = expert_patterns
        
        return patterns
    
    def calculate_keyword_score(self, text: str, expert_id: str) -> float:
        """Calcula score baseado em keywords encontradas"""
        if expert_id not in self.keyword_patterns:
            return 0.0
        
        patterns = self.keyword_patterns[expert_id]
        text_lower = text.lower()
        
        matches = 0
        for pattern in patterns:
            if pattern.search(text_lower):
                matches += 1
        
        # Normaliza pelo número de patterns
        return matches / len(patterns) if patterns else 0.0
    
    def select_expert_by_keywords(
        self, text: str, force_expert_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Seleciona especialista baseado em keywords"""
        if force_expert_id:
            expert = next((e for e in self.experts if e.id == force_expert_id), None)
            if expert:
                return {
                    "expert": expert.to_dict(1.0),
                    "method": "forced",
                    "confidence": 1.0,
                    "matched_keywords": [],
                }
        
        # Calcula scores para todos os especialistas
        scores = []
        for expert in self.experts:
            score = self.calculate_keyword_score(text, expert.id)
            if score > 0:
                scores.append((expert, score))
        
        # Ordena por score (maior para menor)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if not scores:
            # Nenhum especialista encontrado - retorna o primeiro como fallback
            expert = self.experts[0]
            return {
                "expert": expert.to_dict(0.1),
                "method": "fallback",
                "confidence": 0.1,
                "matched_keywords": [],
            }
        
        # Retorna o especialista com maior score
        best_expert, best_score = scores[0]
        
        # Encontra keywords correspondentes
        matched_keywords = []
        if best_expert.id in self.keyword_patterns:
            text_lower = text.lower()
            for i, pattern in enumerate(self.keyword_patterns[best_expert.id]):
                if pattern.search(text_lower):
                    matched_keywords.append(best_expert.keywords[i])
        
        return {
            "expert": best_expert.to_dict(best_score),
            "method": "keyword_match",
            "confidence": best_score,
            "matched_keywords": matched_keywords,
        }
    
    async def select_expert_with_llm(
        self,
        text: str,
        force_expert_id: Optional[str] = None,
        user_context: Optional[str] = None,
        llm_manager=None
    ) -> Dict[str, Any]:
        """Seleciona especialista usando LLM para análise mais sofisticada"""
        if force_expert_id:
            expert = next((e for e in self.experts if e.id == force_expert_id), None)
            if expert:
                return {
                    "expert": expert.to_dict(1.0),
                    "method": "forced",
                    "confidence": 1.0,
                    "matched_keywords": [],
                }
        
        if not llm_manager:
            # Fallback para seleção por keywords
            return self.select_expert_by_keywords(text)
        
        # Prepara prompt para LLM
        expert_list = "\n".join([
            f"- {e.id}: {e.description}" 
            for e in self.experts
        ])
        
        capabilities = ExpertRegistry.get_capabilities_catalog(self.experts)
        
        router_prompt = f"""Você é um router inteligente que seleciona o especialista mais adequado para uma solicitação.

ESPECIALISTAS DISPONÍVEIS:
{expert_list}

CAPACIDADES DETALHADAS:
{capabilities}

ANÁLISE DA SOLICITAÇÃO:
Usuário: "{text}"

TAREFA:
1. Analise cuidadosamente a solicitação do usuário
2. Identifique o especialista mais adequado baseado em:
   - Keywords e termos técnicos
   - Tipo de tarefa solicitada
   - Complexidade e domínio
   - Capacidades do especialista
3. Retorne APENAS o ID do especialista escolhido

RESPOSTA (apenas o ID do especialista):"""
        
        try:
            # Usa LLM para selecionar especialista
            collected = ""
            async for chunk in llm_manager.stream_generate(
                router_prompt,
                {"prompt": "Você é um router de especialistas."},
                user_context
            ):
                collected += chunk
            
            # Limpa a resposta para obter apenas o ID
            selected_id = collected.strip().lower()
            
            # Valida se o ID corresponde a um especialista
            expert = next((e for e in self.experts if e.id == selected_id), None)
            
            if expert:
                # Calcula score de keywords para confiança
                keyword_score = self.calculate_keyword_score(text, expert.id)
                
                return {
                    "expert": expert.to_dict(keyword_score),
                    "method": "llm_selection",
                    "confidence": max(keyword_score, 0.5),  # Mínimo 0.5 para seleção LLM
                    "matched_keywords": [],
                    "llm_response": collected.strip(),
                }
            else:
                # LLM retornou ID inválido - fallback para keywords
                return self.select_expert_by_keywords(text)
        
        except Exception as e:
            # Erro no LLM - fallback para keywords
            return self.select_expert_by_keywords(text)
    
    def analyze_expert_selection(self, text: str) -> Dict[str, Any]:
        """Análise detalhada da seleção de especialista"""
        text_lower = text.lower()
        analysis = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "expert_scores": {},
            "top_keywords": {},
            "recommendation": None,
        }
        
        # Calcula scores para todos os especialistas
        for expert in self.experts:
            score = self.calculate_keyword_score(text, expert.id)
            if score > 0:
                analysis["expert_scores"][expert.id] = score
                
                # Encontra keywords correspondentes
                matched = []
                if expert.id in self.keyword_patterns:
                    for i, pattern in enumerate(self.keyword_patterns[expert.id]):
                        if pattern.search(text_lower):
                            matched.append(expert.keywords[i])
                
                if matched:
                    analysis["top_keywords"][expert.id] = matched
        
        # Determina recomendação
        if analysis["expert_scores"]:
            best_expert_id = max(
                analysis["expert_scores"], 
                key=analysis["expert_scores"].get
            )
            analysis["recommendation"] = best_expert_id
        
        return analysis
    
    def get_expert_by_id(self, expert_id: str) -> Optional[Dict[str, Any]]:
        """Retorna especialista por ID"""
        expert = next((e for e in self.experts if e.id == expert_id), None)
        if expert:
            return expert.to_dict(1.0)
        return None
    
    def get_all_experts(self) -> List[Dict[str, Any]]:
        """Retorna todos os especialistas como dicionários"""
        return [expert.to_dict(1.0) for expert in self.experts]
