/**
 * ⚙️ useSettings - Hook para gerenciar configurações do sistema
 */

import { useState, useCallback } from 'react';
import { useLocalStorage } from './useLocalStorage';

/**
 * Hook para gerenciar configurações da aplicação
 * @param {Function} getAuthHeaders - Função para obter headers de autenticação
 * @param {Function} t - Função de tradução
 * @returns {Object} - Estado e funções de configurações
 */
export const useSettings = (getAuthHeaders, t) => {
  // Estados locais (não persistidos no backend)
  const [lang, setLang] = useLocalStorage('open_slap_lang', 'pt-BR');
  const [theme, setTheme] = useLocalStorage('open_slap_theme', 'dark');
  
  // Estados de UI
  const [settingsTab, setSettingsTab] = useState('appearance');
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsError, setSettingsError] = useState('');
  const [settingsSaveStatus, setSettingsSaveStatus] = useState('');

  // Estados de provider status
  const [providerStatusList, setProviderStatusList] = useState([]);
  const [providerStatusLoading, setProviderStatusLoading] = useState(false);
  const [providerStatusError, setProviderStatusError] = useState('');

  /**
   * Salva idioma
   * @param {string} language - Código do idioma
   */
  const saveLanguageSettings = useCallback(async (language) => {
    try {
      setSettingsLoading(true);
      setSettingsError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        setLang(language);
        return true;
      }

      headers['Content-Type'] = 'application/json';

      const response = await fetch('/api/settings/language', {
        method: 'PUT',
        headers,
        body: JSON.stringify({ language })
      });

      if (!response.ok) {
        throw new Error('Failed to save language');
      }

      setLang(language);
      return true;
    } catch (error) {
      console.error('Error saving language:', error);
      setSettingsError(t('language_save_error') || 'Failed to save language');
      return false;
    } finally {
      setSettingsLoading(false);
    }
  }, [getAuthHeaders, setLang, t]);

  /**
   * Salva tema
   * @param {string} themeName - Nome do tema ('dark', 'light')
   */
  const saveThemeSettings = useCallback(async (themeName) => {
    try {
      setSettingsLoading(true);
      setSettingsError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        setTheme(themeName);
        return true;
      }

      headers['Content-Type'] = 'application/json';

      const response = await fetch('/api/settings/theme', {
        method: 'PUT',
        headers,
        body: JSON.stringify({ theme: themeName })
      });

      if (!response.ok) {
        throw new Error('Failed to save theme');
      }

      setTheme(themeName);
      return true;
    } catch (error) {
      console.error('Error saving theme:', error);
      setSettingsError(t('theme_save_error') || 'Failed to save theme');
      return false;
    } finally {
      setSettingsLoading(false);
    }
  }, [getAuthHeaders, setTheme, t]);

  /**
   * Carrega status dos providers
   */
  const loadProviderStatus = useCallback(async () => {
    try {
      setProviderStatusLoading(true);
      setProviderStatusError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return;
      }

      const response = await fetch('/api/settings/llm/provider_status', { headers });

      if (!response.ok) {
        throw new Error('Failed to load provider status');
      }

      const data = await response.json();
      setProviderStatusList(Array.isArray(data?.providers) ? data.providers : []);
    } catch (error) {
      console.error('Error loading provider status:', error);
      setProviderStatusError('Failed to load provider status');
      setProviderStatusList([]);
    } finally {
      setProviderStatusLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Recarrega todas as configurações do backend
   */
  const reloadSettings = useCallback(async () => {
    try {
      setSettingsLoading(true);
      setSettingsError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      const response = await fetch('/api/settings', { headers });

      if (!response.ok) {
        throw new Error('Failed to load settings');
      }

      const data = await response.json();

      // Atualiza configurações locais
      if (data.language) setLang(data.language);
      if (data.theme) setTheme(data.theme);

      return data;
    } catch (error) {
      console.error('Error reloading settings:', error);
      setSettingsError('Failed to reload settings');
      return null;
    } finally {
      setSettingsLoading(false);
    }
  }, [getAuthHeaders, setLang, setTheme]);

  /**
   * Reseta configurações para padrão
   */
  const resetSettings = useCallback(async () => {
    try {
      setSettingsLoading(true);
      setSettingsError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        setLang('pt-BR');
        setTheme('dark');
        return true;
      }

      headers['Content-Type'] = 'application/json';

      const response = await fetch('/api/settings/reset', {
        method: 'POST',
        headers
      });

      if (!response.ok) {
        throw new Error('Failed to reset settings');
      }

      // Reseta para padrões
      setLang('pt-BR');
      setTheme('dark');

      return true;
    } catch (error) {
      console.error('Error resetting settings:', error);
      setSettingsError('Failed to reset settings');
      return false;
    } finally {
      setSettingsLoading(false);
    }
  }, [getAuthHeaders, setLang, setTheme]);

  /**
   * Mostra status de salvamento temporário
   * @param {string} message - Mensagem de status
   * @param {number} duration - Duração em ms
   */
  const showSaveStatus = useCallback((message, duration = 2000) => {
    setSettingsSaveStatus(message);
    setTimeout(() => setSettingsSaveStatus(''), duration);
  }, []);

  /**
   * Limpa erro de configurações
   */
  const clearSettingsError = useCallback(() => {
    setSettingsError('');
  }, []);

  return {
    // Estados principais
    lang,
    theme,
    settingsTab,
    settingsLoading,
    settingsError,
    settingsSaveStatus,

    // Provider status
    providerStatusList,
    providerStatusLoading,
    providerStatusError,

    // Setters
    setLang,
    setTheme,
    setSettingsTab,
    setSettingsError,

    // Funções de configuração
    saveLanguageSettings,
    saveThemeSettings,
    loadProviderStatus,
    reloadSettings,
    resetSettings,
    showSaveStatus,
    clearSettingsError
  };
};

export default useSettings;
