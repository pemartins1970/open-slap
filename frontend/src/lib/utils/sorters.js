/**
 * 🔀 Sorters - Funções de ordenação e agrupamento
 */

/**
 * Ordem preferida para skills por segmento
 */
export const SKILL_SEGMENT_PREFERRED_ORDER = {
  system: ['skill-creator', 'chat-assistant', 'cto', 'systems-architect'],
  finance: ['cfo', 'excel-expert'],
  admin: ['coo', 'project-manager'],
  it_devops: ['backend-dev', 'frontend-dev', 'devops', 'security', 'data-scientist', 'code-review', 'tests'],
  marketing: ['marketing', 'seo'],
  other: []
};

/**
 * Ordem preferida para experts por segmento
 */
export const EXPERT_SEGMENT_PREFERRED_ORDER = {
  system: ['skill-creator', 'general', 'chat-assistant', 'cto', 'systems-architect'],
  finance: ['cfo', 'excel-expert'],
  admin: ['coo', 'project-manager'],
  it_devops: ['backend-dev', 'frontend-dev', 'devops', 'security', 'data-scientist', 'code-review', 'tests'],
  marketing: ['marketing', 'seo'],
  other: []
};

/**
 * Ordem de segmentos
 */
export const SEGMENT_ORDER = ['system', 'admin', 'finance', 'marketing', 'it_devops', 'other'];

/**
 * Ordena items por ordem preferida, depois alfabeticamente
 * @param {Array} items - Items a ordenar
 * @param {Array} preferred - Ordem preferida de IDs
 * @param {Function} getId - Função para extrair ID do item
 * @param {Function} getLabel - Função para extrair label do item
 * @returns {Array} - Items ordenados
 */
export const sortByPreferredOrder = (items, preferred, getId, getLabel) => {
  const order = Array.isArray(preferred) ? preferred : [];
  const idx = (v) => {
    const id = String(getId(v) || '').toLowerCase();
    const i = order.indexOf(id);
    return i === -1 ? 1e9 : i;
  };
  const label = (v) => String(getLabel(v) || '').toLowerCase();
  return (items || []).slice().sort((a, b) => {
    const da = idx(a);
    const db = idx(b);
    if (da !== db) return da - db;
    return label(a).localeCompare(label(b));
  });
};

/**
 * Ordena skills por segmento
 * @param {Array} items - Skills a ordenar
 * @param {string} seg - ID do segmento
 * @param {Function} getSkillDisplayName - Função para obter nome de exibição
 * @returns {Array} - Skills ordenadas
 */
export const sortSkillsForSegment = (items, seg, getSkillDisplayName) => 
  sortByPreferredOrder(
    items, 
    SKILL_SEGMENT_PREFERRED_ORDER?.[seg], 
    (s) => s?.id, 
    getSkillDisplayName
  );

/**
 * Ordena experts por segmento
 * @param {Array} items - Experts a ordenar
 * @param {string} seg - ID do segmento
 * @param {Function} getExpertDisplayName - Função para obter nome de exibição
 * @returns {Array} - Experts ordenados
 */
export const sortExpertsForSegment = (items, seg, getExpertDisplayName) => 
  sortByPreferredOrder(
    items, 
    EXPERT_SEGMENT_PREFERRED_ORDER?.[seg], 
    (e) => e?.id, 
    getExpertDisplayName
  );

/**
 * Agrupa items por segmento
 * @param {Array} items - Items a agrupar
 * @param {Function} getId - Função para extrair ID do segmento
 * @returns {Object} - Objeto com items agrupados por segmento
 */
export const groupBySegment = (items, getId) => {
  const map = {};
  (items || []).forEach((item) => {
    const seg = getId(item);
    if (!map[seg]) map[seg] = [];
    map[seg].push(item);
  });
  return map;
};

/**
 * Ordena conversas por data de atualização (mais recente primeiro)
 * @param {Array} conversations - Conversas a ordenar
 * @returns {Array} - Conversas ordenadas
 */
export const sortConversationsByDate = (conversations) => {
  return (conversations || []).slice().sort((a, b) => {
    const ta = new Date(a?.updated_at || a?.created_at || 0).getTime();
    const tb = new Date(b?.updated_at || b?.created_at || 0).getTime();
    return tb - ta;
  });
};

/**
 * Ordena items alfabeticamente por nome
 * @param {Array} items - Items a ordenar
 * @param {Function} getLabel - Função para extrair label
 * @returns {Array} - Items ordenados
 */
export const sortAlphabetically = (items, getLabel) => {
  return (items || []).slice().sort((a, b) => {
    const labelA = String(getLabel(a) || '').toLowerCase();
    const labelB = String(getLabel(b) || '').toLowerCase();
    return labelA.localeCompare(labelB);
  });
};
