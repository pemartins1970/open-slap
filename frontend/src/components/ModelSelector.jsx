import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

const PROVIDER_LABELS = {
  gemini: 'Gemini',
  groq: 'Groq',
  openai: 'OpenAI',
  openrouter: 'OpenRouter',
  ollama: 'Ollama',
};

const DROPDOWN_WIDTH = 320;

export default function ModelSelector({ styles, getAuthHeaders, onProviderChange, onModelChange }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [data, setData] = useState(null);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);
  const [loading, setLoading] = useState(true);
  const ref = useRef(null);

  useEffect(() => {
    const fetchModels = async () => {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      try {
        const res = await fetch('/api/models/available', { headers });
        const json = await res.json();
        setData(json);
        setSelectedProvider(json.current?.provider || null);
        setSelectedModel(json.current?.model || null);
        if (onProviderChange) onProviderChange(json.current?.provider || null);
        if (onModelChange) onModelChange(json.current?.model || null);
      } catch {
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
  }, []);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const select = useCallback((pid, mid) => {
    setSelectedProvider(pid);
    setSelectedModel(mid);
    if (onProviderChange) onProviderChange(pid);
    if (onModelChange) onModelChange(mid);
    setOpen(false);
  }, [onProviderChange, onModelChange]);

  const providerData = data?.providers || [];
  const currentProviderEntry = providerData.find(p => p.id === selectedProvider);
  const providerName = PROVIDER_LABELS[selectedProvider] || selectedProvider || '...';
  const modelName = currentProviderEntry?.models?.find(m => m.id === selectedModel)?.name || selectedModel || '...';

  const providerIcon = (available) => available
    ? <span style={{ color: 'var(--green)', marginRight: '6px', fontSize: '10px' }}>●</span>
    : <span style={{ color: 'rgba(212, 212, 212, 0.4)', marginRight: '6px', fontSize: '10px' }}>○</span>;

  return (
    <div ref={ref} style={{ position: 'relative', flexShrink: 0 }}>
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        disabled={loading}
        style={{
          background: 'rgba(255,255,255,0.06)',
          border: '1px solid var(--border)',
          borderRadius: '6px',
          padding: '4px 10px',
          color: 'var(--text)',
          fontSize: '12px',
          fontFamily: 'var(--mono)',
          cursor: 'pointer',
          whiteSpace: 'nowrap',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          opacity: loading ? 0.5 : 1,
        }}
        title={loading ? t('loading_models') : `${providerName} · ${modelName}`}
      >
        {loading ? t('loading_models') : <>{providerName} <span style={{ color: 'var(--text-dim)', fontWeight: 300 }}>·</span> {modelName}</>}
        <span style={{ fontSize: '8px', color: 'var(--text-dim)', marginLeft: '2px' }}>▾</span>
      </button>

      {open && data && (
        <div style={{
          position: 'absolute',
          bottom: '100%',
          left: '0',
          marginBottom: '6px',
          width: `${DROPDOWN_WIDTH}px`,
          maxHeight: '360px',
          overflowY: 'auto',
          background: 'var(--bg-panel)',
          border: '1px solid var(--border)',
          borderRadius: '10px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
          zIndex: 9999,
          padding: '6px 0',
        }}>
          {providerData.map((p) => {
            const available = p.available !== false;
            const isActiveProvider = p.id === selectedProvider;
            return (
              <div key={p.id}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '8px 14px 4px',
                  fontSize: '11px',
                  fontWeight: 600,
                  color: 'var(--text-dim)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  cursor: available ? 'pointer' : 'default',
                  opacity: available ? 1 : 0.5,
                }}
                  onClick={() => {
                    if (!available) return;
                    const firstModel = p.models?.[0]?.id;
                    if (firstModel) select(p.id, firstModel);
                  }}
                  title={!available ? t('provider_no_key') : undefined}
                >
                  {providerIcon(available)}
                  {p.name || p.id}
                  {!available && <span style={{ marginLeft: 'auto', fontSize: '10px', color: 'var(--text-dim)' }}>🔒</span>}
                </div>
                {p.models?.map((m) => {
                  const isActive = isActiveProvider && m.id === selectedModel;
                  return (
                    <div
                      key={m.id}
                      onClick={() => {
                        if (!available) return;
                        select(p.id, m.id);
                      }}
                      style={{
                        padding: '5px 14px 5px 32px',
                        fontSize: '13px',
                        fontFamily: 'var(--mono)',
                        cursor: available ? 'pointer' : 'default',
                        color: isActive ? 'var(--amber)' : (available ? 'var(--text)' : 'var(--text-dim)'),
                        background: isActive ? 'rgba(245,166,35,0.08)' : 'transparent',
                        opacity: available ? 1 : 0.35,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                    >
                      {isActive && <span style={{ fontSize: '12px' }}>✓</span>}
                      <span>{m.name || m.id}</span>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
