/**
 * 💬 useConversations - Hook para gerenciar conversas e tarefas
 */

import { useState, useCallback, useRef } from 'react';

/**
 * Hook para gerenciar conversas, tarefas e operações relacionadas
 * @param {Function} getAuthHeaders - Função para obter headers de autenticação
 * @returns {Object} - Estado e funções de conversas
 */
export const useConversations = (getAuthHeaders) => {
  // Estados
  const [conversations, setConversations] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [currentKind, setCurrentKind] = useState('conversation');
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [conversationsError, setConversationsError] = useState('');

  // Refs
  const listsRefreshTimerRef = useRef(null);

  /**
   * Carrega lista de conversas do backend
   */
  const loadConversations = useCallback(async () => {
    try {
      setConversationsLoading(true);
      setConversationsError('');
      
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return;
      }

      const response = await fetch('/api/conversations?kind=conversation&source=user', { headers });
      
      if (!response.ok) {
        throw new Error('Failed to load conversations');
      }

      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error('Error loading conversations:', error);
      setConversationsError(error.message || 'Failed to load conversations');
    } finally {
      setConversationsLoading(false);
    }
  }, [getAuthHeaders]);

  /**
   * Carrega lista de tarefas do backend
   */
  const loadTasks = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return;
      }

      const response = await fetch('/api/conversations?kind=task', { headers });
      
      if (!response.ok) {
        throw new Error('Failed to load tasks');
      }

      const data = await response.json();
      setTasks(data.conversations || []);
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  }, [getAuthHeaders]);

  /**
   * Carrega uma conversa específica
   * @param {string} conversationId - ID da conversa
   * @param {string} sessionId - ID da sessão
   * @param {string} kind - Tipo ('conversation' ou 'task')
   */
  const loadConversation = useCallback(async (conversationId, sessionId, kind = 'conversation') => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      const endpoint = kind === 'task' 
        ? `/api/tasks/${encodeURIComponent(conversationId)}`
        : `/api/conversations/${encodeURIComponent(conversationId)}`;

      const response = await fetch(endpoint, { headers });
      
      if (!response.ok) {
        throw new Error('Failed to load conversation');
      }

      const data = await response.json();
      
      setCurrentConversation(data);
      setCurrentKind(kind);
      
      return data;
    } catch (error) {
      console.error('Error loading conversation:', error);
      return null;
    }
  }, [getAuthHeaders]);

  /**
   * Cria nova conversa
   * @param {string} title - Título da conversa
   * @param {string} kind - Tipo ('conversation' ou 'task')
   */
  const createConversation = useCallback(async (title, kind = 'conversation') => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return null;
      }

      headers['Content-Type'] = 'application/json';

      const response = await fetch('/api/conversations', {
        method: 'POST',
        headers,
        body: JSON.stringify({ 
          title: title || 'Nova Conversa',
          kind 
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create conversation');
      }

      const data = await response.json();
      
      // Atualiza lista local
      if (kind === 'task') {
        setTasks(prev => [data, ...prev]);
      } else {
        setConversations(prev => [data, ...prev]);
      }

      return data;
    } catch (error) {
      console.error('Error creating conversation:', error);
      return null;
    }
  }, [getAuthHeaders]);

  /**
   * Atualiza título de conversa/tarefa
   * @param {string} id - ID do item
   * @param {string} title - Novo título
   * @param {string} kind - Tipo ('conversation' ou 'task')
   */
  const updateConversationTitle = useCallback(async (id, title, kind = 'conversation') => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      headers['Content-Type'] = 'application/json';

      const url = kind === 'task'
        ? `/api/tasks/${encodeURIComponent(id)}/title`
        : `/api/conversations/${encodeURIComponent(id)}/title`;

      const response = await fetch(url, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ title })
      });

      if (!response.ok) {
        throw new Error('Failed to update title');
      }

      // Atualiza localmente
      if (kind === 'task') {
        setTasks(prev => 
          prev.map(t => String(t.id) === String(id) ? { ...t, title } : t)
        );
      } else {
        setConversations(prev => 
          prev.map(c => String(c.id) === String(id) ? { ...c, title } : c)
        );
      }

      return true;
    } catch (error) {
      console.error('Error updating title:', error);
      return false;
    }
  }, [getAuthHeaders]);

  /**
   * Deleta uma conversa/tarefa
   * @param {string} id - ID do item
   * @param {string} kind - Tipo ('conversation' ou 'task')
   */
  const deleteConversation = useCallback(async (id, kind = 'conversation') => {
    try {
      const headers = getAuthHeaders();
      if (!headers.Authorization) {
        return false;
      }

      const url = kind === 'task'
        ? `/api/tasks/${encodeURIComponent(id)}`
        : `/api/conversations/${encodeURIComponent(id)}`;

      const response = await fetch(url, {
        method: 'DELETE',
        headers
      });

      if (!response.ok) {
        throw new Error('Failed to delete');
      }

      // Remove localmente
      if (kind === 'task') {
        setTasks(prev => prev.filter(t => String(t.id) !== String(id)));
      } else {
        setConversations(prev => prev.filter(c => String(c.id) !== String(id)));
      }

      // Limpa conversa atual se for a mesma
      if (currentConversation?.id === id) {
        setCurrentConversation(null);
      }

      return true;
    } catch (error) {
      console.error('Error deleting conversation:', error);
      return false;
    }
  }, [getAuthHeaders, currentConversation]);

  /**
   * Agenda refresh das listas com debounce
   */
  const scheduleListsRefresh = useCallback(() => {
    if (listsRefreshTimerRef.current) return;
    
    listsRefreshTimerRef.current = setTimeout(() => {
      listsRefreshTimerRef.current = null;
      loadConversations().catch(() => {});
      loadTasks().catch(() => {});
    }, 700);
  }, [loadConversations, loadTasks]);

  /**
   * Limpa conversa atual
   */
  const clearCurrentConversation = useCallback(() => {
    setCurrentConversation(null);
    setCurrentKind('conversation');
  }, []);

  return {
    // Estados
    conversations,
    tasks,
    currentConversation,
    currentKind,
    conversationsLoading,
    conversationsError,
    
    // Setters
    setConversations,
    setTasks,
    setCurrentConversation,
    setCurrentKind,
    
    // Funções
    loadConversations,
    loadTasks,
    loadConversation,
    createConversation,
    updateConversationTitle,
    deleteConversation,
    scheduleListsRefresh,
    clearCurrentConversation
  };
};

export default useConversations;
