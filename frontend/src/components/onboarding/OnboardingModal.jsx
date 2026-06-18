import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const LANGUAGES = [
  { id: 'pt', label: 'Português', flag: '🇧🇷' },
  { id: 'en', label: 'English', flag: '🇺🇸' },
  { id: 'es', label: 'Español', flag: '🇪🇸' },
  { id: 'fr', label: 'Français', flag: '🇫🇷' },
  { id: 'de', label: 'Deutsch', flag: '🇩🇪' },
  { id: 'ru', label: 'Русский', flag: '🇷🇺' },
  { id: 'ar', label: 'العربية', flag: '🇸🇦' },
  { id: 'zh', label: '中文', flag: '🇨🇳' },
  { id: 'sw', label: 'Kiswahili', flag: '🇰🇪' },
  { id: 'zu', label: 'isiZulu', flag: '🇿🇦' }
];

const FREE_PROVIDERS = [
  { id: 'gemini', name: 'Google Gemini', url: 'https://aistudio.google.com/apikey', models: 'Gemini 2.0 Flash, Gemini 1.5 Pro' },
  { id: 'groq', name: 'Groq', url: 'https://console.groq.com/keys', models: 'Llama 3, Mixtral' },
  { id: 'openrouter', name: 'OpenRouter', url: 'https://openrouter.ai/keys', models: 'Free: Llama, Mistral, Nous...' }
];

const PAID_PROVIDERS = [
  { id: 'openai', name: 'OpenAI', url: 'https://platform.openai.com/api-keys', models: 'GPT-4o, GPT-4o-mini' },
  { id: 'anthropic', name: 'Anthropic', url: 'https://console.anthropic.com/settings/keys', models: 'Claude 3.5, Claude 3' }
];

const AGE_RANGE_KEYS = [
  'age_range_under_18', 'age_range_18_24', 'age_range_25_34',
  'age_range_35_44', 'age_range_45_54', 'age_range_55_64',
  'age_range_65_plus', 'age_range_prefer_not'
];

const GOAL_KEYS = [
  'goal_learning', 'goal_software', 'goal_personal_projects',
  'goal_work', 'goal_research', 'goal_marketing',
  'goal_creativity', 'goal_other'
];

const TOTAL_STEPS = 4;

