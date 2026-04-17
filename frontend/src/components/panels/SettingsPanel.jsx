import React, { useState } from 'react';

/**
 * SettingsPanel - Painel de configurações gerais da aplicação.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {Object} props.settings - Configurações atuais
 * @param {boolean} props.loading - Se está carregando
 * @param {Function} props.onSaveSettings - Função para salvar configurações
 * @param {Function} props.onResetSettings - Função para resetar configurações
 * @param {Function} props.t - Função de tradução
 */
const SettingsPanel = ({
  styles,
  settings = {},
  loading,
  onSaveSettings,
  onResetSettings,
  t
}) => {
  const [activeTab, setActiveTab] = useState('general');
  const [tempSettings, setTempSettings] = useState(settings);
  const [hasChanges, setHasChanges] = useState(false);

  const updateTempSetting = (category, key, value) => {
    setTempSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
    setHasChanges(true);
  };

  const handleSave = () => {
    onSaveSettings(tempSettings);
    setHasChanges(false);
  };

  const handleReset = () => {
    if (window.confirm(t ? t('reset_settings_confirm') : 'Are you sure you want to reset all settings?')) {
      onResetSettings();
      setTempSettings({});
      setHasChanges(false);
    }
  };

  const tabs = [
    { id: 'general', label: t ? t('general') : 'General' },
    { id: 'appearance', label: t ? t('appearance') : 'Appearance' },
    { id: 'notifications', label: t ? t('notifications') : 'Notifications' },
    { id: 'privacy', label: t ? t('privacy') : 'Privacy' },
    { id: 'advanced', label: t ? t('advanced') : 'Advanced' }
  ];

  const renderGeneralTab = () => (
    <div style={styles.settingsTab}>
      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('language_settings') : 'Language Settings'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('language') : 'Language'}:
          </label>
          <select
            style={styles.settingSelect}
            value={tempSettings.general?.lang || 'en'}
            onChange={(e) => updateTempSetting('general', 'lang', e.target.value)}
          >
            <option value="en">English</option>
            <option value="pt-BR">Português (Brasil)</option>
            <option value="es">Español</option>
            <option value="fr">Français</option>
            <option value="de">Deutsch</option>
            <option value="ja">Japanese</option>
            <option value="zh-CN">Chinese (Simplified)</option>
          </select>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('date_format') : 'Date Format'}:
          </label>
          <select
            style={styles.settingSelect}
            value={tempSettings.general?.dateFormat || 'auto'}
            onChange={(e) => updateTempSetting('general', 'dateFormat', e.target.value)}
          >
            <option value="auto">{t ? t('auto_detect') : 'Auto Detect'}</option>
            <option value="MM/DD/YYYY">MM/DD/YYYY</option>
            <option value="DD/MM/YYYY">DD/MM/YYYY</option>
            <option value="YYYY-MM-DD">YYYY-MM-DD</option>
          </select>
        </div>
      </div>

      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('behavior_settings') : 'Behavior Settings'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.general?.autoSave || false}
              onChange={(e) => updateTempSetting('general', 'autoSave', e.target.checked)}
            />
            {t ? t('auto_save') : 'Auto Save'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.general?.autoBackup || false}
              onChange={(e) => updateTempSetting('general', 'autoBackup', e.target.checked)}
            />
            {t ? t('auto_backup') : 'Auto Backup'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('session_timeout') : 'Session Timeout'} (minutes):
          </label>
          <input
            style={styles.settingInput}
            type="number"
            min="5"
            max="1440"
            value={tempSettings.general?.sessionTimeout || 30}
            onChange={(e) => updateTempSetting('general', 'sessionTimeout', parseInt(e.target.value))}
          />
        </div>
      </div>
    </div>
  );

  const renderAppearanceTab = () => (
    <div style={styles.settingsTab}>
      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('theme_settings') : 'Theme Settings'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('theme') : 'Theme'}:
          </label>
          <select
            style={styles.settingSelect}
            value={tempSettings.appearance?.theme || 'light'}
            onChange={(e) => updateTempSetting('appearance', 'theme', e.target.value)}
          >
            <option value="light">{t ? t('light') : 'Light'}</option>
            <option value="dark">{t ? t('dark') : 'Dark'}</option>
            <option value="auto">{t ? t('auto') : 'Auto'}</option>
            <option value="high-contrast">{t ? t('high_contrast') : 'High Contrast'}</option>
          </select>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('font_size') : 'Font Size'}:
          </label>
          <select
            style={styles.settingSelect}
            value={tempSettings.appearance?.fontSize || 'medium'}
            onChange={(e) => updateTempSetting('appearance', 'fontSize', e.target.value)}
          >
            <option value="small">{t ? t('small') : 'Small'}</option>
            <option value="medium">{t ? t('medium') : 'Medium'}</option>
            <option value="large">{t ? t('large') : 'Large'}</option>
            <option value="extra-large">{t ? t('extra_large') : 'Extra Large'}</option>
          </select>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.appearance?.compactMode || false}
              onChange={(e) => updateTempSetting('appearance', 'compactMode', e.target.checked)}
            />
            {t ? t('compact_mode') : 'Compact Mode'}
          </label>
        </div>
      </div>

      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('layout_settings') : 'Layout Settings'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.appearance?.showSidebar !== false}
              onChange={(e) => updateTempSetting('appearance', 'showSidebar', e.target.checked)}
            />
            {t ? t('show_sidebar') : 'Show Sidebar'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.appearance?.showStatusBar !== false}
              onChange={(e) => updateTempSetting('appearance', 'showStatusBar', e.target.checked)}
            />
            {t ? t('show_status_bar') : 'Show Status Bar'}
          </label>
        </div>
      </div>
    </div>
  );

  const renderNotificationsTab = () => (
    <div style={styles.settingsTab}>
      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('notification_preferences') : 'Notification Preferences'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.notifications?.enabled !== false}
              onChange={(e) => updateTempSetting('notifications', 'enabled', e.target.checked)}
            />
            {t ? t('enable_notifications') : 'Enable Notifications'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.notifications?.soundEnabled !== false}
              onChange={(e) => updateTempSetting('notifications', 'soundEnabled', e.target.checked)}
              disabled={!tempSettings.notifications?.enabled}
            />
            {t ? t('notification_sound') : 'Notification Sound'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.notifications?.desktopEnabled !== false}
              onChange={(e) => updateTempSetting('notifications', 'desktopEnabled', e.target.checked)}
              disabled={!tempSettings.notifications?.enabled}
            />
            {t ? t('desktop_notifications') : 'Desktop Notifications'}
          </label>
        </div>
      </div>

      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('notification_types') : 'Notification Types'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.notifications?.systemAlerts !== false}
              onChange={(e) => updateTempSetting('notifications', 'systemAlerts', e.target.checked)}
              disabled={!tempSettings.notifications?.enabled}
            />
            {t ? t('system_alerts') : 'System Alerts'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.notifications?.taskUpdates !== false}
              onChange={(e) => updateTempSetting('notifications', 'taskUpdates', e.target.checked)}
              disabled={!tempSettings.notifications?.enabled}
            />
            {t ? t('task_updates') : 'Task Updates'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.notifications?.securityAlerts !== false}
              onChange={(e) => updateTempSetting('notifications', 'securityAlerts', e.target.checked)}
              disabled={!tempSettings.notifications?.enabled}
            />
            {t ? t('security_alerts') : 'Security Alerts'}
          </label>
        </div>
      </div>
    </div>
  );

  const renderPrivacyTab = () => (
    <div style={styles.settingsTab}>
      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('data_privacy') : 'Data Privacy'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.privacy?.telemetry !== false}
              onChange={(e) => updateTempSetting('privacy', 'telemetry', e.target.checked)}
            />
            {t ? t('share_telemetry') : 'Share Telemetry Data'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.privacy?.crashReports !== false}
              onChange={(e) => updateTempSetting('privacy', 'crashReports', e.target.checked)}
            />
            {t ? t('send_crash_reports') : 'Send Crash Reports'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.privacy?.usageAnalytics !== false}
              onChange={(e) => updateTempSetting('privacy', 'usageAnalytics', e.target.checked)}
            />
            {t ? t('usage_analytics') : 'Usage Analytics'}
          </label>
        </div>
      </div>

      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('data_retention') : 'Data Retention'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('chat_history_retention') : 'Chat History Retention'}:
          </label>
          <select
            style={styles.settingSelect}
            value={tempSettings.privacy?.chatRetention || '30'}
            onChange={(e) => updateTempSetting('privacy', 'chatRetention', e.target.value)}
          >
            <option value="7">7 {t ? t('days') : 'days'}</option>
            <option value="30">30 {t ? t('days') : 'days'}</option>
            <option value="90">90 {t ? t('days') : 'days'}</option>
            <option value="365">1 {t ? t('year') : 'year'}</option>
            <option value="0">{t ? t('forever') : 'Forever'}</option>
          </select>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('log_retention') : 'Log Retention'}:
          </label>
          <select
            style={styles.settingSelect}
            value={tempSettings.privacy?.logRetention || '7'}
            onChange={(e) => updateTempSetting('privacy', 'logRetention', e.target.value)}
          >
            <option value="1">1 {t ? t('day') : 'day'}</option>
            <option value="7">7 {t ? t('days') : 'days'}</option>
            <option value="30">30 {t ? t('days') : 'days'}</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderAdvancedTab = () => (
    <div style={styles.settingsTab}>
      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('development_settings') : 'Development Settings'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.advanced?.debugMode || false}
              onChange={(e) => updateTempSetting('advanced', 'debugMode', e.target.checked)}
            />
            {t ? t('debug_mode') : 'Debug Mode'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.advanced?.verboseLogging || false}
              onChange={(e) => updateTempSetting('advanced', 'verboseLogging', e.target.checked)}
            />
            {t ? t('verbose_logging') : 'Verbose Logging'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('log_level') : 'Log Level'}:
          </label>
          <select
            style={styles.settingSelect}
            value={tempSettings.advanced?.logLevel || 'info'}
            onChange={(e) => updateTempSetting('advanced', 'logLevel', e.target.value)}
          >
            <option value="error">Error</option>
            <option value="warn">Warning</option>
            <option value="info">Info</option>
            <option value="debug">Debug</option>
            <option value="trace">Trace</option>
          </select>
        </div>
      </div>

      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('performance_settings') : 'Performance Settings'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('max_concurrent_requests') : 'Max Concurrent Requests'}:
          </label>
          <input
            style={styles.settingInput}
            type="number"
            min="1"
            max="100"
            value={tempSettings.advanced?.maxConcurrentRequests || 5}
            onChange={(e) => updateTempSetting('advanced', 'maxConcurrentRequests', parseInt(e.target.value))}
          />
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('request_timeout') : 'Request Timeout'} (seconds):
          </label>
          <input
            style={styles.settingInput}
            type="number"
            min="5"
            max="300"
            value={tempSettings.advanced?.requestTimeout || 30}
            onChange={(e) => updateTempSetting('advanced', 'requestTimeout', parseInt(e.target.value))}
          />
        </div>
      </div>

      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('dangerous_zone') : 'Dangerous Zone'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempSettings.advanced?.experimentalFeatures || false}
              onChange={(e) => updateTempSetting('advanced', 'experimentalFeatures', e.target.checked)}
            />
            {t ? t('enable_experimental_features') : 'Enable Experimental Features'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <button
            style={{...styles.settingButton, ...styles.dangerButton}}
            onClick={handleReset}
            disabled={loading}
          >
            {t ? t('reset_all_settings') : 'Reset All Settings'}
          </button>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general': return renderGeneralTab();
      case 'appearance': return renderAppearanceTab();
      case 'notifications': return renderNotificationsTab();
      case 'privacy': return renderPrivacyTab();
      case 'advanced': return renderAdvancedTab();
      default: return renderGeneralTab();
    }
  };

  return (
    <div style={styles.panel}>
      <div style={styles.panelHeader}>
        <h3 style={styles.panelTitle}>
          {t ? t('settings') : 'Settings'}
          {hasChanges && (
            <span style={styles.unsavedIndicator}>
              *
            </span>
          )}
        </h3>
        <div style={styles.panelActions}>
          <button
            style={styles.panelButton}
            onClick={handleSave}
            disabled={loading || !hasChanges}
            title={t ? t('save_settings') : 'Save Settings'}
          >
            {t ? t('save') : 'Save'}
          </button>
        </div>
      </div>

      <div style={styles.panelContent}>
        {/* Tabs Navigation */}
        <div style={styles.settingsTabs}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              style={{
                ...styles.settingsTab,
                ...(activeTab === tab.id ? styles.settingsTabActive : {})
              }}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div style={styles.settingsContent}>
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
