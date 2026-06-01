import React from 'react';

/**
 * Toggle - Componente de toggle switch reutilizável.
 * 
 * @param {Object} props
 * @param {boolean} props.checked - Se está ativado
 * @param {Function} props.onChange - Handler de mudança
 * @param {string} props.label - Label do toggle
 * @param {string} props.value - Valor do toggle
 * @param {string} props.name - Nome do toggle
 * @param {boolean} props.disabled - Se está desabilitado
 * @param {boolean} props.required - Se é obrigatório
 * @param {string} props.size - Tamanho (small, medium, large)
 * @param {string} props.variant - Variante (default, slider)
 * @param {string} props.color - Cor do toggle (primary, success, warning, danger)
 * @param {string} props.error - Mensagem de erro
 * @param {string} props.helperText - Texto de ajuda
 * @param {boolean} props.fullWidth - Se ocupa toda a largura
 * @param {boolean} props.showLabel - Se mostra o label
 * @param {string} props.onLabel - Texto quando está ON
 * @param {string} props.offLabel - Texto quando está OFF
 * @param {Object} props.styles - Estilos do tema
 * @param {Function} props.t - Função de tradução
 */
const Toggle = ({
  checked = false,
  onChange,
  label,
  value,
  name,
  disabled = false,
  required = false,
  size = 'medium',
  variant = 'default',
  color = 'primary',
  error,
  helperText,
  fullWidth = false,
  showLabel = true,
  onLabel,
  offLabel,
  styles,
  t
}) => {
  const handleChange = (e) => {
    if (disabled) return;
    if (onChange) {
      onChange(e);
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          width: '36px',
          height: '20px',
          thumbSize: '16px'
        };
      case 'large':
        return {
          width: '60px',
          height: '32px',
          thumbSize: '28px'
        };
      default:
        return {
          width: '44px',
          height: '24px',
          thumbSize: '20px'
        };
    }
  };

  const getColorStyles = () => {
    switch (color) {
      case 'success':
        return {
          active: '#28a745',
          hover: '#218838'
        };
      case 'warning':
        return {
          active: '#ffc107',
          hover: '#e0a800'
        };
      case 'danger':
        return {
          active: '#dc3545',
          hover: '#c82333'
        };
      default:
        return {
          active: '#007bff',
          hover: '#0056b3'
        };
    }
  };

  const sizeStyles = getSizeStyles();
  const colorStyles = getColorStyles();

  const toggleStyles = {
    width: sizeStyles.width,
    height: sizeStyles.height,
    backgroundColor: checked ? colorStyles.active : '#dee2e6',
    borderRadius: sizeStyles.height / 2,
    position: 'relative',
    transition: 'all 0.2s ease-in-out',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1,
    '&:hover': {
      backgroundColor: disabled ? '#dee2e6' : checked ? colorStyles.hover : '#ced4da'
    },
    '&:focus': {
      boxShadow: `0 0 0 2px ${colorStyles.active}33`
    }
  };

  const thumbStyles = {
    position: 'absolute',
    top: '2px',
    left: checked ? sizeStyles.width - sizeStyles.thumbSize - 2 : '2px',
    width: sizeStyles.thumbSize,
    height: sizeStyles.thumbSize,
    backgroundColor: 'white',
    borderRadius: '50%',
    transition: 'all 0.2s ease-in-out',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
  };

  const sliderStyles = {
    ...toggleStyles,
    '&:before': {
      content: '""',
      position: 'absolute',
      top: '0',
      left: '0',
      right: '0',
      bottom: '0',
      backgroundColor: checked ? colorStyles.active : '#dee2e6',
      borderRadius: sizeStyles.height / 2,
      transition: 'all 0.2s ease-in-out'
    }
  };

  const labelStyles = {
    marginLeft: '12px',
    fontSize: '14px',
    color: disabled ? '#6c757d' : '#212529',
    cursor: disabled ? 'not-allowed' : 'pointer',
    userSelect: 'none'
  };

  const containerStyles = {
    display: fullWidth ? 'block' : 'inline-flex',
    alignItems: 'center',
    width: fullWidth ? '100%' : 'auto'
  };

  const helperTextStyles = {
    marginTop: '4px',
    fontSize: '12px',
    color: error ? '#dc3545' : '#6c757d'
  };

  const toggleLabelStyles = {
    position: 'absolute',
    top: '50%',
    transform: 'translateY(-50%)',
    fontSize: '10px',
    fontWeight: '500',
    color: 'white',
    userSelect: 'none',
    pointerEvents: 'none'
  };

  const onLabelStyles = {
    ...toggleLabelStyles,
    left: '4px'
  };

  const offLabelStyles = {
    ...toggleLabelStyles,
    right: '4px',
    color: checked ? 'transparent' : '#6c757d'
  };

  const renderToggle = () => {
    const currentStyles = variant === 'slider' ? sliderStyles : toggleStyles;

    return (
      <div style={currentStyles}>
        <div style={thumbStyles} />
        {(onLabel || offLabel) && (
          <>
            {onLabel && (
              <span style={onLabelStyles}>
                {onLabel}
              </span>
            )}
            {offLabel && (
              <span style={offLabelStyles}>
                {offLabel}
              </span>
            )}
          </>
        )}
      </div>
    );
  };

  const renderLabel = () => {
    if (!showLabel || !label) return null;

    return (
      <span style={labelStyles}>
        {label}
        {required && <span style={{ color: '#dc3545', marginLeft: '2px' }}> *</span>}
      </span>
    );
  };

  return (
    <div style={containerStyles}>
      <label style={{ display: 'flex', alignItems: 'center', cursor: disabled ? 'not-allowed' : 'pointer' }}>
        <input
          type="checkbox"
          checked={checked}
          onChange={handleChange}
          value={value}
          name={name}
          disabled={disabled}
          required={required}
          style={{
            position: 'absolute',
            opacity: 0,
            pointerEvents: 'none'
          }}
        />
        
        {renderToggle()}
        {renderLabel()}
      </label>

      {(error || helperText) && (
        <div style={helperTextStyles}>
          {error || helperText}
        </div>
      )}
    </div>
  );
};

export default Toggle;
