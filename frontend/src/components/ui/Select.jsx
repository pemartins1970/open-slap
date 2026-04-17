import React, { useState } from 'react';

/**
 * Select - Componente de select reutilizável com múltiplas variantes e busca.
 * 
 * @param {Object} props
 * @param {Array} props.options - Array de opções [{value, label, disabled, group}]
 * @param {string} props.value - Valor selecionado
 * @param {Function} props.onChange - Handler de mudança
 * @param {string} props.placeholder - Placeholder text
 * @param {string} props.label - Label do select
 * @param {string} props.error - Mensagem de erro
 * @param {string} props.helperText - Texto de ajuda
 * @param {boolean} props.required - Se é obrigatório
 * @param {boolean} props.disabled - Se está desabilitado
 * @param {boolean} props.readonly - Se é somente leitura
 * @param {boolean} props.fullWidth - Se ocupa toda a largura
 * @param {boolean} props.searchable - Se permite busca
 * @param {boolean} props.clearable - Se permite limpar seleção
 * @param {boolean} props.multiSelect - Se permite múltipla seleção
 * @param {string} props.size - Tamanho (small, medium, large)
 * @param {string} props.variant - Variante (outlined, filled, standard)
 * @param {Function} props.onSearch - Handler de busca
 * @param {string} props.searchPlaceholder - Placeholder do campo de busca
 * @param {Object} props.styles - Estilos do tema
 * @param {Function} props.t - Função de tradução
 */
