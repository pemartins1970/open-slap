import React from 'react';

/**
 * MainContent - Área principal de conteúdo da aplicação.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {boolean} props.leftSidebarCollapsed - Se a sidebar esquerda está colapsada
 * @param {boolean} props.rightSidebarCollapsed - Se a sidebar direita está colapsada
 * @param {boolean} props.isMobile - Se está em modo mobile
 * @param {Object} props.children - Conteúdo a ser renderizado
 * @param {Object} props.chatProps - Props para componente de chat
 * @param {Object} props.executionProps - Props para painel de execução
 * @param {Object} props.panelProps - Props para painéis de configuração
 * @param {Function} props.t - Função de tradução
 */
const MainContent = ({
  styles,
  leftSidebarCollapsed,
  rightSidebarCollapsed,
  isMobile,
  children,
  chatProps,
  executionProps,
  panelProps,
  t
}) => {
  const contentStyles = {
    ...styles.mainContent,
    ...(leftSidebarCollapsed ? styles.mainContentLeftExpanded : {}),
    ...(rightSidebarCollapsed ? styles.mainContentRightExpanded : {}),
    ...(isMobile ? styles.mainContentMobile : {})
  };

  return (
    <div style={contentStyles}>
      {/* Content Area */}
      <div style={styles.contentArea}>
        {children || (
          <div style={styles.defaultContent}>
            <div style={styles.welcomeMessage}>
              <h2 style={styles.welcomeTitle}>
                {t ? t('welcome_to_antigravity') : 'Welcome to Antigravity'}
              </h2>
              <p style={styles.welcomeDescription}>
                {t ? t('get_started_description') : 'Start by creating a new conversation or opening an existing project.'}
              </p>
            </div>

            <div style={styles.quickActions}>
              <button style={styles.quickActionButton}>
                {t ? t('new_conversation') : 'New Conversation'}
              </button>
              <button style={styles.quickActionButton}>
                {t ? t('new_project') : 'New Project'}
              </button>
              <button style={styles.quickActionButton}>
                {t ? t('browse_projects') : 'Browse Projects'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Chat Container (if provided) */}
      {chatProps && (
        <div style={styles.chatContainer}>
          {/* Chat component would be rendered here */}
          <div style={styles.placeholderChat}>
            {t ? t('chat_placeholder') : 'Chat will be rendered here'}
          </div>
        </div>
      )}

      {/* Execution Panel (if provided) */}
      {executionProps && (
        <div style={styles.executionPanel}>
          {/* ExecutionPanel component would be rendered here */}
          <div style={styles.placeholderExecution}>
            {t ? t('execution_panel_placeholder') : 'Execution panel will be rendered here'}
          </div>
        </div>
      )}

      {/* Configuration Panels (if provided) */}
      {panelProps && (
        <div style={styles.configPanels}>
          {/* Various panels would be rendered here */}
          <div style={styles.placeholderPanels}>
            {t ? t('panels_placeholder') : 'Configuration panels will be rendered here'}
          </div>
        </div>
      )}

      {/* Status Bar */}
      <div style={styles.statusBar}>
        <div style={styles.statusBarLeft}>
          <span style={styles.statusItem}>
            {t ? t('ready') : 'Ready'}
          </span>
        </div>

        <div style={styles.statusBarCenter}>
          <span style={styles.statusItem}>
            {t ? t('no_active_tasks') : 'No active tasks'}
          </span>
        </div>

        <div style={styles.statusBarRight}>
          <span style={styles.statusItem}>
            {new Date().toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default MainContent;
