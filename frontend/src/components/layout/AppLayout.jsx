import React, { useState, useEffect } from 'react';
import Header from './Header';
import LeftSidebar from './LeftSidebar';
import RightSidebar from './RightSidebar';

const AppLayout = ({
  styles,
  user,
  leftSidebarCollapsed,
  setLeftSidebarCollapsed,
  children,
  connected,
  runtimeLlmLabel,
  onSettingsClick,
  onLogout,
  conversations,
  currentConversation,
  onSelectConversation,
  onCreateConversation,
  onCreateNote,
  centerView,
  onNavigate
}) => {
  const [isMobile, setIsMobile] = useState(false);
  const [hideRightPanel, setHideRightPanel] = useState(false);
  const [rightSidebarCollapsed, setRightSidebarCollapsed] = useState(false);

  useEffect(() => {
    const checkViewport = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      setHideRightPanel(window.innerWidth < 900);
    };
    checkViewport();
    window.addEventListener('resize', checkViewport);
    return () => window.removeEventListener('resize', checkViewport);
  }, []);

  return (
    <div style={{ ...styles.app, height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        styles={styles}
        user={user}
        leftSidebarCollapsed={leftSidebarCollapsed}
        onToggleLeftSidebar={() => setLeftSidebarCollapsed(v => !v)}
        isMobile={isMobile}
        onSettingsClick={onSettingsClick}
        runtimeLlmLabel={runtimeLlmLabel}
        connected={connected}
        onLogout={onLogout}
      />

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <LeftSidebar
          styles={styles}
          collapsed={leftSidebarCollapsed}
          onToggle={() => setLeftSidebarCollapsed(v => !v)}
          isMobile={isMobile}
          conversations={conversations}
          currentConversation={currentConversation}
          onSelectConversation={onSelectConversation}
          onCreateConversation={onCreateConversation}
          onCreateNote={onCreateNote}
          centerView={centerView}
          onNavigate={onNavigate}
        />

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {children}
        </div>

        {!hideRightPanel && (
          <RightSidebar styles={styles} collapsed={rightSidebarCollapsed} onToggle={() => setRightSidebarCollapsed(v => !v)} />
        )}
      </div>
    </div>
  );
};

export default AppLayout;
