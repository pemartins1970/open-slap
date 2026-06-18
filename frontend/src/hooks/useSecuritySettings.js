import { useState, useCallback, useEffect } from 'react';

const normalizeSecuritySettings = (raw) => {
  const base = {
    sandbox: false,
    allow_os_commands: true,
    allow_file_write: true,
    allow_web_retrieval: true,
    allow_connectors: true,
    allow_system_profile: true
  };
  const out = { ...base };
  if (raw && typeof raw === 'object') {
    Object.keys(base).forEach((k) => {
      if (raw[k] === undefined || raw[k] === null) return;
      out[k] = Boolean(raw[k]);
    });
  }
  if (out.sandbox) {
    out.allow_os_commands = false;
    out.allow_file_write = false;
    out.allow_web_retrieval = false;
    out.allow_connectors = false;
  }
  return out;
};

export const useSecuritySettings = ({
  getAuthHeaders,
  t,
  setSettingsLoading,
  setSettingsError,
  settingsOpen,
  settingsTab,
  isAuthenticated
}) => {
  const [securitySettings, setSecuritySettings] = useState({
    sandbox: false,
    allow_os_commands: true,
    allow_file_write: true,
    allow_web_retrieval: true,
    allow_connectors: true,
    allow_system_profile: true
  });
  const [securitySettingsUpdatedAt, setSecuritySettingsUpdatedAt] = useState('');
  const [authSettings, setAuthSettings] = useState({
    jwt_expire_minutes: 120,
    default_jwt_expire_minutes: 120,
    has_override: false
  });
  const [authSettingsUpdatedAt, setAuthSettingsUpdatedAt] = useState('');
  const [jwtExpireMinutesDraft, setJwtExpireMinutesDraft] = useState(120);
  const [authSettingsSaving, setAuthSettingsSaving] = useState(false);
  const [autoApproveCommands, setAutoApproveCommands] = useState([]);
  const [autoApproveCommandsLoading, setAutoApproveCommandsLoading] = useState(false);
  const [autoApproveCommandsError, setAutoApproveCommandsError] = useState('');
  const [genericModal, setGenericModal] = useState(null);

  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

  const loadSecuritySettings = useCallback(async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      const res = await fetch('/api/settings/security', { headers });
      const json = await res.json().catch(() => ({}));
      if (res.ok) {
        setSecuritySettings(normalizeSecuritySettings(json?.settings || {}));
        setSecuritySettingsUpdatedAt(json?.updated_at || '');
      }
    } catch {}
  }, [getAuthHeaders]);

  const loadAuthSettings = useCallback(async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      const res = await fetch('/api/settings/auth', { headers });
      const json = await res.json().catch(() => ({}));
      if (res.ok) {
        const effective = Number(json?.settings?.jwt_expire_minutes || 120) || 120;
        const def = Number(json?.defaults?.jwt_expire_minutes || 120) || 120;
        const hasOverride = Boolean(json?.has_override);
        setAuthSettings({
          jwt_expire_minutes: effective,
          default_jwt_expire_minutes: def,
          has_override: hasOverride
        });
        setAuthSettingsUpdatedAt(json?.updated_at || '');
        setJwtExpireMinutesDraft(effective);
      }
    } catch {}
  }, [getAuthHeaders]);

  const saveSecuritySettings = useCallback(async (override) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return;
      setSettingsLoading(true);
      setSettingsError('');
      const toSave = normalizeSecuritySettings(override || securitySettings);
      const res = await fetch('/api/settings/security', {
        method: 'PUT',
        headers,
        body: JSON.stringify(toSave)
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Error saving security settings.');
      }
      setSecuritySettings(normalizeSecuritySettings(json?.settings || toSave));
      setSecuritySettingsUpdatedAt(json?.updated_at || '');
    } catch {
      setSettingsError(t('security_settings_save_error'));
    } finally {
      setSettingsLoading(false);
    }
  }, [getAuthHeaders, securitySettings, setSettingsLoading, setSettingsError, t]);

  const applySecuritySettingChange = useCallback((patch, { needsConfirm }) => {
    const next = normalizeSecuritySettings({ ...securitySettings, ...(patch || {}) });
    if (needsConfirm) {
      setGenericModal({
        title: t('agent_security'),
        body: `${t('security_caps_warning')}\n\n${JSON.stringify(next, null, 2)}`,
        onConfirm: () => {
          setSecuritySettings(next);
          saveSecuritySettings(next);
        }
      });
      return;
    }
    setSecuritySettings(next);
    saveSecuritySettings(next);
  }, [securitySettings, saveSecuritySettings, t]);

  const saveAuthSettings = useCallback(async ({ jwt_expire_minutes, use_default }) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      setAuthSettingsSaving(true);
      const payload = {
        jwt_expire_minutes: use_default ? null : Number(jwt_expire_minutes || 0),
        use_default: Boolean(use_default)
      };
      const res = await fetch('/api/settings/auth', {
        method: 'PUT',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || t('settings_save_failed'));
      }
      const effective = Number(json?.settings?.jwt_expire_minutes || 120) || 120;
      const def = Number(json?.defaults?.jwt_expire_minutes || 120) || 120;
      const hasOverride = Boolean(json?.has_override);
      setAuthSettings({
        jwt_expire_minutes: effective,
        default_jwt_expire_minutes: def,
        has_override: hasOverride
      });
      setAuthSettingsUpdatedAt(json?.updated_at || '');
      setJwtExpireMinutesDraft(effective);
      return true;
    } catch (e) {
      setGenericModal({ title: t('error'), body: e?.message || t('settings_save_failed') });
      return false;
    } finally {
      setAuthSettingsSaving(false);
    }
  }, [getAuthHeaders, t]);

  const applyJwtExpiryChange = useCallback(({ use_default = false } = {}) => {
    const def = Number(authSettings?.default_jwt_expire_minutes || 120) || 120;
    const raw = Number(jwtExpireMinutesDraft || 0) || 0;
    const minutes = clamp(raw, 15, 10080);
    const next = use_default ? def : minutes;
    const risk =
      next >= 24 * 60
        ? t('jwt_risk_high')
        : next >= 4 * 60
          ? t('jwt_risk_warning')
          : t('jwt_risk_low');
    const body = [
      t('jwt_change_title'),
      '',
      `${t('jwt_new_value')}: ${next} min`,
      `${t('jwt_default_value')}: ${def} min`,
      '',
      risk,
      '',
      t('jwt_new_tokens_note')
    ].join('\n');
    setGenericModal({
      title: t('security'),
      body,
      onConfirm: () => saveAuthSettings({ jwt_expire_minutes: next, use_default })
    });
  }, [authSettings, jwtExpireMinutesDraft, saveAuthSettings, t]);

  const loadAutoApproveCommands = useCallback(async ({ silent = false } = {}) => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) return;
    try {
      if (!silent) {
        setAutoApproveCommandsLoading(true);
        setAutoApproveCommandsError('');
      }
      const res = await fetch('/api/commands/autoapprove?limit=200', { headers });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Could not load auto-approvals.');
      }
      setAutoApproveCommands(Array.isArray(json?.items) ? json.items : []);
    } catch (e) {
      if (!silent) {
        setAutoApproveCommandsError(e?.message || 'Could not load auto-approvals.');
      }
      setAutoApproveCommands([]);
    } finally {
      if (!silent) {
        setAutoApproveCommandsLoading(false);
      }
    }
  }, [getAuthHeaders]);

  const deleteAutoApproveCommand = useCallback(async (commandNorm) => {
    const cmd = String(commandNorm || '').trim().toLowerCase();
    if (!cmd) return false;
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) return false;
      headers['Content-Type'] = 'application/json';
      const res = await fetch('/api/commands/autoapprove', {
        method: 'DELETE',
        headers,
        body: JSON.stringify({ command_norm: cmd })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json?.detail || 'Could not remove auto-approval.');
      }
      await loadAutoApproveCommands({ silent: true });
      return true;
    } catch (e) {
      setGenericModal({
        title: t('error'),
        body: e?.message || 'Could not remove auto-approval.'
      });
      return false;
    }
  }, [getAuthHeaders, loadAutoApproveCommands, t]);

  useEffect(() => {
    if (!isAuthenticated) return;
    loadAuthSettings();
    loadSecuritySettings();
  }, [isAuthenticated, loadAuthSettings, loadSecuritySettings]);

  useEffect(() => {
    if (!settingsOpen) return;
    if (settingsTab !== 'security') return;
    if (autoApproveCommandsLoading) return;
    if (autoApproveCommands?.length) return;
    loadAutoApproveCommands({ silent: false });
  }, [settingsOpen, settingsTab, autoApproveCommandsLoading, autoApproveCommands, loadAutoApproveCommands]);

  return {
    securitySettings,
    securitySettingsUpdatedAt,
    authSettings,
    authSettingsUpdatedAt,
    jwtExpireMinutesDraft,
    setJwtExpireMinutesDraft,
    authSettingsSaving,
    autoApproveCommands,
    autoApproveCommandsLoading,
    autoApproveCommandsError,
    genericModal,
    setGenericModal,
    applySecuritySettingChange,
    applyJwtExpiryChange,
    loadAutoApproveCommands,
    deleteAutoApproveCommand
  };
};

export default useSecuritySettings;
