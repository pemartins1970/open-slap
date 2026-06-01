import React, { useState, useEffect, useRef } from 'react';
import { formatCompactDateTime } from '../../lib/utils/formatters';

/**
 * LogPanel - Painel de visualização de logs do sistema.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {Array} props.logs - Array de logs
 * @param {boolean} props.loading - Se está carregando
 * @param {boolean} props.realTimeMode - Se está em modo tempo real
 * @param {Function} props.onRefresh - Função para atualizar logs
 * @param {Function} props.onClearLogs - Função para limpar logs
 * @param {Function} props.onExportLogs - Função para exportar logs
 * @param {Function} props.onToggleRealTime - Função para alternar modo tempo real
 * @param {Function} props.t - Função de tradução
 */
const LogPanel = ({
  styles,
  logs = [],
  loading,
  realTimeMode,
  onRefresh,
  onClearLogs,
  onExportLogs,
  onToggleRealTime,
  t
}) => {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedLogs, setExpandedLogs] = useState(new Set());
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef(null);

  const toggleLogExpansion = (logId) => {
    setExpandedLogs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(logId)) {
        newSet.delete(logId);
      } else {
        newSet.add(logId);
      }
      return newSet;
    });
  };

  const getFilteredLogs = () => {
    let filtered = [...logs];

    // Filter by level
    if (filter !== 'all') {
      filtered = filtered.filter(log => log.level === filter);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (log.source && log.source.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (log.context && JSON.stringify(log.context).toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Sort by timestamp (newest first)
    return filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  };

  const getLogLevelColor = (level) => {
    switch (level) {
      case 'error': return styles.logError;
      case 'warn': return styles.logWarning;
      case 'info': return styles.logInfo;
      case 'debug': return styles.logDebug;
      case 'trace': return styles.logTrace;
      default: return styles.logDefault;
    }
  };

  const getLogLevelIcon = (level) => {
    switch (level) {
      case 'error': return '×';
      case 'warn': return '!';
      case 'info': return 'i';
      case 'debug': return 'D';
      case 'trace': return 'T';
      default: return '?';
    }
  };

  const filteredLogs = getFilteredLogs();

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logContainerRef.current && realTimeMode) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [filteredLogs, autoScroll, realTimeMode]);

  const handleScroll = () => {
    if (logContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      setAutoScroll(isAtBottom);
    }
  };

  const getLogStats = () => {
    const stats = {
      total: logs.length,
      error: logs.filter(log => log.level === 'error').length,
      warn: logs.filter(log => log.level === 'warn').length,
      info: logs.filter(log => log.level === 'info').length,
      debug: logs.filter(log => log.level === 'debug').length,
      trace: logs.filter(log => log.level === 'trace').length
    };
    return stats;
  };

  const stats = getLogStats();

  return (
    <div style={styles.panel}>
      <div style={styles.panelHeader}>
        <h3 style={styles.panelTitle}>
          {t ? t('system_logs') : 'System Logs'}
          <span style={styles.panelBadge}>
            {filteredLogs.length} {t ? t('entries') : 'entries'}
          </span>
          {realTimeMode && (
            <span style={styles.realTimeIndicator}>
              {t ? t('real_time') : 'Real-time'}
            </span>
          )}
        </h3>
        <div style={styles.panelActions}>
          <button
            style={styles.panelButton}
            onClick={onToggleRealTime}
            title={realTimeMode ? 'Stop Real-time' : 'Start Real-time'}
          >
            {realTimeMode ? 'Pause' : 'Play'}
          </button>
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
            onClick={onExportLogs}
            title={t ? t('export_logs') : 'Export Logs'}
          >
            Export
          </button>
          <button
            style={styles.panelButton}
            onClick={onClearLogs}
            title={t ? t('clear_logs') : 'Clear Logs'}
          >
            Clear
          </button>
        </div>
      </div>

      <div style={styles.panelContent}>
        {/* Filters and Controls */}
        <div style={styles.panelFilters}>
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>
              {t ? t('level') : 'Level'}:
            </label>
            <select
              style={styles.filterSelect}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">{t ? t('all') : 'All'}</option>
              <option value="error">{t ? t('error') : 'Error'}</option>
              <option value="warn">{t ? t('warning') : 'Warning'}</option>
              <option value="info">{t ? t('info') : 'Info'}</option>
              <option value="debug">{t ? t('debug') : 'Debug'}</option>
              <option value="trace">{t ? t('trace') : 'Trace'}</option>
            </select>
          </div>

          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>
              {t ? t('search') : 'Search'}:
            </label>
            <input
              style={styles.filterInput}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={t ? t('search_logs') : 'Search logs...'}
            />
          </div>

          <div style={styles.filterGroup}>
            <label style={styles.filterCheckbox}>
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
              />
              {t ? t('auto_scroll') : 'Auto Scroll'}
            </label>
          </div>
        </div>

        {/* Statistics */}
        <div style={styles.logStats}>
          <div style={styles.statItem}>
            <span style={styles.statLabel}>
              {t ? t('total') : 'Total'}:
            </span>
            <span style={styles.statValue}>
              {stats.total}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={{...styles.statLabel, ...styles.logError}}>
              {t ? t('errors') : 'Errors'}:
            </span>
            <span style={styles.statValue}>
              {stats.error}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={{...styles.statLabel, ...styles.logWarning}}>
              {t ? t('warnings') : 'Warnings'}:
            </span>
            <span style={styles.statValue}>
              {stats.warn}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={{...styles.statLabel, ...styles.logInfo}}>
              {t ? t('info') : 'Info'}:
            </span>
            <span style={styles.statValue}>
              {stats.info}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={styles.statLabel}>
              {t ? t('filtered') : 'Filtered'}:
            </span>
            <span style={styles.statValue}>
              {filteredLogs.length}
            </span>
          </div>
        </div>

        {/* Logs Container */}
        <div
          ref={logContainerRef}
          style={styles.logsContainer}
          onScroll={handleScroll}
        >
          {filteredLogs.length === 0 ? (
            <div style={styles.emptyState}>
              {searchTerm || filter !== 'all'
                ? (t ? t('no_logs_found') : 'No logs found')
                : (t ? t('no_logs_available') : 'No logs available')
              }
            </div>
          ) : (
            filteredLogs.map((log) => {
              const isExpanded = expandedLogs.has(log.id);
              
              return (
                <div
                  key={log.id}
                  style={{
                    ...styles.logItem,
                    ...getLogLevelColor(log.level)
                  }}
                >
                  <div style={styles.logHeader}>
                    <div style={styles.logMain}>
                      <div style={styles.logIcon}>
                        {getLogLevelIcon(log.level)}
                      </div>
                      
                      <div style={styles.logInfo}>
                        <div style={styles.logMessage}>
                          {log.message}
                        </div>
                        
                        <div style={styles.logMeta}>
                          <span style={styles.logTimestamp}>
                            {formatCompactDateTime(log.timestamp)}
                          </span>
                          
                          {log.source && (
                            <span style={styles.logSource}>
                              {log.source}
                            </span>
                          )}
                          
                          {log.thread && (
                            <span style={styles.logThread}>
                              Thread: {log.thread}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div style={styles.logActions}>
                      <button
                        style={styles.logExpand}
                        onClick={() => toggleLogExpansion(log.id)}
                        title={isExpanded ? 'Collapse' : 'Expand'}
                      >
                        {isExpanded ? 'v' : '>'}
                      </button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div style={styles.logDetails}>
                      {log.context && Object.keys(log.context).length > 0 && (
                        <div style={styles.logContext}>
                          <strong>{t ? t('context') : 'Context'}:</strong>
                          <pre style={styles.logContextPre}>
                            {JSON.stringify(log.context, null, 2)}
                          </pre>
                        </div>
                      )}

                      {log.stackTrace && (
                        <div style={styles.logStackTrace}>
                          <strong>{t ? t('stack_trace') : 'Stack Trace'}:</strong>
                          <pre style={styles.logStackTracePre}>
                            {log.stackTrace}
                          </pre>
                        </div>
                      )}

                      {log.userId && (
                        <div style={styles.logUser}>
                          <strong>{t ? t('user_id') : 'User ID'}:</strong>
                          <span>{log.userId}</span>
                        </div>
                      )}

                      {log.sessionId && (
                        <div style={styles.logSession}>
                          <strong>{t ? t('session_id') : 'Session ID'}:</strong>
                          <span>{log.sessionId}</span>
                        </div>
                      )}

                      {log.requestId && (
                        <div style={styles.logRequest}>
                          <strong>{t ? t('request_id') : 'Request ID'}:</strong>
                          <span>{log.requestId}</span>
                        </div>
                      )}

                      {log.duration && (
                        <div style={styles.logDuration}>
                          <strong>{t ? t('duration') : 'Duration'}:</strong>
                          <span>{log.duration}ms</span>
                        </div>
                      )}

                      {log.metadata && Object.keys(log.metadata).length > 0 && (
                        <div style={styles.logMetadata}>
                          <strong>{t ? t('metadata') : 'Metadata'}:</strong>
                          <pre style={styles.logMetadataPre}>
                            {JSON.stringify(log.metadata, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Auto-scroll indicator */}
        {!autoScroll && (
          <div style={styles.autoScrollIndicator}>
            <button
              style={styles.autoScrollButton}
              onClick={() => {
                if (logContainerRef.current) {
                  logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
                }
                setAutoScroll(true);
              }}
            >
              {t ? t('scroll_to_bottom') : 'Scroll to Bottom'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default LogPanel;
