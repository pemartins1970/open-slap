import React from 'react';

/**
 * Badge - Componente de badge reutilizável com múltiplas variantes.
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Conteúdo do badge
 * @param {string} props.variant - Variante do badge (primary, secondary, success, warning, danger, info, light, dark)
 * @param {string} props.size - Tamanho do badge (small, medium, large)
 * @param {boolean} props.pill - Se tem formato de pílula
 * @param {boolean} props.dot - Se é um dot (ponto indicador)
 * @param {string} props.color - Cor customizada
 * @param {string} props.backgroundColor - Cor de fundo customizada
 * @param {string} props.className - Classes CSS adicionais
 * @param {Object} props.style - Estilos inline adicionais
 * @param {Function} props.onClick - Handler de clique
 * @param {string} props.title - Tooltip
 * @param {boolean} props.dismissible - Se pode ser removido
 * @param {Function} props.onDismiss - Handler de remoção
 * @param {Object} props.styles - Estilos do tema
 * @param {Function} props.t - Função de tradução
 */
const Badge = ({
  children,
  variant = 'primary',
  size = 'medium',
  pill = false,
  dot = false,
  color,
  backgroundColor,
  className = '',
  style = {},
  onClick,
  title,
  dismissible = false,
  onDismiss,
  styles,
  t
}) => {
  const [dismissed, setDismissed] = React.useState(false);

  const handleDismiss = (e) => {
    e.stopPropagation();
    setDismissed(true);
    if (onDismiss) {
      onDismiss(e);
    }
  };

  const getVariantStyles = () => {
    if (color || backgroundColor) {
      return {
        color: color || 'white',
        backgroundColor: backgroundColor || '#6c757d',
        borderColor: backgroundColor || '#6c757d'
      };
    }

    switch (variant) {
      case 'primary':
        return {
          color: 'white',
          backgroundColor: '#007bff',
          borderColor: '#007bff'
        };
      case 'secondary':
        return {
          color: 'white',
          backgroundColor: '#6c757d',
          borderColor: '#6c757d'
        };
      case 'success':
        return {
          color: 'white',
          backgroundColor: '#28a745',
          borderColor: '#28a745'
        };
      case 'warning':
        return {
          color: '#212529',
          backgroundColor: '#ffc107',
          borderColor: '#ffc107'
        };
      case 'danger':
        return {
          color: 'white',
          backgroundColor: '#dc3545',
          borderColor: '#dc3545'
        };
      case 'info':
        return {
          color: 'white',
          backgroundColor: '#17a2b8',
          borderColor: '#17a2b8'
        };
      case 'light':
        return {
          color: '#212529',
          backgroundColor: '#f8f9fa',
          borderColor: '#f8f9fa'
        };
      case 'dark':
        return {
          color: 'white',
          backgroundColor: '#343a40',
          borderColor: '#343a40'
        };
      default:
        return {
          color: 'white',
          backgroundColor: '#007bff',
          borderColor: '#007bff'
        };
    }
  };

  const getSizeStyles = () => {
    if (dot) {
      return {
        width: size === 'small' ? '6px' : size === 'large' ? '10px' : '8px',
        height: size === 'small' ? '6px' : size === 'large' ? '10px' : '8px',
        padding: 0,
        fontSize: '0',
        minWidth: 'auto'
      };
    }

    switch (size) {
      case 'small':
        return {
          padding: '2px 6px',
          fontSize: '10px',
          lineHeight: '1.2',
          minWidth: '16px'
        };
      case 'large':
        return {
          padding: '6px 12px',
          fontSize: '14px',
          lineHeight: '1.4',
          minWidth: '24px'
        };
      default:
        return {
          padding: '4px 8px',
          fontSize: '12px',
          lineHeight: '1.3',
          minWidth: '20px'
        };
    }
  };

  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: '500',
    textAlign: 'center',
    whiteSpace: 'nowrap',
    verticalAlign: 'baseline',
    borderRadius: pill ? '50px' : '4px',
    border: '1px solid transparent',
    transition: 'all 0.2s ease-in-out',
    cursor: onClick ? 'pointer' : 'default',
    userSelect: 'none',
    boxSizing: 'border-box',
    ...getVariantStyles(),
    ...getSizeStyles(),
    style
  };

  const dismissButtonStyles = {
    marginLeft: '4px',
    background: 'none',
    border: 'none',
    color: 'inherit',
    fontSize: 'inherit',
    cursor: 'pointer',
    opacity: 0.7,
    padding: '0',
    '&:hover': {
      opacity: 1
    }
  };

  if (dismissed) {
    return null;
  }

  return (
    <span
      className={className}
      style={baseStyles}
      onClick={onClick}
      title={title}
    >
      {children}
      
      {dismissible && (
        <button
          style={dismissButtonStyles}
          onClick={handleDismiss}
          title={t ? t('dismiss') : 'Dismiss'}
        >
          ×
        </button>
      )}
    </span>
  );
};

export default Badge;
