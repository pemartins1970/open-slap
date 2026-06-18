import React from 'react';
import { useTranslation } from 'react-i18next';

const DEFAULT_NAV_ITEMS = [
  { key: 'conversations', labelKey: 'conversations', icon: '→' },
  { key: 'chat', labelKey: 'chat', icon: '💬' },
  { key: 'skills', labelKey: 'skills', icon: '🧠' },
  { key: 'doctor', labelKey: 'doctor', icon: '🔍' },
];

const LeftSidebar = ({
  styles,
  collapsed,
  onToggle,
  isMobile,
  conversations = [],
  currentConversation,
  onSelectConversation,
  onCreateConversation,
  centerView,
  onNavigate,
  navItems = DEFAULT_NAV_ITEMS,
  // monolith extensions
  mobileOpen,
  onMobileClose,
  hoverKey,
  onHover,
  onHoverLeave,
  onSelectNote,
  onGoHome,
  lang,
  logoWidthCollapsed,
  logoWidthExpanded,
}) => {
  const { t } = useTranslation();
  const isCollapsed = collapsed;

  const sidebarWidth = isMobile ? '280px' : (isCollapsed ? '72px' : '220px');
  const mobileStyle = isMobile ? {
    position: 'fixed',
    top: 0,
    left: mobileOpen ? 0 : '-320px',
    height: '100vh',
    zIndex: 9999,
    transition: 'left 0.18s ease-out',
    boxShadow: '0 10px 30px rgba(0,0,0,0.45)'
  } : {};

  return (
    <div
      style={{
        ...styles.sidebar,
        width: sidebarWidth,
        ...mobileStyle
      }}
      className={`slap-sidebar${mobileOpen ? ' expanded' : ''}`}
      onMouseLeave={onHoverLeave || (() => {})}
    >
      <div style={styles.sidebarContent}>
        <div style={styles.sidebarSection}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
            {!isCollapsed ? <div style={styles.sidebarTitle}>{t('menu')}</div> : <div />}
            <button
              style={styles.iconButton}
              onClick={() => {
                if (isMobile) {
                  if (onMobileClose) onMobileClose();
                  return;
                }
                if (onToggle) onToggle();
              }}
              title={isCollapsed ? t('menu_expand') : t('menu_collapse')}
              className="slap-collapse-toggle"
              hidden={isMobile}
            >
              {isCollapsed ? '»' : '«'}
            </button>
          </div>

          {onCreateConversation && !isCollapsed && (
            <>
              <div style={{ height: '8px' }} />
              <button
                type="button"
                onClick={onCreateConversation}
                style={{
                  ...styles.sidebarButton,
                  background: 'var(--accent-bg)',
                  color: 'var(--accent-text)',
                  fontWeight: 600,
                  width: '100%',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  textAlign: 'center'
                }}
              >
                {t('new_conversation')}
              </button>
            </>
          )}

          <div style={{ height: '12px' }} />
          {navItems.map((item, idx) => {
            const label = item.labelKey ? t(item.labelKey) : (item.label || item.key);
            return (
              <button
                key={item.key}
                style={{
                  ...styles.sidebarButton,
                  ...(centerView === item.key ? styles.sidebarButtonActive : {}),
                  ...(hoverKey === item.key ? styles.sidebarButtonHover : {}),
                  textAlign: isCollapsed ? 'center' : 'left',
                  padding: isCollapsed ? '10px' : styles.sidebarButton.padding,
                  justifyContent: isCollapsed ? 'center' : 'flex-start',
                  ...(idx > 0 ? { marginTop: '8px' } : {})
                }}
                onMouseEnter={() => onHover && onHover(item.key)}
                onMouseLeave={() => onHover && onHover('')}
                onClick={() => {
                  if (item.key === 'notes' && onSelectNote) {
                    onSelectNote();
                  } else {
                    onNavigate(item.key);
                  }
                }}
                title={label}
              >
                {item.icon}{isCollapsed ? '' : ` ${label}`}
              </button>
            );
          })}

          {conversations.length > 0 && !isCollapsed && (
            <div style={{ marginTop: '16px', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px', padding: '0 4px' }}>
                {t('recent')}
              </div>
              {conversations.slice(0, 10).map((conv) => (
                <button
                  key={conv.id}
                  type="button"
                  onClick={() => onSelectConversation && onSelectConversation(conv.id)}
                  style={{
                    display: 'block',
                    width: '100%',
                    background: currentConversation === conv.id ? 'var(--accent-bg)' : 'transparent',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '6px 8px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    color: 'var(--text)',
                    textAlign: 'left',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    marginBottom: '2px'
                  }}
                  title={conv.title}
                >
                  {conv.title || t('new_conversation')}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {onGoHome && (
        <div style={styles.sidebarBottom}>
          <div style={styles.sidebarFooter}>
            <button
              type="button"
              onClick={onGoHome}
              style={{ background: 'transparent', border: 'none', padding: 0, cursor: 'pointer' }}
              title="Tela inicial"
            >
              <img
                src="/open_slap.png"
                alt="Open Slap!"
                style={{
                  ...styles.sidebarLogo,
                  width: isCollapsed ? '44px' : '100%',
                  height: 'auto',
                  maxHeight: '160px',
                  maxWidth: '300px'
                }}
              />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LeftSidebar;
