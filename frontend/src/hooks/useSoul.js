/**
 * 👤 useSoul - Hook para gerenciar Soul (perfil do usuário)
 */

import { useState, useCallback } from 'react';

/**
 * Hook para gerenciar dados de Soul e System Profile
 * @param {Function} getAuthHeaders - Função para obter headers de autenticação
 * @returns {Object} - Estado e funções de Soul
 */
export const useSoul = (getAuthHeaders) => {
  // Estados de Soul Data
  const [soulData, setSoulData] = useState({
    name: '',
    age_range: '',
    gender: '',
    education: '',
    interests: '',
    goals: '',
    learning_style: '',
    language: 'pt-BR',
    audience: '',
    notes: ''
  });

  const [soulMarkdown, setSoulMarkdown] = useState('');
  const [soulUpdate, setSoulUpdate] = useState('');
  const [soulLoading, setSoulLoading] = useState(false);
  const [soulError, setSoulError] = useState('');

  // Estados de System Profile
  const [systemProfileMarkdown, setSystemProfileMarkdown] = useState('');
  const [systemProfileUpdatedAt, setSystemProfileUpdatedAt] = useState('');
  const [systemProfileEnabled, setSystemProfileEnabled] = useState(true);
  const [systemProfileError, setSystemProfileError] = useState('');
  const [systemProfileLoading, setSystemProfileLoading] = useState(false);

  /**
   * Carrega dados de Soul do backend
   */
  const loadSoul = useCallback(async () => {
    try {
      setSoulLoading(true);
      setSoulError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      const response = await fetch('/api/soul', { headers });

      if (!response.ok) {
        throw new Error('Failed to load soul');
      }

      const data = await response.json();

      if (data.soul) {
        setSoulData(prev => ({ ...prev, ...data.soul }));
      }
      if (data.markdown) {
        setSoulMarkdown(data.markdown);
      }

      return data;
    } catch (error) {
      console.error('Error loading soul:', error);
      setSoulError('Failed to load soul data');
      return null;
    } finally {
      setSoulLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Salva dados de Soul no backend
   */
  const saveSoul = useCallback(async (data) => {
    try {
      setSoulLoading(true);
      setSoulError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      headers['Content-Type'] = 'application/json';

      const response = await fetch('/api/soul', {
        method: 'PUT',
        headers,
        body: JSON.stringify(data || soulData)
      });

      if (!response.ok) {
        const json = await response.json().catch(() => ({}));
        throw new Error(json?.detail || 'Failed to save soul');
      }

      const result = await response.json();

      if (result.soul) {
        setSoulData(result.soul);
      }
      if (result.markdown) {
        setSoulMarkdown(result.markdown);
      }

      return true;
    } catch (error) {
      console.error('Error saving soul:', error);
      setSoulError(error.message || 'Failed to save soul');
      return false;
    } finally {
      setSoulLoading(false);
    }
  }, [getAuthHeaders, soulData]);

  /**
   * Atualiza campo específico do Soul
   */
  const updateSoulField = useCallback((field, value) => {
    setSoulData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  /**
   * Deleta dados de Soul
   */
  const deleteSoul = useCallback(async () => {
    try {
      setSoulLoading(true);
      setSoulError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      const response = await fetch('/api/soul', {
        method: 'DELETE',
        headers
      });

      if (!response.ok) {
        throw new Error('Failed to delete soul');
      }

      // Reseta para padrão
      setSoulData({
        name: '',
        age_range: '',
        gender: '',
        education: '',
        interests: '',
        goals: '',
        learning_style: '',
        language: 'pt-BR',
        audience: '',
        notes: ''
      });
      setSoulMarkdown('');

      return true;
    } catch (error) {
      console.error('Error deleting soul:', error);
      setSoulError('Failed to delete soul');
      return false;
    } finally {
      setSoulLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Refresh do System Profile
   */
  const refreshSystemProfile = useCallback(async () => {
    try {
      setSystemProfileLoading(true);
      setSystemProfileError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      const response = await fetch('/api/system_profile/refresh', {
        method: 'POST',
        headers
      });

      if (!response.ok) {
        const json = await response.json().catch(() => ({}));
        throw new Error(json?.detail || 'Failed to refresh system profile');
      }

      const data = await response.json();

      setSystemProfileMarkdown(data?.markdown || '');
      setSystemProfileUpdatedAt(data?.updated_at || '');

      return true;
    } catch (error) {
      console.error('Error refreshing system profile:', error);
      setSystemProfileError('Could not update system profile');
      return false;
    } finally {
      setSystemProfileLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Deleta System Profile
   */
  const deleteSystemProfile = useCallback(async () => {
    try {
      setSystemProfileLoading(true);
      setSystemProfileError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      const response = await fetch('/api/system_profile', {
        method: 'DELETE',
        headers
      });

      if (!response.ok) {
        throw new Error('Failed to delete system profile');
      }

      setSystemProfileMarkdown('');
      setSystemProfileUpdatedAt('');

      return true;
    } catch (error) {
      console.error('Error deleting system profile:', error);
      setSystemProfileError('Could not remove system profile');
      return false;
    } finally {
      setSystemProfileLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Carrega System Profile
   */
  const loadSystemProfile = useCallback(async () => {
    try {
      setSystemProfileLoading(true);
      setSystemProfileError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      const response = await fetch('/api/system_profile', { headers });

      if (!response.ok) {
        throw new Error('Failed to load system profile');
      }

      const data = await response.json();

      setSystemProfileMarkdown(data?.markdown || '');
      setSystemProfileUpdatedAt(data?.updated_at || '');
      setSystemProfileEnabled(data?.enabled !== false);

      return data;
    } catch (error) {
      console.error('Error loading system profile:', error);
      setSystemProfileError('Failed to load system profile');
      return null;
    } finally {
      setSystemProfileLoading(false);
    }
  }, [getAuthHeaders]);

  return {
    // Soul Data
    soulData,
    soulMarkdown,
    soulUpdate,
    soulLoading,
    soulError,

    // System Profile
    systemProfileMarkdown,
    systemProfileUpdatedAt,
    systemProfileEnabled,
    systemProfileError,
    systemProfileLoading,

    // Setters
    setSoulData,
    setSoulMarkdown,
    setSoulUpdate,
    setSystemProfileEnabled,

    // Funções de Soul
    loadSoul,
    saveSoul,
    updateSoulField,
    deleteSoul,

    // Funções de System Profile
    refreshSystemProfile,
    deleteSystemProfile,
    loadSystemProfile
  };
};

export default useSoul;
