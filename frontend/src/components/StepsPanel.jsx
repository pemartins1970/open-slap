import React from 'react';

const StepsPanel = ({ steps = [], isVisible, onClose, t }) => {
  if (!isVisible) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: '80px',
      right: '16px',
      width: '280px',
      maxHeight: '320px',
      overflowY: 'auto',
      backgroundColor: 'var(--bg-secondary, #1e293b)',
      border: '1px solid var(--border-color, #334155)',
      borderRadius: '8px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
      zIndex: 200,
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 12px',
        borderBottom: '1px solid var(--border-color, #334155)',
        flexShrink: 0,
      }}>
        <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary, #94a3b8)' }}>
          {t ? t('progress_steps') : 'Progresso'}
        </span>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary, #94a3b8)',
            cursor: 'pointer',
            fontSize: '14px',
            padding: '0 4px',
            lineHeight: 1,
          }}
          title="Fechar"
        >
          ×
        </button>
      </div>

      <div style={{ padding: '8px 0', flex: 1 }}>
        {steps.length === 0 ? (
          <div style={{
            padding: '12px',
            fontSize: '12px',
            color: 'var(--text-muted, #64748b)',
            textAlign: 'center',
          }}>
            {t ? t('no_steps_yet') : 'Nenhum passo registrado'}
          </div>
        ) : (
          steps.map((step, index) => (
            <div
              key={step.id || index}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                padding: '6px 12px',
              }}
            >
              <div style={{
                flexShrink: 0,
                width: '18px',
                height: '18px',
                borderRadius: '50%',
                backgroundColor: 'var(--accent-color, #6366f1)',
                color: '#fff',
                fontSize: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginTop: '1px',
              }}>
                {index + 1}
              </div>

              <span style={{
                fontSize: '12px',
                color: 'var(--text-primary, #e2e8f0)',
                lineHeight: '1.4',
                flex: 1,
              }}>
                {step.description}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default StepsPanel;
