/**
 * 🔖 Identifiers - Funções de identificação e segmentação
 */

/**
 * Obtém ID de segmento de uma skill
 * @param {Object} skill - Objeto de skill
 * @returns {string} - ID do segmento ('system', 'admin', 'finance', 'marketing', 'it_devops', 'other')
 */
export const getSkillSegmentId = (skill) => {
  const id = String(skill?.id || '').toLowerCase();
  
  if (['cto', 'systems-architect', 'chat-assistant', 'skill-creator'].includes(id)) {
    return 'system';
  }
  if (['coo', 'project-manager'].includes(id)) {
    return 'admin';
  }
  if (['cfo', 'excel-expert'].includes(id)) {
    return 'finance';
  }
  if (['seo', 'marketing'].includes(id)) {
    return 'marketing';
  }
  if (['backend-dev', 'frontend-dev', 'devops', 'security', 'data-scientist', 'code-review', 'tests'].includes(id)) {
    return 'it_devops';
  }
  
  return 'other';
};

/**
 * Obtém ID de segmento de um expert
 * @param {Object} expert - Objeto de expert
 * @returns {string} - ID do segmento
 */
export const getExpertSegmentId = (expert) => {
  const id = String(expert?.id || '').toLowerCase();
  
  if (['general', 'cto', 'systems-architect', 'chat-assistant', 'skill-creator'].includes(id)) {
    return 'system';
  }
  if (['coo', 'project-manager'].includes(id)) {
    return 'admin';
  }
  if (['cfo', 'excel-expert'].includes(id)) {
    return 'finance';
  }
  if (['seo', 'marketing'].includes(id)) {
    return 'marketing';
  }
  if (['backend-dev', 'frontend-dev', 'devops', 'security', 'data-scientist', 'code-review', 'tests'].includes(id)) {
    return 'it_devops';
  }
  
  return 'other';
};

/**
 * Obtém label de segmento para exibição
 * @param {string} segmentId - ID do segmento
 * @param {Function} t - Função de tradução
 * @returns {string} - Label traduzido
 */
export const getSegmentLabel = (segmentId, t) => {
  const key = `segment_${segmentId}`;
  const translated = t(key);
  return translated === key ? segmentId : translated;
};

/**
 * Gera ID único de sessão
 * @returns {string} - ID de sessão único
 */
export const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Gera ID único genérico
 * @param {string} prefix - Prefixo do ID (ex: 'conv', 'task', 'msg')
 * @returns {string} - ID único com prefixo
 */
export const generateId = (prefix = 'id') => {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Gera slug a partir de string
 * @param {string} text - Texto a converter
 * @returns {string} - Slug (lowercase, sem espaços, sem caracteres especiais)
 */
export const generateSlug = (text) => {
  return String(text || '')
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

/**
 * Encurta ID para exibição
 * @param {string} id - ID completo
 * @param {number} length - Tamanho desejado (padrão: 8)
 * @returns {string} - ID encurtado
 */
export const shortenId = (id, length = 8) => {
  const str = String(id || '');
  return str.length <= length ? str : str.slice(0, length);
};

/**
 * Valida se é um ID UUID válido
 * @param {string} id - ID a validar
 * @returns {boolean} - true se é UUID válido
 */
export const isValidUuid = (id) => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(String(id || ''));
};

/**
 * Extrai ID de diferentes formatos de URL/path
 * @param {string} pathOrUrl - Path ou URL contendo ID
 * @returns {string|null} - ID extraído ou null
 */
export const extractIdFromPath = (pathOrUrl) => {
  const str = String(pathOrUrl || '').trim();
  
  // Tenta extrair UUID
  const uuidMatch = str.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i);
  if (uuidMatch) return uuidMatch[0];
  
  // Tenta extrair ID numérico
  const numMatch = str.match(/\/(\d+)(?:\/|$)/);
  if (numMatch) return numMatch[1];
  
  // Tenta extrair último segmento
  const segments = str.split('/').filter(Boolean);
  if (segments.length) return segments[segments.length - 1];
  
  return null;
};

/**
 * Cria hash simples de string (para identificação, não segurança)
 * @param {string} str - String para hash
 * @returns {string} - Hash em hexadecimal
 */
export const simpleHash = (str) => {
  let hash = 0;
  const text = String(str || '');
  
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  
  return Math.abs(hash).toString(16);
};

/**
 * Verifica se dois IDs são equivalentes (case-insensitive)
 * @param {string} id1 - Primeiro ID
 * @param {string} id2 - Segundo ID
 * @returns {boolean} - true se são equivalentes
 */
export const idsMatch = (id1, id2) => {
  const a = String(id1 || '').toLowerCase().trim();
  const b = String(id2 || '').toLowerCase().trim();
  return a === b;
};
