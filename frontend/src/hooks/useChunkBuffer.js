import { useCallback, useEffect, useRef } from 'react';

export default function useChunkBuffer({ setMessages }) {
  const bufferRef = useRef('');
  const flushHandleRef = useRef(null);
  const flushHandleKindRef = useRef('');

  const flush = useCallback(() => {
    const buffered = bufferRef.current;
    if (!buffered) return;
    bufferRef.current = '';
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last && last.role === 'assistant' && last.streaming) {
        next[next.length - 1] = { ...last, content: `${last.content}${buffered}` };
        return next;
      }
      next.push({
        role: 'assistant',
        content: buffered,
        streaming: true,
        id: `chunk-${Date.now()}-${Math.random().toString(16).slice(2)}`
      });
      return next;
    });
  }, [setMessages]);

  const scheduleFlush = useCallback(() => {
    if (flushHandleRef.current) return;
    const raf = typeof window !== 'undefined' ? window.requestAnimationFrame : null;
    if (raf) {
      flushHandleKindRef.current = 'raf';
      flushHandleRef.current = raf(() => {
        flushHandleRef.current = null;
        flushHandleKindRef.current = '';
        flush();
      });
      return;
    }
    flushHandleKindRef.current = 'timeout';
    flushHandleRef.current = setTimeout(() => {
      flushHandleRef.current = null;
      flushHandleKindRef.current = '';
      flush();
    }, 16);
  }, [flush]);

  const appendChunk = useCallback((chunkText) => {
    const txt = String(chunkText || '');
    if (!txt) return;
    bufferRef.current = `${bufferRef.current}${txt}`;
    scheduleFlush();
  }, [scheduleFlush]);

  const hasBuffered = useCallback(() => Boolean(bufferRef.current), []);

  useEffect(() => {
    return () => {
      const h = flushHandleRef.current;
      const k = flushHandleKindRef.current;
      flushHandleRef.current = null;
      flushHandleKindRef.current = '';
      if (!h) return;
      if (k === 'raf' && typeof window !== 'undefined' && window.cancelAnimationFrame) {
        try {
          window.cancelAnimationFrame(h);
        } catch {}
        return;
      }
      if (k === 'timeout') {
        try {
          clearTimeout(h);
        } catch {}
      }
    };
  }, []);

  return { appendChunk, flush, hasBuffered };
}

