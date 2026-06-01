/**
 * 💾 useLocalStorage - Hook para gerenciar localStorage com sync
 */

import { useState, useEffect, useCallback } from 'react';

/**
 * Hook para gerenciar estado sincronizado com localStorage
 * @param {string} key - Chave do localStorage
 * @param {*} initialValue - Valor inicial se não existir no localStorage
 * @returns {[*, Function]} - [valor, setValue]
 */
export const useLocalStorage = (key, initialValue) => {
  // State para armazenar o valor
  const [storedValue, setStoredValue] = useState(() => {
    try {
      // Tenta obter do localStorage
      const item = window.localStorage.getItem(key);
      // Parse do JSON armazenado ou retorna initialValue
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Erro ao ler localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  // Retorna função wrapped para persistir o novo valor no localStorage
  const setValue = useCallback((value) => {
    try {
      // Permite value ser função como useState
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      
      // Salva no state
      setStoredValue(valueToStore);
      
      // Salva no localStorage
      if (valueToStore === undefined) {
        window.localStorage.removeItem(key);
      } else {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.warn(`Erro ao salvar localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  // Escuta mudanças em outras tabs/windows
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === key && e.newValue !== null) {
        try {
          setStoredValue(JSON.parse(e.newValue));
        } catch (error) {
          console.warn(`Erro ao sync localStorage key "${key}":`, error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key]);

  return [storedValue, setValue];
};

/**
 * Hook para múltiplas chaves de localStorage
 * @param {Object} keysWithDefaults - Objeto {key: defaultValue}
 * @returns {Object} - Objeto com {values, setters, clearAll}
 */
export const useMultipleLocalStorage = (keysWithDefaults) => {
  const entries = Object.entries(keysWithDefaults);
  const values = {};
  const setters = {};

  entries.forEach(([key, defaultValue]) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [value, setValue] = useLocalStorage(key, defaultValue);
    values[key] = value;
    setters[key] = setValue;
  });

  const clearAll = useCallback(() => {
    entries.forEach(([key]) => {
      window.localStorage.removeItem(key);
    });
  }, [entries]);

  return { values, setters, clearAll };
};

/**
 * Hook para objeto completo no localStorage
 * @param {string} key - Chave do localStorage
 * @param {Object} initialObject - Objeto inicial
 * @returns {[Object, Function, Function]} - [object, updateField, resetObject]
 */
export const useLocalStorageObject = (key, initialObject = {}) => {
  const [obj, setObj] = useLocalStorage(key, initialObject);

  const updateField = useCallback((field, value) => {
    setObj(prev => ({
      ...prev,
      [field]: value
    }));
  }, [setObj]);

  const resetObject = useCallback(() => {
    setObj(initialObject);
  }, [setObj, initialObject]);

  return [obj, updateField, resetObject];
};

export default useLocalStorage;
