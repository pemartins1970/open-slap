import React from 'react';
import { useTranslation } from 'react-i18next';

const COLLAPSED_WIDTH = 36;

const RightSidebar = ({ styles, collapsed, onToggle }) => {
  const { t } = useTranslation();

  if (collapsed) {
    return (
      <div style={{
        width: `${COLLAPSED_WIDTH}px`,
        minWidth: `${COLLAPSED_WIDTH}px`,
        borderLeft: '1px solid var(--border)',
        background: 'var(--bg-panel)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: '12px',
        overflow: 'hidden'
      }}>
        <button
          type="button"
          onClick={onToggle}
          title={t('show_status') || 'Show status'}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-dim)',
            fontSize: '14px',
            cursor: 'pointer',
            padding: '4px',
            writingMode: 'vertical-rl',
            fontFamily: 'var(--mono)',
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
            fontWeight: 600,
          }}
        >
          ◀ {t('status')}
        </button>
      </div>
    );
  }

  return (
    <div style={{
      width: '320px',
      minWidth: '320px',
      borderLeft: '1px solid var(--border)',
      background: 'var(--bg-panel)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid var(--border)',
        fontSize: '12px',
        fontWeight: 600,
        color: 'var(--text-dim)',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <span>{t('status')}</span>
        <button
          type="button"
          onClick={onToggle}
          title={t('hide_status') || 'Hide status'}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-dim)',
            fontSize: '12px',
            cursor: 'pointer',
            padding: '2px 4px',
            lineHeight: 1
          }}
        >
          ▶
        </button>
      </div>
      <div style={{ flex: 1 }} />
    </div>
  );
};

export default RightSidebar;
