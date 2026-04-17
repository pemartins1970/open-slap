import React, { useState, useEffect } from 'react';
import { formatCompactDateTime } from '../../lib/utils/formatters';

/**
 * ExecutionPanel - Painel de execução de comandos e tarefas.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {Object} props.executionState - Estado da execução
 * @param {Array} props.commandHistory - Histórico de comandos
 * @param {Array} props.activeCommands - Comandos em execução
 * @param {boolean} props.showExecutionPanel - Se o painel está visível
 * @param {Function} props.setShowExecutionPanel - Função para alternar visibilidade
 * @param {Function} props.onExecuteCommand - Função para executar comando
 * @param {Function} props.onStopCommand - Função para parar comando
 * @param {Function} props.onClearHistory - Função para limpar histórico
 * @param {Function} props.t - Função de tradução
 */
const ExecutionPanel = ({
  styles,
  executionState = {},
  commandHistory = [],
  activeCommands = [],
  showExecutionPanel,
  setShowExecutionPanel,
  onExecuteCommand,
  onStopCommand,
  onClearHistory,
  t
}) => {
  const [expandedCommands, setExpandedCommands] = useState(new Set());
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const toggleCommandExpansion = (commandId) => {
    setExpandedCommands(prev => {
      const newSet = new Set(prev);
      if (newSet.has(commandId)) {
        newSet.delete(commandId);
      } else {
        newSet.add(commandId);
      }
      return newSet;
    });
  };

  const getFilteredCommands = () => {
    let commands = [...commandHistory, ...activeCommands];

    // Filter by status
    if (filter !== 'all') {
      commands = commands.filter(cmd => cmd.status === filter);
    }

    // Filter by search term
    if (searchTerm) {
      commands = commands.filter(cmd => 
        cmd.command.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (cmd.description && cmd.description.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Sort by timestamp (newest first)
    return commands.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  };

  const getCommandStatusColor = (status) => {
    switch (status) {
      case 'running': return styles.statusRunning;
      case 'completed': return styles.statusCompleted;
      case 'failed': return styles.statusFailed;
      case 'cancelled': return styles.statusCancelled;
      case 'pending': return styles.statusPending;
      default: return styles.statusDefault;
    }
  };

  const getCommandIcon = (status) => {
    switch (status) {
      case 'running': return 'spinner';
      case 'completed': return 'check';
      case 'failed': return 'cross';
      case 'cancelled': return 'stop';
      case 'pending': return 'clock';
      default: return 'question';
    }
  };

  const filteredCommands = getFilteredCommands();

  useEffect(() => {
    // Auto-expand running commands
    const runningCommandIds = activeCommands
      .filter(cmd => cmd.status === 'running')
      .map(cmd => cmd.id);
    
    setExpandedCommands(prev => new Set([...prev, ...runningCommandIds]));
  }, [activeCommands]);

  return (
    <div style={{
      ...styles.panel,
      ...(showExecutionPanel ? styles.panelVisible : styles.panelHidden)
    }}>
      <div style={styles.panelHeader}>
        <h3 style={styles.panelTitle}>
          {t ? t('execution_panel') : 'Execution Panel'}
          <span style={styles.panelBadge}>
            {activeCommands.length} {t ? t('running') : 'running'}
          </span>
        </h3>
        <div style={styles.panelActions}>
          <button
            style={styles.panelButton}
            onClick={() => setShowExecutionPanel(!showExecutionPanel)}
            title={showExecutionPanel ? 'Hide Panel' : 'Show Panel'}
          >
            {showExecutionPanel ? 'v' : '^'}
          </button>
        </div>
      </div>

      {showExecutionPanel && (
        <div style={styles.panelContent}>
          {/* Filters */}
          <div style={styles.panelFilters}>
            <div style={styles.filterGroup}>
              <label style={styles.filterLabel}>
                {t ? t('filter') : 'Filter'}:
              </label>
              <select
                style={styles.filterSelect}
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              >
                <option value="all">{t ? t('all') : 'All'}</option>
                <option value="running">{t ? t('running') : 'Running'}</option>
                <option value="completed">{t ? t('completed') : 'Completed'}</option>
                <option value="failed">{t ? t('failed') : 'Failed'}</option>
                <option value="cancelled">{t ? t('cancelled') : 'Cancelled'}</option>
                <option value="pending">{t ? t('pending') : 'Pending'}</option>
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
                placeholder={t ? t('search_commands') : 'Search commands...'}
              />
            </div>

            <div style={styles.filterGroup}>
              <button
                style={styles.filterButton}
                onClick={onClearHistory}
                title={t ? t('clear_history') : 'Clear History'}
              >
                {t ? t('clear') : 'Clear'}
              </button>
            </div>
          </div>

          {/* Commands List */}
          <div style={styles.commandsList}>
            {filteredCommands.length === 0 ? (
              <div style={styles.emptyState}>
                {t ? t('no_commands_found') : 'No commands found'}
              </div>
            ) : (
              filteredCommands.map((command) => {
                const isExpanded = expandedCommands.has(command.id);
                const isActive = activeCommands.some(cmd => cmd.id === command.id);

                return (
                  <div
                    key={command.id}
                    style={{
                      ...styles.commandItem,
                      ...(isActive ? styles.commandItemActive : {})
                    }}
                  >
                    <div style={styles.commandHeader}>
                      <div style={styles.commandMain}>
                        <div style={styles.commandIcon}>
                          {getCommandIcon(command.status)}
                        </div>
                        
                        <div style={styles.commandInfo}>
                          <div style={styles.commandText}>
                            {command.command}
                          </div>
                          
                          <div style={styles.commandMeta}>
                            <span style={styles.commandId}>
                              #{command.id}
                            </span>
                            
                            <span style={styles.commandTimestamp}>
                              {formatCompactDateTime(command.timestamp)}
                            </span>
                            
                            <span style={{
                              ...styles.commandStatus,
                              ...getCommandStatusColor(command.status)
                            }}>
                              {t ? t(command.status) : command.status}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div style={styles.commandActions}>
                        {isActive && command.status === 'running' && (
                          <button
                            style={styles.commandStop}
                            onClick={() => onStopCommand(command.id)}
                            title={t ? t('stop_command') : 'Stop Command'}
                          >
                            Stop
                          </button>
                        )}
                        
                        <button
                          style={styles.commandExpand}
                          onClick={() => toggleCommandExpansion(command.id)}
                          title={isExpanded ? 'Collapse' : 'Expand'}
                        >
                          {isExpanded ? 'v' : '>'}
                        </button>
                      </div>
                    </div>

                    {isExpanded && (
                      <div style={styles.commandDetails}>
                        {command.description && (
                          <div style={styles.commandDescription}>
                            <strong>{t ? t('description') : 'Description'}:</strong>
                            <div style={styles.commandDescriptionText}>
                              {command.description}
                            </div>
                          </div>
                        )}

                        {command.cwd && (
                          <div style={styles.commandCwd}>
                            <strong>{t ? t('working_directory') : 'Working Directory'}:</strong>
                            <code style={styles.commandCode}>
                              {command.cwd}
                            </code>
                          </div>
                        )}

                        {command.intent && (
                          <div style={styles.commandIntent}>
                            <strong>{t ? t('intent') : 'Intent'}:</strong>
                            <span>{command.intent}</span>
                          </div>
                        )}

                        {command.risk && (
                          <div style={styles.commandRisk}>
                            <strong>{t ? t('risk_level') : 'Risk Level'}:</strong>
                            <span style={{
                              ...styles.riskBadge,
                              ...(command.risk === 'high' ? styles.riskHigh :
                                 command.risk === 'medium' ? styles.riskMedium :
                                 styles.riskLow)
                            }}>
                              {t ? t(command.risk) : command.risk}
                            </span>
                          </div>
                        )}

                        {command.output && (
                          <div style={styles.commandOutput}>
                            <strong>{t ? t('output') : 'Output'}:</strong>
                            <pre style={styles.commandOutputPre}>
                              {command.output}
                            </pre>
                          </div>
                        )}

                        {command.error && (
                          <div style={styles.commandError}>
                            <strong>{t ? t('error') : 'Error'}:</strong>
                            <pre style={styles.commandErrorPre}>
                              {command.error}
                            </pre>
                          </div>
                        )}

                        {command.duration && (
                          <div style={styles.commandDuration}>
                            <strong>{t ? t('duration') : 'Duration'}:</strong>
                            <span>{command.duration}ms</span>
                          </div>
                        )}

                        {command.metadata && Object.keys(command.metadata).length > 0 && (
                          <div style={styles.commandMetadata}>
                            <strong>{t ? t('metadata') : 'Metadata'}:</strong>
                            <pre style={styles.commandMetadataPre}>
                              {JSON.stringify(command.metadata, null, 2)}
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

          {/* Statistics */}
          <div style={styles.panelStats}>
            <div style={styles.statItem}>
              <span style={styles.statLabel}>
                {t ? t('total_commands') : 'Total Commands'}:
              </span>
              <span style={styles.statValue}>
                {commandHistory.length}
              </span>
            </div>
            
            <div style={styles.statItem}>
              <span style={styles.statLabel}>
                {t ? t('running_commands') : 'Running Commands'}:
              </span>
              <span style={styles.statValue}>
                {activeCommands.filter(cmd => cmd.status === 'running').length}
              </span>
            </div>
            
            <div style={styles.statItem}>
              <span style={styles.statLabel}>
                {t ? t('success_rate') : 'Success Rate'}:
              </span>
              <span style={styles.statValue}>
                {commandHistory.length > 0 
                  ? `${Math.round((commandHistory.filter(cmd => cmd.status === 'completed').length / commandHistory.length) * 100)}%`
                  : 'N/A'
                }
              </span>
            </div>
            
            <div style={styles.statItem}>
              <span style={styles.statLabel}>
                {t ? t('filtered_commands') : 'Filtered Commands'}:
              </span>
              <span style={styles.statValue}>
                {filteredCommands.length}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutionPanel;
