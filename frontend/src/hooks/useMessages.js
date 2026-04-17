/**
 * 💬 useMessages - Hook para gerenciar mensagens, input e anexos
 */

import { useState, useCallback, useRef } from 'react';

/**
 * Hook para gerenciar mensagens, input e arquivos anexados
 * @param {Object} options - Opções de configuração
 * @returns {Object} - Estado e funções de mensagens
 */
export const useMessages = (options = {}) => {
  const { onSendMessage, maxFileSize = 10 * 1024 * 1024 } = options;

  // Estados
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [currentMessageId, setCurrentMessageId] = useState(null);

  // Refs
  const messagesEndRef = useRef(null);

  /**
   * Adiciona nova mensagem à lista
   * @param {Object} message - Objeto de mensagem
   */
  const addMessage = useCallback((message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  /**
   * Atualiza mensagem existente
   * @param {string} messageId - ID da mensagem
   * @param {Object} updates - Atualizações parciais
   */
  const updateMessage = useCallback((messageId, updates) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId ? { ...msg, ...updates } : msg
      )
    );
  }, []);

  /**
   * Remove mensagem
   * @param {string} messageId - ID da mensagem
   */
  const removeMessage = useCallback((messageId) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
  }, []);

  /**
   * Limpa todas as mensagens
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  /**
   * Adiciona arquivo anexado
   * @param {File} file - Arquivo a anexar
   * @returns {boolean} - true se sucesso
   */
  const addAttachment = useCallback((file) => {
    if (!file) return false;

    // Valida tamanho
    if (file.size > maxFileSize) {
      console.warn(`File too large: ${file.size} bytes (max: ${maxFileSize})`);
      return false;
    }

    // Verifica duplicatas
    const isDuplicate = attachedFiles.some(
      f => f.name === file.name && f.size === file.size
    );

    if (isDuplicate) {
      console.warn('File already attached');
      return false;
    }

    setAttachedFiles(prev => [...prev, file]);
    return true;
  }, [attachedFiles, maxFileSize]);

  /**
   * Remove arquivo anexado
   * @param {number} index - Índice do arquivo
   */
  const removeAttachment = useCallback((index) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  /**
   * Limpa todos os anexos
   */
  const clearAttachments = useCallback(() => {
    setAttachedFiles([]);
  }, []);

  /**
   * Processa múltiplos arquivos
   * @param {FileList} fileList - Lista de arquivos
   * @returns {number} - Número de arquivos adicionados
   */
  const addMultipleAttachments = useCallback((fileList) => {
    let added = 0;
    
    Array.from(fileList).forEach(file => {
      if (addAttachment(file)) {
        added++;
      }
    });

    return added;
  }, [addAttachment]);

  /**
   * Envia mensagem
   */
  const sendMessage = useCallback(async () => {
    const content = input.trim();
    
    if (!content && attachedFiles.length === 0) {
      return false;
    }

    try {
      setStreaming(true);

      // Cria mensagem do usuário
      const userMessage = {
        id: `msg_${Date.now()}`,
        role: 'user',
        content,
        files: attachedFiles.map(f => ({
          name: f.name,
          size: f.size,
          type: f.type
        })),
        timestamp: new Date().toISOString()
      };

      addMessage(userMessage);

      // Limpa input e anexos
      setInput('');
      clearAttachments();

      // Callback externo se fornecido
      if (onSendMessage) {
        await onSendMessage(userMessage, attachedFiles);
      }

      return true;
    } catch (error) {
      console.error('Error sending message:', error);
      return false;
    } finally {
      setStreaming(false);
    }
  }, [input, attachedFiles, onSendMessage, addMessage, clearAttachments]);

  /**
   * Inicia streaming de mensagem
   * @param {string} messageId - ID da mensagem sendo streamada
   */
  const startStreaming = useCallback((messageId) => {
    setStreaming(true);
    setCurrentMessageId(messageId);
  }, []);

  /**
   * Para streaming de mensagem
   */
  const stopStreaming = useCallback(() => {
    setStreaming(false);
    setCurrentMessageId(null);
  }, []);

  /**
   * Append de conteúdo a mensagem em streaming
   * @param {string} messageId - ID da mensagem
   * @param {string} chunk - Chunk de conteúdo
   */
  const appendToMessage = useCallback((messageId, chunk) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, content: (msg.content || '') + chunk }
          : msg
      )
    );
  }, []);

  /**
   * Scrolla para última mensagem
   */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  /**
   * Busca mensagem por ID
   * @param {string} messageId - ID da mensagem
   * @returns {Object|null} - Mensagem encontrada ou null
   */
  const getMessageById = useCallback((messageId) => {
    return messages.find(msg => msg.id === messageId) || null;
  }, [messages]);

  /**
   * Filtra mensagens por role
   * @param {string} role - Role ('user', 'assistant', 'system')
   * @returns {Array} - Mensagens filtradas
   */
  const getMessagesByRole = useCallback((role) => {
    return messages.filter(msg => msg.role === role);
  }, [messages]);

  /**
   * Retorna estatísticas das mensagens
   * @returns {Object} - {total, user, assistant, system}
   */
  const getMessageStats = useCallback(() => {
    return {
      total: messages.length,
      user: messages.filter(m => m.role === 'user').length,
      assistant: messages.filter(m => m.role === 'assistant').length,
      system: messages.filter(m => m.role === 'system').length
    };
  }, [messages]);

  return {
    // Estados
    messages,
    input,
    attachedFiles,
    streaming,
    currentMessageId,
    messagesEndRef,

    // Setters
    setMessages,
    setInput,
    setAttachedFiles,
    setStreaming,

    // Funções de mensagens
    addMessage,
    updateMessage,
    removeMessage,
    clearMessages,
    getMessageById,
    getMessagesByRole,
    getMessageStats,

    // Funções de anexos
    addAttachment,
    removeAttachment,
    clearAttachments,
    addMultipleAttachments,

    // Funções de envio
    sendMessage,

    // Funções de streaming
    startStreaming,
    stopStreaming,
    appendToMessage,

    // Utilitários
    scrollToBottom
  };
};

export default useMessages;