const S = {
  overlay: {
    position: 'fixed', inset: 0,
    background: 'rgba(0,0,0,0.65)',
    backdropFilter: 'blur(6px)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 9999, padding: '20px'
  },
  modal: {
    width: '96vw', maxWidth: '1200px', 
    height: '92vh', maxHeight: '900px',
    borderRadius: '16px',
    border: '1px solid rgba(255,255,255,0.08)',
    background: 'var(--bg2)',
    boxShadow: '0 24px 80px rgba(0,0,0,0.5)',
    display: 'flex', flexDirection: 'column',
    overflow: 'hidden'
  },
  header: {
    padding: '16px 28px 0 28px',
    display: 'flex', justifyContent: 'space-between', alignItems: 'center'
  },
  title: {
    fontSize: '18px', fontWeight: 700,
    color: 'var(--text-bright)',
    fontFamily: 'var(--sans)'
  },
  closeBtn: {
    background: 'transparent', border: 'none',
    color: 'var(--text-dim)', fontSize: '22px',
    cursor: 'pointer', padding: '4px 8px',
    borderRadius: '6px', transition: 'color 0.15s'
  },
  body: {
    flex: 1, padding: '12px 28px 4px 28px',
    overflowY: 'auto', fontSize: '13px',
    color: 'var(--text)', fontFamily: 'var(--sans)',
    lineHeight: 1.5
  },
  footer: {
    padding: '12px 28px 20px 28px',
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    gap: '12px'
  },
  progressBar: {
    display: 'flex', gap: '8px', alignItems: 'center',
    marginBottom: '20px'
  },
  progressDot: (active) => ({
    height: '4px', flex: 1, borderRadius: '999px',
    background: active ? 'var(--accent)' : 'rgba(255,255,255,0.08)',
    transition: 'background 0.3s'
  }),
  btnPrimary: {
    background: 'var(--accent)', border: 'none',
    borderRadius: '8px', padding: '10px 24px',
    color: 'var(--bg)', fontSize: '13px', fontWeight: 600,
    fontFamily: 'var(--mono)', cursor: 'pointer',
    transition: 'opacity 0.15s', minWidth: '100px'
  },
  btnSecondary: {
    background: 'transparent',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '8px', padding: '10px 24px',
    color: 'var(--text)', fontSize: '13px',
    fontFamily: 'var(--mono)', cursor: 'pointer',
    transition: 'all 0.15s', minWidth: '100px'
  },
  langGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
    gap: '10px', marginTop: '14px'
  },
  langCard: (active) => ({
    display: 'flex', alignItems: 'center', gap: '10px',
    padding: '12px 14px', borderRadius: '10px',
    border: active ? '2px solid var(--accent)' : '1px solid rgba(255,255,255,0.08)',
    background: active ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.02)',
    cursor: 'pointer', transition: 'all 0.15s',
    fontSize: '14px', fontFamily: 'var(--sans)',
    color: active ? 'var(--accent)' : 'var(--text)',
    fontWeight: active ? 600 : 400
  }),
  langFlag: { fontSize: '20px', lineHeight: 1 },
  sectionLabel: {
    fontSize: '11px', fontWeight: 600, letterSpacing: '1px',
    textTransform: 'uppercase', color: 'var(--text-dim)',
    fontFamily: 'var(--mono)', marginBottom: '10px', marginTop: '20px'
  },
  providerGrid: {
    display: 'grid', gap: '10px',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))'
  },
  providerCard: {
    display: 'flex', flexDirection: 'column', gap: '10px',
    padding: '12px 16px', borderRadius: '10px',
    border: '1px solid rgba(255,255,255,0.08)',
    background: 'rgba(255,255,255,0.02)',
    transition: 'border-color 0.15s'
  },
  providerHeader: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    gap: '10px'
  },
  providerInfo: {
    display: 'flex', flexDirection: 'column', gap: '2px', minWidth: 0
  },
  providerName: {
    fontSize: '13px', fontWeight: 600, color: 'var(--text-bright)',
    fontFamily: 'var(--sans)'
  },
  providerModels: {
    fontSize: '11px', color: 'var(--text-dim)',
    fontFamily: 'var(--mono)', whiteSpace: 'nowrap',
    overflow: 'hidden', textOverflow: 'ellipsis'
  },
  freeBadge: {
    fontSize: '10px', fontWeight: 700, letterSpacing: '0.5px',
    padding: '3px 8px', borderRadius: '999px',
    background: 'rgba(74, 222, 128, 0.12)',
    color: 'var(--green)', border: '1px solid rgba(74, 222, 128, 0.25)',
    whiteSpace: 'nowrap'
  },
  getLinkBtn: {
    display: 'inline-flex', alignItems: 'center', gap: '6px',
    padding: '6px 12px', borderRadius: '6px',
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.12)',
    color: 'var(--accent)', fontSize: '12px', fontWeight: 500,
    fontFamily: 'var(--mono)', cursor: 'pointer',
    textDecoration: 'none', transition: 'all 0.15s',
    whiteSpace: 'nowrap'
  },
  keyInputWrapper: {
    display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap'
  },
  testBtn: {
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '6px', padding: '6px 12px',
    color: 'var(--text)', fontSize: '12px', fontWeight: 600,
    fontFamily: 'var(--mono)', cursor: 'pointer',
    transition: 'all 0.15s'
  },
  keyInput: {
    flex: 1, minWidth: '160px', background: 'var(--bg3)',
    border: '1px solid rgba(255,255,255,0.10)',
    borderRadius: '6px', padding: '6px 10px',
    fontSize: '12px', color: 'var(--text-bright)',
    fontFamily: 'var(--mono)', outline: 'none',
    transition: 'border-color 0.15s'
  },
  saveBtn: {
    background: 'var(--accent)', border: 'none',
    borderRadius: '6px', padding: '6px 12px',
    color: 'var(--bg)', fontSize: '12px', fontWeight: 600,
    fontFamily: 'var(--mono)', cursor: 'pointer',
    transition: 'opacity 0.15s'
  },
  savedBadge: {
    fontSize: '11px', fontWeight: 600, color: 'var(--green)',
    fontFamily: 'var(--sans)', padding: '6px 10px',
    background: 'rgba(74, 222, 128, 0.1)', borderRadius: '6px',
    border: '1px solid rgba(74, 222, 128, 0.2)'
  },
  fieldGroup: { display: 'grid', gap: '6px', marginBottom: '14px' },
  fieldLabel: {
    fontSize: '12px', fontWeight: 500, color: 'var(--text)',
    fontFamily: 'var(--mono)'
  },
  input: {
    width: '100%', boxSizing: 'border-box', background: 'var(--bg3)',
    border: '1px solid rgba(255,255,255,0.10)',
    borderRadius: '10px', padding: '12px 16px',
    fontSize: '14px', color: 'var(--text-bright)',
    fontFamily: 'var(--sans)', outline: 'none',
    transition: 'border-color 0.15s'
  },
  select: {
    width: '100%', background: 'var(--bg3)',
    border: '1px solid rgba(255,255,255,0.10)',
    borderRadius: '10px', padding: '12px 16px',
    fontSize: '13px', color: 'var(--text-bright)',
    fontFamily: 'var(--sans)', outline: 'none',
    cursor: 'pointer', appearance: 'auto'
  },
  privacyNote: {
    display: 'flex', alignItems: 'flex-start', gap: '10px',
    padding: '12px 16px', borderRadius: '10px',
    background: 'rgba(74, 158, 255, 0.06)',
    border: '1px solid rgba(74, 158, 255, 0.15)',
    fontSize: '12px', color: 'var(--text-dim)',
    fontFamily: 'var(--sans)', lineHeight: 1.5,
    marginTop: '10px'
  },
  configNote: {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '10px 16px', borderRadius: '10px',
    background: 'rgba(245,166,35,0.06)',
    border: '1px solid rgba(245,166,35,0.15)',
    fontSize: '13px', color: 'var(--text-dim)',
    fontFamily: 'var(--sans)', lineHeight: 1.4,
    marginTop: '20px'
  },
  tipGrid: {
    display: 'grid', gap: '12px',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))'
  },
  tipCard: {
    padding: '14px 18px', borderRadius: '10px',
    border: '1px solid rgba(255,255,255,0.06)',
    background: 'rgba(255,255,255,0.02)',
    transition: 'border-color 0.15s'
  },
  tipTitle: {
    fontWeight: 600, fontSize: '14px', color: 'var(--accent)',
    fontFamily: 'var(--sans)', marginBottom: '6px'
  },
  tipDesc: {
    fontSize: '13px', color: 'var(--text-dim)',
    fontFamily: 'var(--sans)', lineHeight: 1.5
  },
  error: {
    background: 'rgba(248, 113, 113, 0.12)',
    border: '1px solid rgba(248, 113, 113, 0.4)',
    borderRadius: '10px', padding: '12px 16px',
    color: 'var(--text)', fontFamily: 'var(--sans)',
    fontSize: '13px', marginBottom: '12px'
  }
};

