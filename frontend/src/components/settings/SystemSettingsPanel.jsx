import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function SystemSettingsPanel({
  styles,
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
  planAutoApproveAll,
  onPlanAutoApproveAllChange,
}) {
  const { t } = useTranslation();
  const [expandedChecks, setExpandedChecks] = useState({});

  const toggleCheck = (id) => {
    setExpandedChecks(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const renderCheckDetail = (check) => {
    const id = String(check?.id || '');
    if (!expandedChecks[id]) return null;

    let content = null;
    if (id === 'system_profile') {
      const md = doctorReport?.system_profile_markdown || doctorReport?.system_profile_summary || '';
      content = md ? (
        <pre style={{
          marginTop: '8px',
          padding: '10px',
          borderRadius: '8px',
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          color: 'var(--text)',
          fontFamily: 'var(--mono)',
          fontSize: '11px',
          lineHeight: 1.4,
          whiteSpace: 'pre-wrap',
          maxHeight: '400px',
          overflowY: 'auto'
        }}>
          {md}
        </pre>
      ) : null;
    } else if (id === 'llm_configured' && doctorReport?.llm_settings) {
      const s = doctorReport.llm_settings;
      content = (
        <div style={{ marginTop: '8px', fontSize: '12px', fontFamily: 'var(--mono)', color: 'var(--text-dim)' }}>
          <div>{t('provider')}: {s.provider || '—'}</div>
          <div>{t('model')}: {s.model || '—'}</div>
        </div>
      );
    } else if (id === 'api_reachable' && doctorReport?.connectivity?.length) {
      content = (
        <div style={{ marginTop: '8px', display: 'grid', gap: '4px' }}>
          {doctorReport.connectivity.map((conn, i) => (
            <div key={i} style={{
              fontSize: '11px',
              fontFamily: 'var(--mono)',
              color: conn.ok ? 'var(--green)' : 'var(--red)',
              padding: '6px 8px',
              borderRadius: '6px',
              background: 'rgba(255,255,255,0.03)'
            }}>
              {conn.provider}: {conn.ok
                ? `OK (${conn.latency_ms}ms)`
                : `${t('connectivity_failed')} ${conn.error || t('connectivity_no_response')}`}
            </div>
          ))}
        </div>
      );
    } else {
      content = (
        <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
          {check.detail || '—'}
        </div>
      );
    }
    return <div style={{ marginTop: '4px' }}>{content}</div>;
  };

  return (
    <>
      <div style={styles.settingsSection}>
        <div style={styles.settingsSectionTitle}>{t('workflow')}</div>
        <div style={{
          background: 'var(--bg-panel)',
          borderRadius: '10px',
          padding: '12px 16px',
          border: '1px solid var(--border)',
          display: 'grid',
          gap: '14px'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '13px', color: 'var(--text)', fontFamily: 'var(--sans)', marginBottom: '2px' }}>
                {t('auto_approve_all_plans')}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--sans)' }}>
                {t('auto_approve_all_plans_desc')}
              </div>
            </div>
            <label style={{ position: 'relative', display: 'inline-block', width: '40px', height: '22px', cursor: 'pointer' }}>
              <input type="checkbox" style={{ opacity: 0, width: 0, height: 0 }}
                checked={planAutoApproveAll}
                onChange={(e) => onPlanAutoApproveAllChange(e.target.checked)}
              />
              <span style={{
                position: 'absolute', inset: 0, borderRadius: '22px',
                background: planAutoApproveAll ? 'var(--amber)' : 'rgba(255,255,255,0.15)',
                transition: '0.2s'
              }}>
                <span style={{
                  position: 'absolute', top: '2px', left: planAutoApproveAll ? '20px' : '2px',
                  width: '18px', height: '18px', borderRadius: '50%', background: 'white',
                  transition: '0.2s'
                }} />
              </span>
            </label>
          </div>
        </div>
      </div>

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
                const expanded = Boolean(expandedChecks[String(c.id || '')]);
                const statusStyle = {
                  ...styles.doctorStatus,
                  borderColor: ok ? 'rgba(34, 197, 94, 0.45)' : 'rgba(248, 113, 113, 0.45)',
                  color: ok ? 'var(--green)' : 'var(--red)',
                  background: ok ? 'rgba(34, 197, 94, 0.10)' : 'rgba(248, 113, 113, 0.10)'
                };
                return (
                  <div
                    key={c.id || idx}
                    style={{
                      ...styles.doctorRow,
                      ...(isLast ? styles.doctorRowLast : {}),
                      cursor: 'pointer',
                      userSelect: 'none'
                    }}
                    onClick={() => toggleCheck(c.id)}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '10px', color: 'var(--text-dim)', transition: 'transform 0.15s', transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>
                          ▶
                        </span>
                        <div style={styles.doctorLabel}>{getDoctorLabel(c)}</div>
                      </div>
                      {expanded ? renderCheckDetail(c) : (c.detail ? <div style={{ ...styles.doctorDetail, marginLeft: '18px' }}>{c.detail}</div> : null)}
                      {String(c.id || '') === 'system_profile' && !ok ? (
                        <div style={{ marginTop: '8px' }}>
                          <button
                            style={styles.settingsSecondaryButton}
                            onClick={(e) => { e.stopPropagation(); setSettingsTab('memory'); }}
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
              {t('system_map')}
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <button
                style={styles.settingsSecondaryButton}
                onClick={() => fetchSystemMap({ silent: false, refresh: false })}
                disabled={settingsLoading || systemMapLoading}
              >
                {systemMapLoading ? t('loading') : t('load')}
              </button>
              <button
                style={styles.settingsPrimaryButton}
                onClick={() => fetchSystemMap({ silent: false, refresh: true })}
                disabled={settingsLoading || systemMapLoading}
              >
                {systemMapLoading ? t('running') : t('refresh')}
              </button>
            </div>
          </div>
          {systemMapError ? (
            <div style={{ ...styles.settingsError, marginTop: '10px' }}>{systemMapError}</div>
          ) : null}
          <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
            {t('updated_at')} {systemMapUpdatedAt || '—'}
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
