import React, { useState, useEffect } from 'react';

/**
 * RightPanel - Drawer component for displaying artifacts, logs, or previews
 * Opens as a drawer from the right side without page reload
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {boolean} props.isOpen - Se o painel está aberto
 * @param {Function} props.onClose - Função para fechar o painel
 * @param {string} props.panelType - Tipo de painel: 'artifacts', 'logs', 'preview'
 * @param {Object} props.content - Conteúdo a ser exibido
 * @param {Function} props.t - Função de tradução
 */
const RightPanel = ({
  styles,
  isOpen,
  onClose,
  panelType = 'artifacts',
  content = null,
  t
}) => {
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsAnimating(true);
    }
  }, [isOpen]);

  const handleClose = () => {
    setIsAnimating(false);
    setTimeout(() => onClose(), 300);
  };

  const panelStyles = {
    position: 'fixed',
    top: '0',
    right: '0',
    width: '400px',
    maxWidth: '80vw',
    height: '100vh',
    background: 'var(--bg-panel)',
    borderLeft: '1px solid var(--border)',
    boxShadow: '-4px 0 20px rgba(0, 0, 0, 0.15)',
    transform: isOpen ? 'translateX(0)' : 'translateX(100%)',
    transition: 'transform 0.3s ease-in-out',
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column'
  };

  const overlayStyles = {
    position: 'fixed',
    top: '0',
    left: '0',
    width: '100%',
    height: '100%',
    background: 'rgba(0, 0, 0, 0.5)',
    opacity: isOpen ? '1' : '0',
    transition: 'opacity 0.3s ease-in-out',
    zIndex: 999,
    pointerEvents: isOpen ? 'auto' : 'none'
  };

  const headerStyles = {
    padding: '20px',
    borderBottom: '1px solid var(--border)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    background: 'var(--bg3)'
  };

  const titleStyles = {
    fontSize: '18px',
    fontWeight: '600',
    color: 'var(--text)',
    fontFamily: 'var(--sans)'
  };

  const closeButtonStyles = {
    background: 'none',
    border: 'none',
    fontSize: '24px',
    color: 'var(--text-dim)',
    cursor: 'pointer',
    padding: '4px 8px',
    transition: 'color 0.2s'
  };

  const contentStyles = {
    flex: 1,
    overflow: 'auto',
    padding: '20px'
  };

  const renderContent = () => {
    switch (panelType) {
      case 'artifacts':
        return (
          <div>
            <h3 style={{...titleStyles, marginBottom: '16px'}}>
              {t ? t('artifacts') : 'Artifacts'}
            </h3>
            {content?.artifacts?.length > 0 ? (
              content.artifacts.map((artifact, index) => (
                <div
                  key={index}
                  style={{
                    background: 'var(--bg3)',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    padding: '12px',
                    marginBottom: '12px'
                  }}
                >
                  <div style={{fontWeight: '600', marginBottom: '4px'}}>
                    {artifact.name}
                  </div>
                  <div style={{fontSize: '12px', color: 'var(--text-dim)'}}>
                    {artifact.type}
                  </div>
                </div>
              ))
            ) : (
              <div style={{color: 'var(--text-dim)'}}>
                {t ? t('no_artifacts') : 'No artifacts available'}
              </div>
            )}
          </div>
        );

      case 'logs':
        return (
          <div>
            <h3 style={{...titleStyles, marginBottom: '16px'}}>
              {t ? t('logs') : 'Logs'}
            </h3>
            {content?.logs?.length > 0 ? (
              <div style={{
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '12px',
                fontFamily: 'monospace',
                fontSize: '12px',
                maxHeight: '400px',
                overflow: 'auto'
              }}>
                {content.logs.map((log, index) => (
                  <div key={index} style={{marginBottom: '4px', color: 'var(--text)'}}>
                    <span style={{color: 'var(--text-dim)'}}>
                      [{log.timestamp}]
                    </span>
                    <span style={{marginLeft: '8px'}}>
                      {log.message}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{color: 'var(--text-dim)'}}>
                {t ? t('no_logs') : 'No logs available'}
              </div>
            )}
          </div>
        );

      case 'preview':
        return (
          <div>
            <h3 style={{...titleStyles, marginBottom: '16px'}}>
              {t ? t('preview') : 'Preview'}
            </h3>
            {content?.preview ? (
              <div style={{
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '12px',
                minHeight: '200px'
              }}>
                {content.preview}
              </div>
            ) : (
              <div style={{color: 'var(--text-dim)'}}>
                {t ? t('no_preview') : 'No preview available'}
              </div>
            )}
          </div>
        );

      default:
        return (
          <div style={{color: 'var(--text-dim)'}}>
            {t ? t('select_panel') : 'Select a panel type'}
          </div>
        );
    }
  };

  return (
    <>
      {/* Overlay */}
      <div style={overlayStyles} onClick={handleClose} />

      {/* Panel */}
      <div style={panelStyles}>
        {/* Header */}
        <div style={headerStyles}>
          <div style={titleStyles}>
            {panelType.charAt(0).toUpperCase() + panelType.slice(1)}
          </div>
          <button
            style={closeButtonStyles}
            onClick={handleClose}
            title={t ? t('close') : 'Close'}
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div style={contentStyles}>
          {renderContent()}
        </div>
      </div>
    </>
  );
};

export default RightPanel;
