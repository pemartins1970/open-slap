import React, { useState } from 'react';
import { getSkillDisplayName, getSkillStatus, SKILL_SEGMENT_PREFERRED_ORDER } from '../../lib/utils/display';
import { sortSkillsForSegment } from '../../lib/utils/sorters';

/**
 * SkillsPanel - Painel de gerenciamento de skills.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {Array} props.skills - Array de skills
 * @param {boolean} props.loading - Se está carregando
 * @param {Function} props.onRefresh - Função para atualizar
 * @param {Function} props.onToggleSkill - Função para ativar/desativar skill
 * @param {Function} props.onUpdateSkill - Função para atualizar skill
 * @param {Function} props.t - Função de tradução
 */
const SkillsPanel = ({
  styles,
  skills = [],
  loading,
  onRefresh,
  onToggleSkill,
  onUpdateSkill,
  t
}) => {
  const [selectedSegment, setSelectedSegment] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedSkills, setExpandedSkills] = useState(new Set());

  const toggleSkillExpansion = (skillId) => {
    setExpandedSkills(prev => {
      const newSet = new Set(prev);
      if (newSet.has(skillId)) {
        newSet.delete(skillId);
      } else {
        newSet.add(skillId);
      }
      return newSet;
    });
  };

  const getSegments = () => {
    const segments = new Set();
    skills.forEach(skill => {
      if (skill.segment) segments.add(skill.segment);
    });
    return Array.from(segments);
  };

  const getFilteredSkills = () => {
    let filtered = skills;

    // Filter by segment
    if (selectedSegment !== 'all') {
      filtered = filtered.filter(skill => skill.segment === selectedSegment);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(skill => {
        const displayName = getSkillDisplayName(skill);
        const description = skill.description || '';
        return displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
               description.toLowerCase().includes(searchTerm.toLowerCase());
      });
    }

    // Sort by preferred order
    return sortSkillsForSegment(filtered, selectedSegment);
  };

  const getSkillStatusColor = (status) => {
    switch (status) {
      case 'active': return styles.statusActive;
      case 'inactive': return styles.statusInactive;
      case 'error': return styles.statusError;
      case 'loading': return styles.statusLoading;
      default: return styles.statusDefault;
    }
  };

  const segments = getSegments();
  const filteredSkills = getFilteredSkills();

  return (
    <div style={styles.panel}>
      <div style={styles.panelHeader}>
        <h3 style={styles.panelTitle}>
          {t ? t('skills_management') : 'Skills Management'}
          <span style={styles.panelBadge}>
            {skills.length} {t ? t('skills') : 'skills'}
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
              {SKILL_SEGMENT_PREFERRED_ORDER.map(segment => (
                <option key={segment} value={segment}>
                  {t ? t(segment) : segment}
                </option>
              ))}
              {segments
                .filter(segment => !SKILL_SEGMENT_PREFERRED_ORDER.includes(segment))
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
              placeholder={t ? t('search_skills') : 'Search skills...'}
            />
          </div>
        </div>

        {/* Skills List */}
        <div style={styles.skillsList}>
          {filteredSkills.length === 0 ? (
            <div style={styles.emptyState}>
              {searchTerm || selectedSegment !== 'all'
                ? (t ? t('no_skills_found') : 'No skills found')
                : (t ? t('no_skills_available') : 'No skills available')
              }
            </div>
          ) : (
            filteredSkills.map((skill) => {
              const displayName = getSkillDisplayName(skill);
              const status = getSkillStatus(skill);
              const isExpanded = expandedSkills.has(skill.id);

              return (
                <div key={skill.id} style={styles.skillItem}>
                  <div style={styles.skillHeader}>
                    <div style={styles.skillMain}>
                      <div style={styles.skillName}>
                        {displayName}
                      </div>
                      <div style={styles.skillMeta}>
                        <span style={styles.skillSegment}>
                          {skill.segment}
                        </span>
                        <span style={{...styles.skillStatus, ...getSkillStatusColor(status)}}>
                          {t ? t(status) : status}
                        </span>
                      </div>
                    </div>
                    
                    <div style={styles.skillActions}>
                      <button
                        style={styles.skillToggle}
                        onClick={() => onToggleSkill(skill.id)}
                        disabled={loading}
                        title={status === 'active' ? 'Deactivate' : 'Activate'}
                      >
                        {status === 'active' ? 'ON' : 'OFF'}
                      </button>
                      
                      <button
                        style={styles.skillExpand}
                        onClick={() => toggleSkillExpansion(skill.id)}
                        title={isExpanded ? 'Collapse' : 'Expand'}
                      >
                        {isExpanded ? 'v' : '>'}
                      </button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div style={styles.skillDetails}>
                      {skill.description && (
                        <div style={styles.skillDescription}>
                          <strong>{t ? t('description') : 'Description'}:</strong>
                          <div style={styles.skillDescriptionText}>
                            {skill.description}
                          </div>
                        </div>
                      )}

                      {skill.config && Object.keys(skill.config).length > 0 && (
                        <div style={styles.skillConfig}>
                          <strong>{t ? t('configuration') : 'Configuration'}:</strong>
                          <pre style={styles.skillConfigPre}>
                            {JSON.stringify(skill.config, null, 2)}
                          </pre>
                        </div>
                      )}

                      {skill.capabilities && skill.capabilities.length > 0 && (
                        <div style={styles.skillCapabilities}>
                          <strong>{t ? t('capabilities') : 'Capabilities'}:</strong>
                          <ul style={styles.capabilitiesList}>
                            {skill.capabilities.map((capability, index) => (
                              <li key={index} style={styles.capabilityItem}>
                                {capability}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {skill.last_used && (
                        <div style={styles.skillLastUsed}>
                          <strong>{t ? t('last_used') : 'Last Used'}:</strong>
                          <span>{new Date(skill.last_used).toLocaleString()}</span>
                        </div>
                      )}

                      {skill.error_message && (
                        <div style={styles.skillError}>
                          <strong>{t ? t('error') : 'Error'}:</strong>
                          <span style={styles.errorMessage}>
                            {skill.error_message}
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
              {t ? t('total_skills') : 'Total Skills'}:
            </span>
            <span style={styles.statValue}>
              {skills.length}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={styles.statLabel}>
              {t ? t('active_skills') : 'Active Skills'}:
            </span>
            <span style={styles.statValue}>
              {skills.filter(skill => getSkillStatus(skill) === 'active').length}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={styles.statLabel}>
              {t ? t('filtered_skills') : 'Filtered Skills'}:
            </span>
            <span style={styles.statValue}>
              {filteredSkills.length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillsPanel;
