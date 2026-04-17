import React, { useState } from 'react';
import Header from './Header';
import LeftSidebar from './LeftSidebar';
import RightSidebar from './RightSidebar';
import MainContent from './MainContent';

/**
 * AppLayout - Layout principal da aplicação com header, sidebars e conteúdo.
 * 
 * @param {Object} props
 * @param {Object} props.styles - Estilos
 * @param {Object} props.user - Dados do usuário
 * @param {boolean} props.leftSidebarCollapsed - Se a sidebar esquerda está colapsada
 * @param {boolean} props.rightSidebarCollapsed - Se a sidebar direita está colapsada
 * @param {Function} props.setLeftSidebarCollapsed - Toggle da sidebar esquerda
 * @param {Function} props.setRightSidebarCollapsed - Toggle da sidebar direita
 * @param {Object} props.leftSidebarProps - Props para a sidebar esquerda
 * @param {Object} props.rightSidebarProps - Props para a sidebar direita
 * @param {Object} props.mainContentProps - Props para o conteúdo principal
 * @param {Function} props.t - Função de tradução
 */
const AppLayout = ({
  styles,
  user,
  leftSidebarCollapsed,
  rightSidebarCollapsed,
  setLeftSidebarCollapsed,
  setRightSidebarCollapsed,
  leftSidebarProps,
  rightSidebarProps,
  mainContentProps,
  t
}) => {
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile view
  React.useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleToggleLeftSidebar = () => {
    setLeftSidebarCollapsed(!leftSidebarCollapsed);
  };

  const handleToggleRightSidebar = () => {
    setRightSidebarCollapsed(!rightSidebarCollapsed);
  };

  const layoutClasses = {
    ...styles.appLayout,
    ...(isMobile ? styles.appLayoutMobile : {}),
    ...(leftSidebarCollapsed ? styles.appLayoutLeftCollapsed : {}),
    ...(rightSidebarCollapsed ? styles.appLayoutRightCollapsed : {})
  };

  return (
    <div style={layoutClasses}>
      {/* Header */}
      <Header
        styles={styles}
        user={user}
        leftSidebarCollapsed={leftSidebarCollapsed}
        rightSidebarCollapsed={rightSidebarCollapsed}
        onToggleLeftSidebar={handleToggleLeftSidebar}
        onToggleRightSidebar={handleToggleRightSidebar}
        isMobile={isMobile}
        t={t}
      />

      {/* Main Layout Container */}
      <div style={styles.layoutContainer}>
        {/* Left Sidebar */}
        {!leftSidebarCollapsed && (
          <LeftSidebar
            styles={styles}
            collapsed={leftSidebarCollapsed}
            onToggle={handleToggleLeftSidebar}
            isMobile={isMobile}
            {...leftSidebarProps}
          />
        )}

        {/* Main Content */}
        <MainContent
          styles={styles}
          leftSidebarCollapsed={leftSidebarCollapsed}
          rightSidebarCollapsed={rightSidebarCollapsed}
          isMobile={isMobile}
          {...mainContentProps}
        />

        {/* Right Sidebar */}
        {!rightSidebarCollapsed && (
          <RightSidebar
            styles={styles}
            collapsed={rightSidebarCollapsed}
            onToggle={handleToggleRightSidebar}
            isMobile={isMobile}
            {...rightSidebarProps}
          />
        )}
      </div>

      {/* Mobile Overlay */}
      {isMobile && (!leftSidebarCollapsed || !rightSidebarCollapsed) && (
        <div
          style={styles.mobileOverlay}
          onClick={() => {
            if (!leftSidebarCollapsed) setLeftSidebarCollapsed(true);
            if (!rightSidebarCollapsed) setRightSidebarCollapsed(true);
          }}
        />
      )}
    </div>
  );
};

export default AppLayout;
