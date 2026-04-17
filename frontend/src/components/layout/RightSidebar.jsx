import React from 'react';

/**
 * RightSidebar - Sidebar direita com painéis de configuração e informações.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {boolean} props.collapsed - Se está colapsada
 * @param {Function} props.onToggle - Função para toggle
 * @param {boolean} props.isMobile - Se está em modo mobile
 * @param {Object} props.doctorProps - Props para painel do doctor
 * @param {Object} props.executionProps - Props para painel de execução
 * @param {Object} props.logsProps - Props para painel de logs
 * @param {Object} props.settingsProps - Props para painel de configurações
 * @param {Function} props.t - Função de tradução
 */
const RightSidebar = ({
  styles,
  collapsed,
  onToggle,
  isMobile,
  doctorProps,
  executionProps,
  logsProps,
  settingsProps,
  t
}) => {
  const sidebarStyles = {
    ...styles.rightSidebar,
    ...(collapsed ? styles.rightSidebarCollapsed : {}),
    ...(isMobile ? styles.rightSidebarMobile : {})
  };

  return (
    <div style={sidebarStyles}>
      {/* Sidebar Header */}
      <div style={styles.sidebarHeader}>
        <div style={styles.sidebarTitle}>
          {t ? t('panels') : 'Panels'}
        </div>
        
        {!isMobile && (
          <button
            style={styles.sidebarToggle}
            onClick={onToggle}
            title={t ? t('collapse_sidebar') : 'Collapse Sidebar'}
          >
            »
          </button>
        )}
      </div>

      {/* Panel Tabs */}
      <div style={styles.panelTabs}>
        <button style={styles.panelTab}>
          <span style={styles.panelTabIcon}>!</span>
          <span style={styles.panelTabText}>
            {t ? t('doctor') : 'Doctor'}
          </span>
        </button>

        <button style={styles.panelTab}>
          <span style={styles.panelTabIcon}>$</span>
          <span style={styles.panelTabText}>
            {t ? t('execution') : 'Execution'}
          </span>
        </button>

        <button style={styles.panelTab}>
          <span style={styles.panelTabIcon}>#</span>
          <span style={styles.panelTabText}>
            {t ? t('logs') : 'Logs'}
          </span>
        </button>

        <button style={styles.panelTab}>
          <span style={styles.panelTabIcon}>%</span>
          <span style={styles.panelTabText}>
            {t ? t('settings') : 'Settings'}
          </span>
        </button>
      </div>

      {/* Divider */}
      <div style={styles.sidebarDivider} />

      {/* System Status */}
      <div style={styles.systemStatus}>
        <div style={styles.systemStatusHeader}>
          {t ? t('system_status') : 'System Status'}
        </div>

        <div style={styles.statusItem}>
          <div style={styles.statusIndicator} />
          <span style={styles.statusText}>
            {t ? t('api_connected') : 'API Connected'}
          </span>
        </div>

        <div style={styles.statusItem}>
          <div style={styles.statusIndicator} />
          <span style={styles.statusText}>
            {t ? t('database_online') : 'Database Online'}
          </span>
        </div>

        <div style={styles.statusItem}>
          <div style={{...styles.statusIndicator, ...styles.statusWarning}} />
          <span style={styles.statusText}>
            {t ? t('high_memory_usage') : 'High Memory Usage'}
          </span>
        </div>

        <div style={styles.statusItem}>
          <div style={styles.statusIndicator} />
          <span style={styles.statusText}>
            {t ? t('cache_updated') : 'Cache Updated'}
          </span>
        </div>
      </div>

      {/* Divider */}
      <div style={styles.sidebarDivider} />

      {/* Quick Stats */}
      <div style={styles.quickStats}>
        <div style={styles.quickStatsHeader}>
          {t ? t('quick_stats') : 'Quick Stats'}
        </div>

        <div style={styles.statRow}>
          <span style={styles.statLabel}>
            {t ? t('active_conversations') : 'Active Conversations'}:
          </span>
          <span style={styles.statValue}>3</span>
        </div>

        <div style={styles.statRow}>
          <span style={styles.statLabel}>
            {t ? t('running_tasks') : 'Running Tasks'}:
          </span>
          <span style={styles.statValue}>1</span>
        </div>

        <div style={styles.statRow}>
          <span style={styles.statLabel}>
            {t ? t('total_projects') : 'Total Projects'}:
          </span>
          <span style={styles.statValue}>12</span>
        </div>

        <div style={styles.statRow}>
          <span style={styles.statLabel}>
            {t ? t('completed_today') : 'Completed Today'}:
          </span>
          <span style={styles.statValue}>8</span>
        </div>

        <div style={styles.statRow}>
          <span style={styles.statLabel}>
            {t ? t('errors_today') : 'Errors Today'}:
          </span>
          <span style={styles.statValue}>2</span>
        </div>
      </div>

      {/* Divider */}
      <div style={styles.sidebarDivider} />

      {/* Recent Activity */}
      <div style={styles.recentActivity}>
        <div style={styles.recentActivityHeader}>
          {t ? t('recent_activity') : 'Recent Activity'}
        </div>

        <div style={styles.activityList}>
          <div style={styles.activityItem}>
            <div style={styles.activityIcon}>
              <span>!</span>
            </div>
            <div style={styles.activityContent}>
              <div style={styles.activityTitle}>
                {t ? t('command_executed') : 'Command Executed'}
              </div>
              <div style={styles.activityDescription}>
                npm install --save react
              </div>
              <div style={styles.activityTime}>
                2 {t ? t('minutes_ago') : 'minutes ago'}
              </div>
            </div>
          </div>

          <div style={styles.activityItem}>
            <div style={styles.activityIcon}>
              <span>#</span>
            </div>
            <div style={styles.activityContent}>
              <div style={styles.activityTitle}>
                {t ? t('project_created') : 'Project Created'}
              </div>
              <div style={styles.activityDescription}>
                {t ? t('new_web_project') : 'New Web Project'}
              </div>
              <div style={styles.activityTime}>
                15 {t ? t('minutes_ago') : 'minutes ago'}
              </div>
            </div>
          </div>

          <div style={styles.activityItem}>
            <div style={styles.activityIcon}>
              <span>@</span>
            </div>
            <div style={styles.activityContent}>
              <div style={styles.activityTitle}>
                {t ? t('task_completed') : 'Task Completed'}
              </div>
              <div style={styles.activityDescription}>
                {t ? t('bug_fixed') : 'Bug Fixed'}
              </div>
              <div style={styles.activityTime}>
                1 {t ? t('hour_ago') : 'hour ago'}
              </div>
            </div>
          </div>

          <div style={styles.activityItem}>
            <div style={styles.activityIcon}>
              <span>$</span>
            </div>
            <div style={styles.activityContent}>
              <div style={styles.activityTitle}>
                {t ? t('skill_updated') : 'Skill Updated'}
              </div>
              <div style={styles.activityDescription}>
                {t ? t('python_analyzer') : 'Python Analyzer'}
              </div>
              <div style={styles.activityTime}>
                2 {t ? t('hours_ago') : 'hours ago'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div style={styles.sidebarDivider} />

      {/* Performance Metrics */}
      <div style={styles.performanceMetrics}>
        <div style={styles.performanceHeader}>
          {t ? t('performance') : 'Performance'}
        </div>

        <div style={styles.metricRow}>
          <span style={styles.metricLabel}>
            {t ? t('cpu_usage') : 'CPU Usage'}:
          </span>
          <div style={styles.metricBar}>
            <div style={{...styles.metricBarFill, width: '35%'}} />
          </div>
          <span style={styles.metricValue}>35%</span>
        </div>

        <div style={styles.metricRow}>
          <span style={styles.metricLabel}>
            {t ? t('memory_usage') : 'Memory Usage'}:
          </span>
          <div style={styles.metricBar}>
            <div style={{...styles.metricBarFill, width: '78%'}} />
          </div>
          <span style={styles.metricValue}>78%</span>
        </div>

        <div style={styles.metricRow}>
          <span style={styles.metricLabel}>
            {t ? t('disk_usage') : 'Disk Usage'}:
          </span>
          <div style={styles.metricBar}>
            <div style={{...styles.metricBarFill, width: '45%'}} />
          </div>
          <span style={styles.metricValue}>45%</span>
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

export default RightSidebar;
