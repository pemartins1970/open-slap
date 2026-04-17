import React, { useState, useRef } from 'react';

/**
 * Input - Componente de input reutilizável com validação e múltiplos tipos.
 * 
 * @param {Object} props
 * @param {string} props.type - Tipo do input (text, password, email, number, tel, url, search)
 * @param {string} props.placeholder - Placeholder text
 * @param {string} props.value - Valor controlado
 * @param {Function} props.onChange - Handler de mudança
 * @param {Function} props.onBlur - Handler de blur
 * @param {Function} props.onFocus - Handler de focus
 * @param {string} props.label - Label do input
 * @param {string} props.error - Mensagem de erro
 * @param {string} props.helperText - Texto de ajuda
 * @param {boolean} props.required - Se é obrigatório
 * @param {boolean} props.disabled - Se está desabilitado
 * @param {boolean} props.readonly - Se é somente leitura
 * @param {boolean} props.fullWidth - Se ocupa toda a largura
 * @param {string} props.size - Tamanho (small, medium, large)
 * @param {string} props.variant - Variante (outlined, filled, standard)
 * @param {Object} props.validation - Regras de validação
 * @param {boolean} props.showPasswordToggle - Mostra toggle para senha
 * @param {string} props.startAdornment - Elemento no início
 * @param {string} props.endAdornment - Elemento no fim
 * @param {Object} props.styles - Estilos do tema
 * @param {Function} props.t - Função de tradução
 */
const Input = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  onBlur,
  onFocus,
  label,
  error,
  helperText,
  required = false,
  disabled = false,
  readonly = false,
  fullWidth = false,
  size = 'medium',
  variant = 'outlined',
  validation,
  showPasswordToggle = false,
  startAdornment,
  endAdornment,
  styles,
  t
}) => {
  const [focused, setFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const inputRef = useRef(null);

  const handleFocus = (e) => {
    setFocused(true);
    if (onFocus) onFocus(e);
  };

  const handleBlur = (e) => {
    setFocused(false);
    if (onBlur) onBlur(e);
  };

  const handleChange = (e) => {
    if (onChange) {
      onChange(e);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'outlined':
        return {
          border: `1px solid ${error ? '#dc3545' : focused ? '#007bff' : '#dee2e6'}`,
          backgroundColor: disabled ? '#f8f9fa' : 'white',
          borderRadius: '4px',
          boxShadow: focused ? '0 0 0 2px rgba(0, 123, 255, 0.25)' : 'none'
        };
      case 'filled':
        return {
          border: 'none',
          backgroundColor: disabled ? '#e9ecef' : '#f8f9fa',
          borderBottom: `1px solid ${error ? '#dc3545' : focused ? '#007bff' : '#dee2e6'}`,
          borderRadius: '4px 4px 0 0'
        };
      default:
        return {
          border: 'none',
          borderBottom: `1px solid ${error ? '#dc3545' : focused ? '#007bff' : '#dee2e6'}`,
          backgroundColor: 'transparent',
          borderRadius: 0
        };
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          padding: '4px 8px',
          fontSize: '12px',
          lineHeight: '1.2'
        };
      case 'large':
        return {
          padding: '12px 16px',
          fontSize: '16px',
          lineHeight: '1.4'
        };
      default:
        return {
          padding: '8px 12px',
          fontSize: '14px',
          lineHeight: '1.3'
        };
    }
  };

  const inputType = type === 'password' && showPassword ? 'text' : type;

  const baseStyles = {
    width: fullWidth ? '100%' : 'auto',
    outline: 'none',
    transition: 'all 0.2s ease-in-out',
    boxSizing: 'border-box',
    fontFamily: 'inherit',
    color: disabled ? '#6c757d' : '#212529',
    cursor: disabled ? 'not-allowed' : readonly ? 'default' : 'text',
    ...getVariantStyles(),
    ...getSizeStyles(),
    ...(startAdornment && { paddingLeft: '32px' }),
    ...(endAdornment && { paddingRight: '32px' })
  };

  const containerStyles = {
    position: 'relative',
    display: fullWidth ? 'block' : 'inline-block',
    width: fullWidth ? '100%' : 'auto'
  };

  const labelStyles = {
    display: 'block',
    marginBottom: '4px',
    fontSize: '12px',
    fontWeight: '500',
    color: error ? '#dc3545' : '#495057',
    ...(required && {
      '::after': { content: '" *"', color: '#dc3545' }
    })
  };

  const helperTextStyles = {
    marginTop: '4px',
    fontSize: '12px',
    color: error ? '#dc3545' : '#6c757d'
  };

  const adornmentStyles = {
    position: 'absolute',
    top: '50%',
    transform: 'translateY(-50%)',
    display: 'flex',
    alignItems: 'center',
    color: '#6c757d',
    fontSize: '14px'
  };

  const startAdornmentStyles = {
    ...adornmentStyles,
    left: '8px'
  };

  const endAdornmentStyles = {
    ...adornmentStyles,
    right: '8px'
  };

  const passwordToggleStyles = {
    ...adornmentStyles,
    right: '8px',
    cursor: 'pointer',
    userSelect: 'none',
    '&:hover': {
      color: '#007bff'
    }
  };

  return (
    <div style={containerStyles}>
      {label && (
        <label style={labelStyles}>
          {label}
          {required && <span style={{ color: '#dc3545' }}> *</span>}
        </label>
      )}

      <div style={{ position: 'relative' }}>
        {startAdornment && (
          <div style={startAdornmentStyles}>
            {startAdornment}
          </div>
        )}

        <input
          ref={inputRef}
          type={inputType}
          placeholder={placeholder}
          value={value || ''}
          onChange={handleChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          disabled={disabled}
          readOnly={readonly}
          required={required}
          style={baseStyles}
        />

        {type === 'password' && showPasswordToggle && !readonly && !disabled && (
          <div
            style={passwordToggleStyles}
            onClick={togglePasswordVisibility}
            title={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? 'Hide' : 'Show'}
          </div>
        )}

        {endAdornment && type !== 'password' && (
          <div style={endAdornmentStyles}>
            {endAdornment}
          </div>
        )}
      </div>

      {(error || helperText) && (
        <div style={helperTextStyles}>
          {error || helperText}
        </div>
      )}
    </div>
  );
};

export default Input;
