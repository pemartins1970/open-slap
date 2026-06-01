import { useCallback, useEffect, useRef } from 'react';
import useChunkBuffer from './useChunkBuffer';
import { applyHistoryEvent, applySoftwareOperatorEvent, applyWsCloseEvent, applyWsErrorEvent, reduceDoneEvent, reduceStatusEvent } from '../lib/chatSocketReducers';

const useChatSocket = ({
  user,
  token,
  lang,
  llmMode,
  skills,
  selectedSkillId,
  forceExpertId,
  agentConfigs,
  showRoutingDebug,
  currentConversation,
  currentKind,
  sessionIdRef,
  wsRef,
  pendingAutoSendRef,
  messagesEndRef,
  setMessages,
  input,
  setInput,
  setConnected,
  setStreaming,
  setStreamStatusText,
  setRuntimeLlmLabel,
  setLastExpertReason,
  setLastExpertKeywords,
  setShowExecutionPanel,
  setActivePlanMessageId,
  setActivePlanLocalMsgId,
  pendingPlanTasksRef,
  scheduleListsRefresh,
  formatRuntimeLlmLabel,
  parseAssistantDirectivesFromText,
  runUiActions,
  loadTaskTodos,
  loadGlobalTodos,
  loadTasks,
  buildSysGlobalKernelPrompt,
  maybeRepoDisambiguationInternalPrompt,
  fetchRuntimeLlmLabel,
  streaming,
}) => {
  const streamingRef = useRef(false);
  const { appendChunk, flush, hasBuffered } = useChunkBuffer({ setMessages });

  useEffect(() => {
    streamingRef.current = Boolean(streaming);
  }, [streaming]);

  const connectWebSocket = useCallback(() => {
    const tokenValue = token || localStorage.getItem('agentic_token');
    if (!tokenValue) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${wsProtocol}://${window.location.host}/ws/${sessionIdRef.current}?token=${tokenValue}`);
    wsRef.current = ws;

    ws.onopen = () => {
      if (wsRef.current !== ws) return;
      setConnected(true);
      console.log('WebSocket conectado');
      fetchRuntimeLlmLabel();

      if (pendingAutoSendRef.current) {
        const pending = pendingAutoSendRef.current;
        pendingAutoSendRef.current = null;

        const pendingContentRaw =
          typeof pending === 'string'
            ? pending
            : String(pending?.content || '');
        const pendingContent = pendingContentRaw;
        const extraPrompt = maybeRepoDisambiguationInternalPrompt({ lang, text: pendingContentRaw });
        const kernelPrompt = buildSysGlobalKernelPrompt(lang);
        const internalPrompt =
          typeof pending === 'string'
            ? ''
            : String(pending?.internalPrompt || '');
        const forceExpertOverride =
          typeof pending === 'string'
            ? ''
            : String(pending?.forceExpertId || '');

        const now = Date.now();
        const userMessage = {
          role: 'user',
          content: pendingContent,
          id: `${now}-${Math.random().toString(16).slice(2)}`
        };

        setStreaming(true);
        setMessages((prev) => [
          ...prev,
          userMessage,
          {
            role: 'assistant',
            content: '',
            streaming: true,
            id: `${now + 1}-${Math.random().toString(16).slice(2)}`
          }
        ]);
        setInput('');

        const activeSkill = (skills || []).find((s) => s.id === selectedSkillId) || null;
        ws.send(JSON.stringify({
          type: 'chat',
          content: pendingContent,
          internal_prompt: [kernelPrompt, internalPrompt, extraPrompt].filter(Boolean).join('\n\n') || null,
          skill_id: activeSkill?.id || null,
          skill_web_search: activeSkill?.content?.web_search === true,
          force_expert_id: (forceExpertOverride || forceExpertId) || null,
          debug_router: Boolean(showRoutingDebug),
          client_message_id: userMessage.id,
        }));
      }
    };

    ws.onmessage = (event) => {
      if (wsRef.current !== ws) return;
      let data = null;
      try {
        data = JSON.parse(event.data);
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
        return;
      }

      const handlers = {
        user_ack: (d) => {
          const clientId = String(d?.client_message_id || '').trim();
          const msg = d?.message || null;
          if (!clientId || !msg) return;
          setMessages((prev) => {
            const next = Array.isArray(prev) ? [...prev] : [];
            const idx = next.findIndex((m) => String(m?.id) === clientId);
            if (idx === -1) return prev;
            next[idx] = {
              ...(next[idx] || {}),
              ...(msg || {}),
              id: next[idx]?.id,
              message_id: (next[idx]?.message_id ?? msg?.id) || null,
            };
            return next;
          });
        },
        history: (d) => {
          const nowMs = Date.now();
          setMessages((prev) => applyHistoryEvent(prev, d, { nowMs }));
        },
        chunk: (d) => {
          appendChunk(d.content);
        },
        done: (d) => {
          flush();
          let meta = null;
          setMessages((prev) => {
            meta = reduceDoneEvent(prev, d, parseAssistantDirectivesFromText);
            return meta.nextMessages;
          });
          const selectionReason = meta?.selectionReason || '';
          const matchedKeywords = meta?.matchedKeywords || [];
          if (selectionReason) setLastExpertReason(selectionReason);
          if (matchedKeywords?.length) setLastExpertKeywords(matchedKeywords || []);

          const doneMessageId = meta?.doneMessageId || null;
          if (d.plan_detected && d.plan_tasks?.length && currentConversation) {
            const tasks = Array.isArray(d.plan_tasks) ? d.plan_tasks : [];
            if (tasks.length) setShowExecutionPanel(true);
            setActivePlanMessageId(doneMessageId || null);
            setActivePlanLocalMsgId(meta?.anchorLocalId || null);
            pendingPlanTasksRef.current = {
              ...(pendingPlanTasksRef.current || {}),
              [String(currentConversation)]: tasks
            };
          }
          if (meta?.actionsToRun?.length) {
            runUiActions(meta.actionsToRun);
          }
          if (meta?.assistantPartsToSchedule?.length) {
            for (const p of meta.assistantPartsToSchedule) {
              const delay = Number(p?.delayMs) || 0;
              const content = String(p?.text || '').trim();
              if (!content) continue;
              setTimeout(() => {
                setMessages((prev) => [
                  ...prev,
                  {
                    role: 'assistant',
                    content,
                    streaming: false,
                    id: `split-${Date.now()}-${Math.random().toString(16).slice(2)}`
                  }
                ]);
              }, Math.max(0, delay));
            }
          }
          if (d.provider || d.model) {
            const label = formatRuntimeLlmLabel(d.provider, d.model, llmMode);
            if (label) setRuntimeLlmLabel(label);
          }
          setStreaming(false);
          setStreamStatusText('');
          scheduleListsRefresh();
        },
        status: (d) => {
          const statusMeta = reduceStatusEvent(d, { currentConversation, currentKind });
          if (statusMeta.txt) setStreamStatusText(statusMeta.txt);
          if (statusMeta.shouldRefreshTodos) {
            loadTaskTodos(currentConversation);
            loadGlobalTodos();
            loadTasks();
          }
          scheduleListsRefresh();
        },
        software_operator: (d) => {
          const nowMs = Date.now();
          setMessages((prev) => applySoftwareOperatorEvent(prev, d, { nowMs }));
          setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
          }, 0);
        },
        error: (d) => {
          const txt = String(d.content || '').trim() || 'Erro no processamento.';
          console.error('WebSocket error:', txt);
          flush();
          const nowMs = Date.now();
          setMessages((prev) => applyWsErrorEvent(prev, txt, { nowMs }));
          setStreaming(false);
          setStreamStatusText('');
        }
      };

      try {
        const handler = handlers[String(data?.type || '')];
        if (handler) handler(data);
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      if (wsRef.current !== ws) return;
      const wasStreaming = Boolean(streamingRef.current) || hasBuffered();
      setConnected(false);
      setStreaming(false);
      setStreamStatusText('');
      flush();
      if (wasStreaming) {
        const txt = 'Conexão perdida durante o processamento. Reabrindo…';
        const nowMs = Date.now();
        setMessages((prev) => applyWsCloseEvent(prev, txt, { nowMs }));
      }
      console.log('WebSocket desconectado');

      setTimeout(() => {
        if (user) {
          connectWebSocket();
        }
      }, 3000);
    };

    ws.onerror = (error) => {
      if (wsRef.current !== ws) return;
      console.error('WebSocket error:', error);
      setConnected(false);
      setStreaming(false);
      setStreamStatusText('');
    };
  }, [
    token,
    sessionIdRef,
    wsRef,
    setConnected,
    fetchRuntimeLlmLabel,
    pendingAutoSendRef,
    maybeRepoDisambiguationInternalPrompt,
    lang,
    buildSysGlobalKernelPrompt,
    setStreaming,
    setMessages,
    setInput,
    skills,
    selectedSkillId,
    forceExpertId,
    showRoutingDebug,
    appendChunk,
    flush,
    hasBuffered,
    setLastExpertReason,
    setLastExpertKeywords,
    parseAssistantDirectivesFromText,
    runUiActions,
    currentConversation,
    setShowExecutionPanel,
    setActivePlanMessageId,
    setActivePlanLocalMsgId,
    pendingPlanTasksRef,
    formatRuntimeLlmLabel,
    llmMode,
    setRuntimeLlmLabel,
    setStreamStatusText,
    scheduleListsRefresh,
    currentKind,
    loadTaskTodos,
    loadGlobalTodos,
    loadTasks,
    messagesEndRef,
    user,
  ]);

  const sendMessage = useCallback(() => {
    if (!input?.trim() || streaming || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    const now = Date.now();
    const contentRaw = input.trim();
    const extraPrompt = maybeRepoDisambiguationInternalPrompt({ lang, text: contentRaw });
    const userMessage = {
      role: 'user',
      content: contentRaw,
      id: `${now}-${Math.random().toString(16).slice(2)}`
    };

    setStreaming(true);

    setMessages((prev) => [
      ...prev,
      userMessage,
      {
        role: 'assistant',
        content: '',
        streaming: true,
        id: `${now + 1}-${Math.random().toString(16).slice(2)}`
      }
    ]);
    setInput('');

    const activeSkill = (skills || []).find((s) => s.id === selectedSkillId) || null;
    const agentPrompt = forceExpertId ? String(agentConfigs?.[forceExpertId]?.prompt || '').trim() : '';
    const kernelPrompt = buildSysGlobalKernelPrompt(lang);
    wsRef.current.send(JSON.stringify({
      type: 'chat',
      content: contentRaw,
      internal_prompt: [kernelPrompt, agentPrompt, extraPrompt].filter(Boolean).join('\n\n') || null,
      skill_id: activeSkill?.id || null,
      skill_web_search: activeSkill?.content?.web_search === true,
      force_expert_id: forceExpertId || null,
      debug_router: Boolean(showRoutingDebug),
    }));
  }, [
    input,
    streaming,
    wsRef,
    maybeRepoDisambiguationInternalPrompt,
    lang,
    setStreaming,
    setMessages,
    setInput,
    skills,
    selectedSkillId,
    forceExpertId,
    agentConfigs,
    buildSysGlobalKernelPrompt,
    showRoutingDebug,
  ]);

  return { connectWebSocket, sendMessage };
};

export default useChatSocket;
