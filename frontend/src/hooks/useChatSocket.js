import { useCallback, useEffect, useRef } from 'react';
import { flushSync } from 'react-dom';
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
  onRequestDone,
  onConversationRenamed,
  selectedProvider,
  selectedModel,
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
      console.log('[WS] Conectado, pending=%s', Boolean(pendingAutoSendRef.current));
      fetchRuntimeLlmLabel();

      if (pendingAutoSendRef.current) {
        console.log('[WS] Processando pendingAutoSendRef');
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
          flushSync(() => {
            setMessages((prev) => {
              meta = reduceDoneEvent(prev, d, parseAssistantDirectivesFromText);
              return meta.nextMessages;
            });
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
          onRequestDone?.();
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
        conversation_renamed: (d) => {
          const cid = d?.conversation_id;
          const title = String(d?.title || '').trim();
          if (cid != null && title) {
            onConversationRenamed?.(String(cid), title);
          }
        },
        cancel_ack: (d) => {
          console.log('Cancelamento solicitado:', d.run_id);
          flush();
          setStreaming(false);
          setStreamStatusText('');
        },
        cancelled: (d) => {
          console.log('Orquestração cancelada:', d.conversation_id);
          flush();
          setStreaming(false);
          setStreamStatusText('');
          const nowMs = Date.now();
          const msgId = `cancelled-${nowMs}-${Math.random().toString(16).slice(2)}`;
          setMessages((prev) => {
            const next = Array.isArray(prev) ? [...prev] : [];
            const last = next[next.length - 1];
            if (last && last.role === 'assistant' && last.streaming) {
              next[next.length - 1] = { ...last, content: '*[Orquestração cancelada pelo usuário]*', streaming: false };
              return next;
            }
            return [...next, {
              role: 'assistant',
              content: '*[Orquestração cancelada pelo usuário]*',
              streaming: false,
              id: msgId,
            }];
          });
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

    ws.onclose = (ev) => {
      if (wsRef.current !== ws) return;
      const wasStreaming = Boolean(streamingRef.current) || hasBuffered();
      setConnected(false);
      setStreaming(false);
      setStreamStatusText('');
      flush();
      console.log('[WS] Desconectado code=%s reason="%s" wasStreaming=%s', ev?.code, ev?.reason, wasStreaming);
      if (wasStreaming) {
        const txt = 'Conexão perdida durante o processamento. Reabrindo\u2026';
        const nowMs = Date.now();
        setMessages((prev) => applyWsCloseEvent(prev, txt, { nowMs }));
      }

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
    onRequestDone,
  ]);

  // Auto-connect quando user e token ficam dispon\u00edveis.
  // connectWebSocket omitido das deps intencionalmente: a fun\u00e7\u00e3o recria o WS
  // completamente; re-executar em cada mudan\u00e7a de callback (lang, skills, etc.)
  // causaria reconex\u00f5es desnecess\u00e1rias. S\u00f3 reconecta em mudan\u00e7a de identidade
  // do usu\u00e1rio ou rota\u00e7\u00e3o de token.
  const userId = user?.id ?? user?.sub ?? user?.email ?? null;
  useEffect(() => {
    if (!userId || !token) return;
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        const ws = wsRef.current;
        ws.onclose = null; // evita loop de reconex\u00e3o no unmount
        ws.close();
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, token]);

  const sendMessage = useCallback((overrideText) => {
    const text = (overrideText || input)?.trim();
    console.log('[sendMessage] called, text="%s", streaming=%s, readyState=%s, hasWs=%s', text, streaming, wsRef.current?.readyState, Boolean(wsRef.current));
    if (!text || streaming || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return false;
    }

    const now = Date.now();
    const contentRaw = text;
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
      provider: selectedProvider || undefined,
      model: selectedModel || undefined,
    }));
    return true;
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
    selectedProvider,
    selectedModel,
  ]);

  return { connectWebSocket, sendMessage };
};

export default useChatSocket;
