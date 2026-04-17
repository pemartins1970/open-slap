import { useState, useEffect } from 'react';

export function OnboardingModal({
  show,
  styles,
  t,
  lang,
  theme,
  setLang,
  setTheme,
  saveLanguageSettings,
  getAuthHeaders,
  setSoulMarkdown,
  setCenterView,
  startNewConversationWithPrompt,
  buildStartProjectPrompt,
  onClose
}) {
  const [step, setStep] = useState(0);
  const [error, setError] = useState('');
  const [soulDraft, setSoulDraft] = useState({ name: '', age_range: '', goals: '' });
  const [soulSaving, setSoulSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

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
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || 'Error completing onboarding.');
      try { localStorage.setItem('open_slap_onboarding_hide_v1', '1'); } catch {}
    } catch {
    } finally {
      setActionLoading(false);
    }
  };

  const handleNext = async () => {
    if (step === 0) {
      try { await saveLanguageSettings(lang); } catch {}
    }
    if (step === 3) {
      const ok = await saveSoulDraft();
      if (!ok) return;
    }
    setStep((s) => Math.min(5, (Number(s) || 0) + 1));
  };

  const handleBack = () => {
    setStep((s) => Math.max(0, (Number(s) || 0) - 1));
  };

  const handleStartFirstTask = () => {
    onClose();
    startNewConversationWithPrompt(
      lang === 'pt' ? 'Quero iniciar um novo projeto.' : 'I want to start a new project.',
      { internalPrompt: buildStartProjectPrompt(), forceExpertId: 'general', kind: 'task' }
    );
  };

  const handleOpenLLMSettings = () => {
    onClose();
    setCenterView('settings');
  };

  const handleDontShowAgain = async () => {
    await completeOnboarding();
    onClose();
  };

  if (!show) return null;

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={{ ...styles.modal, maxWidth: '720px', minHeight: '480px' }} onClick={e => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <div style={styles.modalTitle}>{t('onboarding_title')}</div>
          <button style={styles.iconButton} onClick={onClose}>×</button>
        </div>
        <div style={styles.modalBody}>
          {/* Progress bar */}
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginBottom: '14px' }}>
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                style={{
                  height: '8px',
                  flex: 1,
                  borderRadius: '999px',
                  background: i === step ? 'var(--accent)' : 'rgba(255,255,255,0.10)'
                }}
              />
            ))}
          </div>

          {error ? <div style={styles.settingsError}>{error}</div> : null}

          {/* Step 0: Language */}
          {step === 0 ? (
            <div style={{ display: 'grid', gap: '16px' }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', lineHeight: 1.7 }}>
                {t('language')}
              </div>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                {[
                  { id: 'en', label: 'English' },
                  { id: 'pt', label: 'Português' },
                  { id: 'es', label: 'Español' },
                  { id: 'ar', label: 'العربية' },
                  { id: 'zh', label: '中文' }
                ].map((opt) => {
                  const active = String(lang) === opt.id;
                  return (
                    <button
                      key={opt.id}
                      style={{
                        ...styles.settingsSecondaryButton,
                        borderColor: active ? 'var(--accent)' : 'rgba(255,255,255,0.15)',
                        color: active ? 'var(--accent)' : 'var(--text)'
                      }}
                      onClick={() => {
                        setLang(opt.id);
                        saveLanguageSettings(opt.id);
                      }}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : null}

          {/* Step 1: Theme */}
          {step === 1 ? (
            <div style={{ display: 'grid', gap: '16px' }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', lineHeight: 1.7 }}>
                {t('onboarding_theme_prompt')}
              </div>
              <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                {[
                  { id: 'light', label: t('theme_light'), preview: ['#f5f5f5','#ffffff','#d97706'] },
                  { id: 'deep-space', label: 'Deep Space', preview: ['#0b1220','#0e1626','#22d3ee'] },
                  { id: 'midnight', label: 'Midnight', preview: ['#0a0a0a','#111111','#60a5fa'] }
                ].map((th) => {
                  const isActive = String(theme) === th.id;
                  return (
                    <button
                      key={th.id}
                      style={{
                        ...styles.smallIconButton,
                        width: '100%',
                        padding: '16px',
                        borderRadius: '12px',
                        border: isActive ? '1px solid var(--accent)' : '1px solid rgba(255,255,255,0.15)',
                        background: 'rgba(255,255,255,0.04)'
                      }}
                      onClick={() => {
                        setTheme(th.id);
                        try { localStorage.setItem('open_slap_theme_v1', th.id); } catch {}
                      }}
                    >
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', justifyContent: 'space-between' }}>
                        {th.preview.map((c, i) => (
                          <div key={i} style={{ width: 16, height: 16, borderRadius: '50%', background: c, border: '1px solid rgba(255,255,255,0.15)' }} />
                        ))}
                        <div style={{ fontSize: '12px', fontFamily: 'var(--mono)', color: th.preview[2], fontWeight: isActive ? 600 : 400, whiteSpace: 'nowrap' }}>
                          {th.label}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : null}

          {/* Step 2: Intro */}
          {step === 2 ? (
            <div style={{ display: 'grid', gap: '20px' }}>
              <div style={{ fontSize: '15px', color: 'var(--text)', lineHeight: 1.8 }}>
                {t('onboarding_intro')}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-dim)', lineHeight: 1.7 }}>
                {t('onboarding_welcome_hint')}
              </div>
            </div>
          ) : null}

          {/* Step 3: Profile */}
          {step === 3 ? (
            <div style={{ display: 'grid', gap: '20px' }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', lineHeight: 1.7 }}>
                {t('onboarding_profile_intro')}
              </div>
              <div style={{ display: 'grid', gap: '16px' }}>
                <div style={{ display: 'grid', gap: '6px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--mono)' }}>{t('name_label')}</div>
                  <input
                    style={styles.settingsInput}
                    value={soulDraft?.name || ''}
                    onChange={(e) => setSoulDraft((prev) => ({ ...(prev || {}), name: e.target.value }))}
                  />
                </div>
                <div style={{ display: 'grid', gap: '6px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--mono)' }}>{t('age_range_label')}</div>
                  <input
                    style={styles.settingsInput}
                    value={soulDraft?.age_range || ''}
                    onChange={(e) => setSoulDraft((prev) => ({ ...(prev || {}), age_range: e.target.value }))}
                    placeholder={t('age_range_placeholder')}
                  />
                </div>
                <div style={{ display: 'grid', gap: '6px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--mono)' }}>{t('goals_label')}</div>
                  <textarea
                    style={{ ...styles.settingsTextarea, minHeight: '120px' }}
                    value={soulDraft?.goals || ''}
                    onChange={(e) => setSoulDraft((prev) => ({ ...(prev || {}), goals: e.target.value }))}
                    placeholder={t('goals_placeholder')}
                  />
                </div>
              </div>
            </div>
          ) : null}

          {/* Step 4: LLM Settings */}
          {step === 4 ? (
            <div style={{ display: 'grid', gap: '20px' }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', lineHeight: 1.7 }}>
                {t('onboarding_llm_intro')}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-dim)', lineHeight: 1.6 }}>
                {t('onboarding_llm_hint')}
              </div>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button
                  style={styles.settingsSecondaryButton}
                  onClick={handleOpenLLMSettings}
                >
                  {t('onboarding_open_llm_settings')}
                </button>
              </div>
            </div>
          ) : null}

          {/* Step 5: How to Start */}
          {step === 5 ? (
            <div style={{ display: 'grid', gap: '20px' }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', lineHeight: 1.7 }}>
                {t('onboarding_how_to_start')}
              </div>
              {[
                [t('onboarding_step_task_title'), t('onboarding_step_task_desc')],
                [t('onboarding_step_skills_title'), t('onboarding_step_skills_desc')],
                [t('onboarding_step_connectors_title'), t('onboarding_step_connectors_desc')]
              ].map(([title, desc]) => (
                <div key={title} style={{ marginBottom: '12px' }}>
                  <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--accent)', fontFamily: 'var(--sans)', marginBottom: '6px' }}>{title}</div>
                  <div style={{ fontSize: '13px', color: 'var(--text-dim)', fontFamily: 'var(--sans)', lineHeight: 1.6 }}>{desc}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        {/* Actions */}
        <div style={{ ...styles.commandActions, justifyContent: 'flex-end' }}>
          <button
            style={styles.settingsSecondaryButton}
            onClick={onClose}
            disabled={actionLoading}
          >
            {t('onboarding_explore')}
          </button>
          <button
            style={styles.settingsSecondaryButton}
            onClick={onClose}
            disabled={actionLoading}
          >
            {t('onboarding_skip')}
          </button>
          <button
            style={styles.settingsSecondaryButton}
            onClick={handleDontShowAgain}
            disabled={actionLoading}
          >
            {t('onboarding_dont_show')}
          </button>
          {step > 0 ? (
            <button
              style={styles.settingsSecondaryButton}
              onClick={handleBack}
              disabled={actionLoading}
            >
              {t('onboarding_back')}
            </button>
          ) : null}
          {step < 5 ? (
            <button
              style={styles.settingsPrimaryButton}
              onClick={handleNext}
              disabled={soulSaving || actionLoading}
            >
              {soulSaving ? t('saving') : t('onboarding_next')}
            </button>
          ) : (
            <button
              style={styles.settingsPrimaryButton}
              onClick={handleStartFirstTask}
              disabled={actionLoading}
            >
              {t('onboarding_start_first_task')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
