/**
 * 🎣 React Utility Hooks - Hooks de utilidade para React
 */

import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Hook de debounce de valor
 * @param {*} value - Valor a debounce
 * @param {number} delay - Delay em ms
 * @returns {*} - Valor debounced
 */
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Hook para obter valor anterior
 * @param {*} value - Valor atual
 * @returns {*} - Valor anterior
 */
export const usePrevious = (value) => {
  const ref = useRef();
  
  useEffect(() => {
    ref.current = value;
  }, [value]);
  
  return ref.current;
};

/**
 * Hook para detectar primeiro render
 * @returns {boolean} - true se é o primeiro render
 */
export const useFirstRender = () => {
  const isFirst = useRef(true);

  if (isFirst.current) {
    isFirst.current = false;
    return true;
  }

  return false;
};

/**
 * Hook para executar callback quando componente monta
 * @param {Function} callback - Callback a executar
 */
export const useMount = (callback) => {
  useEffect(() => {
    callback();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
};

/**
 * Hook para executar callback quando componente desmonta
 * @param {Function} callback - Callback a executar
 */
export const useUnmount = (callback) => {
  useEffect(() => {
    return callback;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
};

/**
 * Hook para toggle booleano
 * @param {boolean} initialValue - Valor inicial
 * @returns {[boolean, Function, Function, Function]} - [value, toggle, setTrue, setFalse]
 */
export const useToggle = (initialValue = false) => {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => {
    setValue(v => !v);
  }, []);

  const setTrue = useCallback(() => {
    setValue(true);
  }, []);

  const setFalse = useCallback(() => {
    setValue(false);
  }, []);

  return [value, toggle, setTrue, setFalse];
};

/**
 * Hook para contador
 * @param {number} initialValue - Valor inicial
 * @returns {[number, Function, Function, Function, Function]} - [count, increment, decrement, reset, set]
 */
export const useCounter = (initialValue = 0) => {
  const [count, setCount] = useState(initialValue);

  const increment = useCallback(() => {
    setCount(c => c + 1);
  }, []);

  const decrement = useCallback(() => {
    setCount(c => c - 1);
  }, []);

  const reset = useCallback(() => {
    setCount(initialValue);
  }, [initialValue]);

  return [count, increment, decrement, reset, setCount];
};

/**
 * Hook para gerenciar array
 * @param {Array} initialValue - Array inicial
 * @returns {Object} - {array, set, push, filter, update, remove, clear}
 */
export const useArray = (initialValue = []) => {
  const [array, setArray] = useState(initialValue);

  const push = useCallback((element) => {
    setArray(arr => [...arr, element]);
  }, []);

  const filter = useCallback((callback) => {
    setArray(arr => arr.filter(callback));
  }, []);

  const update = useCallback((index, newElement) => {
    setArray(arr => [
      ...arr.slice(0, index),
      newElement,
      ...arr.slice(index + 1)
    ]);
  }, []);

  const remove = useCallback((index) => {
    setArray(arr => [...arr.slice(0, index), ...arr.slice(index + 1)]);
  }, []);

  const clear = useCallback(() => {
    setArray([]);
  }, []);

  return { array, set: setArray, push, filter, update, remove, clear };
};

/**
 * Hook para timeout
 * @returns {Function} - Função para criar timeout que se auto-limpa
 */
export const useTimeout = () => {
  const timeoutRef = useRef(null);

  const clearTimer = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const createTimeout = useCallback((callback, delay) => {
    clearTimer();
    timeoutRef.current = setTimeout(callback, delay);
  }, [clearTimer]);

  useEffect(() => {
    return clearTimer;
  }, [clearTimer]);

  return createTimeout;
};

/**
 * Hook para interval
 * @param {Function} callback - Callback a executar
 * @param {number} delay - Delay em ms (null para pausar)
 */
export const useInterval = (callback, delay) => {
  const savedCallback = useRef();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay === null) return;

    const tick = () => savedCallback.current();
    const id = setInterval(tick, delay);

    return () => clearInterval(id);
  }, [delay]);
};

/**
 * Hook para detectar clicks fora de elemento
 * @param {React.RefObject} ref - Ref do elemento
 * @param {Function} handler - Handler quando clica fora
 */
export const useClickOutside = (ref, handler) => {
  useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) {
        return;
      }
      handler(event);
    };

    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);

    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
};

/**
 * Hook para copiar para clipboard
 * @returns {[Function, boolean]} - [copy, copied]
 */
export const useCopyToClipboard = () => {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef(null);

  const copy = useCallback(async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setCopied(false), 2000);
      
      return true;
    } catch {
      setCopied(false);
      return false;
    }
  }, []);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return [copy, copied];
};

/**
 * Hook para window size
 * @returns {Object} - {width, height}
 */
export const useWindowSize = () => {
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowSize;
};

/**
 * Hook para scroll position
 * @returns {Object} - {x, y}
 */
export const useScrollPosition = () => {
  const [scrollPosition, setScrollPosition] = useState({
    x: window.pageXOffset,
    y: window.pageYOffset,
  });

  useEffect(() => {
    const handleScroll = () => {
      setScrollPosition({
        x: window.pageXOffset,
        y: window.pageYOffset,
      });
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return scrollPosition;
};
