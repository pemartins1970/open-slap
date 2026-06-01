import React, { useState, useEffect } from 'react';
import { formatCompactDateTime } from '../../lib/utils/formatters';

/**
 * DoctorPanel - Painel de diagnóstico e monitoramento do sistema.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {Object} props.doctorReport - Relatório do doctor
 * @param {boolean} props.loading - Se está carregando
 * @param {Function} props.onRefresh - Função para atualizar
 * @param {Function} props.onRunCheck - Função para executar check
 * @param {Function} props.onLoadSystemMap - Função para carregar mapa do sistema
 * @param {Function} props.t - Função de tradução
 */
const DoctorPanel = ({
  styles,
  doctorReport,
  loading,
  onRefresh,
  onRunCheck,
  onLoadSystemMap,
  t
}) => {
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    checks: false,
    systemMap: false,
    recommendations: false
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return styles.statusHealthy;
      case 'warning': return styles.statusWarning;
      case 'error': return styles.statusError;
      case 'unknown': return styles.statusUnknown;
      default: return styles.statusDefault;
    }
  };

  const getChecksByStatus = (status) => {
    if (!doctorReport?.checks) return [];
    return doctorReport.checks.filter(check => check.status === status);
  };

  const getSystemStatus = () => {
    if (!doctorReport?.checks) return 'unknown';
    
    const hasErrors = doctorReport.checks.some(check => check.status === 'error');
    const hasWarnings = doctorReport.checks.some(check => check.status === 'warning');
    
    if (hasErrors) return 'error';
    if (hasWarnings) return 'warning';
    return 'healthy';
  };

  const systemStatus = getSystemStatus();

  return (
    <div style={styles.panel}>
      <div style={styles.panelHeader}>
        <h3 style={styles.panelTitle}>
          {t ? t('system_doctor') : 'System Doctor'}
          <span style={{...styles.statusBadge, ...getStatusColor(systemStatus)}}>
            {t ? t(systemStatus) : systemStatus}
          </span>
        </h3>
        <div style={styles.panelActions}>
          <button
            style={styles.panelButton}
            onClick={onRefresh}
            disabled={loading}
            title={t ? t('refresh') : 'Refresh'}
          >
            {loading ? '...' : 'Refresh'}
          </button>
          <button
            style={styles.panelButton}
            onClick={onRunCheck}
            disabled={loading}
            title={t ? t('run_check') : 'Run Check'}
          >
            {t ? t('check') : 'Check'}
          </button>
        </div>
      </div>

      <div style={styles.panelContent}>
        {/* Overview Section */}
        <div style={styles.panelSection}>
          <div
            style={styles.sectionHeader}
            onClick={() => toggleSection('overview')}
          >
            <h4 style={styles.sectionTitle}>
              {t ? t('overview') : 'Overview'}
            </h4>
            <span style={styles.sectionToggle}>
              {expandedSections.overview ? 'v' : '>'}
            </span>
          </div>
          
          {expandedSections.overview && (
            <div style={styles.sectionContent}>
              {doctorReport ? (
                <div style={styles.overviewGrid}>
                  <div style={styles.overviewItem}>
                    <div style={styles.overviewLabel}>
                      {t ? t('last_check') : 'Last Check'}
                    </div>
                    <div style={styles.overviewValue}>
                      {formatCompactDateTime(doctorReport.timestamp)}
                    </div>
                  </div>
                  
                  <div style={styles.overviewItem}>
                    <div style={styles.overviewLabel}>
                      {t ? t('total_checks') : 'Total Checks'}
                    </div>
                    <div style={styles.overviewValue}>
                      {doctorReport.checks?.length || 0}
                    </div>
                  </div>
                  
                  <div style={styles.overviewItem}>
                    <div style={styles.overviewLabel}>
                      {t ? t('issues_found') : 'Issues Found'}
                    </div>
                    <div style={styles.overviewValue}>
                      {getChecksByStatus('error').length + getChecksByStatus('warning').length}
                    </div>
                  </div>
                  
                  <div style={styles.overviewItem}>
                    <div style={styles.overviewLabel}>
                      {t ? t('system_health') : 'System Health'}
                    </div>
                    <div style={{...styles.overviewValue, ...getStatusColor(systemStatus)}}>
                      {t ? t(systemStatus) : systemStatus}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={styles.emptyState}>
                  {t ? t('no_data_available') : 'No data available'}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Checks Section */}
        <div style={styles.panelSection}>
          <div
            style={styles.sectionHeader}
            onClick={() => toggleSection('checks')}
          >
            <h4 style={styles.sectionTitle}>
              {t ? t('system_checks') : 'System Checks'}
            </h4>
            <span style={styles.sectionToggle}>
              {expandedSections.checks ? 'v' : '>'}
            </span>
          </div>
          
          {expandedSections.checks && (
            <div style={styles.sectionContent}>
              {doctorReport?.checks?.length > 0 ? (
                <div style={styles.checksList}>
                  {doctorReport.checks.map((check, index) => (
                    <div key={index} style={styles.checkItem}>
                      <div style={styles.checkHeader}>
                        <span style={styles.checkName}>
                          {check.name}
                        </span>
                        <span style={{...styles.statusBadge, ...getStatusColor(check.status)}}>
                          {t ? t(check.status) : check.status}
                        </span>
                      </div>
                      {check.message && (
                        <div style={styles.checkMessage}>
                          {check.message}
                        </div>
                      )}
                      {check.details && (
                        <div style={styles.checkDetails}>
                          <pre style={styles.checkDetailsPre}>
                            {JSON.stringify(check.details, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={styles.emptyState}>
                  {t ? t('no_checks_performed') : 'No checks performed'}
                </div>
              )}
            </div>
          )}
        </div>

        {/* System Map Section */}
        <div style={styles.panelSection}>
          <div
            style={styles.sectionHeader}
            onClick={() => toggleSection('systemMap')}
          >
            <h4 style={styles.sectionTitle}>
              {t ? t('system_map') : 'System Map'}
            </h4>
            <span style={styles.sectionToggle}>
              {expandedSections.systemMap ? 'v' : '>'}
            </span>
          </div>
          
          {expandedSections.systemMap && (
            <div style={styles.sectionContent}>
              <div style={styles.systemMapContainer}>
                <button
                  style={styles.panelButton}
                  onClick={onLoadSystemMap}
                  disabled={loading}
                >
                  {t ? t('load_system_map') : 'Load System Map'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Recommendations Section */}
        <div style={styles.panelSection}>
          <div
            style={styles.sectionHeader}
            onClick={() => toggleSection('recommendations')}
          >
            <h4 style={styles.sectionTitle}>
              {t ? t('recommendations') : 'Recommendations'}
            </h4>
            <span style={styles.sectionToggle}>
              {expandedSections.recommendations ? 'v' : '>'}
            </span>
          </div>
          
          {expandedSections.recommendations && (
            <div style={styles.sectionContent}>
              <div style={styles.recommendationsList}>
                {getChecksByStatus('error').map((check, index) => (
                  <div key={index} style={styles.recommendationItem}>
                    <div style={styles.recommendationTitle}>
                      {t ? t('fix_issue') : 'Fix Issue'}: {check.name}
                    </div>
                    <div style={styles.recommendationDescription}>
                      {check.message}
                    </div>
                  </div>
                ))}
                
                {getChecksByStatus('warning').map((check, index) => (
                  <div key={index} style={styles.recommendationItem}>
                    <div style={styles.recommendationTitle}>
                      {t ? t('review_warning') : 'Review Warning'}: {check.name}
                    </div>
                    <div style={styles.recommendationDescription}>
                      {check.message}
                    </div>
                  </div>
                ))}
                
                {getChecksByStatus('error').length === 0 && 
                 getChecksByStatus('warning').length === 0 && (
                  <div style={styles.emptyState}>
                    {t ? t('no_recommendations') : 'No recommendations - System is healthy!'}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DoctorPanel;
