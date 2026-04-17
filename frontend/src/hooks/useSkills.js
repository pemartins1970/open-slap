/**
 * 🎯 useSkills - Hook para gerenciar Skills e Experts
 */

import { useState, useCallback, useRef } from 'react';

/**
 * Hook para gerenciar Skills e Experts
 * @param {Function} getAuthHeaders - Função para obter headers de autenticação
 * @param {Function} t - Função de tradução
 * @returns {Object} - Estado e funções de Skills
 */
export const useSkills = (getAuthHeaders, t) => {
  // Estados de Skills
  const [skills, setSkills] = useState([]);
  const [skillsLoading, setSkillsLoading] = useState(false);
  const [skillsError, setSkillsError] = useState('');
  const [skillsSaveStatus, setSkillsSaveStatus] = useState('');

  // Estados de Experts
  const [experts, setExperts] = useState([]);
  const [expertsLoading, setExpertsLoading] = useState(false);
  const [expertsError, setExpertsError] = useState('');

  // Refs
  const skillsSaveStatusTimeoutRef = useRef(null);

  /**
   * Carrega skills do backend
   */
  const loadSkills = useCallback(async () => {
    try {
      setSkillsLoading(true);
      setSkillsError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      const response = await fetch('/api/skills', { headers });

      if (!response.ok) {
        throw new Error('Failed to load skills');
      }

      const data = await response.json();
      setSkills(Array.isArray(data?.skills) ? data.skills : []);

      return data;
    } catch (error) {
      console.error('Error loading skills:', error);
      setSkillsError('Failed to load skills');
      setSkills([]);
      return null;
    } finally {
      setSkillsLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Salva skills no backend
   * @param {Array} nextSkills - Array de skills a salvar
   * @param {Object} options - Opções { silent }
   */
  const saveSkills = useCallback(async (nextSkills, { silent = false } = {}) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      headers['Content-Type'] = 'application/json';

      const response = await fetch('/api/skills', {
        method: 'PUT',
        headers,
        body: JSON.stringify({ skills: Array.isArray(nextSkills) ? nextSkills : [] })
      });

      const ok = response.ok;

      if (!silent) {
        // Limpa timeout anterior
        if (skillsSaveStatusTimeoutRef.current) {
          clearTimeout(skillsSaveStatusTimeoutRef.current);
          skillsSaveStatusTimeoutRef.current = null;
        }

        if (ok) {
          setSkillsSaveStatus(t('saved') || 'Saved');
          skillsSaveStatusTimeoutRef.current = setTimeout(() => {
            setSkillsSaveStatus('');
            skillsSaveStatusTimeoutRef.current = null;
          }, 2200);
        } else {
          setSkillsSaveStatus(t('failed_to_save') || 'Failed to save');
          skillsSaveStatusTimeoutRef.current = setTimeout(() => {
            setSkillsSaveStatus('');
            skillsSaveStatusTimeoutRef.current = null;
          }, 3500);
        }
      }

      if (ok) {
        setSkills(nextSkills);
      }

      return ok;
    } catch (error) {
      console.error('Error saving skills:', error);
      if (!silent) {
        setSkillsError('Failed to save skills');
      }
      return false;
    }
  }, [getAuthHeaders, t]);

  /**
   * Toggle de skill (ativa/desativa)
   * @param {string} skillId - ID da skill
   */
  const toggleSkill = useCallback(async (skillId) => {
    const nextSkills = skills.map(skill =>
      skill.id === skillId
        ? { ...skill, enabled: !skill.enabled }
        : skill
    );

    setSkills(nextSkills);
    await saveSkills(nextSkills, { silent: true });
  }, [skills, saveSkills]);

  /**
   * Atualiza skill específica
   * @param {string} skillId - ID da skill
   * @param {Object} updates - Atualizações parciais
   */
  const updateSkill = useCallback(async (skillId, updates) => {
    const nextSkills = skills.map(skill =>
      skill.id === skillId
        ? { ...skill, ...updates }
        : skill
    );

    setSkills(nextSkills);
    await saveSkills(nextSkills, { silent: true });
  }, [skills, saveSkills]);

  /**
   * Adiciona nova skill
   * @param {Object} skill - Objeto de skill
   */
  const addSkill = useCallback(async (skill) => {
    const nextSkills = [...skills, skill];
    setSkills(nextSkills);
    return await saveSkills(nextSkills);
  }, [skills, saveSkills]);

  /**
   * Remove skill
   * @param {string} skillId - ID da skill
   */
  const removeSkill = useCallback(async (skillId) => {
    const nextSkills = skills.filter(skill => skill.id !== skillId);
    setSkills(nextSkills);
    return await saveSkills(nextSkills);
  }, [skills, saveSkills]);

  /**
   * Carrega experts do backend
   */
  const loadExperts = useCallback(async () => {
    try {
      setExpertsLoading(true);
      setExpertsError('');

      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      const response = await fetch('/api/experts', { headers });

      if (!response.ok) {
        throw new Error('Failed to load experts');
      }

      const data = await response.json();
      setExperts(Array.isArray(data?.experts) ? data.experts : []);

      return data;
    } catch (error) {
      console.error('Error loading experts:', error);
      setExpertsError('Failed to load experts');
      setExperts([]);
      return null;
    } finally {
      setExpertsLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Salva experts no backend
   * @param {Array} nextExperts - Array de experts a salvar
   */
  const saveExperts = useCallback(async (nextExperts) => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      headers['Content-Type'] = 'application/json';

      const response = await fetch('/api/experts', {
        method: 'PUT',
        headers,
        body: JSON.stringify({ experts: Array.isArray(nextExperts) ? nextExperts : [] })
      });

      if (response.ok) {
        setExperts(nextExperts);
      }

      return response.ok;
    } catch (error) {
      console.error('Error saving experts:', error);
      return false;
    }
  }, [getAuthHeaders]);

  /**
   * Toggle de expert (ativa/desativa)
   * @param {string} expertId - ID do expert
   */
  const toggleExpert = useCallback(async (expertId) => {
    const nextExperts = experts.map(expert =>
      expert.id === expertId
        ? { ...expert, enabled: !expert.enabled }
        : expert
    );

    setExperts(nextExperts);
    await saveExperts(nextExperts);
  }, [experts, saveExperts]);

  /**
   * Atualiza expert específico
   * @param {string} expertId - ID do expert
   * @param {Object} updates - Atualizações parciais
   */
  const updateExpert = useCallback(async (expertId, updates) => {
    const nextExperts = experts.map(expert =>
      expert.id === expertId
        ? { ...expert, ...updates }
        : expert
    );

    setExperts(nextExperts);
    await saveExperts(nextExperts);
  }, [experts, saveExperts]);

  /**
   * Limpa status de salvamento
   */
  const clearSaveStatus = useCallback(() => {
    if (skillsSaveStatusTimeoutRef.current) {
      clearTimeout(skillsSaveStatusTimeoutRef.current);
      skillsSaveStatusTimeoutRef.current = null;
    }
    setSkillsSaveStatus('');
  }, []);

  return {
    // Skills
    skills,
    skillsLoading,
    skillsError,
    skillsSaveStatus,

    // Experts
    experts,
    expertsLoading,
    expertsError,

    // Setters
    setSkills,
    setExperts,

    // Funções de Skills
    loadSkills,
    saveSkills,
    toggleSkill,
    updateSkill,
    addSkill,
    removeSkill,

    // Funções de Experts
    loadExperts,
    saveExperts,
    toggleExpert,
    updateExpert,

    // Utilitários
    clearSaveStatus
  };
};

export default useSkills;