const Select = ({
  options = [],
  value,
  onChange,
  placeholder,
  label,
  error,
  helperText,
  required = false,
  disabled = false,
  readonly = false,
  fullWidth = false,
  searchable = false,
  clearable = false,
  multiSelect = false,
  size = 'medium',
  variant = 'outlined',
  onSearch,
  searchPlaceholder,
  styles,
  t
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const handleToggle = () => {
    if (disabled || readonly) return;
    setIsOpen(!isOpen);
    if (!isOpen) {
      setSearchTerm('');
      setHighlightedIndex(-1);
    }
  };

  const handleSelect = (option) => {
    if (option.disabled) return;

    if (multiSelect) {
      const currentValue = Array.isArray(value) ? value : [];
      const newValue = currentValue.includes(option.value)
        ? currentValue.filter(v => v !== option.value)
        : [...currentValue, option.value];
      
      if (onChange) {
        onChange({ target: { value: newValue } });
      }
    } else {
      if (onChange) {
        onChange({ target: { value: option.value } });
      }
      setIsOpen(false);
    }
  };

  const handleClear = (e) => {
    e.stopPropagation();
    if (onChange) {
      onChange({ target: { value: multiSelect ? [] : '' } });
    }
  };

  const handleSearch = (term) => {
    setSearchTerm(term);
    if (onSearch) {
      onSearch(term);
    }
  };

  const handleKeyDown = (e) => {
    if (disabled || readonly || !isOpen) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev < filteredOptions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && filteredOptions[highlightedIndex]) {
          handleSelect(filteredOptions[highlightedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
      default:
        break;
    }
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'outlined':
        return {
          border: `1px solid ${error ? '#dc3545' : isOpen ? '#007bff' : '#dee2e6'}`,
          backgroundColor: disabled ? '#f8f9fa' : 'white',
          borderRadius: '4px',
          boxShadow: isOpen ? '0 0 0 2px rgba(0, 123, 255, 0.25)' : 'none'
        };
      case 'filled':
        return {
          border: 'none',
          backgroundColor: disabled ? '#e9ecef' : '#f8f9fa',
          borderBottom: `1px solid ${error ? '#dc3545' : isOpen ? '#007bff' : '#dee2e6'}`,
          borderRadius: '4px 4px 0 0'
        };
      default:
        return {
          border: 'none',
          borderBottom: `1px solid ${error ? '#dc3545' : isOpen ? '#007bff' : '#dee2e6'}`,
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

  const filteredOptions = options.filter(option => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      (option.label || '').toLowerCase().includes(searchLower) ||
      (option.value || '').toString().toLowerCase().includes(searchLower)
    );
  });

  const getSelectedLabel = () => {
    if (multiSelect) {
      const selectedValues = Array.isArray(value) ? value : [];
      const selectedOptions = options.filter(opt => selectedValues.includes(opt.value));
      return selectedOptions.map(opt => opt.label).join(', ') || '';
    } else {
      const selectedOption = options.find(opt => opt.value === value);
      return selectedOption ? selectedOption.label : '';
    }
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

  const selectStyles = {
    width: '100%',
    outline: 'none',
    transition: 'all 0.2s ease-in-out',
    boxSizing: 'border-box',
    fontFamily: 'inherit',
    color: disabled ? '#6c757d' : '#212529',
    cursor: disabled ? 'not-allowed' : readonly ? 'default' : 'pointer',
    userSelect: 'none',
    ...getVariantStyles(),
    ...getSizeStyles(),
    paddingRight: clearable && !disabled && !readonly ? '32px' : '24px'
  };

  const dropdownStyles = {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    backgroundColor: 'white',
    border: '1px solid #dee2e6',
    borderTop: 'none',
    borderRadius: '0 0 4px 4px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    zIndex: 1000,
    maxHeight: '200px',
    overflowY: 'auto'
  };

  const optionStyles = {
    padding: '8px 12px',
    cursor: 'pointer',
    borderBottom: '1px solid #f8f9fa',
    backgroundColor: 'white',
    color: '#212529',
    fontSize: '14px',
    lineHeight: '1.3'
  };

  const optionHighlightedStyles = {
    ...optionStyles,
    backgroundColor: '#f8f9fa'
  };

  const optionDisabledStyles = {
    ...optionStyles,
    color: '#6c757d',
    cursor: 'not-allowed'
  };

  const optionSelectedStyles = {
    ...optionStyles,
    backgroundColor: '#007bff',
    color: 'white'
  };

  const clearButtonStyles = {
    position: 'absolute',
    right: '8px',
    top: '50%',
    transform: 'translateY(-50%)',
    background: 'none',
    border: 'none',
    color: '#6c757d',
    cursor: 'pointer',
    padding: '2px',
    borderRadius: '2px',
    fontSize: '12px',
    '&:hover': {
      color: '#dc3545'
    }
  };

  const helperTextStyles = {
    marginTop: '4px',
    fontSize: '12px',
    color: error ? '#dc3545' : '#6c757d'
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
        <div
          style={selectStyles}
          onClick={handleToggle}
          onKeyDown={handleKeyDown}
          tabIndex={disabled ? -1 : 0}
        >
          {getSelectedLabel() || placeholder || (t ? t('select_option') : 'Select an option')}
        </div>

        {clearable && !disabled && !readonly && value && (
          <button
            style={clearButtonStyles}
            onClick={handleClear}
            title={t ? t('clear_selection') : 'Clear selection'}
          >
            ×
          </button>
        )}

        {isOpen && (
          <div style={dropdownStyles}>
            {searchable && (
              <div style={{ padding: '8px', borderBottom: '1px solid #dee2e6' }}>
                <input
                  type="text"
                  placeholder={searchPlaceholder || (t ? t('search_options') : 'Search options...')}
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    width: '100%',
                    padding: '4px 8px',
                    border: '1px solid #dee2e6',
                    borderRadius: '2px',
                    fontSize: '12px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>
            )}

            {filteredOptions.length === 0 ? (
              <div style={{ padding: '12px', textAlign: 'center', color: '#6c757d' }}>
                {t ? t('no_options_found') : 'No options found'}
              </div>
            ) : (
              filteredOptions.map((option, index) => {
                const isSelected = multiSelect 
                  ? Array.isArray(value) && value.includes(option.value)
                  : value === option.value;
                const isHighlighted = index === highlightedIndex;

                let optionStyle = optionStyles;
                if (option.disabled) {
                  optionStyle = optionDisabledStyles;
                } else if (isSelected) {
                  optionStyle = optionSelectedStyles;
                } else if (isHighlighted) {
                  optionStyle = optionHighlightedStyles;
                }

                return (
                  <div
                    key={option.value}
                    style={optionStyle}
                    onClick={() => handleSelect(option)}
                    onMouseEnter={() => setHighlightedIndex(index)}
                  >
                    {multiSelect && (
                      <span style={{ marginRight: '8px' }}>
                        {isSelected ? '×' : 'o'}
                      </span>
                    )}
                    {option.label}
                  </div>
                );
              })
            )}
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

export default Select;
