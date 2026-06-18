import React from 'react';
import { useTranslation } from 'react-i18next';

export default function SecuritySettingsPanel({
  styles,
  settingsLoading,
  securitySettings,
  securitySettingsUpdatedAt,
  applySecuritySettingChange,
  setGenericModal,
  authSettings,
  authSettingsUpdatedAt,
  jwtExpireMinutesDraft,
  setJwtExpireMinutesDraft,
  authSettingsSaving,
  applyJwtExpiryChange,
  autoApproveCommands,
  autoApproveCommandsLoading,
  autoApproveCommandsError,
  loadAutoApproveCommands,
  deleteAutoApproveCommand,
}) {
  const { t } = useTranslation();
  return (
    <>
      <div style={styles.settingsSection}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
          <div style={styles.settingsSectionTitle}>{t('agent_security')}</div>
          <button
            style={{
              ...styles.smallIconButton,
              width: '26px',
              height: '26px',
              borderRadius: '8px',
              fontFamily: 'var(--mono)',
              fontSize: '14px',
              fontWeight: 700,
              background: 'rgba(245,166,35,0.12)',
              border: '1px solid rgba(245,166,35,0.35)',
              color: 'var(--amber)'
            }}
            title={t('sandbox_help_tooltip')}
            onClick={() => setGenericModal({
              title: t('sandbox_help_title'),
              body: [
                t('sandbox_help_line_1'),
                '',
                t('sandbox_help_body_off_title'),
                `- ${t('sandbox_help_off_1')}`,
                `- ${t('sandbox_help_off_2')}`,
                `- ${t('sandbox_help_off_3')}`,
                `- ${t('sandbox_help_off_4')}`,
                '',
                t('sandbox_help_body_on_title'),
                `- ${t('sandbox_help_on_1')}`,
                `- ${t('sandbox_help_on_2')}`,
                `- ${t('sandbox_help_on_3')}`,
                '',
                t('sandbox_help_privacy_title'),
                `- ${t('sandbox_help_privacy_1')}`,
                `- ${t('sandbox_help_privacy_2')}`,
              ].join('\n')
            })}
          >
            ?
          </button>
        </div>
        <div style={styles.settingsHint}>{t('security_caps_warning')}</div>
        <div style={styles.settingsGrid}>
          <div style={styles.settingsField}>
            <div style={{ ...styles.settingsLabel, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>{t('sandbox_mode')}</span>
              <button
                style={{
                  ...styles.smallIconButton,
                  width: '22px',
                  height: '22px',
                  borderRadius: '7px',
                  fontFamily: 'var(--mono)',
                  fontSize: '13px',
                  fontWeight: 700,
                  background: 'rgba(245,166,35,0.12)',
                  border: '1px solid rgba(245,166,35,0.35)',
                  color: 'var(--amber)'
                }}
                title={t('sandbox_help_tooltip')}
                onClick={() => setGenericModal({
                  title: t('sandbox_help_title'),
                  body: [
                    t('sandbox_help_line_1'),
                    '',
                    t('sandbox_help_body_off_title'),
                    `- ${t('sandbox_help_off_1')}`,
                    `- ${t('sandbox_help_off_2')}`,
                    `- ${t('sandbox_help_off_3')}`,
                    `- ${t('sandbox_help_off_4')}`,
                    '',
                    t('sandbox_help_body_on_title'),
                    `- ${t('sandbox_help_on_1')}`,
                    `- ${t('sandbox_help_on_2')}`,
                    `- ${t('sandbox_help_on_3')}`,
                    '',
                    t('sandbox_help_privacy_title'),
                    `- ${t('sandbox_help_privacy_1')}`,
                    `- ${t('sandbox_help_privacy_2')}`,
                  ].join('\n')
                })}
              >
                ?
              </button>
            </div>
            <select
              style={styles.settingsInput}
              value={securitySettings?.sandbox ? 'on' : 'off'}
              onChange={(e) => {
                const next = e.target.value === 'on';
                applySecuritySettingChange({ sandbox: next }, { needsConfirm: next });
              }}
              disabled={settingsLoading}
            >
              <option value="off">{t('off')}</option>
              <option value="on">{t('on')}</option>
            </select>
          </div>

          {[
            { key: 'allow_os_commands', label: t('allow_os_commands') },
            { key: 'allow_file_write', label: t('allow_file_write') },
            { key: 'allow_web_retrieval', label: t('allow_web_retrieval') },
            { key: 'allow_connectors', label: t('allow_connectors') },
            { key: 'allow_system_profile', label: t('allow_system_profile') }
          ].map((row) => {
            const isDisabled = Boolean(securitySettings?.sandbox) && row.key !== 'allow_system_profile';
            const value = Boolean(securitySettings?.[row.key]) ? 'on' : 'off';
            return (
              <div key={row.key} style={styles.settingsField}>
                <div style={styles.settingsLabel}>{row.label}</div>
                <select
                  style={styles.settingsInput}
                  value={value}
                  onChange={(e) => {
                    const v = e.target.value === 'on';
                    const needsConfirm = row.key === 'allow_file_write' && !v;
                    applySecuritySettingChange({ [row.key]: v }, { needsConfirm });
                  }}
                  disabled={settingsLoading || isDisabled}
                >
                  <option value="off">{t('off')}</option>
                  <option value="on">{t('on')}</option>
                </select>
              </div>
            );
          })}
        </div>
        <div style={styles.settingsHint}>
          {t('last_updated')}: {securitySettingsUpdatedAt || '—'}
        </div>
      </div>

      <div style={styles.settingsSection}>
        <div style={styles.settingsSectionTitle}>{t('session_jwt')}</div>
        <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--sans)', lineHeight: 1.5 }}>
          {t('jwt_description')}
        </div>
        <div style={{ display: 'grid', gap: '10px', marginTop: '10px' }}>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div style={{ flex: 1, minWidth: '220px' }}>
              <div style={styles.settingsLabel}>{t('minutes')}</div>
              <input
                type="number"
                min={15}
                max={10080}
                step={15}
                style={styles.settingsInput}
                value={String(jwtExpireMinutesDraft ?? '')}
                onChange={(e) => setJwtExpireMinutesDraft(e.target.value)}
                disabled={settingsLoading || authSettingsSaving}
              />
              <div style={{ marginTop: '6px', fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
                {t('current_default_values', {
                  current: Number(authSettings?.jwt_expire_minutes || 0),
                  default: Number(authSettings?.default_jwt_expire_minutes || 0)
                })}
              </div>
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              <button
                style={styles.settingsSecondaryButton}
                onClick={() => applyJwtExpiryChange({ use_default: true })}
                disabled={settingsLoading || authSettingsSaving || !Boolean(authSettings?.has_override)}
              >
                {t('reset')}
              </button>
              <button
                style={styles.settingsPrimaryButton}
                onClick={() => applyJwtExpiryChange({ use_default: false })}
                disabled={settingsLoading || authSettingsSaving}
              >
                {authSettingsSaving ? t('updating') : t('apply')}
              </button>
            </div>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
            {t('last_updated')}: {authSettingsUpdatedAt || '—'}
          </div>
        </div>
      </div>

      <div style={styles.settingsSection}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
          <div style={styles.settingsSectionTitle}>
            {t('auto_approvals_commands')}
          </div>
          <button
            style={styles.settingsSecondaryButton}
            onClick={() => loadAutoApproveCommands({ silent: false })}
            disabled={autoApproveCommandsLoading}
          >
            {autoApproveCommandsLoading ? 'Loading...' : t('refresh')}
          </button>
        </div>
        <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', lineHeight: 1.5 }}>
          {t('auto_approvals_desc')}
        </div>
        {autoApproveCommandsError ? (
          <div style={{ ...styles.settingsError, marginTop: '8px' }}>{autoApproveCommandsError}</div>
        ) : null}
        <div style={{ display: 'grid', gap: '8px', marginTop: '10px' }}>
          {(autoApproveCommands || []).length ? (
            (autoApproveCommands || []).slice(0, 200).map((cmd) => (
              <div key={cmd} style={{ ...styles.lightCard, padding: '10px 12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                  <div style={{ flex: 1, minWidth: 0, fontSize: '12px', color: 'var(--text)', fontFamily: 'var(--mono)', wordBreak: 'break-word' }}>
                    {String(cmd || '')}
                  </div>
                  <button
                    style={styles.settingsSecondaryButton}
                    onClick={() => {
                      setGenericModal({
                        title: t('remove_permission'),
                        body: t('remove_permission_confirm'),
                        onConfirm: async () => {
                          await deleteAutoApproveCommand(cmd);
                        }
                      });
                    }}
                  >
                    {t('remove')}
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
              {t('no_auto_approvals')}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
