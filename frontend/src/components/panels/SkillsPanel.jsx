import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { getSkillDisplayName, getSkillStatus, SKILL_SEGMENT_PREFERRED_ORDER } from '../../lib/utils/display';
import { sortSkillsForSegment } from '../../lib/utils/sorters';

const SkillsPanel = ({
  styles,
  skills = [],
  loading,
  onRefresh,
  onToggleSkill,
  onUpdateSkill,
}) => {
  const { t } = useTranslation();
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

    if (selectedSegment !== 'all') {
      filtered = filtered.filter(skill => skill.segment === selectedSegment);
    }

    if (searchTerm) {
      filtered = filtered.filter(skill => {
        const displayName = getSkillDisplayName(skill);
        const description = skill.description || '';
        return displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
               description.toLowerCase().includes(searchTerm.toLowerCase());
      });
    }

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
          {t('skills_management')}
          <span style={styles.panelBadge}>
            {skills.length} {t('skills')}
          </span>
        </h3>
        <div style={styles.panelActions}>
          <button
            style={styles.panelButton}
            onClick={onRefresh}
            disabled={loading}
            title={t('refresh')}
          >
            {loading ? '...' : t('refresh')}
          </button>
        </div>
      </div>

      <div style={styles.panelContent}>
        <div style={styles.panelFilters}>
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>
              {t('segment')}:
            </label>
            <select
              style={styles.filterSelect}
              value={selectedSegment}
              onChange={(e) => setSelectedSegment(e.target.value)}
            >
              <option value="all">
                {t('all_segments')}
              </option>
              {SKILL_SEGMENT_PREFERRED_ORDER.map(segment => (
                <option key={segment} value={segment}>
                  {t(segment)}
                </option>
              ))}
              {segments
                .filter(segment => !SKILL_SEGMENT_PREFERRED_ORDER.includes(segment))
                .map(segment => (
                  <option key={segment} value={segment}>
                    {t(segment)}
                  </option>
                ))}
            </select>
          </div>

          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>
              {t('search')}:
            </label>
            <input
              style={styles.filterInput}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={t('search_skills')}
            />
          </div>
        </div>

        <div style={styles.skillsList}>
          {filteredSkills.length === 0 ? (
            <div style={styles.emptyState}>
              {searchTerm || selectedSegment !== 'all'
                ? t('no_skills_found')
                : t('no_skills_available')
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
                          {t(status)}
                        </span>
                      </div>
                    </div>
                    
                    <div style={styles.skillActions}>
                      <button
                        style={styles.skillToggle}
                        onClick={() => onToggleSkill(skill.id)}
                        disabled={loading}
                      >
                        {status === 'active' ? 'ON' : 'OFF'}
                      </button>
                      
                      <button
                        style={styles.skillExpand}
                        onClick={() => toggleSkillExpansion(skill.id)}
                      >
                        {isExpanded ? 'v' : '>'}
                      </button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div style={styles.skillDetails}>
                      {skill.description && (
                        <div style={styles.skillDescription}>
                          <strong>{t('description')}:</strong>
                          <div style={styles.skillDescriptionText}>
                            {skill.description}
                          </div>
                        </div>
                      )}

                      {skill.config && Object.keys(skill.config).length > 0 && (
                        <div style={styles.skillConfig}>
                          <strong>{t('configuration')}:</strong>
                          <pre style={styles.skillConfigPre}>
                            {JSON.stringify(skill.config, null, 2)}
                          </pre>
                        </div>
                      )}

                      {skill.capabilities && skill.capabilities.length > 0 && (
                        <div style={styles.skillCapabilities}>
                          <strong>{t('capabilities')}:</strong>
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
                          <strong>{t('last_used')}:</strong>
                          <span>{new Date(skill.last_used).toLocaleString()}</span>
                        </div>
                      )}

                      {skill.error_message && (
                        <div style={styles.skillError}>
                          <strong>{t('error')}:</strong>
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

        <div style={styles.panelStats}>
          <div style={styles.statItem}>
            <span style={styles.statLabel}>
              {t('total_skills')}:
            </span>
            <span style={styles.statValue}>
              {skills.length}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={styles.statLabel}>
              {t('active_skills')}:
            </span>
            <span style={styles.statValue}>
              {skills.filter(skill => getSkillStatus(skill) === 'active').length}
            </span>
          </div>
          
          <div style={styles.statItem}>
            <span style={styles.statLabel}>
              {t('filtered_skills')}:
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
