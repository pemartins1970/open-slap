# SPEC P2.5: SabrinaAgent + Renderização de [[add_step: X]]
**Projeto**: Open Slap! v3  
**Data**: 2026-05-30  
**Prioridade**: P2.5  
**Assignee**: Opencode  

---

## Contexto

Dois problemas independentes resolvidos neste sprint:

1. **Backend**: `general` é o único expert do MoE sem `BaseAgent` correspondente — cai no `else` (fallback direto ao llm_manager) no orchestrator. Criar `SabrinaAgent(BaseAgent)` fecha essa lacuna.

2. **Frontend**: A Sabrina produz tokens `[[add_step: Descrição]]` que são parseados mas não têm handler visual. Aparecem como texto puro no chat. Criar um componente `StepsPanel` minimalista e conectar ao parser.

**Premissa importante verificada na leitura do código:**
O `ExecutionPanel` é para comandos CLI (com `commandHistory`, `activeCommands`, output, erro, duração). Steps da Sabrina são marcos de progresso conversacional — conceito diferente. **Não conectar `[[add_step]]` ao `ExecutionPanel`** — criar componente próprio.

---

## PARTE 1 — Backend: SabrinaAgent

### 1.1 `backend/agents/sabrina_agent.py` — CRIAR

```python
"""
SabrinaAgent — Agente conversacional da Sabrina para o fluxo de chat.

A Sabrina é o expert 'general' no MoE router. Este agente herda de BaseAgent
e delega a chamada LLM ao llm_manager usando o system_prompt completo da Sabrina.

O system_prompt NÃO está aqui — está no MoE router (moe_router_simple.py, expert id='general').
O BaseAgent._build_expert_dict() monta o dict de expert a partir de name/system_prompt/description.
Para a Sabrina, o system_prompt vem do MoE — não duplicar aqui.
"""
from backend.agents.base import BaseAgent, agent_registry


# System prompt da Sabrina — espelho do que está no MoE router (expert id='general').
# Mantido aqui para que o BaseAgent.stream_execute() tenha o prompt correto.
# ATENÇÃO: se o system_prompt da Sabrina for atualizado no MoE, atualizar aqui também.
# TODO futuro: MoE e BaseAgent lerem o mesmo source of truth.
SABRINA_SYSTEM_PROMPT = (
    "Seu nome é Sabrina. Você é um agente incorporado (embodied) e orientado à execução. "
    "Se o usuário pedir algo que exija visão, captura de tela, manipulação de arquivos ou interação com a interface, você já tem as ferramentas no MCP e deve usá-las.\n\n"
    "Poderes (MCP / tool-use):\n"
    "- Você pode acionar automação local via software_operator.\n"
    "- Você pode usar python-inline para lógica customizada, visão e geração de artefatos locais quando necessário.\n\n"
    "Atue como um Assistente Executivo de IA Pessoal altamente qualificado, proativo e organizado. "
    "O objetivo é simplificar a rotina, aumentar a produtividade e auxiliar na gestão de tarefas e informações.\n\n"
    "Orquestração:\n"
    "- Você é uma facilitadora e orquestradora geral: identifica a natureza do problema e convoca o orquestrador certo (CTO, CFO, COO) ou especialistas.\n"
    "- Você não está limitada a TI. Você pode trabalhar com finanças, operações, marketing, dados e produtividade.\n\n"
    "Contexto do sistema:\n"
    "- Você recebe no contexto informações de Runtime/system, Settings e Memória. Use isso como fonte válida para inferir caminhos, limitações, conectores e capacidades do sistema.\n"
    "- Evite perguntar ao usuário por informações que já estejam no contexto.\n\n"
    "Execução e Interação:\n"
    "- Responda ao usuário de forma natural. Narre seu raciocínio (Chain of Thought narrativo).\n"
    "- REGISTRO DE PROGRESSO: Durante entrevistas ou processos de design, use a tag `[[add_step: Descrição]]` para registrar marcos no menu lateral. Isso informa o progresso de forma silenciosa.\n"
    "- Se for um início de fluxo técnico simples, seja curta, mas em fases de design, seja explicativa.\n\n"
    "Plano executável (quando necessário):\n"
    "- Se o pedido exigir execução/alteração no projeto, crie um plano em um bloco ```plan``` para que o sistema execute.\n"
    "- Formato: uma linha por tarefa, com \"título | skill_id\".\n"
    "- Use skill_id entre: cto, cfo, coo, project, backend, frontend, devops, security, data_science, software_operator.\n"
    "- Regra prática: para pedidos simples com automação, crie diretamente a tarefa software_operator; para pedidos complexos, delegue ao orquestrador certo e depois às tarefas de execução.\n\n"
    "Documentação e rastreio:\n"
    "- Toda execução relevante deve terminar com uma tarefa final: \"Gerente de Projeto: registrar atividades e decisões no TODO | project\".\n\n"
    "Regra de ouro (credenciais): você nunca solicita chaves de API, tokens ou secrets no chat. "
    "Se precisar orientar configuração, direcione o usuário para Settings → LLM e, se necessário, inclua o token [[open_settings:llm_api_key]].\n\n"
    "Aprendizado: use a memória do usuário disponível no contexto para adaptar o seu estilo ao longo do tempo.\n\n"
    "Capacidades:\n"
    "- Gestão de tarefas: organizar prioridades, criar listas de afazeres e lembrar de prazos.\n"
    "- Organização de agenda: planejar compromissos e gestão de tempo.\n"
    "- Resumo e pesquisa: resumir textos longos, PDFs e planilhas.\n"
    "- Comparação e decisão: comparar opções e apoiar decisões rápidas.\n"
    "- Planejamento: estudos, viagens, lazer e refeições semanais.\n\n"
    "Regras de comportamento:\n"
    "- Seja concisa, direta e profissional, mas amigável.\n"
    "- Sempre que possível, estruture as respostas com tópicos (bullets) ou tabelas.\n"
    "- Se uma solicitação for ambígua, faça perguntas objetivas antes de agir.\n"
    "- Priorize eficiência e organização.\n"
    "- Não faça apresentação/repetição. Se precisar, faça no máximo 1–3 perguntas objetivas.\n"
    "- Se notar falta de contexto pessoal relevante, proponha coletar 3–5 informações rápidas.\n"
)

SABRINA_SKILLS = [
    {"name": "orchestration", "description": "Orquestra especialistas e ferramentas"},
    {"name": "task_management", "description": "Gestão de tarefas e prioridades"},
    {"name": "planning", "description": "Planejamento e organização"},
    {"name": "ideation_capture", "description": "Captura silenciosa de ideações"},
]


class SabrinaAgent(BaseAgent):
    name = "general"
    description = "Sabrina — Assistente Executiva e orquestradora geral"
    system_prompt = SABRINA_SYSTEM_PROMPT
    skills = SABRINA_SKILLS


agent_registry.register(SabrinaAgent())
```

