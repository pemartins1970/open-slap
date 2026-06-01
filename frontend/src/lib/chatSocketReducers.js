export function applySoftwareOperatorEvent(prevMessages, data, opts = {}) {
  const nowMs = Number(opts?.nowMs) || Date.now();
  const executionId = String(data?.execution_id || '').trim() || `cli-${nowMs}`;
  const status = String(data?.status || '').trim().toLowerCase() || 'running';

  const buildCliContent = (cli) => {
    const vs = String(cli?.visual_state_summary || '').trim();
    if (vs) return vs;
    const out = String(cli?.stdout || '').trim();
    const err = String(cli?.stderr || '').trim();
    const pick = out || err;
    if (!pick) return '';
    const lines = pick.split('\n').map((l) => l.trim()).filter(Boolean);
    return lines.slice(0, 6).join('\n').slice(0, 800);
  };

  const next = Array.isArray(prevMessages) ? [...prevMessages] : [];
  const idx = next.findIndex((m) => m?.cli_execution_id === executionId);
  const base = {
    role: 'assistant',
    content: '',
    streaming: false,
    id: `cli-${executionId}`,
    cli_execution_id: executionId,
    cli: {
      status,
      attempt: data?.attempt,
      command: data?.command,
      command_executed: data?.command_executed,
      started_at_ms: data?.started_at_ms,
      timeout_s: data?.timeout_s,
      elapsed_ms: data?.elapsed_ms,
      return_ms: data?.return_ms,
      stdout: data?.stdout,
      stderr: data?.stderr,
      stdout_chunk: data?.stdout_chunk,
      stderr_chunk: data?.stderr_chunk,
      visual_state_summary: data?.visual_state_summary,
      artifacts: data?.artifacts
    }
  };

  if (idx >= 0) {
    const prevCli = next[idx]?.cli || {};
    const appendedStdout = (prevCli.stdout || '') + String(data?.stdout_chunk || '');
    const appendedStderr = (prevCli.stderr || '') + String(data?.stderr_chunk || '');
    const finalStdout = typeof data?.stdout === 'string' ? data.stdout : appendedStdout;
    const finalStderr = typeof data?.stderr === 'string' ? data.stderr : appendedStderr;
    const startedAtMs =
      Number(base?.cli?.started_at_ms) ||
      Number(prevCli?.started_at_ms) ||
      (status === 'running' ? nowMs : 0);
    const timeoutS = Number(base?.cli?.timeout_s) || Number(prevCli?.timeout_s) || 0;
    const returnMs = Number(base?.cli?.return_ms) || Number(prevCli?.return_ms) || 0;

    next[idx] = {
      ...next[idx],
      ...base,
      cli: {
        ...(prevCli || {}),
        ...(base.cli || {}),
        started_at_ms: startedAtMs,
        timeout_s: timeoutS,
        return_ms: returnMs,
        stdout: finalStdout,
        stderr: finalStderr
      }
    };

    if (status !== 'running') {
      const content = buildCliContent({
        ...(next[idx]?.cli || {}),
        stdout: finalStdout,
        stderr: finalStderr,
        visual_state_summary: data?.visual_state_summary
      });
      if (content) next[idx] = { ...next[idx], content };
    }

    return next;
  }

  let parentIdx = -1;
  for (let i = next.length - 1; i >= 0; i -= 1) {
    const m = next[i];
    if (!m) continue;
    if (m.role !== 'assistant') continue;
    if (m.streaming) continue;
    if (m.cli_execution_id) continue;
    parentIdx = i;
    break;
  }

  if (parentIdx >= 0) {
    const parent = next[parentIdx] || {};
    const runs = { ...(parent.cli_runs || {}) };
    const prevCli = runs[executionId] || {};
    const startedAtMs =
      Number(base?.cli?.started_at_ms) ||
      Number(prevCli?.started_at_ms) ||
      (status === 'running' ? nowMs : 0);
    const timeoutS = Number(base?.cli?.timeout_s) || Number(prevCli?.timeout_s) || 0;
    const returnMs = Number(base?.cli?.return_ms) || Number(prevCli?.return_ms) || 0;

    runs[executionId] = {
      ...prevCli,
      ...(base.cli || {}),
      started_at_ms: startedAtMs,
      timeout_s: timeoutS,
      return_ms: returnMs,
    };
    next[parentIdx] = { ...parent, cli_runs: runs };
    return next;
  }

  if (!base?.cli?.started_at_ms && status === 'running') {
    base.cli.started_at_ms = nowMs;
  }
  if (status !== 'running') {
    const content = buildCliContent(base.cli);
    if (content) base.content = content;
  }
  next.push(base);
  return next;
}

