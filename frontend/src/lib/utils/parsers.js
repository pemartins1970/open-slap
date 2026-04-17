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
 * @param {string} text - Texto contendo blocos JSON
 * @param {string} startTag - Tag de início (ex: '<JSON>')
 * @param {string} endTag - Tag de fim (ex: '</JSON>')
 * @returns {Array} - Array de objetos JSON parseados
 */
export const extractTaggedJsonBlocks = (text, startTag, endTag) => {
  const blocks = [];
  let remaining = String(text || '');
  
  while (remaining.includes(startTag)) {
    const start = remaining.indexOf(startTag);
    const end = remaining.indexOf(endTag, start);
    
    if (end === -1) break;
    
    const jsonStr = remaining.slice(start + startTag.length, end).trim();
    try {
      const parsed = JSON.parse(jsonStr);
      blocks.push(parsed);
    } catch (e) {
      console.warn('Falha ao parsear JSON:', e);
    }
    
    remaining = remaining.slice(end + endTag.length);
  }
  
  return blocks;
};

/**
 * Parse de requisições de comando do conteúdo
 * @param {string} content - Conteúdo da mensagem
 * @returns {Array} - Array de comandos parseados
 */
export const parseCommandRequestsFromContent = (content) => {
  const commandTag = '<COMMAND_REQUEST>';
  const endTag = '</COMMAND_REQUEST>';
  
  const extracted = extractTaggedJsonBlocks(content, commandTag, endTag);
  return extracted.filter(cmd => cmd && (cmd.command || cmd.script));
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
