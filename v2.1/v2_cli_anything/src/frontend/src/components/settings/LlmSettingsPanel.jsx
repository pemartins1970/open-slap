import React from 'react';

export default function LlmSettingsPanel({
  styles,
  t,
  lang,
  settingsLoading,
  llmMode,
  setLlmMode,
  llmProvider,
  setLlmProvider,
  llmModel,
  setLlmModel,
  llmBaseUrl,
  setLlmBaseUrl,
  llmApiKey,
  setLlmApiKey,
  llmHasApiKey,
  llmApiKeySource,
  llmApiKeyOpen,
  setLlmApiKeyOpen,
  llmApiKeyInputRef,
  llmProviderKeys,
  llmProviderKeysLoading,
  llmProviderKeysError,
  setActiveLlmProviderKey,
  deleteLlmProviderKey,
  saveLlmSettings,
  removeLlmApiKey,
  llmHasStoredApiKey,
  llmHasEnvApiKey,
  providerStatusList,
  providerStatusLoading,
  providerStatusError,
  loadProviderStatus,
}) {
  return (
    <>
      <div style={styles.settingsSection}>
        <div style={styles.settingsSectionTitle}>{t('llm_free_keys_title')}</div>
        <div style={styles.settingsHint}>{t('llm_free_keys_body')}</div>
        <div style={{ marginTop: '10px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            style={{ ...styles.settingsSecondaryButton, background: '#fff', color: '#000', border: '1px solid rgba(0,0,0,0.15)' }}
            onClick={() => window.open('https://aistudio.google.com/app/apikey', '_blank')}
          >
            {t('llm_free_keys_gemini')}
          </button>
          <button
            style={{ ...styles.settingsSecondaryButton, background: '#fff', color: '#000', border: '1px solid rgba(0,0,0,0.15)' }}
            onClick={() => window.open('https://console.groq.com/keys', '_blank')}
          >
            {t('llm_free_keys_groq')}
          </button>
          <button
            style={{ ...styles.settingsSecondaryButton, background: '#fff', color: '#000', border: '1px solid rgba(0,0,0,0.15)' }}
            onClick={() => window.open('https://openrouter.ai/keys', '_blank')}
          >
            {t('llm_free_keys_openrouter')}
          </button>
        </div>
      </div>

      <div style={styles.settingsSection}>
        <div style={styles.settingsSectionTitle}>{t('llm_settings_title')}</div>

        <div style={styles.settingsGrid}>
          <div style={styles.settingsField}>
            <div style={styles.settingsLabel}>{t('mode')}</div>
            <select
              style={styles.settingsInput}
              value={llmMode}
              onChange={(e) => setLlmMode(e.target.value)}
              disabled={settingsLoading}
            >
              <option value="env">{t('server_default')}</option>
              <option value="api">{t('api_cloud')}</option>
              <option value="local">{t('local_ollama')}</option>
            </select>
          </div>

          <div style={styles.settingsField}>
            <div style={styles.settingsLabel}>{t('provider')}</div>
            <select
              style={styles.settingsInput}
              value={llmProvider}
              onChange={(e) => setLlmProvider(e.target.value)}
              disabled={settingsLoading}
            >
              {llmMode === 'local' ? (
                <option value="ollama">Ollama</option>
              ) : (
                <>
                  <option value="openai">OpenAI</option>
                  <option value="groq">Groq</option>
                  <option value="gemini">Gemini</option>
                </>
              )}
            </select>
          </div>

          <div style={styles.settingsField}>
            <div style={styles.settingsLabel}>{t('model')}</div>
            <input
              style={styles.settingsInput}
              value={llmModel}
              onChange={(e) => setLlmModel(e.target.value)}
              placeholder={llmMode === 'local' ? 'ex.: llama3.2' : 'ex.: gpt-4o-mini'}
              disabled={settingsLoading}
            />
          </div>

          <div style={styles.settingsField}>
            <div style={styles.settingsLabel}>{t('base_url')}</div>
            <input
              style={styles.settingsInput}
              value={llmBaseUrl}
              onChange={(e) => setLlmBaseUrl(e.target.value)}
              placeholder={llmMode === 'local' ? 'http://localhost:11434' : 'opcional'}
              disabled={settingsLoading}
            />
          </div>

          {llmMode === 'api' ? (
            <div style={{ ...styles.settingsField, gridColumn: '1 / -1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                <div style={styles.settingsLabel}>{t('api_key')}</div>
                <button
                  style={styles.settingsSecondaryButton}
                  onClick={() => {
                    setLlmApiKeyOpen((v) => {
                      const next = !v;
                      if (!v && next) {
                        setTimeout(() => {
                          if (llmApiKeyInputRef.current) {
                            try {
                              llmApiKeyInputRef.current.focus();
                            } catch {}
                          }
                        }, 50);
                      }
                      return next;
                    });
                  }}
                  disabled={settingsLoading}
                >
                  {llmApiKeyOpen ? t('api_key_close') : (llmHasApiKey ? t('api_key_switch') : t('api_key_register'))}
                </button>
              </div>

              {llmApiKeyOpen ? (
                <input
                  ref={llmApiKeyInputRef}
                  style={styles.settingsInput}
                  value={llmApiKey}
                  onChange={(e) => setLlmApiKey(e.target.value)}
                  placeholder={t('api_key_placeholder')}
                  disabled={settingsLoading}
                />
              ) : (
                <div style={styles.settingsHint}>
                  {llmHasApiKey
                    ? (
                      llmApiKeySource === 'env'
                        ? t('llm_api_key_hint_env')
                        : t('llm_api_key_hint_saved')
                    )
                    : t('llm_api_key_hint_none')}
                </div>
              )}
              <div style={styles.settingsHint}>
                {t('llm_api_key_hint_storage')}
              </div>
              <div style={styles.settingsHint}>
                {t('llm_api_key_warning_shared')}
              </div>
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginBottom: '6px' }}>
                  {t('saved_keys_for')}: {llmProvider}
                </div>
                {llmProviderKeysError ? (
                  <div style={styles.settingsError}>{llmProviderKeysError}</div>
                ) : null}
                {llmProviderKeysLoading ? (
                  <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                    {t('loading')}
                  </div>
                ) : (
                  <div style={{ display: 'grid', gap: '6px' }}>
                    {(llmProviderKeys || []).length ? (
                      (llmProviderKeys || []).map((k) => {
                        const active = Boolean(k?.is_active);
                        return (
                          <div
                            key={k?.id}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: '10px',
                              padding: '10px',
                              borderRadius: '10px',
                              border: '1px solid rgba(255,255,255,0.10)',
                              background: 'rgba(255,255,255,0.04)'
                            }}
                          >
                            <div style={{ minWidth: 0 }}>
                              <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--mono)' }}>
                                #{k?.id}{active ? ` · ${t('active_key')}` : ''}
                              </div>
                              <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginTop: '4px' }}>
                                {(k?.created_at || '').toString()}
                              </div>
                            </div>
                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                              {!active ? (
                                <button
                                  style={styles.settingsSecondaryButton}
                                  onClick={() => setActiveLlmProviderKey(llmProvider, k?.id)}
                                  disabled={settingsLoading}
                                >
                                  {t('activate')}
                                </button>
                              ) : null}
                              <button
                                style={styles.settingsSecondaryButton}
                                onClick={() => deleteLlmProviderKey(llmProvider, k?.id)}
                                disabled={settingsLoading}
                              >
                                {t('remove')}
                              </button>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                        {t('no_saved_keys')}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>

        <div style={styles.settingsActions}>
          {llmMode === 'api' ? (
            <button
              style={styles.settingsSecondaryButton}
              onClick={() => {
                removeLlmApiKey();
              }}
              disabled={settingsLoading || (!llmHasStoredApiKey && llmHasEnvApiKey)}
            >
              {(!llmHasStoredApiKey && llmHasEnvApiKey) ? t('llm_key_from_env') : t('llm_remove_key')}
            </button>
          ) : null}
          <button
            style={styles.settingsPrimaryButton}
            onClick={saveLlmSettings}
            disabled={settingsLoading}
          >
            {settingsLoading ? t('llm_saving') : t('save_llm')}
          </button>
        </div>
      </div>

      <div style={styles.settingsSection}>
        <div style={styles.settingsSectionTitle}>{t('configured_providers')}</div>
        {providerStatusError ? (
          <div style={styles.settingsError}>{providerStatusError}</div>
        ) : null}
        <div style={{ display: 'grid', gap: '6px', marginTop: '8px' }}>
          {(providerStatusList || []).map((p) => {
            const online = Boolean(p.online);
            const enabled = Boolean(p.enabled);
            const dotColor = enabled ? (online ? 'var(--green)' : 'var(--red)') : 'rgba(212,212,212,0.35)';
            return (
              <div
                key={p.id || p.name}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 0',
                  borderBottom: '1px solid var(--border)',
                  fontSize: '13px',
                  fontFamily: 'var(--mono)'
                }}
              >
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: dotColor, flexShrink: 0 }} />
                <span>{p.name || p.id}</span>
                <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: enabled ? 'rgba(245,166,35,0.12)' : 'rgba(212,212,212,0.10)', color: enabled ? 'var(--amber)' : 'var(--text-dim)' }}>
                  {enabled ? t('provider_enabled') : t('provider_disabled')}
                </span>
                <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: 'rgba(127,119,221,0.12)', color: '#7F77DD' }}>
                  {t('provider_keys')}: {Number(p.keys_count) || 0}
                </span>
                <span style={{ marginLeft: 'auto', color: 'var(--text-dim)', fontSize: '11px' }}>
                  {p.model || ''}
                </span>
              </div>
            );
          })}
          {!providerStatusLoading && (!providerStatusList || providerStatusList.length === 0) ? (
            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
              {t('no_provider_status')}
            </div>
          ) : null}
        </div>
        <div style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            style={styles.settingsSecondaryButton}
            onClick={loadProviderStatus}
            disabled={providerStatusLoading}
          >
            {providerStatusLoading ? 'Testando...' : 'Testar conexão'}
          </button>
        </div>
      </div>
    </>
  );
}
