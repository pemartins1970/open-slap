import React from 'react';

export default function SystemSettingsPanel({
  styles,
  t,
  lang,
  settingsLoading,
  doctorError,
  doctorReport,
  doctorLoading,
  refreshSystemProfile,
  fetchDoctorReport,
  getDoctorLabel,
  setSettingsTab,
  systemMapLoading,
  systemMapError,
  systemMapUpdatedAt,
  systemMapText,
  fetchSystemMap,
}) {
  return (
    <>
      <div style={styles.settingsSection}>
        <div style={styles.settingsSectionTitle}>{t('doctor_diagnostics')}</div>
        {doctorError ? (
          <div style={styles.settingsError}>{doctorError}</div>
        ) : null}

        <div style={styles.doctorCard}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
              {doctorReport
                ? (doctorReport.ok ? t('doctor_all_ok') : t('doctor_some_attention'))
                : t('doctor_click_run')}
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <button
                style={styles.settingsSecondaryButton}
                onClick={() => {
                  refreshSystemProfile().finally(() => fetchDoctorReport({ silent: true }));
                }}
                disabled={settingsLoading || doctorLoading}
              >
                {t('update_profile')}
              </button>
              <button
                style={styles.settingsPrimaryButton}
                onClick={() => fetchDoctorReport({ silent: false })}
                disabled={settingsLoading || doctorLoading}
              >
                {doctorLoading ? t('running') : t('run_diagnostics')}
              </button>
            </div>
          </div>

          {doctorReport?.checks?.length ? (
            <div style={{ marginTop: '10px' }}>
              {doctorReport.checks.map((c, idx) => {
                const ok = Boolean(c.ok);
                const isLast = idx === doctorReport.checks.length - 1;
                const statusStyle = {
                  ...styles.doctorStatus,
                  borderColor: ok ? 'rgba(34, 197, 94, 0.45)' : 'rgba(248, 113, 113, 0.45)',
                  color: ok ? 'var(--green)' : 'var(--red)',
                  background: ok ? 'rgba(34, 197, 94, 0.10)' : 'rgba(248, 113, 113, 0.10)'
                };
                return (
                  <div
                    key={c.id || idx}
                    style={{ ...styles.doctorRow, ...(isLast ? styles.doctorRowLast : {}) }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={styles.doctorLabel}>{getDoctorLabel(c)}</div>
                      {c.detail ? <div style={styles.doctorDetail}>{c.detail}</div> : null}
                      {String(c.id || '') === 'system_profile' && !ok ? (
                        <div style={{ marginTop: '8px' }}>
                          <button
                            style={styles.settingsSecondaryButton}
                            onClick={() => setSettingsTab('memory')}
                          >
                            {t('doctor_view_in_memory')}
                          </button>
                        </div>
                      ) : null}
                    </div>
                    <div style={statusStyle}>{ok ? 'OK' : t('status_failed')}</div>
                  </div>
                );
              })}
            </div>
          ) : null}

          {doctorReport?.recommendations?.length ? (
            <div style={{ marginTop: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', marginBottom: '8px' }}>
                {t('recommendations')}
              </div>
              <div style={{ display: 'grid', gap: '6px' }}>
                {doctorReport.recommendations.map((r, i) => (
                  <div key={i} style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
                    {r}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <div style={{ ...styles.doctorCard, marginTop: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--sans)' }}>
              {lang === 'pt' ? 'Mapa do sistema' : 'System map'}
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <button
                style={styles.settingsSecondaryButton}
                onClick={() => fetchSystemMap({ silent: false, refresh: false })}
                disabled={settingsLoading || systemMapLoading}
              >
                {systemMapLoading ? t('loading') : (lang === 'pt' ? 'Carregar' : 'Load')}
              </button>
              <button
                style={styles.settingsPrimaryButton}
                onClick={() => fetchSystemMap({ silent: false, refresh: true })}
                disabled={settingsLoading || systemMapLoading}
              >
                {systemMapLoading ? t('running') : (lang === 'pt' ? 'Atualizar' : 'Refresh')}
              </button>
            </div>
          </div>
          {systemMapError ? (
            <div style={{ ...styles.settingsError, marginTop: '10px' }}>{systemMapError}</div>
          ) : null}
          <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
            {lang === 'pt'
              ? `Atualizado em: ${systemMapUpdatedAt || '—'}`
              : `Updated at: ${systemMapUpdatedAt || '—'}`}
          </div>
          {systemMapText ? (
            <pre style={{
              marginTop: '10px',
              padding: '12px',
              borderRadius: '10px',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.10)',
              color: 'var(--text)',
              fontFamily: 'var(--mono)',
              fontSize: '12px',
              lineHeight: 1.35,
              whiteSpace: 'pre-wrap',
              overflowX: 'auto'
            }}>
              {systemMapText}
            </pre>
          ) : null}
        </div>
      </div>
    </>
  );
}
