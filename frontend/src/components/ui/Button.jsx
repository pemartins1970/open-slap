import React from 'react';

/**
 * Button - Componente de botão reutilizável com múltiplas variantes.
 * 
 * @param {Object} props
 * @param {string} props.variant - Variante do botão (primary, secondary, danger, warning, success, ghost)
 * @param {string} props.size - Tamanho do botão (small, medium, large)
 * @param {boolean} props.disabled - Se está desabilitado
 * @param {boolean} props.loading - Se está em estado de loading
 * @param {boolean} props.block - Se ocupa toda a largura disponível
 * @param {string} props.className - Classes CSS adicionais
 * @param {Object} props.style - Estilos inline adicionais
 * @param {Function} props.onClick - Handler de clique
 * @param {Function} props.onMouseDown - Handler de mouse down
 * @param {Function} props.onMouseUp - Handler de mouse up
 * @param {string} props.type - Tipo do botão (button, submit, reset)
 * @param {string} props.title - Tooltip
 * @param {React.ReactNode} props.children - Conteúdo do botão
 * @param {Object} props.styles - Estilos do tema
 * @param {Function} props.t - Função de tradução
 */
const Button = ({
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  block = false,
  className = '',
  style = {},
  onClick,
  onMouseDown,
  onMouseUp,
  type = 'button',
  title,
  children,
  styles,
  t
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return styles.buttonPrimary || {
          backgroundColor: '#007bff',
          color: 'white',
          border: '1px solid #007bff'
        };
      case 'secondary':
        return styles.buttonSecondary || {
          backgroundColor: '#6c757d',
          color: 'white',
          border: '1px solid #6c757d'
        };
      case 'danger':
        return styles.buttonDanger || {
          backgroundColor: '#dc3545',
          color: 'white',
          border: '1px solid #dc3545'
        };
      case 'warning':
        return styles.buttonWarning || {
          backgroundColor: '#ffc107',
          color: '#212529',
          border: '1px solid #ffc107'
        };
      case 'success':
        return styles.buttonSuccess || {
          backgroundColor: '#28a745',
          color: 'white',
          border: '1px solid #28a745'
        };
      case 'ghost':
        return styles.buttonGhost || {
          backgroundColor: 'transparent',
          color: '#007bff',
          border: '1px solid #007bff'
        };
      default:
        return styles.buttonDefault || {
          backgroundColor: '#f8f9fa',
          color: '#212529',
          border: '1px solid #dee2e6'
        };
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return styles.buttonSmall || {
          padding: '4px 8px',
          fontSize: '12px',
          lineHeight: '1.2'
        };
      case 'large':
        return styles.buttonLarge || {
          padding: '12px 24px',
          fontSize: '16px',
          lineHeight: '1.4'
        };
      default:
        return styles.buttonMedium || {
          padding: '8px 16px',
          fontSize: '14px',
          lineHeight: '1.3'
        };
    }
  };

  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '4px',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    fontWeight: '500',
    textAlign: 'center',
    textDecoration: 'none',
    transition: 'all 0.2s ease-in-out',
    outline: 'none',
    boxSizing: 'border-box',
    userSelect: 'none',
    ...getVariantStyles(),
    ...getSizeStyles(),
    ...(block && { width: '100%' }),
    ...(disabled && { opacity: 0.6, pointerEvents: 'none' }),
    ...(loading && { opacity: 0.8 }),
    style
  };

  const handleClick = (e) => {
    if (disabled || loading) {
      e.preventDefault();
      return;
    }
    if (onClick) {
      onClick(e);
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <>
          <span style={{
            display: 'inline-block',
            width: '12px',
            height: '12px',
            border: '2px solid transparent',
            borderTop: '2px solid currentColor',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            marginRight: '8px'
          }} />
          {t ? t('loading') : 'Loading...'}
        </>
      );
    }

    return children;
  };

  return (
    <button
      type={type}
      className={className}
      style={baseStyles}
      onClick={handleClick}
      onMouseDown={onMouseDown}
      onMouseUp={onMouseUp}
      title={title}
      disabled={disabled || loading}
    >
      {renderContent()}
    </button>
  );
};

export default Button;
