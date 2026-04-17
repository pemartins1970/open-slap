import React, { useState } from 'react';
import { getExpertDisplayName, getExpertStatus, EXPERT_SEGMENT_PREFERRED_ORDER } from '../../lib/utils/display';
import { sortExpertsForSegment } from '../../lib/utils/sorters';

/**
 * ExpertsPanel - Painel de gerenciamento de experts.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {Array} props.experts - Array de experts
 * @param {boolean} props.loading - Se está carregando
 * @param {Function} props.onRefresh - Função para atualizar
 * @param {Function} props.onToggleExpert - Função para ativar/desativar expert
 * @param {Function} props.onUpdateExpert - Função para atualizar expert
 * @param {Function} props.t - Função de tradução
 */
const ExpertsPanel = ({
  styles,
  experts = [],
  loading,
  onRefresh,
  onToggleExpert,
  onUpdateExpert,
  t
}) => {
  const [selectedSegment, setSelectedSegment] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedExperts, setExpandedExperts] = useState(new Set());

  const toggleExpertExpansion = (expertId) => {
    setExpandedExperts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(expertId)) {
        newSet.delete(expertId);
      } else {
        newSet.add(expertId);
      }
      return newSet;
    });
  };

  const getSegments = () => {
    const segments = new Set();
    experts.forEach(expert => {
      if (expert.segment) segments.add(expert.segment);
    });
    return Array.from(segments);
  };

  const getFilteredExperts = () => {
    let filtered = experts;

    // Filter by segment
    if (selectedSegment !== 'all') {
      filtered = filtered.filter(expert => expert.segment === selectedSegment);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(expert => {
        const displayName = getExpertDisplayName(expert);
        const description = expert.description || '';
        const specialties = expert.specialties?.join(' ') || '';
        return displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
               description.toLowerCase().includes(searchTerm.toLowerCase()) ||
               specialties.toLowerCase().includes(searchTerm.toLowerCase());
      });
    }

    // Sort by preferred order
    return sortExpertsForSegment(filtered, selectedSegment);
  };

  const getExpertStatusColor = (status) => {
    switch (status) {
      case 'active': return styles.statusActive;
      case 'inactive': return styles.statusInactive;
      case 'busy': return styles.statusBusy;
      case 'error': return styles.statusError;
      case 'offline': return styles.statusOffline;
      default: return styles.statusDefault;
    }
  };

  const getExpertAvailabilityColor = (availability) => {
    switch (availability) {
      case 'available': return styles.availabilityAvailable;
      case 'busy': return styles.availabilityBusy;
      case 'unavailable': return styles.availabilityUnavailable;
      default: return styles.availabilityUnknown;
    }
  };

  const segments = getSegments();
  const filteredExperts = getFilteredExperts();

  return (
    <div style={styles.panel}>
      <div style={styles.panelHeader}>
        <h3 style={styles.panelTitle}>
          {t ? t('experts_management') : 'Experts Management'}
          <span style={styles.panelBadge}>
            {experts.length} {t ? t('experts') : 'experts'}
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
        </div>
      </div>

      <div style={styles.panelContent}>
        {/* Filters */}
        <div style={styles.panelFilters}>
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>
              {t ? t('segment') : 'Segment'}:
            </label>
            <select
              style={styles.filterSelect}
              value={selectedSegment}
              onChange={(e) => setSelectedSegment(e.target.value)}
            >
              <option value="all">
                {t ? t('all_segments') : 'All Segments'}
              </option>
              {EXPERT_SEGMENT_PREFERRED_ORDER.map(segment => (
                <option key={segment} value={segment}>
                  {t ? t(segment) : segment}
                </option>
              ))}
              {segments
                .filter(segment => !EXPERT_SEGMENT_PREFERRED_ORDER.includes(segment))
                .map(segment => (
                  <option key={segment} value={segment}>
                    {t ? t(segment) : segment}
                  </option>
                ))}
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
              placeholder={t ? t('search_experts') : 'Search experts...'}
            />
          </div>
        </div>

        {/* Experts List */}
        <div style={styles.expertsList}>
          {filteredExperts.length === 0 ? (
            <div style={styles.emptyState}>
              {searchTerm || selectedSegment !== 'all'
                ? (t ? t('no_experts_found') : 'No experts found')
                : (t ? t('no_experts_available') : 'No experts available')
              }
            </div>
          ) : (
            filteredExperts.map((expert) => {
              const displayName = getExpertDisplayName(expert);
              const status = getExpertStatus(expert);
              const availability = expert.availability || 'unknown';
              const isExpanded = expandedExperts.has(expert.id);

              return (
                <div key={expert.id} style={styles.expertItem}>
                  <div style={styles.expertHeader}>
                    <div style={styles.expertMain}>
                      <div style={styles.expertName}>
                        {displayName}
                      </div>
                      <div style={styles.expertMeta}>
                        <span style={styles.expertSegment}>
                          {expert.segment}
                        </span>
                        <span style={{...styles.expertStatus, ...getExpertStatusColor(status)}}>
                          {t ? t(status) : status}
                        </span>
                        <span style={{...styles.expertAvailability, ...getExpertAvailabilityColor(availability)}}>
                          {t ? t(availability) : availability}
                        </span>
                      </div>
                    </div>
                    
                    <div style={styles.expertActions}>
                      <button
                        style={styles.expertToggle}
                        onClick={() => onToggleExpert(expert.id)}
                        disabled={loading || status === 'busy'}
                        title={status === 'active' ? 'Deactivate' : 'Activate'}
                      >
                        {status === 'active' ? 'ON' : 'OFF'}
                      </button>
                      
                      <button
                        style={styles.expertExpand}
                        onClick={() => toggleExpertExpansion(expert.id)}
                        title={isExpanded ? 'Collapse' : 'Expand'}
                      >
                        {isExpanded ? 'v' : '>'}
                      </button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div style={styles.expertDetails}>
                      {expert.description && (
                        <div style={styles.expertDescription}>
                          <strong>{t ? t('description') : 'Description'}:</strong>
                          <div style={styles.expertDescriptionText}>
                            {expert.description}
                          </div>
                        </div>
                      )}

                      {expert.specialties && expert.specialties.length > 0 && (
                        <div style={styles.expertSpecialties}>
                          <strong>{t ? t('specialties') : 'Specialties'}:</strong>
                          <div style={styles.specialtiesList}>
                            {expert.specialties.map((specialty, index) => (
                              <span key={index} style={styles.specialtyTag}>
                                {specialty}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {expert.capabilities && expert.capabilities.length > 0 && (
                        <div style={styles.expertCapabilities}>
                          <strong>{t ? t('capabilities') : 'Capabilities'}:</strong>
                          <ul style={styles.capabilitiesList}>
                            {expert.capabilities.map((capability, index) => (
                              <li key={index} style={styles.capabilityItem}>
                                {capability}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {expert.performance && (
                        <div style={styles.expertPerformance}>
                          <strong>{t ? t('performance') : 'Performance'}:</strong>
                          <div style={styles.performanceMetrics}>
                            {expert.performance.response_time && (
                              <div style={styles.performanceMetric}>
                                <span style={styles.metricLabel}>
                                  {t ? t('response_time') : 'Response Time'}:
                                </span>
                                <span style={styles.metricValue}>
                                  {expert.performance.response_time}ms
                                </span>
                              </div>
                            )}
                            
                            {expert.performance.success_rate && (
                              <div style={styles.performanceMetric}>
                                <span style={styles.metricLabel}>
                                  {t ? t('success_rate') : 'Success Rate'}:
                                </span>
                                <span style={styles.metricValue}>
                                  {expert.performance.success_rate}%
                                </span>
                              </div>
                            )}
                            
                            {expert.performance.tasks_completed && (
                              <div style={styles.performanceMetric}>
                                <span style={styles.metricLabel}>
                                  {t ? t('tasks_completed') : 'Tasks Completed'}:
                                </span>
                                <span style={styles.metricValue}>
                                  {expert.performance.tasks_completed}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {expert.config && Object.keys(expert.config).length > 0 && (
                        <div style={styles.expertConfig}>
                          <strong>{t ? t('configuration') : 'Configuration'}:</strong>
                          <pre style={styles.expertConfigPre}>
                            {JSON.stringify(expert.config, null, 2)}
                          </pre>
                        </div>
                      )}

                      {expert.last_active && (
                        <div style={styles.expertLastActive}>
                          <strong>{t ? t('last_active') : 'Last Active'}:</strong>
                          <span>{new Date(expert.last_active).toLocaleString()}</span>
                        </div>
                      )}

                      {expert.error_message && (
                        <div style={styles.expertError}>
                          <strong>{t ? t('error') : 'Error'}:</strong>
                          <span style={styles.errorMessage}>
                            {expert.error_message}
                          </span>
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
              {t ? t('total_experts') : 'Total Experts'}:
            </span>
            <span style={styles.statValue}>
              {experts.length}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={styles.statLabel}>
              {t ? t('active_experts') : 'Active Experts'}:
            </span>
            <span style={styles.statValue}>
              {experts.filter(expert => getExpertStatus(expert) === 'active').length}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={styles.statLabel}>
              {t ? t('available_experts') : 'Available Experts'}:
            </span>
            <span style={styles.statValue}>
              {experts.filter(expert => expert.availability === 'available').length}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={styles.statLabel}>
              {t ? t('filtered_experts') : 'Filtered Experts'}:
            </span>
            <span style={styles.statValue}>
              {filteredExperts.length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExpertsPanel;
