import React from 'react';

export default function SecuritySettingsPanel({
  styles,
  t,
  lang,
  settingsLoading,
  securitySettings,
  securitySettingsUpdatedAt,
  applySecuritySettingChange,
  setGenericModal,
  autoApproveCommands,
  autoApproveCommandsLoading,
  autoApproveCommandsError,
  loadAutoApproveCommands,
  deleteAutoApproveCommand,
}) {
  return (
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
      <div style={{ marginTop: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
            {lang === 'pt' ? 'Permissões automáticas (comandos)' : 'Auto-approvals (commands)'}
          </div>
          <button
            style={styles.settingsSecondaryButton}
            onClick={() => loadAutoApproveCommands({ silent: false })}
            disabled={autoApproveCommandsLoading}
          >
            {autoApproveCommandsLoading ? t('loading') : (lang === 'pt' ? 'Recarregar' : 'Refresh')}
          </button>
        </div>
        <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', lineHeight: 1.5 }}>
          {lang === 'pt'
            ? 'Comandos aqui podem ser executados automaticamente quando forem idênticos. Remova se não quiser mais essa permissão.'
            : 'Commands here may run automatically when identical. Remove if you no longer want this permission.'}
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
                        title: lang === 'pt' ? 'Remover permissão' : 'Remove permission',
                        body: lang === 'pt'
                          ? 'Remover esta permissão automática? O comando voltará a pedir confirmação.'
                          : 'Remove this auto-approval? The command will ask for confirmation again.',
                        onConfirm: async () => {
                          await deleteAutoApproveCommand(cmd);
                        }
                      });
                    }}
                  >
                    {lang === 'pt' ? 'Remover' : 'Remove'}
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div style={{ fontSize: '12px', color: 'var(--text-dim)', fontFamily: 'var(--mono)' }}>
              {lang === 'pt' ? 'Nenhuma permissão automática salva.' : 'No auto-approvals saved.'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