### 1.2 `backend/agents/__init__.py` — adicionar import

```python
from backend.agents.sabrina_agent import SabrinaAgent  # noqa: F401
```

Padrão idêntico ao dos outros agentes.

### 1.3 Verificar: orchestrator `else` após este sprint

Após registrar `SabrinaAgent` com `name="general"`, o `agent_registry.get("general")` vai retornar o agente. O bloco `else` no orchestrator vai ser atingido apenas para experts sem BaseAgent (`cfo`, `coo`, `project`, `security`, `data`, `ide_editor`, `software_operator`).

**Não remover o `else`** — ainda é necessário para os 7 experts restantes.

---

## PARTE 2 — Frontend: StepsPanel e handler de [[add_step: X]]

### 2.1 `frontend/src/components/StepsPanel.jsx` — CRIAR

Componente minimalista. Exibe lista de steps em ordem cronológica. Sem filtros, sem busca, sem histórico de comandos — não é o ExecutionPanel.

```jsx
import React from 'react';

/**
 * StepsPanel — Painel de progresso da Sabrina.
 * Exibe os marcos registrados via [[add_step: Descrição]] durante um fluxo.
 *
 * Props:
 *   steps: Array<{ id: string, description: string, timestamp: string }>
 *   isVisible: boolean
 *   onClose: () => void
 *   t: função de tradução (opcional)
 */
const StepsPanel = ({ steps = [], isVisible, onClose, t }) => {
  if (!isVisible) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: '80px',
      right: '16px',
      width: '280px',
      maxHeight: '320px',
      overflowY: 'auto',
      backgroundColor: 'var(--bg-secondary, #1e293b)',
      border: '1px solid var(--border-color, #334155)',
      borderRadius: '8px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
      zIndex: 200,
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 12px',
        borderBottom: '1px solid var(--border-color, #334155)',
        flexShrink: 0,
      }}>
        <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary, #94a3b8)' }}>
          {t ? t('progress_steps') : 'Progresso'}
        </span>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary, #94a3b8)',
            cursor: 'pointer',
            fontSize: '14px',
            padding: '0 4px',
            lineHeight: 1,
          }}
          title="Fechar"
        >
          ×
        </button>
      </div>

      {/* Steps list */}
      <div style={{ padding: '8px 0', flex: 1 }}>
        {steps.length === 0 ? (
          <div style={{
            padding: '12px',
            fontSize: '12px',
            color: 'var(--text-muted, #64748b)',
            textAlign: 'center',
          }}>
            {t ? t('no_steps_yet') : 'Nenhum passo registrado'}
          </div>
        ) : (
          steps.map((step, index) => (
            <div
              key={step.id || index}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                padding: '6px 12px',
              }}
            >
              {/* Indicador numérico */}
              <div style={{
                flexShrink: 0,
                width: '18px',
                height: '18px',
                borderRadius: '50%',
                backgroundColor: 'var(--accent-color, #6366f1)',
                color: '#fff',
                fontSize: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginTop: '1px',
              }}>
                {index + 1}
              </div>

              {/* Descrição */}
              <span style={{
                fontSize: '12px',
                color: 'var(--text-primary, #e2e8f0)',
                lineHeight: '1.4',
                flex: 1,
              }}>
                {step.description}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default StepsPanel;
```

