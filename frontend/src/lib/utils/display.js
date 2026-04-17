/**
 * 🎨 Display - Funções de exibição e formatação de labels
 */

/**
 * Obtém metadata builtin de tabela de i18n
 * @param {Object} table - Tabela de i18n
 * @param {string} id - ID do item
 * @param {string} key - Chave a buscar (name, description, etc.)
 * @param {string} fallback - Valor padrão
 * @param {string} lang - Idioma atual
 * @returns {string} - Valor encontrado ou fallback
 */
export const getBuiltinMeta = (table, id, key, fallback, lang = 'en') => {
  const cleanId = String(id || '').toLowerCase();
  const langKey = String(lang || 'en').toLowerCase();
  const byId = table?.[cleanId];
  const fromLang = byId?.[langKey]?.[key];
  const fromEn = byId?.en?.[key];
  return String(fromLang || fromEn || fallback || '').trim();
};

/**
 * Obtém nome de exibição de uma skill
 * @param {Object} skill - Objeto de skill
 * @param {Object} i18nTable - Tabela de i18n de skills
 * @param {string} lang - Idioma atual
 * @returns {string} - Nome para exibição
 */
export const getSkillDisplayName = (skill, i18nTable, lang = 'en') => 
  getBuiltinMeta(i18nTable, skill?.id, 'name', skill?.name || skill?.id, lang);

/**
 * Obtém descrição de exibição de uma skill
 * @param {Object} skill - Objeto de skill
 * @param {Object} i18nTable - Tabela de i18n de skills
 * @param {string} lang - Idioma atual
 * @returns {string} - Descrição para exibição
 */
export const getSkillDisplayDescription = (skill, i18nTable, lang = 'en') => 
  getBuiltinMeta(i18nTable, skill?.id, 'description', skill?.description || '', lang);

/**
 * Obtém nome de exibição de um expert
 * @param {Object} expert - Objeto de expert
 * @param {Object} expertI18n - Tabela de i18n de experts
 * @param {Object} skillI18n - Tabela de i18n de skills (fallback)
 * @param {string} lang - Idioma atual
 * @returns {string} - Nome para exibição
 */
export const getExpertDisplayName = (expert, expertI18n, skillI18n, lang = 'en') => {
  const fromExpert = getBuiltinMeta(expertI18n, expert?.id, 'name', '', lang);
  if (fromExpert) return fromExpert;
  return getBuiltinMeta(skillI18n, expert?.id, 'name', expert?.name || expert?.id, lang);
};

/**
 * Obtém descrição de exibição de um expert
 * @param {Object} expert - Objeto de expert
 * @param {Object} expertI18n - Tabela de i18n de experts
 * @param {Object} skillI18n - Tabela de i18n de skills (fallback)
 * @param {string} lang - Idioma atual
 * @returns {string} - Descrição para exibição
 */
export const getExpertDisplayDescription = (expert, expertI18n, skillI18n, lang = 'en') => {
  const fromExpert = getBuiltinMeta(expertI18n, expert?.id, 'description', '', lang);
  if (fromExpert) return fromExpert;
  return getBuiltinMeta(skillI18n, expert?.id, 'description', expert?.description || '', lang);
};

/**
 * Obtém label de um check do doctor
 * @param {Object} check - Objeto de check
 * @param {Function} t - Função de tradução
 * @returns {string} - Label traduzido ou padrão
 */
export const getDoctorLabel = (check, t) => {
  const id = String(check?.id || '').trim();
  if (!id) return check?.label || '';
  const k = `doctor_check_${id}`;
  const v = t(k);
  return v === k ? (check?.label || id) : v;
};

/**
 * Obtém saudação do boot baseada na hora do dia
 * @param {Function} t - Função de tradução
 * @param {Object} soulData - Dados do soul/perfil
 * @param {Object} user - Dados do usuário
 * @returns {string} - Saudação personalizada
 */
