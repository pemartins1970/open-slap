import React, { useState, useRef, useEffect } from 'react';

/**
 * Tooltip - Componente de tooltip reutilizável com múltiplas posições.
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Elemento que receberá o tooltip
 * @param {React.ReactNode} props.content - Conteúdo do tooltip
 * @param {string} props.position - Posição do tooltip (top, bottom, left, right, top-left, top-right, bottom-left, bottom-right)
 * @param {string} props.trigger - Gatilho para mostrar (hover, click, focus, manual)
 * @param {boolean} props.visible - Se o tooltip está visível (para trigger manual)
 * @param {Function} props.onVisibilityChange - Callback quando visibilidade muda
 * @param {number} props.delay - Delay em ms para mostrar/esconder
 * @param {number} props.showDelay - Delay específico para mostrar
 * @param {number} props.hideDelay - Delay específico para esconder
 * @param {boolean} props.arrow - Se mostra seta
 * @param {string} props.variant - Variante do tooltip (default, dark, light)
 * @param {string} props.size - Tamanho do tooltip (small, medium, large)
 * @param {boolean} props.disabled - Se está desabilitado
 * @param {boolean} props.persistent - Se persiste visível após hover
 * @param {Object} props.styles - Estilos do tema
 * @param {Function} props.t - Função de tradução
 */