export function reduceDoneEvent(prevMessages, data, parseAssistantDirectivesFromText) {
  const selectionReason = String(data?.selection_reason || '').trim();
  const matchedKeywords = Array.isArray(data?.matched_keywords) ? data.matched_keywords : [];
  const doneMessageId = data?.message_id || null;

  const nextMessages = Array.isArray(prevMessages) ? [...prevMessages] : [];
  let last = nextMessages[nextMessages.length - 1];
  if (!last || last.role !== 'assistant') {
    for (let i = nextMessages.length - 1; i >= 0; i -= 1) {
      const m = nextMessages[i];
      if (m && m.role === 'assistant') {
        last = m;
        break;
      }
    }
  }

  let actionsToRun = [];
  let assistantPartsToSchedule = [];
  let anchorLocalId = null;

  if (last && last.role === 'assistant') {
    anchorLocalId = last.id || null;
    const extracted = parseAssistantDirectivesFromText ? parseAssistantDirectivesFromText(last.content) : null;
    actionsToRun = extracted?.actions || [];
    assistantPartsToSchedule = (extracted?.parts || []).slice(1);
    nextMessages[nextMessages.length - 1] = {
      ...last,
      content: extracted?.cleaned ?? last.content,
      streaming: false,
      expert: data?.expert,
      expert_reason: selectionReason,
      expert_keywords: matchedKeywords,
      provider: data?.provider,
      model: data?.model,
      message_id: doneMessageId,
    };
  }

  return {
    selectionReason,
    matchedKeywords,
    doneMessageId,
    nextMessages,
    actionsToRun,
    assistantPartsToSchedule,
    anchorLocalId,
  };
}

export function applyHistoryEvent(prevMessages, data, opts = {}) {
  const msg = data?.message || {};
  const nowMs = Number(opts?.nowMs) || Date.now();
  const rand = typeof opts?.rand === 'function' ? opts.rand : Math.random;
  const id = msg?.id ?? `history-${nowMs}-${rand().toString(16).slice(2)}`;

  const prev = Array.isArray(prevMessages) ? prevMessages : [];
  if (prev.some((m) => String(m?.message_id || '') === String(id))) return prev;
  if (prev.some((m) => String(m?.id) === String(id))) return prev;
  const incomingRole = String(msg?.role || '').trim();
  const incomingContent = String(msg?.content || '').trim();
  if (incomingRole && incomingContent) {
    const lookback = Math.min(25, prev.length);
    for (let i = prev.length - 1; i >= prev.length - lookback; i -= 1) {
      const m = prev[i];
      if (!m) continue;
      const mr = String(m?.role || '').trim();
      const mc = String(m?.content || '').trim();
      if (mr !== incomingRole) continue;
      if (mc !== incomingContent) continue;
      const hasCreatedAt = Boolean(m?.created_at);
      const optimisticId = typeof m?.id === 'string' && /^\d{10,}-[0-9a-f]+$/i.test(String(m.id));
      if (!hasCreatedAt && optimisticId) {
        const next = [...prev];
        next[i] = {
          ...m,
          ...msg,
          id: m.id,
          message_id: m?.message_id ?? msg?.id ?? null,
        };
        return next;
      }
      return prev;
    }
  }
  return [...prev, { ...msg, id }];
}

export function applyWsErrorEvent(prevMessages, txt, opts = {}) {
  const nowMs = Number(opts?.nowMs) || Date.now();
  const rand = typeof opts?.rand === 'function' ? opts.rand : Math.random;
  const messageId = `ws-error-${nowMs}-${rand().toString(16).slice(2)}`;

  const next = Array.isArray(prevMessages) ? [...prevMessages] : [];
  const last = next[next.length - 1];
  if (last && last.role === 'assistant' && last.streaming) {
    next[next.length - 1] = { ...last, content: txt, streaming: false };
    return next;
  }
  next.push({
    role: 'assistant',
    content: txt,
    streaming: false,
    id: messageId
  });
  return next;
}

export function applyWsCloseEvent(prevMessages, txt, opts = {}) {
  const nowMs = Number(opts?.nowMs) || Date.now();
  const rand = typeof opts?.rand === 'function' ? opts.rand : Math.random;
  const messageId = `ws-close-${nowMs}-${rand().toString(16).slice(2)}`;

  const next = Array.isArray(prevMessages) ? [...prevMessages] : [];
  const last = next[next.length - 1];
  if (last && last.role === 'assistant' && last.streaming) {
    next[next.length - 1] = { ...last, content: txt, streaming: false };
    return next;
  }
  next.push({
    role: 'assistant',
    content: txt,
    streaming: false,
    id: messageId
  });
  return next;
}

export function reduceStatusEvent(data, ctx = {}) {
  const txt = String(data?.content || '').trim();
  const currentConversation = ctx?.currentConversation ?? null;
  const currentKind = String(ctx?.currentKind || '').trim();
  const lower = txt.toLowerCase();
  const shouldRefreshTodos =
    Boolean(txt) &&
    Boolean(currentConversation) &&
    currentKind === 'task' &&
    lower.includes('todo');

  return { txt, shouldRefreshTodos };
}
