import React from 'react';

/**
 * Radio - Componente de radio button reutilizável com múltiplas variantes.
 * 
 * @param {Object} props
 * @param {boolean} props.checked - Se está selecionado
 * @param {Function} props.onChange - Handler de mudança
 * @param {string} props.label - Label do radio
 * @param {string} props.value - Valor do radio
 * @param {string} props.name - Nome do grupo de radio
 * @param {boolean} props.disabled - Se está desabilitado
 * @param {boolean} props.required - Se é obrigatório
 * @param {string} props.size - Tamanho (small, medium, large)
 * @param {string} props.variant - Variante (default, button)
 * @param {string} props.error - Mensagem de erro
 * @param {string} props.helperText - Texto de ajuda
 * @param {boolean} props.fullWidth - Se ocupa toda a largura
 * @param {Object} props.styles - Estilos do tema
 * @param {Function} props.t - Função de tradução
 */
const Radio = ({
  checked = false,
  onChange,
  label,
  value,
  name,
  disabled = false,
  required = false,
  size = 'medium',
  variant = 'default',
  error,
  helperText,
  fullWidth = false,
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
          width: '14px',
          height: '14px',
          fontSize: '12px'
        };
      case 'large':
        return {
          width: '20px',
          height: '20px',
          fontSize: '16px'
        };
      default:
        return {
          width: '16px',
          height: '16px',
          fontSize: '14px'
        };
    }
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'button':
        return {
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '8px 16px',
          border: `1px solid ${checked ? '#007bff' : '#dee2e6'}`,
          backgroundColor: checked ? '#007bff' : 'white',
          color: checked ? 'white' : '#212529',
          borderRadius: '4px',
          cursor: disabled ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease-in-out',
          userSelect: 'none'
        };
      default:
        return {
          display: 'inline-flex',
          alignItems: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          userSelect: 'none'
        };
    }
  };

  const radioStyles = {
    ...getSizeStyles(),
    border: `2px solid ${error ? '#dc3545' : checked ? '#007bff' : '#dee2e6'}`,
    borderRadius: '50%',
    backgroundColor: checked ? '#007bff' : disabled ? '#f8f9fa' : 'white',
    cursor: disabled ? 'not-allowed' : 'pointer',
    position: 'relative',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease-in-out',
    outline: 'none',
    '&:hover': {
      borderColor: disabled ? '#dee2e6' : '#007bff'
    },
    '&:focus': {
      boxShadow: '0 0 0 2px rgba(0, 123, 255, 0.25)'
    }
  };

  const radioDotStyles = {
    width: '50%',
    height: '50%',
    backgroundColor: 'white',
    borderRadius: '50%',
    opacity: checked ? 1 : 0,
    transition: 'opacity 0.2s ease-in-out'
  };

  const labelStyles = {
    marginLeft: '8px',
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

  const renderRadio = () => {
    if (variant === 'button') {
      return (
        <div style={getVariantStyles()}>
          {checked ? '×' : 'o'}
          {label && <span style={{ marginLeft: '8px' }}>{label}</span>}
        </div>
      );
    }

    return (
      <div style={radioStyles}>
        <div style={radioDotStyles} />
      </div>
    );
  };

  const renderLabel = () => {
    if (variant === 'button') return null;
    if (!label) return null;

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
          type="radio"
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
        
        {renderRadio()}
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

export default Radio;
