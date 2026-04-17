import React, { useState, useRef } from 'react';

/**
 * Textarea - Componente de textarea reutilizável com validação e auto-resize.
 * 
 * @param {Object} props
 * @param {string} props.placeholder - Placeholder text
 * @param {string} props.value - Valor controlado
 * @param {Function} props.onChange - Handler de mudança
 * @param {Function} props.onBlur - Handler de blur
 * @param {Function} props.onFocus - Handler de focus
 * @param {string} props.label - Label do textarea
 * @param {string} props.error - Mensagem de erro
 * @param {string} props.helperText - Texto de ajuda
 * @param {boolean} props.required - Se é obrigatório
 * @param {boolean} props.disabled - Se está desabilitado
 * @param {boolean} props.readonly - Se é somente leitura
 * @param {boolean} props.fullWidth - Se ocupa toda a largura
 * @param {boolean} props.autoResize - Se redimensiona automaticamente
 * @param {number} props.minRows - Número mínimo de linhas
 * @param {number} props.maxRows - Número máximo de linhas
 * @param {string} props.resize - Tipo de redimensionamento (none, both, horizontal, vertical)
 * @param {string} props.size - Tamanho (small, medium, large)
 * @param {string} props.variant - Variante (outlined, filled, standard)
 * @param {Object} props.validation - Regras de validação
 * @param {number} props.maxLength - Máximo de caracteres
 * @param {boolean} props.showCharCount - Mostra contador de caracteres
 * @param {Object} props.styles - Estilos do tema
 * @param {Function} props.t - Função de tradução
 */
const Textarea = ({
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
  autoResize = false,
  minRows = 3,
  maxRows = 10,
  resize = 'vertical',
  size = 'medium',
  variant = 'outlined',
  validation,
  maxLength,
  showCharCount = false,
  styles,
  t
}) => {
  const [focused, setFocused] = useState(false);
  const [charCount, setCharCount] = useState((value || '').length);
  const textareaRef = useRef(null);

  const handleFocus = (e) => {
    setFocused(true);
    if (onFocus) onFocus(e);
  };

  const handleBlur = (e) => {
    setFocused(false);
    if (onBlur) onBlur(e);
  };

  const handleChange = (e) => {
    const newValue = e.target.value;
    setCharCount(newValue.length);
    
    if (maxLength && newValue.length > maxLength) {
      return; // Don't update if exceeds max length
    }
    
    if (onChange) {
      onChange(e);
    }

    // Auto-resize functionality
    if (autoResize && textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const newHeight = Math.min(
        textareaRef.current.scrollHeight,
        maxRows * 20 // Approximate height per row
      );
      textareaRef.current.style.height = `${newHeight}px`;
    }
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
          padding: '6px 8px',
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

  const getResizeStyles = () => {
    switch (resize) {
      case 'none':
        return { resize: 'none' };
      case 'both':
        return { resize: 'both' };
      case 'horizontal':
        return { resize: 'horizontal' };
      case 'vertical':
        return { resize: 'vertical' };
      default:
        return { resize: 'vertical' };
    }
  };

  const getHeightStyles = () => {
    if (autoResize) {
      return {
        minHeight: `${minRows * 20}px`,
        maxHeight: `${maxRows * 20}px`,
        height: `${minRows * 20}px`
      };
    }
    return {
      minHeight: `${minRows * 20}px`
    };
  };

  const baseStyles = {
    width: fullWidth ? '100%' : 'auto',
    outline: 'none',
    transition: 'all 0.2s ease-in-out',
    boxSizing: 'border-box',
    fontFamily: 'inherit',
    color: disabled ? '#6c757d' : '#212529',
    cursor: disabled ? 'not-allowed' : readonly ? 'default' : 'text',
    overflowY: 'auto',
    ...getVariantStyles(),
    ...getSizeStyles(),
    ...getResizeStyles(),
    ...getHeightStyles()
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
    color: error ? '#dc3545' : '#495057'
  };

  const helperTextStyles = {
    marginTop: '4px',
    fontSize: '12px',
    color: error ? '#dc3545' : '#6c757d'
  };

  const charCountStyles = {
    position: 'absolute',
    bottom: '4px',
    right: '8px',
    fontSize: '11px',
    color: maxLength && charCount > maxLength * 0.9 ? '#dc3545' : '#6c757d',
    backgroundColor: 'white',
    padding: '0 4px',
    borderRadius: '2px'
  };

  const isOverLimit = maxLength && charCount >= maxLength;
  const isNearLimit = maxLength && charCount > maxLength * 0.9;

  return (
    <div style={containerStyles}>
      {label && (
        <label style={labelStyles}>
          {label}
          {required && <span style={{ color: '#dc3545' }}> *</span>}
        </label>
      )}

      <div style={{ position: 'relative' }}>
        <textarea
          ref={textareaRef}
          placeholder={placeholder}
          value={value || ''}
          onChange={handleChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          disabled={disabled}
          readOnly={readonly}
          required={required}
          maxLength={maxLength}
          style={baseStyles}
        />

        {showCharCount && (
          <div style={charCountStyles}>
            {charCount}
            {maxLength && ` / ${maxLength}`}
          </div>
        )}
      </div>

      {(error || helperText) && (
        <div style={helperTextStyles}>
          {error || helperText}
        </div>
      )}

      {maxLength && showCharCount && !error && !helperText && (
        <div style={helperTextStyles}>
          {isOverLimit 
            ? (t ? t('character_limit_exceeded') : 'Character limit exceeded')
            : isNearLimit 
              ? (t ? t('approaching_character_limit') : 'Approaching character limit')
              : ''
          }
        </div>
      )}
    </div>
  );
};

export default Textarea;
