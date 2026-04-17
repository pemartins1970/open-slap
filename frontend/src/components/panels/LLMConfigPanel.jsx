import React, { useState } from 'react';

/**
 * LLMConfigPanel - Painel de configuração de provedores LLM.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {Object} props.llmConfig - Configurações LLM atuais
 * @param {Array} props.providers - Lista de provedores disponíveis
 * @param {Array} props.models - Lista de modelos disponíveis
 * @param {boolean} props.loading - Se está carregando
 * @param {Function} props.onSaveConfig - Função para salvar configurações
 * @param {Function} props.onTestConnection - Função para testar conexão
 * @param {Function} props.onRemoveApiKey - Função para remover API key
 * @param {Function} props.t - Função de tradução
 */
const LLMConfigPanel = ({
  styles,
  llmConfig = {},
  providers = [],
  models = [],
  loading,
  onSaveConfig,
  onTestConnection,
  onRemoveApiKey,
  t
}) => {
  const [activeTab, setActiveTab] = useState('provider');
  const [tempConfig, setTempConfig] = useState(llmConfig);
  const [hasChanges, setHasChanges] = useState(false);
  const [testResults, setTestResults] = useState({});

  const updateTempConfig = (key, value) => {
    setTempConfig(prev => ({
      ...prev,
      [key]: value
    }));
    setHasChanges(true);
  };

  const handleSave = () => {
    onSaveConfig(tempConfig);
    setHasChanges(false);
  };

  const handleTestConnection = async (provider) => {
    setTestResults(prev => ({
      ...prev,
      [provider]: { status: 'testing', message: t ? t('testing_connection') : 'Testing connection...' }
    }));

    try {
      const result = await onTestConnection(provider);
      setTestResults(prev => ({
        ...prev,
        [provider]: { status: 'success', message: result.message || 'Connection successful' }
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [provider]: { status: 'error', message: error.message || 'Connection failed' }
      }));
    }
  };

  const handleRemoveApiKey = (provider) => {
    if (window.confirm(t ? t('remove_api_key_confirm') : 'Are you sure you want to remove this API key?')) {
      onRemoveApiKey(provider);
      updateTempConfig(`${provider}_apiKey`, '');
    }
  };

  const getTestResultColor = (status) => {
    switch (status) {
      case 'success': return styles.testSuccess;
      case 'error': return styles.testError;
      case 'testing': return styles.testTesting;
      default: return styles.testDefault;
    }
  };

  const tabs = [
    { id: 'provider', label: t ? t('provider_settings') : 'Provider Settings' },
    { id: 'models', label: t ? t('model_settings') : 'Model Settings' },
    { id: 'advanced', label: t ? t('advanced_settings') : 'Advanced Settings' }
  ];

  const renderProviderTab = () => (
    <div style={styles.settingsTab}>
      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('default_provider') : 'Default Provider'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('select_provider') : 'Select Provider'}:
          </label>
          <select
            style={styles.settingSelect}
            value={tempConfig.llmProvider || ''}
            onChange={(e) => updateTempConfig('llmProvider', e.target.value)}
          >
            <option value="">{t ? t('select_one') : 'Select one...'}</option>
            {providers.map(provider => (
              <option key={provider.id} value={provider.id}>
                {provider.name}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('default_model') : 'Default Model'}:
          </label>
          <select
            style={styles.settingSelect}
            value={tempConfig.llmModel || ''}
            onChange={(e) => updateTempConfig('llmModel', e.target.value)}
            disabled={!tempConfig.llmProvider}
          >
            <option value="">{t ? t('select_one') : 'Select one...'}</option>
            {models
              .filter(model => model.provider === tempConfig.llmProvider)
              .map(model => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
          </select>
        </div>
      </div>

      {providers.map(provider => {
        const apiKey = tempConfig[`${provider.id}_apiKey`] || '';
        const hasApiKey = apiKey.length > 0;
        const testResult = testResults[provider.id];

        return (
          <div key={provider.id} style={styles.settingGroup}>
            <h4 style={styles.settingGroupTitle}>
              {provider.name}
              <span style={{
                ...styles.providerStatus,
                ...(hasApiKey ? styles.providerConnected : styles.providerDisconnected)
              }}>
                {hasApiKey ? 'Connected' : 'Not Connected'}
              </span>
            </h4>

            <div style={styles.settingItem}>
              <label style={styles.settingLabel}>
                {t ? t('api_key') : 'API Key'}:
              </label>
              <div style={styles.apiKeyContainer}>
                <input
                  style={styles.settingInput}
                  type={hasApiKey ? 'password' : 'text'}
                  value={apiKey}
                  onChange={(e) => updateTempConfig(`${provider.id}_apiKey`, e.target.value)}
                  placeholder={t ? t('enter_api_key') : 'Enter API key...'}
                />
                <div style={styles.apiKeyActions}>
                  {hasApiKey && (
                    <button
                      style={styles.apiKeyToggle}
                      onClick={() => {
                        const input = document.querySelector(`input[value="${apiKey}"]`);
                        if (input.type === 'password') {
                          input.type = 'text';
                        } else {
                          input.type = 'password';
                        }
                      }}
                      title={t ? t('toggle_visibility') : 'Toggle visibility'}
                    >
                      {hasApiKey ? 'Show' : 'Hide'}
                    </button>
                  )}
                  
                  {hasApiKey && (
                    <button
                      style={styles.apiKeyRemove}
                      onClick={() => handleRemoveApiKey(provider.id)}
                      title={t ? t('remove_api_key') : 'Remove API key'}
                    >
                      Remove
                    </button>
                  )}
                </div>
              </div>
            </div>

            {provider.description && (
              <div style={styles.settingDescription}>
                {provider.description}
              </div>
            )}

            <div style={styles.providerActions}>
              <button
                style={styles.providerButton}
                onClick={() => handleTestConnection(provider.id)}
                disabled={!hasApiKey || loading}
                title={t ? t('test_connection') : 'Test Connection'}
              >
                {t ? t('test') : 'Test'}
              </button>
            </div>

            {testResult && (
              <div style={{
                ...styles.testResult,
                ...getTestResultColor(testResult.status)
              }}>
                {testResult.message}
              </div>
            )}

            {provider.config && Object.keys(provider.config).length > 0 && (
              <div style={styles.providerConfig}>
                <h5 style={styles.configTitle}>
                  {t ? t('additional_config') : 'Additional Configuration'}
                </h5>
                {Object.entries(provider.config).map(([key, config]) => (
                  <div key={key} style={styles.settingItem}>
                    <label style={styles.settingLabel}>
                      {config.label || key}:
                    </label>
                    {config.type === 'select' ? (
                      <select
                        style={styles.settingSelect}
                        value={tempConfig[`${provider.id}_${key}`] || config.default || ''}
                        onChange={(e) => updateTempConfig(`${provider.id}_${key}`, e.target.value)}
                      >
                        {config.options.map(option => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    ) : config.type === 'checkbox' ? (
                      <label style={styles.settingCheckbox}>
                        <input
                          type="checkbox"
                          checked={tempConfig[`${provider.id}_${key}`] || config.default || false}
                          onChange={(e) => updateTempConfig(`${provider.id}_${key}`, e.target.checked)}
                        />
                        {config.checkboxLabel || key}
                      </label>
                    ) : (
                      <input
                        style={styles.settingInput}
                        type={config.type || 'text'}
                        value={tempConfig[`${provider.id}_${key}`] || config.default || ''}
                        onChange={(e) => updateTempConfig(`${provider.id}_${key}`, e.target.value)}
                        placeholder={config.placeholder || ''}
                      />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );

  const renderModelsTab = () => (
    <div style={styles.settingsTab}>
      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('model_preferences') : 'Model Preferences'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('max_tokens') : 'Max Tokens'}:
          </label>
          <input
            style={styles.settingInput}
            type="number"
            min="1"
            max="32000"
            value={tempConfig.maxTokens || 2048}
            onChange={(e) => updateTempConfig('maxTokens', parseInt(e.target.value))}
          />
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('temperature') : 'Temperature'}:
          </label>
          <input
            style={styles.settingInput}
            type="number"
            min="0"
            max="2"
            step="0.1"
            value={tempConfig.temperature || 0.7}
            onChange={(e) => updateTempConfig('temperature', parseFloat(e.target.value))}
          />
          <div style={styles.settingDescription}>
            {t ? t('temperature_description') : 'Higher values make the output more creative, lower values make it more focused and deterministic.'}
          </div>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('top_p') : 'Top P'}:
          </label>
          <input
            style={styles.settingInput}
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={tempConfig.topP || 1}
            onChange={(e) => updateTempConfig('topP', parseFloat(e.target.value))}
          />
          <div style={styles.settingDescription}>
            {t ? t('top_p_description') : 'Alternative to temperature, uses nucleus sampling.'}
          </div>
        </div>
      </div>

      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('available_models') : 'Available Models'}
        </h4>
        
        <div style={styles.modelsList}>
          {models
            .filter(model => !tempConfig.llmProvider || model.provider === tempConfig.llmProvider)
            .map(model => (
              <div key={model.id} style={styles.modelItem}>
                <div style={styles.modelHeader}>
                  <div style={styles.modelName}>
                    {model.name}
                  </div>
                  <div style={styles.modelProvider}>
                    {providers.find(p => p.id === model.provider)?.name || model.provider}
                  </div>
                </div>
                
                <div style={styles.modelDetails}>
                  {model.description && (
                    <div style={styles.modelDescription}>
                      {model.description}
                    </div>
                  )}
                  
                  {model.contextWindow && (
                    <div style={styles.modelMeta}>
                      <span style={styles.modelMetaLabel}>
                        {t ? t('context_window') : 'Context Window'}:
                      </span>
                      <span style={styles.modelMetaValue}>
                        {model.contextWindow.toLocaleString()} tokens
                      </span>
                    </div>
                  )}
                  
                  {model.pricing && (
                    <div style={styles.modelMeta}>
                      <span style={styles.modelMetaLabel}>
                        {t ? t('pricing') : 'Pricing'}:
                      </span>
                      <span style={styles.modelMetaValue}>
                        {model.pricing.input || 'N/A'} / {model.pricing.output || 'N/A'}
                      </span>
                    </div>
                  )}
                  
                  {model.capabilities && model.capabilities.length > 0 && (
                    <div style={styles.modelCapabilities}>
                      <span style={styles.modelMetaLabel}>
                        {t ? t('capabilities') : 'Capabilities'}:
                      </span>
                      <div style={styles.capabilityTags}>
                        {model.capabilities.map(capability => (
                          <span key={capability} style={styles.capabilityTag}>
                            {capability}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );

  const renderAdvancedTab = () => (
    <div style={styles.settingsTab}>
      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('request_settings') : 'Request Settings'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('request_timeout') : 'Request Timeout'} (seconds):
          </label>
          <input
            style={styles.settingInput}
            type="number"
            min="5"
            max="300"
            value={tempConfig.requestTimeout || 30}
            onChange={(e) => updateTempConfig('requestTimeout', parseInt(e.target.value))}
          />
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('retry_attempts') : 'Retry Attempts'}:
          </label>
          <input
            style={styles.settingInput}
            type="number"
            min="0"
            max="10"
            value={tempConfig.retryAttempts || 3}
            onChange={(e) => updateTempConfig('retryAttempts', parseInt(e.target.value))}
          />
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('retry_delay') : 'Retry Delay'} (ms):
          </label>
          <input
            style={styles.settingInput}
            type="number"
            min="100"
            max="10000"
            step="100"
            value={tempConfig.retryDelay || 1000}
            onChange={(e) => updateTempConfig('retryDelay', parseInt(e.target.value))}
          />
        </div>
      </div>

      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('streaming_settings') : 'Streaming Settings'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempConfig.enableStreaming !== false}
              onChange={(e) => updateTempConfig('enableStreaming', e.target.checked)}
            />
            {t ? t('enable_streaming') : 'Enable Streaming'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('stream_buffer_size') : 'Stream Buffer Size'}:
          </label>
          <input
            style={styles.settingInput}
            type="number"
            min="1"
            max="100"
            value={tempConfig.streamBufferSize || 10}
            onChange={(e) => updateTempConfig('streamBufferSize', parseInt(e.target.value))}
            disabled={!tempConfig.enableStreaming}
          />
        </div>
      </div>

      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('fallback_settings') : 'Fallback Settings'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempConfig.enableFallback || false}
              onChange={(e) => updateTempConfig('enableFallback', e.target.checked)}
            />
            {t ? t('enable_fallback') : 'Enable Fallback'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingLabel}>
            {t ? t('fallback_provider') : 'Fallback Provider'}:
          </label>
          <select
            style={styles.settingSelect}
            value={tempConfig.fallbackProvider || ''}
            onChange={(e) => updateTempConfig('fallbackProvider', e.target.value)}
            disabled={!tempConfig.enableFallback}
          >
            <option value="">{t ? t('select_one') : 'Select one...'}</option>
            {providers
              .filter(p => p.id !== tempConfig.llmProvider)
              .map(provider => (
                <option key={provider.id} value={provider.id}>
                  {provider.name}
                </option>
              ))}
          </select>
        </div>
      </div>

      <div style={styles.settingGroup}>
        <h4 style={styles.settingGroupTitle}>
          {t ? t('debug_settings') : 'Debug Settings'}
        </h4>
        
        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempConfig.debugMode || false}
              onChange={(e) => updateTempConfig('debugMode', e.target.checked)}
            />
            {t ? t('debug_mode') : 'Debug Mode'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempConfig.logRequests || false}
              onChange={(e) => updateTempConfig('logRequests', e.target.checked)}
            />
            {t ? t('log_requests') : 'Log Requests'}
          </label>
        </div>

        <div style={styles.settingItem}>
          <label style={styles.settingCheckbox}>
            <input
              type="checkbox"
              checked={tempConfig.logResponses || false}
              onChange={(e) => updateTempConfig('logResponses', e.target.checked)}
            />
            {t ? t('log_responses') : 'Log Responses'}
          </label>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'provider': return renderProviderTab();
      case 'models': return renderModelsTab();
      case 'advanced': return renderAdvancedTab();
      default: return renderProviderTab();
    }
  };

  return (
    <div style={styles.panel}>
      <div style={styles.panelHeader}>
        <h3 style={styles.panelTitle}>
          {t ? t('llm_configuration') : 'LLM Configuration'}
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
            title={t ? t('save_configuration') : 'Save Configuration'}
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

export default LLMConfigPanel;
