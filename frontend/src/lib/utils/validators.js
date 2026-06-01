/**
 * ✅ Validators - Funções de validação e sanitização
 */

/**
 * Valida se é um email válido
 * @param {string} email - Email a validar
 * @returns {boolean} - true se válido
 */
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(String(email || '').trim());
};

/**
 * Valida se é uma URL válida
 * @param {string} url - URL a validar
 * @returns {boolean} - true se válido
 */
export const validateUrl = (url) => {
  try {
    const parsed = new URL(String(url || '').trim());
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
};

/**
 * Valida se é um número de telefone válido (formato brasileiro)
 * @param {string} phone - Telefone a validar
 * @returns {boolean} - true se válido
 */
export const validatePhone = (phone) => {
  const phoneRegex = /^\+?55?\s?\(?[1-9]{2}\)?\s?9?\d{4}-?\d{4}$/;
  return phoneRegex.test(String(phone || '').trim());
};

/**
 * Valida se é um CPF válido
 * @param {string} cpf - CPF a validar
 * @returns {boolean} - true se válido
 */
export const validateCPF = (cpf) => {
  const cleaned = String(cpf || '').replace(/\D/g, '');
  
  if (cleaned.length !== 11) return false;
  if (/^(\d)\1+$/.test(cleaned)) return false; // Todos dígitos iguais
  
  // Validação dos dígitos verificadores
  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += parseInt(cleaned.charAt(i)) * (10 - i);
  }
  let digit = 11 - (sum % 11);
  if (digit >= 10) digit = 0;
  if (digit !== parseInt(cleaned.charAt(9))) return false;
  
  sum = 0;
  for (let i = 0; i < 10; i++) {
    sum += parseInt(cleaned.charAt(i)) * (11 - i);
  }
  digit = 11 - (sum % 11);
  if (digit >= 10) digit = 0;
  if (digit !== parseInt(cleaned.charAt(10))) return false;
  
  return true;
};

/**
 * Valida se senha atende requisitos mínimos
 * @param {string} password - Senha a validar
 * @param {Object} requirements - Requisitos {minLength, requireUppercase, requireNumber, requireSpecial}
 * @returns {Object} - {valid: boolean, errors: string[]}
 */
export const validatePassword = (password, requirements = {}) => {
  const {
    minLength = 8,
    requireUppercase = false,
    requireNumber = false,
    requireSpecial = false
  } = requirements;
  
  const errors = [];
  const pwd = String(password || '');
  
  if (pwd.length < minLength) {
    errors.push(`Mínimo de ${minLength} caracteres`);
  }
  
  if (requireUppercase && !/[A-Z]/.test(pwd)) {
    errors.push('Deve conter ao menos uma letra maiúscula');
  }
  
  if (requireNumber && !/\d/.test(pwd)) {
    errors.push('Deve conter ao menos um número');
  }
  
  if (requireSpecial && !/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) {
    errors.push('Deve conter ao menos um caractere especial');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
};

/**
 * Sanitiza input removendo caracteres perigosos
 * @param {string} input - Input a sanitizar
 * @param {Object} options - Opções {allowHTML, maxLength}
 * @returns {string} - Input sanitizado
 */
export const sanitizeInput = (input, options = {}) => {
  const { allowHTML = false, maxLength = 10000 } = options;
  
  let sanitized = String(input || '').trim();
  
  // Limita tamanho
  if (sanitized.length > maxLength) {
    sanitized = sanitized.slice(0, maxLength);
  }
  
  // Remove HTML se não permitido
  if (!allowHTML) {
    sanitized = sanitized
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
  
  // Remove scripts sempre
  sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  
  return sanitized;
};

/**
 * Valida se é um JSON válido
 * @param {string} jsonString - String JSON a validar
 * @returns {boolean} - true se válido
 */
export const validateJSON = (jsonString) => {
  try {
    JSON.parse(String(jsonString || ''));
    return true;
  } catch {
    return false;
  }
};

/**
 * Valida range de número
 * @param {number} value - Valor a validar
 * @param {number} min - Mínimo (inclusive)
 * @param {number} max - Máximo (inclusive)
 * @returns {boolean} - true se dentro do range
 */
export const validateNumberRange = (value, min, max) => {
  const num = Number(value);
  return Number.isFinite(num) && num >= min && num <= max;
};

/**
 * Valida se string tem tamanho permitido
 * @param {string} str - String a validar
 * @param {number} minLength - Tamanho mínimo
 * @param {number} maxLength - Tamanho máximo
 * @returns {boolean} - true se válido
 */
export const validateStringLength = (str, minLength = 0, maxLength = Infinity) => {
  const length = String(str || '').length;
  return length >= minLength && length <= maxLength;
};

/**
 * Valida se array não está vazio
 * @param {Array} arr - Array a validar
 * @returns {boolean} - true se não vazio
 */
export const validateNotEmpty = (arr) => {
  return Array.isArray(arr) && arr.length > 0;
};

/**
 * Valida se valor não é null/undefined
 * @param {*} value - Valor a validar
 * @returns {boolean} - true se não é null/undefined
 */
export const validateNotNull = (value) => {
  return value !== null && value !== undefined;
};

/**
 * Valida se é um hex color válido
 * @param {string} color - Cor a validar (#RRGGBB ou #RGB)
 * @returns {boolean} - true se válido
 */
export const validateHexColor = (color) => {
  const hexRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
  return hexRegex.test(String(color || '').trim());
};

/**
 * Valida se é um IP válido (IPv4)
 * @param {string} ip - IP a validar
 * @returns {boolean} - true se válido
 */
export const validateIPv4 = (ip) => {
  const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
  if (!ipRegex.test(String(ip || '').trim())) return false;
  
  const parts = ip.split('.');
  return parts.every(part => {
    const num = parseInt(part, 10);
    return num >= 0 && num <= 255;
  });
};

/**
 * Valida se é um port válido
 * @param {number|string} port - Porta a validar
 * @returns {boolean} - true se válido (1-65535)
 */
export const validatePort = (port) => {
  const num = parseInt(port, 10);
  return Number.isFinite(num) && num >= 1 && num <= 65535;
};
