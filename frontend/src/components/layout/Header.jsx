import React from 'react';
import { useTranslation } from 'react-i18next';

const RPM_LIMITS = { gemini: 15, groq: 30, openrouter: 10, openai: 3, ollama: 0 };

const rpMeter = (recentRpm, activeProvider, runtimeLlmLabel, isMobile) => {
  const provider = (activeProvider?.provider || runtimeLlmLabel || '').toLowerCase();
  const limit = Object.entries(RPM_LIMITS).find(([k]) => provider.includes(k))?.[1] ?? 15;
  if (limit === 0) return null;
  const pct = Math.min(1, recentRpm / limit);
  const color = pct < 0.5 ? 'var(--green)' : pct < 0.8 ? 'var(--amber)' : '#e55';
  const label = `${recentRpm}/${limit} req/min`;
  return (
    <div title={label} style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'default', margin: '0 8px' }}>
      <div style={{ width: '52px', height: '4px', background: 'var(--bg-panel)', borderRadius: '2px', overflow: 'hidden', border: '1px solid var(--border)' }}>
        <div style={{ width: `${pct * 100}%`, height: '100%', background: color, transition: 'width 0.4s ease, background-color 0.4s ease', borderRadius: '2px' }} />
      </div>
      {!isMobile && (
        <span style={{ fontFamily: 'var(--mono)', fontSize: '10px', color, minWidth: '32px', transition: 'color 0.4s ease' }}>
          {recentRpm}/{limit}
        </span>
      )}
    </div>
  );
};

const Header = ({
  styles,
  user,
  leftSidebarCollapsed,
  onToggleLeftSidebar,
  isMobile,
  onSettingsClick,
  runtimeLlmLabel,
  connected,
  onLogout,
  // monolith extensions
  mobileSidebarOpen,
  onToggleMobileSidebar,
  recentRpm = 0,
  activeProvider,
  savedLlmProvider,
  doctorReport,
  onDoctorClick
}) => {
  const { t } = useTranslation();

  return (
    <div style={styles.header}>
      <div style={styles.headerTitle} className="slap-header-title">{t('app_title')}</div>
      <div style={styles.headerRight}>
        <button
          className="slap-sidebar-toggle"
          style={{
            background: 'none',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            padding: '6px 10px',
            color: 'var(--text)',
            cursor: 'pointer',
            fontSize: '16px',
            display: isMobile ? 'inline-flex' : 'none',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          onClick={() => onToggleMobileSidebar ? onToggleMobileSidebar() : onToggleLeftSidebar()}
          title="Menu"
        >
          {mobileSidebarOpen ? '✕' : '☰'}
        </button>
        <div style={{ ...styles.connectionStatus, display: isMobile ? 'none' : styles.connectionStatus.display }} className="slap-conn-status">
          <div style={styles.connectionDot}></div>
          {connected ? (() => {
            const configured = savedLlmProvider?.toLowerCase().trim() || '';
            const ap = activeProvider?.provider || '';
            const primary = configured || ap;
            const rl = runtimeLlmLabel || '';
            const rlProvider = rl.split(' — ')[0].trim().toLowerCase();
            const showRuntime = rl && primary && rlProvider !== primary.toLowerCase();
            if (primary && showRuntime) return `${t('connected')} — ${primary} (runtime: ${rl})`;
            if (primary) return `${t('connected')} — ${primary}`;
            if (rl) return `${t('connected')} — ${rl}`;
            return t('connected');
          })() : t('disconnected')}
        </div>
        {connected && rpMeter(recentRpm, activeProvider, runtimeLlmLabel, isMobile)}
        {doctorReport && doctorReport.ok === false ? (
          isMobile ? (
            <button style={{ ...styles.iconButton, color: 'var(--amber)' }} onClick={onDoctorClick} title="Há itens de diagnóstico pendentes">⚠</button>
          ) : (
            <button style={{ ...styles.userButton, borderColor: 'var(--amber)', color: 'var(--amber)' }} onClick={onDoctorClick} title="Há itens de diagnóstico pendentes">Doctor ⚠</button>
          )
        ) : null}
        <button style={styles.iconButton} onClick={onSettingsClick}>⚙️</button>
        {isMobile ? (
          <button style={styles.iconButton} onClick={onLogout} title={t('sign_out')}>⎋</button>
        ) : (
          <button style={styles.userButton} onClick={onLogout}>{user?.email} → {t('sign_out')}</button>
        )}
      </div>
    </div>
  );
};

export default Header;
