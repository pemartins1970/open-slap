/**
 * 🤖 useLLMConfig - Hook para gerenciar configurações de LLM
 */

import { useState, useCallback, useRef } from 'react';

/**
 * Hook para gerenciar configurações de Large Language Model
 * @param {Function} getAuthHeaders - Função para obter headers de autenticação
 * @param {Function} t - Função de tradução
 * @returns {Object} - Estado e funções de configuração LLM
 */
export const useLLMConfig = (getAuthHeaders, t) => {
  // Estados principais
  const [llmMode, setLlmMode] = useState('env');
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [llmModel, setLlmModel] = useState('');
  const [llmBaseUrl, setLlmBaseUrl] = useState('');
  const [llmApiKey, setLlmApiKey] = useState('');

  // Estados de status de API Key
  const [llmHasApiKey, setLlmHasApiKey] = useState(false);
  const [llmApiKeySource, setLlmApiKeySource] = useState('none');
  const [llmHasStoredApiKey, setLlmHasStoredApiKey] = useState(false);
  const [llmHasEnvApiKey, setLlmHasEnvApiKey] = useState(false);
  const [llmApiKeyOpen, setLlmApiKeyOpen] = useState(false);

  // Estados de provider keys
  const [llmProviderKeys, setLlmProviderKeys] = useState([]);
  const [llmProviderKeysLoading, setLlmProviderKeysLoading] = useState(false);
  const [llmProviderKeysError, setLlmProviderKeysError] = useState('');

  // Estados de loading/error
  const [llmLoading, setLlmLoading] = useState(false);
  const [llmError, setLlmError] = useState('');

  // Refs
  const llmApiKeyInputRef = useRef(null);
  const pendingSettingsActionRef = useRef(null);

  /**
   * Obtém preferências de LLM do localStorage
   */
  const getStoredLlmPrefs = useCallback(() => {
    try {
      const raw = localStorage.getItem('open_slap_llm_prefs');
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object') return null;
      return parsed;
    } catch {
      return null;
    }
  }, []);

  /**
   * Salva preferências de LLM no localStorage
   */
  const setStoredLlmPrefs = useCallback((prefs) => {
    try {
      localStorage.setItem('open_slap_llm_prefs', JSON.stringify(prefs || {}));
    } catch (e) {
      console.error('Error saving LLM prefs:', e);
    }
  }, []);

  /**
   * Carrega provider keys do backend
   */
  const loadProviderKeys = useCallback(async () => {
    try {
      setLlmProviderKeysLoading(true);
      setLlmProviderKeysError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return;
      }

      const response = await fetch('/api/settings/llm/provider_keys', { headers });

      if (!response.ok) {
        throw new Error('Failed to load provider keys');
      }

      const data = await response.json();
      setLlmProviderKeys(Array.isArray(data?.keys) ? data.keys : []);
    } catch (error) {
      console.error('Error loading provider keys:', error);
      setLlmProviderKeysError('Failed to load provider keys');
      setLlmProviderKeys([]);
    } finally {
      setLlmProviderKeysLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Salva configurações de LLM no backend
   */
  const saveLlmSettings = useCallback(async () => {
    try {
      setLlmLoading(true);
      setLlmError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      headers['Content-Type'] = 'application/json';

      // Infere provider da API key
      const rawKey = llmApiKey.trim();
      const inferredProvider = rawKey.startsWith('AIza')
        ? 'gemini'
        : rawKey.startsWith('gsk_')
          ? 'groq'
          : rawKey.startsWith('sk-or-')
            ? 'openrouter'
            : rawKey.startsWith('sk-ant-')
              ? 'anthropic'
              : rawKey.startsWith('sk-')
                ? 'openai'
                : '';

      const providerToSave = inferredProvider || llmProvider || (rawKey ? 'openai' : '');
      
      // Limpa base URL
      const normalizedBaseUrl = (llmBaseUrl || '').trim();
      const cleanedBaseUrl = normalizedBaseUrl.replace(/[`'"]/g, '').replace(/,+$/, '');

      const payload = {
        mode: llmMode,
        provider: providerToSave,
        model: llmModel.trim(),
        base_url: cleanedBaseUrl,
        api_key: rawKey
      };

      const response = await fetch('/api/settings/llm', {
        method: 'PUT',
        headers,
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data?.detail || 'Failed to save LLM settings');
      }

      const data = await response.json();

      // Atualiza estados com resposta do backend
      setLlmHasApiKey(Boolean(data?.has_api_key));
      setLlmApiKeySource(data?.api_key_source || 'none');
      setLlmHasStoredApiKey(Boolean(data?.has_stored_api_key));
      setLlmHasEnvApiKey(Boolean(data?.has_env_api_key));

      // Salva preferências localmente
      setStoredLlmPrefs({
        mode: llmMode,
        provider: providerToSave,
        model: llmModel.trim(),
        base_url: cleanedBaseUrl
      });

      return true;
    } catch (error) {
      console.error('Error saving LLM settings:', error);
      setLlmError(error.message || 'Failed to save LLM settings');
      return false;
    } finally {
      setLlmLoading(false);
    }
  }, [
    getAuthHeaders,
    llmMode,
    llmProvider,
    llmModel,
    llmBaseUrl,
    llmApiKey,
    setStoredLlmPrefs
  ]);

  /**
   * Remove API key do backend
   */
  const removeLlmApiKey = useCallback(async () => {
    try {
      setLlmLoading(true);
      setLlmError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      const response = await fetch('/api/settings/llm/api_key', {
        method: 'DELETE',
        headers
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data?.detail || 'Failed to remove API key');
      }

      const data = await response.json();

      // Atualiza estados
      setLlmApiKey('');
      setLlmApiKeyOpen(false);
      setLlmHasApiKey(Boolean(data?.has_api_key));
      setLlmApiKeySource(data?.api_key_source || 'none');
      setLlmHasStoredApiKey(Boolean(data?.has_stored_api_key));
      setLlmHasEnvApiKey(Boolean(data?.has_env_api_key));

      return true;
    } catch (error) {
      console.error('Error removing API key:', error);
      setLlmError(t('llm_key_remove_error') || 'Failed to remove API key');
      return false;
    } finally {
      setLlmLoading(false);
    }
  }, [getAuthHeaders, t]);

  /**
   * Testa conexão com LLM
   */
  const testLlmConnection = useCallback(async () => {
    try {
      setLlmLoading(true);
      setLlmError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      const response = await fetch('/api/settings/llm/test', {
        method: 'POST',
        headers
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data?.detail || 'Connection test failed');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error testing LLM connection:', error);
      setLlmError(error.message || 'Failed to test connection');
      return null;
    } finally {
      setLlmLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Carrega configurações de LLM do backend
   */
  const loadLlmSettings = useCallback(async () => {
    try {
      setLlmLoading(true);
      setLlmError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      const response = await fetch('/api/settings/llm', { headers });

      if (!response.ok) {
        throw new Error('Failed to load LLM settings');
      }

      const data = await response.json();

      // Atualiza estados
      if (data.mode) setLlmMode(data.mode);
      if (data.provider) setLlmProvider(data.provider);
      if (data.model) setLlmModel(data.model);
      if (data.base_url) setLlmBaseUrl(data.base_url);
      if (data.has_api_key !== undefined) setLlmHasApiKey(data.has_api_key);
      if (data.api_key_source) setLlmApiKeySource(data.api_key_source);
      if (data.has_stored_api_key !== undefined) setLlmHasStoredApiKey(data.has_stored_api_key);
      if (data.has_env_api_key !== undefined) setLlmHasEnvApiKey(data.has_env_api_key);

      return data;
    } catch (error) {
      console.error('Error loading LLM settings:', error);
      setLlmError('Failed to load LLM settings');
      return null;
    } finally {
      setLlmLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Reseta configurações de LLM para padrão
   */
  const resetLlmSettings = useCallback(() => {
    setLlmMode('env');
    setLlmProvider('ollama');
    setLlmModel('');
    setLlmBaseUrl('');
    setLlmApiKey('');
    setLlmApiKeyOpen(false);
    setStoredLlmPrefs({});
  }, [setStoredLlmPrefs]);

  return {
    // Estados principais
    llmMode,
    llmProvider,
    llmModel,
    llmBaseUrl,
    llmApiKey,

    // Estados de API Key
    llmHasApiKey,
    llmApiKeySource,
    llmHasStoredApiKey,
    llmHasEnvApiKey,
    llmApiKeyOpen,

    // Provider keys
    llmProviderKeys,
    llmProviderKeysLoading,
    llmProviderKeysError,

    // Loading/Error
    llmLoading,
    llmError,

    // Refs
    llmApiKeyInputRef,
    pendingSettingsActionRef,

    // Setters
    setLlmMode,
    setLlmProvider,
    setLlmModel,
    setLlmBaseUrl,
    setLlmApiKey,
    setLlmApiKeyOpen,
    setLlmError,

    // Funções
    getStoredLlmPrefs,
    setStoredLlmPrefs,
    loadProviderKeys,
    saveLlmSettings,
    removeLlmApiKey,
    testLlmConnection,
    loadLlmSettings,
    resetLlmSettings
  };
};

export default useLLMConfig;
