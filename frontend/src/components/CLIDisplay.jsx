import React from 'react';

const CLIDisplay = ({ payload, loadingTick, onOpenArtifact, styles }) => {
  const status = String(payload?.status || '').toLowerCase();
  const borderColor =
    status === 'success' ? 'var(--green)' : status === 'error' ? 'var(--red)' : 'var(--border)';
  const titleIcon =
    status === 'success' ? '✅' : status === 'error' ? '❌' : '⏳';
  const attempt = Number(payload?.attempt) || 1;
  const cmd = String(payload?.command_executed || payload?.command || '').trim();
  const stdout = String(payload?.stdout || '').trim();
  const stderr = String(payload?.stderr || '').trim();
  const visual = String(payload?.visual_state_summary || '').trim();
  const cursor = status === 'running' && loadingTick % 2 === 0 ? '▌' : '';
  const artifacts = Array.isArray(payload?.artifacts) ? payload.artifacts : [];
  const dots = status === 'running' ? '.'.repeat((loadingTick % 4) + 1) : '';
  const startedAtMs = Number(payload?.started_at_ms) || 0;
  const timeoutS = Number(payload?.timeout_s) || 0;
  const returnMs = Number(payload?.return_ms) || 0;
  const elapsedMs =
    status === 'running'
      ? Math.max(0, Date.now() - (startedAtMs || Date.now()))
      : Math.max(0, returnMs);

  const fmtTime = (ms) => {
    const total = Math.max(0, Math.floor(Number(ms || 0) / 1000));
    const m = String(Math.floor(total / 60)).padStart(2, '0');
    const s = String(total % 60).padStart(2, '0');
    return `${m}:${s}`;
  };

  const ratio = timeoutS ? Math.min(1, elapsedMs / (timeoutS * 1000)) : null;
  const pct = ratio === null ? (loadingTick % 20) / 20 : ratio;
  const barColor =
    ratio === null
      ? 'rgba(212,212,212,0.35)'
      : ratio < 0.7
        ? 'var(--green)'
        : ratio < 0.9
          ? '#f6c177'
          : 'var(--red)';

  return (
    <div
      style={{
        background: '#1e1e1e',
        border: `1px solid ${borderColor}`,
        borderRadius: '10px',
        padding: '10px 12px',
        fontFamily: 'JetBrains Mono, Consolas, var(--mono)',
        fontSize: '12px',
        color: '#d4d4d4',
        boxShadow: '0 6px 24px rgba(0,0,0,0.35)',
        maxWidth: '100%',
        overflowX: 'auto'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
        <div style={{ fontSize: '12px', color: 'rgba(212,212,212,0.75)' }}>
          {titleIcon} ExternalSoftwareSkill • tentativa {attempt}
        </div>
      </div>
      <div style={{ color: 'var(--green)', whiteSpace: 'pre-wrap' }}>
        {'> '}
        {cmd}
        {cursor}
      </div>
      {status === 'running' ? (
        <>
          <div style={{ marginTop: '8px', color: 'rgba(212,212,212,0.75)', whiteSpace: 'pre-wrap' }}>
            Processando no Sistema{dots}
          </div>
          <div style={{ marginTop: '6px', color: 'rgba(212,212,212,0.75)' }}>
            Tempo: {fmtTime(elapsedMs)}{timeoutS ? ` / ${fmtTime(timeoutS * 1000)}` : ''}
          </div>
          <div
            style={{
              marginTop: '6px',
              height: '6px',
              width: '100%',
              background: 'rgba(255,255,255,0.08)',
              borderRadius: '999px',
              overflow: 'hidden'
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${Math.max(2, Math.min(100, Math.floor(pct * 100)))}%`,
                background: barColor,
                transition: 'width 250ms linear'
              }}
            />
          </div>
        </>
      ) : null}
      {stdout ? (
        <div style={{ marginTop: '10px', whiteSpace: 'pre-wrap', color: '#d4d4d4' }}>
          {stdout}
        </div>
      ) : null}
      {stderr ? (
        <div style={{ marginTop: '10px', whiteSpace: 'pre-wrap', color: 'var(--red)' }}>
          {stderr}
        </div>
      ) : null}
      {visual ? (
        <div style={{ marginTop: '10px', whiteSpace: 'pre-wrap', color: 'rgba(212,212,212,0.75)' }}>
          {visual}
        </div>
      ) : null}
      {artifacts.length ? (
        <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {artifacts.map((a) => {
            const name = String(a?.name || '').trim();
            const ext = name.split('.').pop()?.toLowerCase() || '';
            const isImage = ['png', 'jpg', 'jpeg', 'webp'].includes(ext);
            const label = isImage ? '🖼️ Ver Diagrama' : '📂 Abrir Arquivo';
            return (
              <button
                key={String(a?.id || a?.url || name || Math.random())}
                style={{
                  ...styles.settingsSecondaryButton,
                  background: 'transparent',
                  border: `1px solid ${borderColor}`,
                  color: '#d4d4d4'
                }}
                onClick={() => onOpenArtifact(a)}
              >
                {label}{name ? ` — ${name}` : ''}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
};

export default CLIDisplay;
