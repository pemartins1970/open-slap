import React, { useState } from 'react';

/**
 * Header - Cabeçalho principal da aplicação com navegação e controles.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {Object} props.user - Dados do usuário
 * @param {boolean} props.leftSidebarCollapsed - Se a sidebar esquerda está colapsada
 * @param {boolean} props.rightSidebarCollapsed - Se a sidebar direita está colapsada
 * @param {Function} props.onToggleLeftSidebar - Toggle da sidebar esquerda
 * @param {Function} props.onToggleRightSidebar - Toggle da sidebar direita
 * @param {boolean} props.isMobile - Se está em modo mobile
 * @param {Function} props.t - Função de tradução
 */
const Header = ({
  styles,
  user,
  leftSidebarCollapsed,
  rightSidebarCollapsed,
  onToggleLeftSidebar,
  onToggleRightSidebar,
  isMobile,
  t
}) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const handleUserMenuToggle = () => {
    setShowUserMenu(!showUserMenu);
    setShowNotifications(false);
  };

  const handleNotificationsToggle = () => {
    setShowNotifications(!showNotifications);
    setShowUserMenu(false);
  };

  const handleClickOutside = () => {
    setShowUserMenu(false);
    setShowNotifications(false);
  };

  return (
    <>
      <div style={styles.header}>
        {/* Left Section */}
        <div style={styles.headerLeft}>
          {/* Logo */}
          <div style={styles.headerLogo}>
            <span style={styles.logoText}>
              {t ? t('app_name') : 'Antigravity'}
            </span>
          </div>

          {/* Sidebar Toggle */}
          <button
            style={styles.headerButton}
            onClick={onToggleLeftSidebar}
            title={leftSidebarCollapsed ? 'Show Sidebar' : 'Hide Sidebar'}
          >
            {leftSidebarCollapsed ? '»' : '«'}
          </button>
        </div>

        {/* Center Section */}
        <div style={styles.headerCenter}>
          {/* Search Bar */}
          <div style={styles.headerSearch}>
            <input
              style={styles.searchInput}
              type="text"
              placeholder={t ? t('search_placeholder') : 'Search...'}
            />
            <button style={styles.searchButton}>
              {t ? t('search') : 'Search'}
            </button>
          </div>
        </div>

        {/* Right Section */}
        <div style={styles.headerRight}>
          {/* Notifications */}
          <div style={styles.headerNotifications}>
            <button
              style={styles.headerButton}
              onClick={handleNotificationsToggle}
              title={t ? t('notifications') : 'Notifications'}
            >
              <span style={styles.notificationIcon}>?</span>
              <span style={styles.notificationBadge}>3</span>
            </button>
          </div>

          {/* User Menu */}
          <div style={styles.headerUser}>
            <button
              style={styles.userButton}
              onClick={handleUserMenuToggle}
              title={t ? t('user_menu') : 'User Menu'}
            >
              <div style={styles.userAvatar}>
                {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
              </div>
              <span style={styles.userName}>
                {user?.name || user?.email || 'User'}
              </span>
              <span style={styles.userDropdown}>v</span>
            </button>
          </div>

          {/* Right Sidebar Toggle */}
          <button
            style={styles.headerButton}
            onClick={onToggleRightSidebar}
            title={rightSidebarCollapsed ? 'Show Right Panel' : 'Hide Right Panel'}
          >
            {rightSidebarCollapsed ? '«' : '»'}
          </button>
        </div>
      </div>

      {/* User Menu Dropdown */}
      {showUserMenu && (
        <div style={styles.dropdownMenu}>
          <div style={styles.dropdownHeader}>
            <div style={styles.userInfo}>
              <div style={styles.userAvatarLarge}>
                {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
              </div>
              <div style={styles.userDetails}>
                <div style={styles.userFullName}>
                  {user?.name || 'User'}
                </div>
                <div style={styles.userEmail}>
                  {user?.email || 'user@example.com'}
                </div>
              </div>
            </div>
          </div>

          <div style={styles.dropdownContent}>
            <button style={styles.dropdownItem}>
              {t ? t('profile') : 'Profile'}
            </button>
            <button style={styles.dropdownItem}>
              {t ? t('settings') : 'Settings'}
            </button>
            <button style={styles.dropdownItem}>
              {t ? t('preferences') : 'Preferences'}
            </button>
            <div style={styles.dropdownSeparator} />
            <button style={styles.dropdownItem}>
              {t ? t('help') : 'Help'}
            </button>
            <button style={styles.dropdownItem}>
              {t ? t('about') : 'About'}
            </button>
            <div style={styles.dropdownSeparator} />
            <button style={{...styles.dropdownItem, ...styles.dropdownItemDanger}}>
              {t ? t('logout') : 'Logout'}
            </button>
          </div>
        </div>
      )}

      {/* Notifications Dropdown */}
      {showNotifications && (
        <div style={styles.dropdownMenu}>
          <div style={styles.dropdownHeader}>
            <h4 style={styles.dropdownTitle}>
              {t ? t('notifications') : 'Notifications'}
            </h4>
          </div>

          <div style={styles.dropdownContent}>
            <div style={styles.notificationItem}>
              <div style={styles.notificationIcon}>
                <span style={styles.notificationTypeIcon}>!</span>
              </div>
              <div style={styles.notificationContent}>
                <div style={styles.notificationTitle}>
                  {t ? t('system_update') : 'System Update'}
                </div>
                <div style={styles.notificationMessage}>
                  {t ? t('new_version_available') : 'A new version is available'}
                </div>
                <div style={styles.notificationTime}>
                  2 {t ? t('hours_ago') : 'hours ago'}
                </div>
              </div>
            </div>

            <div style={styles.notificationItem}>
              <div style={styles.notificationIcon}>
                <span style={styles.notificationTypeIcon}>?</span>
              </div>
              <div style={styles.notificationContent}>
                <div style={styles.notificationTitle}>
                  {t ? t('task_completed') : 'Task Completed'}
                </div>
                <div style={styles.notificationMessage}>
                  {t ? t('task_finished_successfully') : 'Task finished successfully'}
                </div>
                <div style={styles.notificationTime}>
                  5 {t ? t('minutes_ago') : 'minutes ago'}
                </div>
              </div>
            </div>

            <div style={styles.notificationItem}>
              <div style={styles.notificationIcon}>
                <span style={styles.notificationTypeIcon}>×</span>
              </div>
              <div style={styles.notificationContent}>
                <div style={styles.notificationTitle}>
                  {t ? t('error_occurred') : 'Error Occurred'}
                </div>
                <div style={styles.notificationMessage}>
                  {t ? t('failed_to_execute_command') : 'Failed to execute command'}
                </div>
                <div style={styles.notificationTime}>
                  1 {t ? t('hour_ago') : 'hour ago'}
                </div>
              </div>
            </div>

            <div style={styles.dropdownFooter}>
              <button style={styles.dropdownItem}>
                {t ? t('view_all_notifications') : 'View All Notifications'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Overlay for mobile */}
      {(showUserMenu || showNotifications) && (
        <div
          style={styles.dropdownOverlay}
          onClick={handleClickOutside}
        />
      )}
    </>
  );
};

export default Header;
