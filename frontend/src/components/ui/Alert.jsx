import React from 'react';

/**
 * Alert - Componente de alerta reutilizável com múltiplas variantes.
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Conteúdo do alerta
 * @param {string} props.variant - Variante do alerta (primary, secondary, success, warning, danger, info, light, dark)
 * @param {boolean} props.dismissible - Se pode ser removido
 * @param {Function} props.onDismiss - Handler de remoção
 * @param {string} props.title - Título do alerta
 * @param {boolean} props.showIcon - Se mostra ícone
 * @param {string} props.icon - Ícone customizado
 * @param {boolean} props.fullWidth - Se ocupa toda a largura
 * @param {string} props.size - Tamanho (small, medium, large)
 * @param {string} props.className - Classes CSS adicionais
 * @param {Object} props.style - Estilos inline adicionais
 * @param {Object} props.styles - Estilos do tema
 * @param {Function} props.t - Função de tradução
 */
const Alert = ({
  children,
  variant = 'info',
  dismissible = false,
  onDismiss,
  title,
  showIcon = true,
  icon,
  fullWidth = false,
  size = 'medium',
  className = '',
  style = {},
  styles,
  t
}) => {
  const [dismissed, setDismissed] = React.useState(false);

  const handleDismiss = () => {
    setDismissed(true);
    if (onDismiss) {
      onDismiss();
    }
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: '#d1ecf1',
          borderColor: '#bee5eb',
          color: '#0c5460',
          iconColor: '#0c5460'
        };
      case 'secondary':
        return {
          backgroundColor: '#e2e3e5',
          borderColor: '#d6d8db',
          color: '#383d41',
          iconColor: '#383d41'
        };
      case 'success':
        return {
          backgroundColor: '#d4edda',
          borderColor: '#c3e6cb',
          color: '#155724',
          iconColor: '#155724'
        };
      case 'warning':
        return {
          backgroundColor: '#fff3cd',
          borderColor: '#ffeeba',
          color: '#856404',
          iconColor: '#856404'
        };
      case 'danger':
        return {
          backgroundColor: '#f8d7da',
          borderColor: '#f5c6cb',
          color: '#721c24',
          iconColor: '#721c24'
        };
      case 'info':
        return {
          backgroundColor: '#d1ecf1',
          borderColor: '#bee5eb',
          color: '#0c5460',
          iconColor: '#0c5460'
        };
      case 'light':
        return {
          backgroundColor: '#fefefe',
          borderColor: '#fdfdfe',
          color: '#818182',
          iconColor: '#818182'
        };
      case 'dark':
        return {
          backgroundColor: '#d6d8d9',
          borderColor: '#c6c8ca',
          color: '#1b1e21',
          iconColor: '#1b1e21'
        };
      default:
        return {
          backgroundColor: '#d1ecf1',
          borderColor: '#bee5eb',
          color: '#0c5460',
          iconColor: '#0c5460'
        };
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          padding: '8px 12px',
          fontSize: '12px',
          lineHeight: '1.2'
        };
      case 'large':
        return {
          padding: '16px 20px',
          fontSize: '16px',
          lineHeight: '1.4'
        };
      default:
        return {
          padding: '12px 16px',
          fontSize: '14px',
          lineHeight: '1.3'
        };
    }
  };

  const getIcon = () => {
    if (icon) return icon;
    
    switch (variant) {
      case 'success':
        return '×';
      case 'warning':
        return '!';
      case 'danger':
        return '×';
      case 'info':
        return 'i';
      default:
        return 'i';
    }
  };

  const variantStyles = getVariantStyles();
  const sizeStyles = getSizeStyles();

  const baseStyles = {
    position: 'relative',
    padding: sizeStyles.padding,
    marginBottom: '16px',
    border: `1px solid ${variantStyles.borderColor}`,
    borderRadius: '4px',
    backgroundColor: variantStyles.backgroundColor,
    color: variantStyles.color,
    fontSize: sizeStyles.fontSize,
    lineHeight: sizeStyles.lineHeight,
    width: fullWidth ? '100%' : 'auto',
    boxSizing: 'border-box',
    transition: 'all 0.2s ease-in-out',
    ...style
  };

  const titleStyles = {
    fontWeight: '600',
    marginBottom: '4px',
    fontSize: '1.1em',
    color: 'inherit'
  };

  const iconStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '20px',
    height: '20px',
    marginRight: '8px',
    fontSize: '14px',
    fontWeight: 'bold',
    color: variantStyles.iconColor,
    flexShrink: 0
  };

  const contentStyles = {
    display: 'flex',
    alignItems: 'flex-start'
  };

  const dismissButtonStyles = {
    position: 'absolute',
    top: '8px',
    right: '8px',
    background: 'none',
    border: 'none',
    color: variantStyles.color,
    fontSize: '16px',
    cursor: 'pointer',
    opacity: 0.7,
    padding: '0',
    lineHeight: '1',
    '&:hover': {
      opacity: 1
    }
  };

  if (dismissed) {
    return null;
  }

  return (
    <div
      className={className}
      style={baseStyles}
      role="alert"
    >
      <div style={contentStyles}>
        {showIcon && (
          <div style={iconStyles}>
            {getIcon()}
          </div>
        )}
        
        <div style={{ flex: 1 }}>
          {title && (
            <div style={titleStyles}>
              {title}
            </div>
          )}
          
          <div>
            {children}
          </div>
        </div>
      </div>

      {dismissible && (
        <button
          style={dismissButtonStyles}
          onClick={handleDismiss}
          title={t ? t('dismiss_alert') : 'Dismiss alert'}
        >
          ×
        </button>
      )}
    </div>
  );
};

export default Alert;
