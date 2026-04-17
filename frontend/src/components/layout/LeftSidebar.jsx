import React from 'react';

/**
 * LeftSidebar - Sidebar esquerda com navegação e listas.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {boolean} props.collapsed - Se está colapsada
 * @param {Function} props.onToggle - Função para toggle
 * @param {boolean} props.isMobile - Se está em modo mobile
 * @param {Object} props.conversationProps - Props para lista de conversas
 * @param {Object} props.projectProps - Props para lista de projetos
 * @param {Object} props.taskProps - Props para lista de tarefas
 * @param {Object} props.navigationProps - Props para navegação
 * @param {Function} props.t - Função de tradução
 */
const LeftSidebar = ({
  styles,
  collapsed,
  onToggle,
  isMobile,
  conversationProps,
  projectProps,
  taskProps,
  navigationProps,
  t
}) => {
  const sidebarStyles = {
    ...styles.leftSidebar,
    ...(collapsed ? styles.leftSidebarCollapsed : {}),
    ...(isMobile ? styles.leftSidebarMobile : {})
  };

  return (
    <div style={sidebarStyles}>
      {/* Sidebar Header */}
      <div style={styles.sidebarHeader}>
        <div style={styles.sidebarTitle}>
          {t ? t('navigation') : 'Navigation'}
        </div>
        
        {!isMobile && (
          <button
            style={styles.sidebarToggle}
            onClick={onToggle}
            title={t ? t('collapse_sidebar') : 'Collapse Sidebar'}
          >
            «
          </button>
        )}
      </div>

      {/* Navigation Menu */}
      <div style={styles.navigationMenu}>
        <button style={styles.navItem}>
          <span style={styles.navIcon}>?</span>
          <span style={styles.navText}>
            {t ? t('dashboard') : 'Dashboard'}
          </span>
        </button>

        <button style={styles.navItem}>
          <span style={styles.navIcon}>!</span>
          <span style={styles.navText}>
            {t ? t('conversations') : 'Conversations'}
          </span>
        </button>

        <button style={styles.navItem}>
          <span style={styles.navIcon}>#</span>
          <span style={styles.navText}>
            {t ? t('projects') : 'Projects'}
          </span>
        </button>

        <button style={styles.navItem}>
          <span style={styles.navIcon}>@</span>
          <span style={styles.navText}>
            {t ? t('tasks') : 'Tasks'}
          </span>
        </button>

        <button style={styles.navItem}>
          <span style={styles.navIcon}>$</span>
          <span style={styles.navText}>
            {t ? t('skills') : 'Skills'}
          </span>
        </button>

        <button style={styles.navItem}>
          <span style={styles.navIcon}>%</span>
          <span style={styles.navText}>
            {t ? t('experts') : 'Experts'}
          </span>
        </button>
      </div>

      {/* Divider */}
      <div style={styles.sidebarDivider} />

      {/* Quick Actions */}
      <div style={styles.quickActions}>
        <button style={styles.quickActionButton}>
          <span style={styles.quickActionIcon}>+</span>
          <span style={styles.quickActionText}>
            {t ? t('new_conversation') : 'New Conversation'}
          </span>
        </button>

        <button style={styles.quickActionButton}>
          <span style={styles.quickActionIcon}>+</span>
          <span style={styles.quickActionText}>
            {t ? t('new_project') : 'New Project'}
          </span>
        </button>

        <button style={styles.quickActionButton}>
          <span style={styles.quickActionIcon}>+</span>
          <span style={styles.quickActionText}>
            {t ? t('new_task') : 'New Task'}
          </span>
        </button>
      </div>

      {/* Divider */}
      <div style={styles.sidebarDivider} />

      {/* Recent Items */}
      <div style={styles.recentItems}>
        <div style={styles.recentItemsHeader}>
          {t ? t('recent') : 'Recent'}
        </div>

        <div style={styles.recentItemList}>
          <button style={styles.recentItem}>
            <span style={styles.recentItemIcon}>!</span>
            <div style={styles.recentItemContent}>
              <div style={styles.recentItemTitle}>
                {t ? t('project_discussion') : 'Project Discussion'}
              </div>
              <div style={styles.recentItemMeta}>
                2 {t ? t('hours_ago') : 'hours ago'}
              </div>
            </div>
          </button>

          <button style={styles.recentItem}>
            <span style={styles.recentItemIcon}>#</span>
            <div style={styles.recentItemContent}>
              <div style={styles.recentItemTitle}>
                {t ? t('website_redesign') : 'Website Redesign'}
              </div>
              <div style={styles.recentItemMeta}>
                5 {t ? t('hours_ago') : 'hours ago'}
              </div>
            </div>
          </button>

          <button style={styles.recentItem}>
            <span style={styles.recentItemIcon}>@</span>
            <div style={styles.recentItemContent}>
              <div style={styles.recentItemTitle}>
                {t ? t('bug_fixes') : 'Bug Fixes'}
              </div>
              <div style={styles.recentItemMeta}>
                1 {t ? t('day_ago') : 'day ago'}
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Divider */}
      <div style={styles.sidebarDivider} />

      {/* Storage Info */}
      <div style={styles.storageInfo}>
        <div style={styles.storageHeader}>
          {t ? t('storage') : 'Storage'}
        </div>
        
        <div style={styles.storageBar}>
          <div style={styles.storageBarFill} />
        </div>
        
        <div style={styles.storageText}>
          2.3 GB / 5 GB {t ? t('used') : 'used'}
        </div>
      </div>

      {/* Mobile Close Button */}
      {isMobile && (
        <div style={styles.mobileCloseSection}>
          <button
            style={styles.mobileCloseButton}
            onClick={onToggle}
          >
            {t ? t('close_sidebar') : 'Close Sidebar'}
          </button>
        </div>
      )}
    </div>
  );
};

export default LeftSidebar;
