/**
 * 📦 Utils - Exportação centralizada de todos os utilitários
 */

// Formatters
export {
  parseSqliteTimestampUtc,
  formatCompactDateTime,
  getMessageTimestamp,
  formatBytes,
  formatDuration,
  formatNumber,
  formatPercentage
} from './formatters';

// Parsers
export {
  parseMessageBlocks,
  parsePlanTasksFromText,
  extractTaggedJsonBlocks,
  parseCommandRequestsFromContent,
  parseFileMetadata,
  parseSimpleMarkdown,
  parseQueryString
} from './parsers';

// Sorters
export {
  SKILL_SEGMENT_PREFERRED_ORDER,
  EXPERT_SEGMENT_PREFERRED_ORDER,
  SEGMENT_ORDER,
  sortByPreferredOrder,
  sortSkillsForSegment,
  sortExpertsForSegment,
  groupBySegment,
  sortConversationsByDate,
  sortAlphabetically
} from './sorters';

// Display
export {
  getBuiltinMeta,
  getSkillDisplayName,
  getSkillDisplayDescription,
  getExpertDisplayName,
  getExpertDisplayDescription,
  getDoctorLabel,
  getBootGreeting,
  getConversationTitle,
  getSkillStatus,
  getExpertStatus,
  getDoctorStatusColor,
  getDoctorStatusIcon,
  formatFilename
} from './display';

// Identifiers
export {
  getSkillSegmentId,
  getExpertSegmentId,
  getSegmentLabel,
  generateSessionId,
  generateId,
  generateSlug,
  shortenId,
  isValidUuid,
  extractIdFromPath,
  simpleHash,
  idsMatch
} from './identifiers';

// Validators
export {
  validateEmail,
  validateUrl,
  validatePhone,
  validateCPF,
  validatePassword,
  sanitizeInput,
  validateJSON,
  validateNumberRange,
  validateStringLength,
  validateNotEmpty,
  validateNotNull,
  validateHexColor,
  validateIPv4,
  validatePort
} from './validators';

// Helpers
export {
  clamp,
  debounce,
  throttle,
  deepClone,
  deepMerge,
  isObject,
  getNestedValue,
  setNestedValue,
  removeDuplicates,
  groupBy,
  range,
  sleep,
  retry,
  truncate,
  capitalize,
  toCamelCase,
  toSnakeCase,
  copyToClipboard,
  isMobile,
  isDarkMode
} from './helpers';