export function OnboardingModal({
  show,
  styles,
  theme,
  setTheme,
  saveLanguageSettings,
  getAuthHeaders,
  setSoulMarkdown,
  setCenterView,
  startNewConversationWithPrompt,
  onClose
}) {
  const { t, i18n } = useTranslation();
  const [step, setStep] = useState(0);
  const [error, setError] = useState('');
  const [soulDraft, setSoulDraft] = useState({ name: '', age_range: '', goals: '' });
  const [soulSaving, setSoulSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  
  const [apiKeys, setApiKeys] = useState({});
  const [keySavedStatus, setKeySavedStatus] = useState({});
  const [keySaving, setKeySaving] = useState({});
  const [keyTesting, setKeyTesting] = useState({});
  const [keyTestingStatus, setKeyTestingStatus] = useState({});
  const [keyConfigured, setKeyConfigured] = useState({});

  useEffect(() => {
    if (!show) return;
    setStep(0);
    setError('');
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    fetch('/api/soul', { headers })
      .then((r) => r.json())
      .then((d) => {
        setSoulDraft({
          name: d?.data?.name || '',
          age_range: d?.data?.age_range || '',
          goals: d?.data?.goals || ''
        });
      })
      .catch(() => {});
    fetch('/api/settings/llm/keys', { headers })
      .then(r => r.json().catch(() => ({})))
      .then(d => {
        const configured = {};
        (d?.keys || []).forEach(k => {
          if (k.provider) configured[k.provider] = true;
        });
        setKeyConfigured(configured);
      })
      .catch(() => {});
  }, [show, getAuthHeaders]);

  const saveSoulDraft = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return false;
    setSoulSaving(true);
    setError('');
    try {
      const currentRes = await fetch('/api/soul', { headers });
      const currentJson = await currentRes.json().catch(() => ({}));
      const base = (currentJson?.data && typeof currentJson.data === 'object') ? currentJson.data : {};
      const next = {
        ...base,
        name: String(soulDraft?.name || '').trim(),
        age_range: String(soulDraft?.age_range || '').trim(),
        goals: String(soulDraft?.goals || '').trim()
      };
      const res = await fetch('/api/soul', {
        method: 'PUT',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: next })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || 'Failed to save soul.');
      setSoulMarkdown(json?.markdown || '');
      return true;
    } catch (e) {
      setError(t('soul_save_error'));
      return false;
    } finally {
      setSoulSaving(false);
    }
  };

  const completeOnboarding = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      setActionLoading(true);
      const res = await fetch('/api/onboarding/complete', { method: 'POST', headers });
      await res.json().catch(() => ({}));
      try { localStorage.setItem('open_slap_onboarding_hide_v1', '1'); } catch {}
    } catch {
    } finally {
      setActionLoading(false);
    }
  };

  const handleTestApiKey = async (providerId) => {
    const key = apiKeys[providerId];
    if (!key || !key.trim()) return;

    setKeyTesting(prev => ({ ...prev, [providerId]: true }));
    setKeyTestingStatus(prev => ({ ...prev, [providerId]: 'testing' }));
    setError('');

    try {
      const headers = getAuthHeaders();
      const res = await fetch('/api/settings/llm/keys/test', {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: providerId, api_key: key.trim() })
      });
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.detail || 'Failed to test key');
      
      if (data.ok) {
        setKeyTestingStatus(prev => ({ ...prev, [providerId]: 'valid' }));
      } else {
        setKeyTestingStatus(prev => ({ ...prev, [providerId]: 'invalid' }));
        setError(`${providerId.toUpperCase()}: ${data.error || 'Invalid API Key'}`);
      }
    } catch (err) {
      setKeyTestingStatus(prev => ({ ...prev, [providerId]: 'invalid' }));
      setError(`Error testing ${providerId} key: ${err.message}`);
    } finally {
      setKeyTesting(prev => ({ ...prev, [providerId]: false }));
    }
  };

  const handleSaveApiKey = async (providerId) => {
    const key = apiKeys[providerId];
    if (!key || !key.trim()) return;

    setKeySaving(prev => ({ ...prev, [providerId]: true }));
    setError('');

    try {
      const headers = getAuthHeaders();
      const res = await fetch('/api/settings/llm/keys', {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: providerId, api_key: key.trim() })
      });
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.detail || 'Failed to save key');
      
      setKeySavedStatus(prev => ({ ...prev, [providerId]: true }));
      setKeyConfigured(prev => ({ ...prev, [providerId]: true }));
      setApiKeys(prev => ({ ...prev, [providerId]: '' }));
      
      setTimeout(() => {
        setKeySavedStatus(prev => ({ ...prev, [providerId]: false }));
      }, 3000);
      
    } catch (err) {
      setError(`Error saving ${providerId} key: ${err.message}`);
    } finally {
      setKeySaving(prev => ({ ...prev, [providerId]: false }));
    }
  };

  const handleNext = async () => {
    if (step === 0) {
      try { await saveLanguageSettings(i18n.language); } catch {}
    }
    if (step === 2) {
      const ok = await saveSoulDraft();
      if (!ok) return;
    }
    if (step >= TOTAL_STEPS - 1) return;
    setStep((s) => s + 1);
  };

  const handleBack = () => {
    setStep((s) => Math.max(0, s - 1));
  };

  const handleStartFirstTask = async () => {
    await completeOnboarding();
    onClose();
    startNewConversationWithPrompt(
      t('start_new_project'),
      { forceExpertId: 'general', kind: 'task' }
    );
  };

  const handleFinish = async () => {
    await completeOnboarding();
    onClose();
  };

  if (!show) return null;

  const isLastStep = step === TOTAL_STEPS - 1;

  return (
    <div style={S.overlay} onClick={onClose}>
      <div style={S.modal} onClick={e => e.stopPropagation()}>

        <div style={S.header}>
          <div style={S.title}>{t('onboarding_title')}</div>
          <button style={S.closeBtn} onClick={onClose} title={t('close')}>×</button>
        </div>

        <div style={S.body}>
          <div style={S.progressBar}>
            {Array.from({ length: TOTAL_STEPS }, (_, i) => (
              <div key={i} style={S.progressDot(i <= step)} />
            ))}
          </div>

          {error ? <div style={S.error}>{error}</div> : null}

          {step === 0 && (
            <div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-bright)', marginBottom: '6px' }}>
                {t('language')}
              </div>
              <div style={{ fontSize: '14px', color: 'var(--text-dim)', marginBottom: '14px' }}>
                {t('select_language_desc')}
              </div>
              <div style={S.langGrid}>
                {LANGUAGES.map((opt) => {
                  const active = i18n.language === opt.id;
                  return (
                    <button
                      key={opt.id}
                      style={S.langCard(active)}
                      onClick={() => {
                        i18n.changeLanguage(opt.id);
                        saveLanguageSettings(opt.id);
                      }}
                    >
                      <span style={S.langFlag}>{opt.flag}</span>
                      <span>{opt.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {step === 1 && (
            <div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-bright)', marginBottom: '6px' }}>
                {t('onboarding_providers_title')}
              </div>
              <div style={{ fontSize: '14px', color: 'var(--text-dim)', marginBottom: '10px', lineHeight: 1.5 }}>
                {t('onboarding_providers_desc')}
              </div>

              <div style={S.sectionLabel}>
                <span style={{ color: 'var(--green)' }}>●</span>&ensp;{t('onboarding_free_providers')}
              </div>
              <div style={S.providerGrid}>
                {FREE_PROVIDERS.map((p) => (
                  <div key={p.id} style={S.providerCard}>
                    <div style={S.providerHeader}>
                      <div style={S.providerInfo}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={S.providerName}>{p.name}</span>
                          <span style={S.freeBadge}>FREE</span>
                          {keyConfigured[p.id] ? <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--green)', display: 'inline-block', flexShrink: 0 }} title={t('key_set_and_active')} /> : null}
                        </div>
                        <div style={S.providerModels}>{p.models}</div>
                      </div>
                      <a href={p.url} target="_blank" rel="noopener noreferrer" style={S.getLinkBtn}>
                        {t('onboarding_get_free_key')}&nbsp;↗
                      </a>
                    </div>
                    <div style={S.keyInputWrapper}>
                      <input 
                        type="password" 
                        placeholder={t('paste_api_key_here')}
                        style={S.keyInput} 
                        value={apiKeys[p.id] || ''} 
                        onChange={(e) => {
                          setApiKeys({...apiKeys, [p.id]: e.target.value});
                          setKeyTestingStatus(prev => ({ ...prev, [p.id]: 'idle' }));
                          setKeySavedStatus(prev => ({ ...prev, [p.id]: false }));
                        }} 
                      />
                      {apiKeys[p.id] && apiKeys[p.id].trim() && (
                        <button
                          style={{
                            ...S.testBtn,
                            opacity: keyTesting[p.id] ? 0.5 : 1,
                            borderColor: keyTestingStatus[p.id] === 'valid' ? '#22c55e' :
                                         keyTestingStatus[p.id] === 'invalid' ? '#ef4444' : 'rgba(255,255,255,0.12)',
                            color: keyTestingStatus[p.id] === 'valid' ? '#22c55e' :
                                   keyTestingStatus[p.id] === 'invalid' ? '#ef4444' : 'var(--text)'
                          }}
                          onClick={() => handleTestApiKey(p.id)}
                          disabled={keyTesting[p.id]}
                        >
                          {keyTesting[p.id] ? '...' :
                           keyTestingStatus[p.id] === 'valid' ? t('valid') :
                           keyTestingStatus[p.id] === 'invalid' ? t('invalid') :
                           t('test')}
                        </button>
                      )}
                      {keySavedStatus[p.id] ? (
                        <span style={S.savedBadge}>✓ {t('saved')}</span>
                      ) : (
                        <button 
                          style={{...S.saveBtn, opacity: (!apiKeys[p.id] || keySaving[p.id]) ? 0.5 : 1}} 
                          onClick={() => handleSaveApiKey(p.id)}
                          disabled={!apiKeys[p.id] || keySaving[p.id]}
                        >
                          {keySaving[p.id] ? '...' : t('save')}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div style={S.sectionLabel}>{t('onboarding_paid_providers')}</div>
              <div style={S.providerGrid}>
                {PAID_PROVIDERS.map((p) => (
                  <div key={p.id} style={S.providerCard}>
                    <div style={S.providerHeader}>
                      <div style={S.providerInfo}>
                        <span style={S.providerName}>{p.name}{keyConfigured[p.id] ? <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--green)', display: 'inline-block', marginLeft: '8px', verticalAlign: 'middle' }} title={t('key_set_and_active')} /> : null}</span>
                        <div style={S.providerModels}>{p.models}</div>
                      </div>
                      <a href={p.url} target="_blank" rel="noopener noreferrer" style={S.getLinkBtn}>
                        {t('onboarding_get_free_key')}&nbsp;↗
                      </a>
                    </div>
                    <div style={S.keyInputWrapper}>
                      <input 
                        type="password" 
                        placeholder={t('paste_api_key_here')}
                        style={S.keyInput} 
                        value={apiKeys[p.id] || ''} 
                        onChange={(e) => {
                          setApiKeys({...apiKeys, [p.id]: e.target.value});
                          setKeyTestingStatus(prev => ({ ...prev, [p.id]: 'idle' }));
                          setKeySavedStatus(prev => ({ ...prev, [p.id]: false }));
                        }} 
                      />
                      {apiKeys[p.id] && apiKeys[p.id].trim() && (
                        <button
                          style={{
                            ...S.testBtn,
                            opacity: keyTesting[p.id] ? 0.5 : 1,
                            borderColor: keyTestingStatus[p.id] === 'valid' ? '#22c55e' :
                                         keyTestingStatus[p.id] === 'invalid' ? '#ef4444' : 'rgba(255,255,255,0.12)',
                            color: keyTestingStatus[p.id] === 'valid' ? '#22c55e' :
                                   keyTestingStatus[p.id] === 'invalid' ? '#ef4444' : 'var(--text)'
                          }}
                          onClick={() => handleTestApiKey(p.id)}
                          disabled={keyTesting[p.id]}
                        >
                          {keyTesting[p.id] ? '...' :
                           keyTestingStatus[p.id] === 'valid' ? t('valid') :
                           keyTestingStatus[p.id] === 'invalid' ? t('invalid') :
                           t('test')}
                        </button>
                      )}
                      {keySavedStatus[p.id] ? (
                        <span style={S.savedBadge}>✓ {t('saved')}</span>
                      ) : (
                        <button 
                          style={{...S.saveBtn, opacity: (!apiKeys[p.id] || keySaving[p.id]) ? 0.5 : 1}} 
                          onClick={() => handleSaveApiKey(p.id)}
                          disabled={!apiKeys[p.id] || keySaving[p.id]}
                        >
                          {keySaving[p.id] ? '...' : t('save')}
                        </button>
                      )}
                    </div>
                  </div>
                ))}

                <div style={S.providerCard}>
                  <div style={S.providerHeader}>
                    <div style={S.providerInfo}>
                      <span style={S.providerName}>Ollama</span>
                      <div style={S.providerModels}>{t('onboarding_local_llm_desc')}</div>
                    </div>
                    <a
                      href="https://ollama.com/download"
                      target="_blank"
                      rel="noopener noreferrer"
                      style={S.getLinkBtn}
                    >
                      {t('onboarding_download')}&nbsp;↗
                    </a>
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                    {t('auto_detected_ollama')}
                  </div>
                </div>
              </div>

              <div style={S.configNote}>
                <span style={{ fontSize: '18px' }}>💡</span>
                <span>{t('onboarding_configure_later')}</span>
              </div>
            </div>
          )}

          {step === 2 && (
            <div style={{ maxWidth: '600px', margin: '0 auto' }}>
              <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-bright)', marginBottom: '18px' }}>
                {t('onboarding_profile_question')}
              </div>

              <div style={S.fieldGroup}>
                <div style={S.fieldLabel}>{t('name_label')}</div>
                <input
                  style={S.input}
                  value={soulDraft?.name || ''}
                  onChange={(e) => setSoulDraft((prev) => ({ ...(prev || {}), name: e.target.value }))}
                  placeholder={t('your_name_or_nickname')}
                  autoFocus
                />
              </div>

              <div style={S.fieldGroup}>
                <div style={S.fieldLabel}>{t('age_range_label')}</div>
                <select
                  style={S.select}
                  value={soulDraft?.age_range || ''}
                  onChange={(e) => setSoulDraft((prev) => ({ ...(prev || {}), age_range: e.target.value }))}
                >
                  <option value="">{t('select')}</option>
                  {AGE_RANGE_KEYS.map((key) => (
                    <option key={key} value={t(key)}>{t(key)}</option>
                  ))}
                </select>
              </div>

              <div style={S.fieldGroup}>
                <div style={S.fieldLabel}>{t('goals_label')}</div>
                <select
                  style={S.select}
                  value={soulDraft?.goals || ''}
                  onChange={(e) => setSoulDraft((prev) => ({ ...(prev || {}), goals: e.target.value }))}
                >
                  <option value="">{t('select')}</option>
                  {GOAL_KEYS.map((key) => (
                    <option key={key} value={t(key)}>{t(key)}</option>
                  ))}
                </select>
              </div>

              <div style={S.privacyNote}>
                <span style={{ fontSize: '18px', flexShrink: 0 }}>🔒</span>
                <span>{t('onboarding_privacy_note')}</span>
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-bright)', marginBottom: '16px' }}>
                {t('onboarding_how_to_start')}
              </div>
              <div style={S.tipGrid}>
                {[
                  [t('onboarding_step_task_title'), t('onboarding_step_task_desc')],
                  [t('onboarding_step_skills_title'), t('onboarding_step_skills_desc')],
                  [t('onboarding_step_connectors_title'), t('onboarding_step_connectors_desc')]
                ].map(([title, desc]) => (
                  <div key={title} style={S.tipCard}>
                    <div style={S.tipTitle}>{title}</div>
                    <div style={S.tipDesc}>{desc}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div style={S.footer}>
          <div>
            {step > 0 ? (
              <button
                style={S.btnSecondary}
                onClick={handleBack}
                disabled={actionLoading}
              >
                ← {t('onboarding_back')}
              </button>
            ) : <span />}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            {isLastStep ? (
              <>
                <button
                  style={S.btnSecondary}
                  onClick={handleFinish}
                  disabled={actionLoading}
                >
                  {t('close')}
                </button>
                <button
                  style={S.btnPrimary}
                  onClick={handleStartFirstTask}
                  disabled={actionLoading}
                >
                  {t('onboarding_start_first_task')}
                </button>
              </>
            ) : (
              <button
                style={{ ...S.btnPrimary, opacity: soulSaving ? 0.6 : 1 }}
                onClick={handleNext}
                disabled={soulSaving || actionLoading}
              >
                {soulSaving
                  ? t('saving')
                  : t('onboarding_next')
                } →
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