const Tooltip = ({
  children,
  content,
  position = 'top',
  trigger = 'hover',
  visible: controlledVisible,
  onVisibilityChange,
  delay = 0,
  showDelay,
  hideDelay,
  arrow = true,
  variant = 'default',
  size = 'medium',
  disabled = false,
  persistent = false,
  styles,
  t
}) => {
  const [visible, setVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState(null);
  const triggerRef = useRef(null);
  const tooltipRef = useRef(null);

  const isControlled = controlledVisible !== undefined;
  const currentVisible = isControlled ? controlledVisible : visible;

  const showTooltip = () => {
    if (disabled) return;
    
    const delayToUse = showDelay !== undefined ? showDelay : delay;
    
    if (timeoutId) {
      clearTimeout(timeoutId);
      setTimeoutId(null);
    }
    
    if (delayToUse > 0) {
      const id = setTimeout(() => {
        setVisible(true);
        if (onVisibilityChange) onVisibilityChange(true);
      }, delayToUse);
      setTimeoutId(id);
    } else {
      setVisible(true);
      if (onVisibilityChange) onVisibilityChange(true);
    }
  };

  const hideTooltip = () => {
    if (disabled || persistent) return;
    
    const delayToUse = hideDelay !== undefined ? hideDelay : delay;
    
    if (timeoutId) {
      clearTimeout(timeoutId);
      setTimeoutId(null);
    }
    
    if (delayToUse > 0) {
      const id = setTimeout(() => {
        setVisible(false);
        if (onVisibilityChange) onVisibilityChange(false);
      }, delayToUse);
      setTimeoutId(id);
    } else {
      setVisible(false);
      if (onVisibilityChange) onVisibilityChange(false);
    }
  };

  const handleClick = () => {
    if (trigger === 'click') {
      if (currentVisible) {
        hideTooltip();
      } else {
        showTooltip();
      }
    }
  };

  const handleMouseEnter = () => {
    if (trigger === 'hover') {
      showTooltip();
    }
  };

  const handleMouseLeave = () => {
    if (trigger === 'hover') {
      hideTooltip();
    }
  };

  const handleFocus = () => {
    if (trigger === 'focus') {
      showTooltip();
    }
  };

  const handleBlur = () => {
    if (trigger === 'focus') {
      hideTooltip();
    }
  };

  const getPositionStyles = () => {
    const baseStyles = {
      position: 'absolute',
      zIndex: 1000,
      pointerEvents: 'none'
    };

    switch (position) {
      case 'top':
        return {
          ...baseStyles,
          bottom: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          marginBottom: '8px'
        };
      case 'bottom':
        return {
          ...baseStyles,
          top: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          marginTop: '8px'
        };
      case 'left':
        return {
          ...baseStyles,
          right: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          marginRight: '8px'
        };
      case 'right':
        return {
          ...baseStyles,
          left: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          marginLeft: '8px'
        };
      case 'top-left':
        return {
          ...baseStyles,
          bottom: '100%',
          left: '0',
          marginBottom: '8px'
        };
      case 'top-right':
        return {
          ...baseStyles,
          bottom: '100%',
          right: '0',
          marginBottom: '8px'
        };
      case 'bottom-left':
        return {
          ...baseStyles,
          top: '100%',
          left: '0',
          marginTop: '8px'
        };
      case 'bottom-right':
        return {
          ...baseStyles,
          top: '100%',
          right: '0',
          marginTop: '8px'
        };
      default:
        return {
          ...baseStyles,
          bottom: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          marginBottom: '8px'
        };
    }
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'dark':
        return {
          backgroundColor: '#212529',
          color: 'white',
          border: '1px solid #212529'
        };
      case 'light':
        return {
          backgroundColor: 'white',
          color: '#212529',
          border: '1px solid #dee2e6',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)'
        };
      default:
        return {
          backgroundColor: '#212529',
          color: 'white',
          border: '1px solid #212529',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)'
        };
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          padding: '4px 8px',
          fontSize: '11px',
          lineHeight: '1.2',
          maxWidth: '150px'
        };
      case 'large':
        return {
          padding: '12px 16px',
          fontSize: '14px',
          lineHeight: '1.4',
          maxWidth: '400px'
        };
      default:
        return {
          padding: '8px 12px',
          fontSize: '12px',
          lineHeight: '1.3',
          maxWidth: '250px'
        };
    }
  };

  const getArrowStyles = () => {
    const arrowSize = 6;
    const variantStyles = getVariantStyles();
    
    switch (position) {
      case 'top':
        return {
          position: 'absolute',
          bottom: `-${arrowSize}px`,
          left: '50%',
          transform: 'translateX(-50%)',
          width: 0,
          height: 0,
          borderLeft: `${arrowSize}px solid transparent`,
          borderRight: `${arrowSize}px solid transparent`,
          borderTop: `${arrowSize}px solid ${variantStyles.backgroundColor}`
        };
      case 'bottom':
        return {
          position: 'absolute',
          top: `-${arrowSize}px`,
          left: '50%',
          transform: 'translateX(-50%)',
          width: 0,
          height: 0,
          borderLeft: `${arrowSize}px solid transparent`,
          borderRight: `${arrowSize}px solid transparent`,
          borderBottom: `${arrowSize}px solid ${variantStyles.backgroundColor}`
        };
      case 'left':
        return {
          position: 'absolute',
          right: `-${arrowSize}px`,
          top: '50%',
          transform: 'translateY(-50%)',
          width: 0,
          height: 0,
          borderTop: `${arrowSize}px solid transparent`,
          borderBottom: `${arrowSize}px solid transparent`,
          borderLeft: `${arrowSize}px solid ${variantStyles.backgroundColor}`
        };
      case 'right':
        return {
          position: 'absolute',
          left: `-${arrowSize}px`,
          top: '50%',
          transform: 'translateY(-50%)',
          width: 0,
          height: 0,
          borderTop: `${arrowSize}px solid transparent`,
          borderBottom: `${arrowSize}px solid transparent`,
          borderRight: `${arrowSize}px solid ${variantStyles.backgroundColor}`
        };
      default:
        return {
          position: 'absolute',
          bottom: `-${arrowSize}px`,
          left: '50%',
          transform: 'translateX(-50%)',
          width: 0,
          height: 0,
          borderLeft: `${arrowSize}px solid transparent`,
          borderRight: `${arrowSize}px solid transparent`,
          borderTop: `${arrowSize}px solid ${variantStyles.backgroundColor}`
        };
    }
  };

  const tooltipStyles = {
    ...getPositionStyles(),
    ...getVariantStyles(),
    ...getSizeStyles(),
    borderRadius: '4px',
    textAlign: 'center',
    wordWrap: 'break-word',
    opacity: currentVisible ? 1 : 0,
    visibility: currentVisible ? 'visible' : 'hidden',
    transition: 'opacity 0.2s ease-in-out, visibility 0.2s ease-in-out'
  };

  const containerStyles = {
    position: 'relative',
    display: 'inline-block'
  };

  useEffect(() => {
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [timeoutId]);

  const getEventHandlers = () => {
    const handlers = {};
    
    switch (trigger) {
      case 'hover':
        handlers.onMouseEnter = handleMouseEnter;
        handlers.onMouseLeave = handleMouseLeave;
        break;
      case 'click':
        handlers.onClick = handleClick;
        break;
      case 'focus':
        handlers.onFocus = handleFocus;
        handlers.onBlur = handleBlur;
        break;
      default:
        break;
    }
    
    return handlers;
  };

  return (
    <div style={containerStyles} ref={triggerRef}>
      <div
        {...getEventHandlers()}
        style={{ cursor: trigger === 'click' ? 'pointer' : 'default' }}
      >
        {children}
      </div>
      
      {currentVisible && (
        <div style={tooltipStyles} ref={tooltipRef}>
          {content}
          
          {arrow && (
            <div style={getArrowStyles()} />
          )}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
