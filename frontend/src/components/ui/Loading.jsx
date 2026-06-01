import React from 'react';

/**
 * Loading - Componente de loading reutilizável com múltiplas variantes.
 * 
 * @param {Object} props
 * @param {string} props.variant - Variante do loading (spinner, dots, bars, pulse, skeleton)
 * @param {string} props.size - Tamanho do loading (small, medium, large)
 * @param {string} props.color - Cor do loading
 * @param {string} props.text - Texto de loading
 * @param {boolean} props.overlay - Se mostra como overlay
 * @param {boolean} props.fullscreen - Se ocupa tela inteira
 * @param {boolean} props.centered - Se está centralizado
 * @param {number} props.speed - Velocidade da animação (em segundos)
 * @param {Object} props.styles - Estilos do tema
 * @param {Function} props.t - Função de tradução
 */
const Loading = ({
  variant = 'spinner',
  size = 'medium',
  color = '#007bff',
  text,
  overlay = false,
  fullscreen = false,
  centered = false,
  speed = 1,
  styles,
  t
}) => {
  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          width: '16px',
          height: '16px',
          fontSize: '12px'
        };
      case 'large':
        return {
          width: '48px',
          height: '48px',
          fontSize: '18px'
        };
      default:
        return {
          width: '24px',
          height: '24px',
          fontSize: '14px'
        };
    }
  };

  const getContainerStyles = () => {
    const sizeStyles = getSizeStyles();
    
    if (fullscreen) {
      return {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999
      };
    }

    if (overlay) {
      return {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
      };
    }

    if (centered) {
      return {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      };
    }

    return {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px'
    };
  };

  const renderSpinner = () => {
    const sizeStyles = getSizeStyles();
    
    return (
      <div
        style={{
          width: sizeStyles.width,
          height: sizeStyles.height,
          border: `2px solid transparent`,
          borderTop: `2px solid ${color}`,
          borderRadius: '50%',
          animation: `spin ${speed}s linear infinite`
        }}
      />
    );
  };

  const renderDots = () => {
    const sizeStyles = getSizeStyles();
    const dotSize = parseInt(sizeStyles.width) / 3;
    
    return (
      <div style={{ display: 'flex', gap: '4px' }}>
        {[0, 1, 2].map((index) => (
          <div
            key={index}
            style={{
              width: dotSize,
              height: dotSize,
              backgroundColor: color,
              borderRadius: '50%',
              animation: `bounce ${speed}s ease-in-out infinite`,
              animationDelay: `${index * 0.2}s`
            }}
          />
        ))}
      </div>
    );
  };

  const renderBars = () => {
    const sizeStyles = getSizeStyles();
    const barHeight = parseInt(sizeStyles.height);
    const barWidth = barHeight / 6;
    
    return (
      <div style={{ display: 'flex', gap: '2px', alignItems: 'flex-end' }}>
        {[0, 1, 2, 3, 4].map((index) => (
          <div
            key={index}
            style={{
              width: barWidth,
              height: barHeight,
              backgroundColor: color,
              borderRadius: '1px',
              animation: `bars ${speed}s ease-in-out infinite`,
              animationDelay: `${index * 0.1}s`
            }}
          />
        ))}
      </div>
    );
  };

  const renderPulse = () => {
    const sizeStyles = getSizeStyles();
    
    return (
      <div
        style={{
          width: sizeStyles.width,
          height: sizeStyles.height,
          backgroundColor: color,
          borderRadius: '50%',
          animation: `pulse ${speed}s ease-in-out infinite`
        }}
      />
    );
  };

  const renderSkeleton = () => {
    const sizeStyles = getSizeStyles();
    
    return (
      <div
        style={{
          width: sizeStyles.width,
          height: sizeStyles.height,
          backgroundColor: '#e9ecef',
          borderRadius: '4px',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent)',
            animation: `skeleton ${speed * 2}s ease-in-out infinite`
          }}
        />
      </div>
    );
  };

  const renderContent = () => {
    switch (variant) {
      case 'dots':
        return renderDots();
      case 'bars':
        return renderBars();
      case 'pulse':
        return renderPulse();
      case 'skeleton':
        return renderSkeleton();
      default:
        return renderSpinner();
    }
  };

  const containerStyles = getContainerStyles();
  const sizeStyles = getSizeStyles();

  const textStyles = {
    fontSize: sizeStyles.fontSize,
    color: '#6c757d',
    marginLeft: '8px'
  };

  return (
    <div style={containerStyles}>
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          
          @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
          }
          
          @keyframes bars {
            0%, 40%, 100% { height: 20%; }
            20% { height: 100%; }
          }
          
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
          
          @keyframes skeleton {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
          }
        `}
      </style>
      
      {renderContent()}
      
      {text && (
        <span style={textStyles}>
          {text}
        </span>
      )}
    </div>
  );
};

export default Loading;
