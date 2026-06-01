/**
 * 🎣 Hooks - Exportação centralizada de todos os hooks customizados
 */

// Hooks existentes
export { default as useAuth } from './useAuth';
export { default as useChatSocket } from './useChatSocket';
export { default as useChunkBuffer } from './useChunkBuffer';

// Hooks novos - Utilitários
export { useLocalStorage, useMultipleLocalStorage, useLocalStorageObject } from './useLocalStorage';
export {
  useDebounce,
  usePrevious,
  useFirstRender,
  useMount,
  useUnmount,
  useToggle,
  useCounter,
  useArray,
  useTimeout,
  useInterval,
  useClickOutside,
  useCopyToClipboard,
  useWindowSize,
  useScrollPosition
} from './useReactUtils';
export { useModals, useModalWithData, useAppModals } from './useModals';

// Hooks novos - Funcionalidades
export { useConversations } from './useConversations';
export { useMessages } from './useMessages';
export { useSettings } from './useSettings';
export { useLLMConfig } from './useLLMConfig';
export { useSoul } from './useSoul';
export { useSkills } from './useSkills';
export { useDoctor } from './useDoctor';