export const getBootGreeting = (t, soulData, user) => {
  const h = new Date().getHours();
  const key = h < 12 ? 'boot_greeting_morning' : (h < 18 ? 'boot_greeting_afternoon' : 'boot_greeting_evening');
  const base = t(key);
  
  const candidates = [
    String(soulData?.name || '').trim(),
    String(soulData?.full_name || '').trim(),
    String(soulData?.user_name || '').trim(),
    (() => {
      const em = String(user?.email || '').trim();
      return em.includes('@') ? em.split('@')[0] : '';
    })()
  ].filter(Boolean);
  
  const name = candidates.length ? candidates[0] : '';
  return `${base}${name ? `, ${name}` : ''}.`;
};

/**
 * Obtém título de conversa para exibição
 * @param {Object} conversation - Objeto de conversa
 * @param {Function} t - Função de tradução
 * @returns {string} - Título formatado
 */
export const getConversationTitle = (conversation, t) => {
  const title = String(conversation?.title || '').trim();
  if (title) return title;
  const id = String(conversation?.id || '').slice(0, 8);
  return `${t('conversation_label')} ${id}`;
};

/**
 * Ordem preferida de exibição dos segmentos de skills
 */
export const SKILL_SEGMENT_PREFERRED_ORDER = [
  'core', 'productivity', 'communication', 'data', 'automation', 'integration', 'utility',
];

/**
 * Ordem preferida de exibição dos segmentos de experts
 */
export const EXPERT_SEGMENT_PREFERRED_ORDER = [
  'core', 'productivity', 'communication', 'data', 'automation', 'integration', 'utility',
];

/**
 * Obtém status visual de uma skill
 * @param {Object} skill - Objeto de skill
 * @returns {Object} - {color, icon, label}
 */
export const getSkillStatus = (skill) => {
  const enabled = skill?.enabled !== false;
  return {
    enabled,
    color: enabled ? 'var(--success)' : 'var(--text-dim)',
    icon: enabled ? '✓' : '○',
    label: enabled ? 'Ativada' : 'Desativada'
  };
};

/**
 * Obtém status visual de um expert
 * @param {Object} expert - Objeto de expert
 * @returns {Object} - {color, icon, label}
 */
export const getExpertStatus = (expert) => {
  const enabled = expert?.enabled !== false;
  return {
    enabled,
    color: enabled ? 'var(--success)' : 'var(--text-dim)',
    icon: enabled ? '✓' : '○',
    label: enabled ? 'Ativo' : 'Inativo'
  };
};

/**
 * Obtém cor de status do doctor check
 * @param {string} status - Status do check ('ok', 'warning', 'error')
 * @returns {string} - Cor CSS
 */
export const getDoctorStatusColor = (status) => {
  const statusMap = {
    ok: 'var(--success)',
    warning: 'var(--warning)',
    error: 'var(--error)',
    info: 'var(--info)'
  };
  return statusMap[status] || 'var(--text-dim)';
};

/**
 * Obtém ícone de status do doctor check
 * @param {string} status - Status do check
 * @returns {string} - Emoji do ícone
 */
export const getDoctorStatusIcon = (status) => {
  const iconMap = {
    ok: '✓',
    warning: '⚠',
    error: '✗',
    info: 'ℹ'
  };
  return iconMap[status] || '○';
};

/**
 * Formata nome de arquivo para exibição
 * @param {string} filename - Nome do arquivo
 * @param {number} maxLength - Tamanho máximo (padrão: 30)
 * @returns {string} - Nome formatado (truncado se necessário)
 */
export const formatFilename = (filename, maxLength = 30) => {
  const name = String(filename || '').trim();
  if (name.length <= maxLength) return name;
  
  const ext = name.split('.').pop();
  const nameWithoutExt = name.slice(0, -(ext.length + 1));
  const truncated = nameWithoutExt.slice(0, maxLength - ext.length - 4);
  
  return `${truncated}...${ext}`;
};
