/**
 * 🛠️ Helpers - Funções auxiliares gerais
 */

/**
 * Clamp - Limita valor entre mínimo e máximo
 * @param {number} value - Valor a limitar
 * @param {number} min - Mínimo
 * @param {number} max - Máximo
 * @returns {number} - Valor limitado
 */
export const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

/**
 * Debounce - Atrasa execução de função
 * @param {Function} func - Função a debounce
 * @param {number} wait - Tempo de espera em ms
 * @returns {Function} - Função debounced
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Throttle - Limita taxa de execução de função
 * @param {Function} func - Função a throttle
 * @param {number} limit - Tempo mínimo entre execuções em ms
 * @returns {Function} - Função throttled
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Deep clone de objeto (via JSON)
 * @param {*} obj - Objeto a clonar
 * @returns {*} - Clone do objeto
 */
export const deepClone = (obj) => {
  try {
    return JSON.parse(JSON.stringify(obj));
  } catch {
    return obj;
  }
};

/**
 * Deep merge de objetos
 * @param {Object} target - Objeto alvo
 * @param {Object} source - Objeto fonte
 * @returns {Object} - Objeto merged
 */
export const deepMerge = (target, source) => {
  const output = { ...target };
  
  if (isObject(target) && isObject(source)) {
    Object.keys(source).forEach(key => {
      if (isObject(source[key])) {
        if (!(key in target)) {
          Object.assign(output, { [key]: source[key] });
        } else {
          output[key] = deepMerge(target[key], source[key]);
        }
      } else {
        Object.assign(output, { [key]: source[key] });
      }
    });
  }
  
  return output;
};

/**
 * Verifica se valor é objeto
 * @param {*} item - Item a verificar
 * @returns {boolean} - true se é objeto
 */
export const isObject = (item) => {
  return item && typeof item === 'object' && !Array.isArray(item);
};

/**
 * Obtém valor aninhado de objeto via path
 * @param {Object} obj - Objeto
 * @param {string} path - Path (ex: 'user.profile.name')
 * @param {*} defaultValue - Valor padrão se não encontrado
 * @returns {*} - Valor encontrado ou defaultValue
 */
export const getNestedValue = (obj, path, defaultValue = undefined) => {
  const keys = String(path || '').split('.');
  let result = obj;
  
  for (const key of keys) {
    if (result && typeof result === 'object' && key in result) {
      result = result[key];
    } else {
      return defaultValue;
    }
  }
  
  return result;
};

/**
 * Define valor aninhado em objeto via path
 * @param {Object} obj - Objeto
 * @param {string} path - Path (ex: 'user.profile.name')
 * @param {*} value - Valor a definir
 * @returns {Object} - Objeto modificado
 */
export const setNestedValue = (obj, path, value) => {
  const keys = String(path || '').split('.');
  const lastKey = keys.pop();
  
  let current = obj;
  for (const key of keys) {
    if (!(key in current)) {
      current[key] = {};
    }
    current = current[key];
  }
  
  current[lastKey] = value;
  return obj;
};

/**
 * Remove duplicatas de array
 * @param {Array} arr - Array com possíveis duplicatas
 * @param {Function} key - Função para extrair chave única (opcional)
 * @returns {Array} - Array sem duplicatas
 */
export const removeDuplicates = (arr, key) => {
  if (!key) {
    return [...new Set(arr)];
  }
  
  const seen = new Set();
  return arr.filter(item => {
    const k = key(item);
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
};

/**
 * Agrupa array de objetos por chave
 * @param {Array} arr - Array a agrupar
 * @param {string|Function} key - Chave ou função para extrair chave
 * @returns {Object} - Objeto agrupado
 */
export const groupBy = (arr, key) => {
  const keyFunc = typeof key === 'function' ? key : (item) => item[key];
  
  return (arr || []).reduce((acc, item) => {
    const group = keyFunc(item);
    if (!acc[group]) acc[group] = [];
    acc[group].push(item);
    return acc;
  }, {});
};

/**
 * Cria range de números
 * @param {number} start - Início
 * @param {number} end - Fim (exclusive)
 * @param {number} step - Passo (padrão: 1)
 * @returns {Array} - Array de números
 */
export const range = (start, end, step = 1) => {
  const result = [];
  for (let i = start; i < end; i += step) {
    result.push(i);
  }
  return result;
};

/**
 * Pausa execução (async)
 * @param {number} ms - Milissegundos a esperar
 * @returns {Promise} - Promise que resolve após ms
 */
export const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Retry de função async com backoff exponencial
 * @param {Function} fn - Função async a executar
 * @param {number} maxRetries - Máximo de tentativas (padrão: 3)
 * @param {number} delay - Delay inicial em ms (padrão: 1000)
 * @returns {Promise} - Promise com resultado ou erro
 */
export const retry = async (fn, maxRetries = 3, delay = 1000) => {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        await sleep(delay * Math.pow(2, i)); // Exponential backoff
      }
    }
  }
  
  throw lastError;
};

/**
 * Trunca texto com ellipsis
 * @param {string} text - Texto a truncar
 * @param {number} maxLength - Tamanho máximo
 * @param {string} suffix - Sufixo (padrão: '...')
 * @returns {string} - Texto truncado
 */
export const truncate = (text, maxLength, suffix = '...') => {
  const str = String(text || '');
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - suffix.length) + suffix;
};

/**
 * Capitaliza primeira letra
 * @param {string} str - String a capitalizar
 * @returns {string} - String capitalizada
 */
export const capitalize = (str) => {
  const s = String(str || '');
  return s.charAt(0).toUpperCase() + s.slice(1);
};

/**
 * Converte para camelCase
 * @param {string} str - String a converter
 * @returns {string} - String em camelCase
 */
export const toCamelCase = (str) => {
  return String(str || '')
    .toLowerCase()
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, chr) => chr.toUpperCase());
};

/**
 * Converte para snake_case
 * @param {string} str - String a converter
 * @returns {string} - String em snake_case
 */
export const toSnakeCase = (str) => {
  return String(str || '')
    .replace(/([A-Z])/g, '_$1')
    .toLowerCase()
    .replace(/^_/, '');
};

/**
 * Copia texto para clipboard
 * @param {string} text - Texto a copiar
 * @returns {Promise<boolean>} - true se sucesso
 */
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(String(text || ''));
    return true;
  } catch {
    // Fallback para navegadores antigos
    try {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      return true;
    } catch {
      return false;
    }
  }
};

/**
 * Detecta se está em mobile
 * @returns {boolean} - true se mobile
 */
export const isMobile = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

/**
 * Detecta se está em modo escuro
 * @returns {boolean} - true se dark mode
 */
export const isDarkMode = () => {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
};
