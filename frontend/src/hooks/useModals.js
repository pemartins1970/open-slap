/**
 * 🪟 useModals - Hook para gerenciar estado de modais
 */

import { useState, useCallback } from 'react';

/**
 * Hook para gerenciar múltiplos modais
 * @param {Array<string>} modalNames - Array com nomes dos modais
 * @returns {Object} - {modalStates, openModal, closeModal, closeAllModals, toggleModal}
 */
export const useModals = (modalNames = []) => {
  // Inicializa estado de todos os modais como fechados
  const initialState = modalNames.reduce((acc, name) => {
    acc[name] = false;
    return acc;
  }, {});

  const [modalStates, setModalStates] = useState(initialState);

  // Abre um modal específico
  const openModal = useCallback((modalName) => {
    setModalStates(prev => ({
      ...prev,
      [modalName]: true
    }));
  }, []);

  // Fecha um modal específico
  const closeModal = useCallback((modalName) => {
    setModalStates(prev => ({
      ...prev,
      [modalName]: false
    }));
  }, []);

  // Fecha todos os modais
  const closeAllModals = useCallback(() => {
    setModalStates(initialState);
  }, [initialState]);

  // Toggle de um modal específico
  const toggleModal = useCallback((modalName) => {
    setModalStates(prev => ({
      ...prev,
      [modalName]: !prev[modalName]
    }));
  }, []);

  return {
    modalStates,
    openModal,
    closeModal,
    closeAllModals,
    toggleModal
  };
};

/**
 * Hook para modal com dados
 * @param {*} initialData - Dados iniciais do modal
 * @returns {Object} - {isOpen, data, openModal, closeModal, updateData}
 */
export const useModalWithData = (initialData = null) => {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState(initialData);

  const openModal = useCallback((modalData = null) => {
    setData(modalData);
    setIsOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    setIsOpen(false);
    // Limpa dados após animação de fechamento
    setTimeout(() => setData(initialData), 300);
  }, [initialData]);

  const updateData = useCallback((newData) => {
    setData(newData);
  }, []);

  return {
    isOpen,
    data,
    openModal,
    closeModal,
    updateData
  };
};

/**
 * Hook específico para modais do App_auth
 * Gerencia todos os modais da aplicação
 */
export const useAppModals = () => {
  // Estado de cada modal
  const [commandModal, setCommandModal] = useState({ open: false, command: null });
  const [connectorModal, setConnectorModal] = useState({ open: false, type: null });
  const [renameModal, setRenameModal] = useState({ open: false, itemId: null, itemType: null, currentName: '' });
  const [genericModal, setGenericModal] = useState({ open: false, title: '', message: '', type: 'info' });
  const [agentConfigModal, setAgentConfigModal] = useState({ open: false, config: null });
  const [skillModal, setSkillModal] = useState({ open: false, skill: null });
  const [expertModal, setExpertModal] = useState({ open: false, expert: null });
  const [todoModal, setTodoModal] = useState({ open: false, todo: null, mode: 'create' });
  const [deleteConfirmModal, setDeleteConfirmModal] = useState({ open: false, itemId: null, itemType: null });

  // Command Modal
  const openCommandModal = useCallback((command) => {
    setCommandModal({ open: true, command });
  }, []);

  const closeCommandModal = useCallback(() => {
    setCommandModal({ open: false, command: null });
  }, []);

  // Connector Modal
  const openConnectorModal = useCallback((type) => {
    setConnectorModal({ open: true, type });
  }, []);

  const closeConnectorModal = useCallback(() => {
    setConnectorModal({ open: false, type: null });
  }, []);

  // Rename Modal
  const openRenameModal = useCallback((itemId, itemType, currentName) => {
    setRenameModal({ open: true, itemId, itemType, currentName });
  }, []);

  const closeRenameModal = useCallback(() => {
    setRenameModal({ open: false, itemId: null, itemType: null, currentName: '' });
  }, []);

  // Generic Modal (alerts, confirmations)
  const openGenericModal = useCallback((title, message, type = 'info') => {
    setGenericModal({ open: true, title, message, type });
  }, []);

  const closeGenericModal = useCallback(() => {
    setGenericModal({ open: false, title: '', message: '', type: 'info' });
  }, []);

  // Agent Config Modal
  const openAgentConfigModal = useCallback((config) => {
    setAgentConfigModal({ open: true, config });
  }, []);

  const closeAgentConfigModal = useCallback(() => {
    setAgentConfigModal({ open: false, config: null });
  }, []);

  // Skill Modal
  const openSkillModal = useCallback((skill) => {
    setSkillModal({ open: true, skill });
  }, []);

  const closeSkillModal = useCallback(() => {
    setSkillModal({ open: false, skill: null });
  }, []);

  // Expert Modal
  const openExpertModal = useCallback((expert) => {
    setExpertModal({ open: true, expert });
  }, []);

  const closeExpertModal = useCallback(() => {
    setExpertModal({ open: false, expert: null });
  }, []);

  // Todo Modal
  const openTodoModal = useCallback((todo = null, mode = 'create') => {
    setTodoModal({ open: true, todo, mode });
  }, []);

  const closeTodoModal = useCallback(() => {
    setTodoModal({ open: false, todo: null, mode: 'create' });
  }, []);

  // Delete Confirm Modal
  const openDeleteConfirmModal = useCallback((itemId, itemType) => {
    setDeleteConfirmModal({ open: true, itemId, itemType });
  }, []);

  const closeDeleteConfirmModal = useCallback(() => {
    setDeleteConfirmModal({ open: false, itemId: null, itemType: null });
  }, []);

  // Fecha todos os modais
  const closeAllModals = useCallback(() => {
    closeCommandModal();
    closeConnectorModal();
    closeRenameModal();
    closeGenericModal();
    closeAgentConfigModal();
    closeSkillModal();
    closeExpertModal();
    closeTodoModal();
    closeDeleteConfirmModal();
  }, [
    closeCommandModal,
    closeConnectorModal,
    closeRenameModal,
    closeGenericModal,
    closeAgentConfigModal,
    closeSkillModal,
    closeExpertModal,
    closeTodoModal,
    closeDeleteConfirmModal
  ]);

  return {
    // Estados
    commandModal,
    connectorModal,
    renameModal,
    genericModal,
    agentConfigModal,
    skillModal,
    expertModal,
    todoModal,
    deleteConfirmModal,
    
    // Funções de abertura
    openCommandModal,
    openConnectorModal,
    openRenameModal,
    openGenericModal,
    openAgentConfigModal,
    openSkillModal,
    openExpertModal,
    openTodoModal,
    openDeleteConfirmModal,
    
    // Funções de fechamento
    closeCommandModal,
    closeConnectorModal,
    closeRenameModal,
    closeGenericModal,
    closeAgentConfigModal,
    closeSkillModal,
    closeExpertModal,
    closeTodoModal,
    closeDeleteConfirmModal,
    closeAllModals
  };
};

export default useModals;
