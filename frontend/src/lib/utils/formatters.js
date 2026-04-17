/**
 * 📅 Formatters - Funções de formatação de datas, bytes, duração, etc.
 */

/**
 * Parse de timestamp UTC no formato SQLite
 * @param {string} raw - Timestamp no formato YYYY-MM-DD HH:MM:SS
 * @returns {Date|null} - Data parseada ou null se inválido
 */
export const parseSqliteTimestampUtc = (raw) => {
  const s = String(raw || '').trim();
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?/);
  if (!m) return null;
  const year = Number(m[1]);
  const month = Number(m[2]);
  const day = Number(m[3]);
  const hour = Number(m[4]);
  const minute = Number(m[5]);
  const second = Number(m[6] || '0');
  if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day)) return null;
  return new Date(Date.UTC(year, month - 1, day, hour, minute, second));
};

/**
 * Formata data/hora de forma compacta
 * @param {string|Date} value - Valor a ser formatado
 * @returns {string} - String formatada ou vazia se inválido
 */
export const formatCompactDateTime = (value) => {
  const d =
    value && typeof value === 'string' && /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}/.test(value)
      ? parseSqliteTimestampUtc(value)
      : value
        ? new Date(value)
        : null;
  if (!d || Number.isNaN(d.getTime())) return '';
  return d.toLocaleString(undefined, { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  });
};

/**
 * Extrai timestamp de uma mensagem (vários formatos possíveis)
 * @param {Object} message - Objeto de mensagem
 * @returns {string} - Timestamp extraído ou vazio
 */
export const getMessageTimestamp = (message) => 
  message?.created_at || message?.createdAt || message?.timestamp || message?.time || '';

/**
 * Formata bytes em formato legível (KB, MB, GB)
 * @param {number} bytes - Número de bytes
 * @param {number} decimals - Casas decimais (padrão: 2)
 * @returns {string} - String formatada (ex: "1.50 MB")
 */
export const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Formata duração em milissegundos para formato legível
 * @param {number} ms - Milissegundos
 * @returns {string} - String formatada (ex: "1m 30s", "45s")
 */
export const formatDuration = (ms) => {
  if (ms < 1000) return `${ms}ms`;
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
};

/**
 * Formata número para formato com separadores
 * @param {number} num - Número a formatar
 * @param {string} locale - Locale (padrão: 'pt-BR')
 * @returns {string} - Número formatado
 */
export const formatNumber = (num, locale = 'pt-BR') => {
  return new Intl.NumberFormat(locale).format(num);
};

/**
 * Formata percentual
 * @param {number} value - Valor (0-1 ou 0-100)
 * @param {boolean} isDecimal - Se true, valor está entre 0-1 (padrão: false)
 * @param {number} decimals - Casas decimais (padrão: 1)
 * @returns {string} - Percentual formatado (ex: "75.5%")
 */
export const formatPercentage = (value, isDecimal = false, decimals = 1) => {
  const percent = isDecimal ? value * 100 : value;
  return `${percent.toFixed(decimals)}%`;
};