### 2.2 `App_auth.jsx` — adicionar state e handler

**Localizar** o bloco de `useState` declarations e adicionar:

```jsx
// Steps da Sabrina ([[add_step: X]])
const [sabrinaSteps, setSabrinaSteps] = useState([]);
const [showStepsPanel, setShowStepsPanel] = useState(false);
```

**Localizar** a função `parseAssistantDirectivesFromText` (ou equivalente que processa o texto final após `done`). Adicionar o handler de `[[add_step: X]]`:

```javascript
// Dentro de parseAssistantDirectivesFromText ou no bloco reduceDoneEvent:

// Handler [[add_step: Descrição]]
const addStepMatches = [...text.matchAll(/\[\[add_step:\s*([^\]]+)\]\]/gi)];
if (addStepMatches.length > 0) {
  const newSteps = addStepMatches.map((m, i) => ({
    id: `step-${Date.now()}-${i}`,
    description: m[1].trim(),
    timestamp: new Date().toISOString(),
  }));
  setSabrinaSteps(prev => [...prev, ...newSteps]);
  setShowStepsPanel(true);  // abre o painel automaticamente quando há steps
}
```

**Localizar** onde `[[open_settings:llm_api_key]]` é processado — o `[[add_step: X]]` deve ser tratado no mesmo bloco para consistência.

**Importante**: remover os tokens `[[add_step: X]]` do texto exibido no chat, assim como `[[open_settings:X]]` já é removido. O usuário não deve ver o token cru na resposta.

### 2.3 Renderizar `StepsPanel` no JSX

**Localizar** a área de modais e painéis flutuantes no return do `App_auth.jsx` e adicionar:

