/**
 * 🔍 Parsers - Funções de parsing de conteúdo e estruturas
 */

/**
 * Parse de blocos de mensagem (texto, thinking, plan, etc.)
 * @param {string} content - Conteúdo a ser parseado
 * @returns {Array} - Array de blocos {type, content}
 */
export const parseMessageBlocks = (content) => {
  const blocks = [];
  let remaining = String(content || '');
  
  while (remaining) {
    const thinkingStart = remaining.indexOf('<THINKING>');
    const planStart = remaining.indexOf('```plan');
    const candidates = [thinkingStart, planStart].filter((n) => n >= 0);
    
    if (!candidates.length) break;
    
    const nextStart = Math.min(...candidates);
    if (nextStart > 0) {
      const prefix = remaining.slice(0, nextStart);
      if (prefix.trim()) blocks.push({ type: 'text', content: prefix.trim() });
      remaining = remaining.slice(nextStart);
    }

    if (remaining.startsWith('<THINKING>')) {
      const end = remaining.indexOf('</THINKING>');
      if (end === -1) break;
      const inner = remaining.slice('<THINKING>'.length, end);
      blocks.push({ type: 'thinking', content: inner.trim() });
      remaining = remaining.slice(end + '</THINKING>'.length);
      continue;
    }

    if (remaining.startsWith('```plan_auto')) {
      const fenceEnd = remaining.indexOf('```', '```plan_auto'.length);
      if (fenceEnd === -1) break;
      const inner = remaining.slice('```plan_auto'.length, fenceEnd);
      blocks.push({ type: 'plan_auto', content: inner.replace(/^\s+/, '').replace(/\s+$/, '') });
      remaining = remaining.slice(fenceEnd + 3);
      continue;
    }

    if (remaining.startsWith('```plan')) {
      const fenceEnd = remaining.indexOf('```', '```plan'.length);
      if (fenceEnd === -1) break;
      const inner = remaining.slice('```plan'.length, fenceEnd);
      blocks.push({ type: 'plan', content: inner.replace(/^\s+/, '').replace(/\s+$/, '') });
      remaining = remaining.slice(fenceEnd + 3);
      continue;
    }

    break;
  }
  
  if (remaining.trim()) blocks.push({ type: 'text', content: remaining.trim() });
  return blocks.length ? blocks : [{ type: 'text', content: String(content || '') }];
};

/**
 * Parse de tarefas do formato plan (título | skill_id)
 * @param {string} raw - Texto bruto do plano
 * @returns {Array} - Array de tarefas {title, skill_id}
 */
export const parsePlanTasksFromText = (raw) => {
  const lines = String(raw || '')
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);
  
  const out = [];
  for (const line of lines) {
    if (!line.includes('|')) continue;
    const [left, right] = line.split('|');
    const title = String(left || '').trim();
    const skill_id = String(right || '').trim();
    if (!title || title.toLowerCase() === 'tarefa') continue;
    out.push({ title, skill_id });
  }
  return out;
};

/**
 * Extrai blocos JSON marcados com tags específicas
 * Remove as tags do texto e retorna blocos parseados + texto limpo
 * @param {string} text - Texto contendo blocos JSON
 * @param {string} startTag - Tag de início (ex: '<JSON>')
 * @param {string} endTag - Tag de fim (ex: '</JSON>')
 * @returns {{ text: string, blocks: Array }} - Texto limpo e blocos parseados
 */
export const extractTaggedJsonBlocks = (text, startTag, endTag) => {
  const blocks = [];
  if (!text) return { text: '', blocks };

  let cursor = 0;
  let out = '';
  while (true) {
    const start = text.indexOf(startTag, cursor);
    if (start === -1) break;
    const end = text.indexOf(endTag, start + startTag.length);
    if (end === -1) break;

    out += text.slice(cursor, start);
    const raw = text.slice(start + startTag.length, end).trim();
    let obj = null;
    try {
      obj = raw ? JSON.parse(raw) : null;
    } catch {
      obj = null;
    }
    if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
      blocks.push(obj);
    } else {
      out += text.slice(start, end + endTag.length);
    }
    cursor = end + endTag.length;
  }
  out += text.slice(cursor);
  return { text: out.trim(), blocks };
};

/**
 * Parse de requisições de comando do conteúdo
 * Extrai blocos COMMAND_REQUEST_JSON e COMMAND_JSON, retorna texto limpo + requests
 * @param {string} content - Conteúdo da mensagem
 * @returns {{ text: string, requests: Array }} - Texto sem tags de comando e requests parseados
 */
export const parseCommandRequestsFromContent = (content) => {
  const first = extractTaggedJsonBlocks(
    content || '',
    '<COMMAND_REQUEST_JSON>',
    '</COMMAND_REQUEST_JSON>'
  );
  const second = extractTaggedJsonBlocks(
    first.text || '',
    '<COMMAND_JSON>',
    '</COMMAND_JSON>'
  );
  return {
    text: second.text || '',
    requests: [...(first.blocks || []), ...(second.blocks || [])]
  };
};

/**
 * Parse de metadata de arquivo anexado
 * @param {string} filename - Nome do arquivo
 * @returns {Object} - {name, extension, type}
 */
export const parseFileMetadata = (filename) => {
  const name = String(filename || '').trim();
  const lastDot = name.lastIndexOf('.');
  const extension = lastDot > 0 ? name.slice(lastDot + 1).toLowerCase() : '';
  
  // Determina tipo MIME básico
  const imageExts = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'];
  const docExts = ['pdf', 'doc', 'docx', 'txt', 'md'];
  const codeExts = ['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'go', 'rs'];
  
  let type = 'unknown';
  if (imageExts.includes(extension)) type = 'image';
  else if (docExts.includes(extension)) type = 'document';
  else if (codeExts.includes(extension)) type = 'code';
  
  return { name, extension, type };
};

/**
 * Parse de markdown simples para HTML
 * @param {string} markdown - Texto em markdown
 * @returns {string} - HTML renderizado
 */
export const parseSimpleMarkdown = (markdown) => {
  let html = String(markdown || '');
  
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  
  // Italic
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');
  
  // Code inline
  html = html.replace(/`(.*?)`/gim, '<code>$1</code>');
  
  // Links
  html = html.replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2">$1</a>');
  
  // Line breaks
  html = html.replace(/\n/gim, '<br>');
  
  return html;
};

/**
 * Parse de query string
 * @param {string} queryString - Query string (ex: "?foo=bar&baz=qux")
 * @returns {Object} - Objeto com parâmetros parseados
 */
export const parseQueryString = (queryString) => {
  const params = {};
  const query = queryString.startsWith('?') ? queryString.slice(1) : queryString;
  
  query.split('&').forEach(pair => {
    const [key, value] = pair.split('=');
    if (key) {
      params[decodeURIComponent(key)] = value ? decodeURIComponent(value) : '';
    }
  });
  
  return params;
};
