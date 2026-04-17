/**
 * 🏥 useDoctor - Hook para gerenciar Doctor (health check do sistema)
 */

import { useState, useCallback } from 'react';

/**
 * Hook para gerenciar Doctor health checks
 * @param {Function} getAuthHeaders - Função para obter headers de autenticação
 * @returns {Object} - Estado e funções de Doctor
 */
export const useDoctor = (getAuthHeaders) => {
  // Estados principais
  const [doctorReport, setDoctorReport] = useState(null);
  const [doctorLoading, setDoctorLoading] = useState(false);
  const [doctorError, setDoctorError] = useState('');

  // Estados de System Map
  const [systemMapText, setSystemMapText] = useState('');
  const [systemMapUpdatedAt, setSystemMapUpdatedAt] = useState('');
  const [systemMapError, setSystemMapError] = useState('');
  const [systemMapLoading, setSystemMapLoading] = useState(false);

  /**
   * Carrega relatório do Doctor
   * @param {Object} options - Opções { silent, force }
   */
  const loadDoctorSummary = useCallback(async ({ silent = false, force = false } = {}) => {
    try {
      if (!silent) {
        setDoctorLoading(true);
        setDoctorError('');
      }

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      const url = force 
        ? '/api/doctor/summary?force=true'
        : '/api/doctor/summary';

      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error('Failed to load doctor summary');
      }

      const data = await response.json();
      setDoctorReport(data);

      return data;
    } catch (error) {
      console.error('Error loading doctor summary:', error);
      if (!silent) {
        setDoctorError('Failed to load health check');
      }
      return null;
    } finally {
      if (!silent) {
        setDoctorLoading(false);
      }
    }
  }, [getAuthHeaders]);

  /**
   * Força refresh do Doctor
   */
  const refreshDoctor = useCallback(async () => {
    return await loadDoctorSummary({ force: true });
  }, [loadDoctorSummary]);

  /**
   * Executa check específico do Doctor
   * @param {string} checkId - ID do check a executar
   */
  const runDoctorCheck = useCallback(async (checkId) => {
    try {
      setDoctorLoading(true);
      setDoctorError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      headers['Content-Type'] = 'application/json';

      const response = await fetch('/api/doctor/run_check', {
        method: 'POST',
        headers,
        body: JSON.stringify({ check_id: checkId })
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data?.detail || 'Failed to run check');
      }

      const data = await response.json();

      // Atualiza relatório local
      if (doctorReport && data.check) {
        setDoctorReport(prev => {
          if (!prev?.checks) return prev;
          return {
            ...prev,
            checks: prev.checks.map(check =>
              check.id === checkId ? data.check : check
            )
          };
        });
      }

      return data;
    } catch (error) {
      console.error('Error running doctor check:', error);
      setDoctorError(error.message || 'Failed to run check');
      return null;
    } finally {
      setDoctorLoading(false);
    }
  }, [getAuthHeaders, doctorReport]);

  /**
   * Carrega System Map
   */
  const loadSystemMap = useCallback(async () => {
    try {
      setSystemMapLoading(true);
      setSystemMapError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      const response = await fetch('/api/system_map', { headers });

      if (!response.ok) {
        throw new Error('Failed to load system map');
      }

      const data = await response.json();

      setSystemMapText(data?.markdown || data?.text || '');
      setSystemMapUpdatedAt(data?.updated_at || '');

      return data;
    } catch (error) {
      console.error('Error loading system map:', error);
      setSystemMapError('Failed to load system map');
      return null;
    } finally {
      setSystemMapLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Refresh do System Map
   */
  const refreshSystemMap = useCallback(async () => {
    try {
      setSystemMapLoading(true);
      setSystemMapError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      const response = await fetch('/api/system_map/refresh', {
        method: 'POST',
        headers
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data?.detail || 'Failed to refresh system map');
      }

      const data = await response.json();

      setSystemMapText(data?.markdown || data?.text || '');
      setSystemMapUpdatedAt(data?.updated_at || '');

      return true;
    } catch (error) {
      console.error('Error refreshing system map:', error);
      setSystemMapError('Could not update system map');
      return false;
    } finally {
      setSystemMapLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Deleta System Map
   */
  const deleteSystemMap = useCallback(async () => {
    try {
      setSystemMapLoading(true);
      setSystemMapError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      const response = await fetch('/api/system_map', {
        method: 'DELETE',
        headers
      });

      if (!response.ok) {
        throw new Error('Failed to delete system map');
      }

      setSystemMapText('');
      setSystemMapUpdatedAt('');

      return true;
    } catch (error) {
      console.error('Error deleting system map:', error);
      setSystemMapError('Could not remove system map');
      return false;
    } finally {
      setSystemMapLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Obtém status geral do sistema
   * @returns {Object} - {status: 'ok'|'warning'|'error', message}
   */
  const getSystemStatus = useCallback(() => {
    if (!doctorReport?.checks) {
      return { status: 'unknown', message: 'No health check data' };
    }

    const checks = doctorReport.checks;
    const hasError = checks.some(check => check.status === 'error');
    const hasWarning = checks.some(check => check.status === 'warning');

    if (hasError) {
      return { status: 'error', message: 'System has errors' };
    }
    if (hasWarning) {
      return { status: 'warning', message: 'System has warnings' };
    }

    return { status: 'ok', message: 'All systems operational' };
  }, [doctorReport]);

  /**
   * Obtém checks por status
   * @param {string} status - Status ('ok', 'warning', 'error')
   * @returns {Array} - Checks filtrados
   */
  const getChecksByStatus = useCallback((status) => {
    if (!doctorReport?.checks) return [];
    return doctorReport.checks.filter(check => check.status === status);
  }, [doctorReport]);

  /**
   * Limpa erros
   */
  const clearDoctorError = useCallback(() => {
    setDoctorError('');
  }, []);

  const clearSystemMapError = useCallback(() => {
    setSystemMapError('');
  }, []);

  return {
    // Doctor Report
    doctorReport,
    doctorLoading,
    doctorError,

    // System Map
    systemMapText,
    systemMapUpdatedAt,
    systemMapError,
    systemMapLoading,

    // Setters
    setDoctorReport,
    setSystemMapText,

    // Funções de Doctor
    loadDoctorSummary,
    refreshDoctor,
    runDoctorCheck,
    getSystemStatus,
    getChecksByStatus,

    // Funções de System Map
    loadSystemMap,
    refreshSystemMap,
    deleteSystemMap,

    // Utilitários
    clearDoctorError,
    clearSystemMapError
  };
};

export default useDoctor;