```jsx
{/* Steps da Sabrina */}
<StepsPanel
  steps={sabrinaSteps}
  isVisible={showStepsPanel}
  onClose={() => setShowStepsPanel(false)}
  t={t}
/>
```

### 2.4 Limpar steps ao iniciar nova conversa

Onde `startNewConversation()` ou `handleNewChat()` é chamado, adicionar:

```javascript
setSabrinaSteps([]);
setShowStepsPanel(false);
```

### 2.5 Import no `App_auth.jsx`

```jsx
import StepsPanel from './components/StepsPanel';
```

---

## Testes

### Backend — adicionar em `test_agent_llm.py`

```python
@pytest.mark.asyncio
async def test_sabrina_agent_registered():
    """SabrinaAgent deve estar registrado com name='general'."""
    from backend.agents.base import agent_registry
    import backend.agents.sabrina_agent  # noqa: F401
    agent = agent_registry.get("general")
    assert agent is not None
    assert agent.name == "general"
    assert "Sabrina" in agent.system_prompt
    assert len(agent.system_prompt) > 200


@pytest.mark.asyncio
async def test_sabrina_agent_execute():
    """SabrinaAgent deve executar via LLM (mockado)."""
    from backend.agents.sabrina_agent import SabrinaAgent
    from unittest.mock import patch

    async def fake_stream(*args, **kwargs):
        yield {"provider": "mock", "model": "mock"}
        yield "Olá! Como posso ajudar?"

    agent = SabrinaAgent()
    with patch("backend.llm_manager_simple.llm_manager") as mock_llm:
        mock_llm.stream_generate = fake_stream
        result = await agent.execute("oi sabrina", {})
    assert result.status == "success"
    assert result.data["agent"] == "general"
```

### Frontend — checklist manual (sem Jest configurado)

1. Enviar mensagem que aciona a Sabrina (score baixo, sem keyword específica)
2. A resposta **não** deve conter `[[add_step: ...]]` visível no texto
3. Se a Sabrina emitir `[[add_step: X]]`, o `StepsPanel` deve aparecer no canto inferior direito com o step listado
4. Botão `×` no painel fecha sem apagar os steps (steps persistem até nova conversa)
5. Ao clicar "Nova Conversa", steps são limpos e painel fecha

---

## Critérios de Aceite

1. `agent_registry.get("general")` retorna `SabrinaAgent`
2. Mensagem sem keyword específica roteia para `general` e recebe resposta via `SabrinaAgent.stream_execute()` — sem cair no `else`
3. `pytest backend/tests/ -v` — 123 passed (2 novos), 0 failed, 0 errors
4. Token `[[add_step: X]]` não aparece como texto puro no chat
5. `StepsPanel` exibe steps em ordem cronológica quando a Sabrina os emite
6. Steps são limpos ao iniciar nova conversa

---

## O que este sprint NÃO faz

- Não configura `OPENSLAP_ROUTER_PROVIDER` — isso é configuração de ambiente, não código
- Não remove o `else` do orchestrator — 7 experts ainda sem BaseAgent
- Não cria BaseAgent para `cfo`, `coo`, `project`, `security`, `data`, `ide_editor`, `software_operator`
- Não reforma a topbar/navbar — próxima rodada de UI
- Não remove "Fale com a Sabrina" e "Iniciar Projeto" do menu esquerdo — próxima rodada de UI
- Não sincroniza automaticamente o system_prompt entre MoE e SabrinaAgent — TODO futuro

---

## Nota de arquitetura — duplicação do system_prompt

O system_prompt da Sabrina existe em dois lugares: no MoE router (`moe_router_simple.py`, expert `general`) e no `SabrinaAgent`. Isso é dívida técnica consciente — o MoE usa o prompt para a seleção `select_expert_llm_first`, e o BaseAgent usa para a chamada LLM.

A solução futura é o MoE exportar os prompts como constantes importáveis, e o `SabrinaAgent` importar de lá. Por ora, manter os dois sincronizados manualmente e documentar no `CURRENT_STATE.md`.
