export function buildAppAuthStyles({ connected } = {}) {
  return {
    app: {
      height: '100vh',
      background: 'var(--bg)',
      color: 'var(--text)',
      fontFamily: 'var(--sans)',
      display: 'flex',
      flexDirection: 'column'
    },
    header: {
      background: 'var(--bg2)',
      borderBottom: '1px solid var(--border)',
      padding: '16px 24px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    },
    headerTitle: {
      fontSize: '16px',
      fontWeight: '600',
      color: 'var(--text)',
      fontFamily: 'var(--sans)',
      lineHeight: '1.2',
      maxWidth: '520px'
    },
    headerRight: {
      display: 'flex',
      alignItems: 'center',
      gap: '16px'
    },
    iconButton: {
      background: 'transparent',
      border: '1px solid var(--border)',
      borderRadius: '6px',
      width: '36px',
      height: '36px',
      color: 'var(--text)',
      fontSize: '16px',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'all 0.15s'
    },
    connectionStatus: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      color: connected ? 'var(--green)' : 'var(--red)'
    },
    connectionDot: {
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      background: connected ? 'var(--green)' : 'var(--red)'
    },
    userButton: {
      background: 'transparent',
      border: '1px solid var(--border)',
      borderRadius: '6px',
      padding: '8px 12px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      cursor: 'pointer',
      transition: 'all 0.15s'
    },
    main: {
      flex: 1,
      display: 'flex',
      overflow: 'hidden'
    },
    sidebar: {
      width: '220px',
      background: 'var(--bg2)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      minHeight: 0
    },
    sidebarContent: {
      flex: 1,
      minHeight: 0,
      overflowY: 'auto'
    },
    sidebarSection: {
      padding: '16px',
      borderBottom: '1px solid var(--border)'
    },
    sidebarTitle: {
      fontSize: '10px',
      letterSpacing: '2',
      textTransform: 'uppercase',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)',
      marginBottom: '12px'
    },
    sidebarButton: {
      background: 'transparent',
      border: '1px solid transparent',
      borderRadius: '6px',
      padding: '10px 12px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      cursor: 'pointer',
      transition: 'all 0.15s',
      width: '100%',
      textAlign: 'left',
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    },
    sidebarButtonHover: {
      background: 'rgba(245, 166, 35, 0.08)',
      borderColor: 'rgba(245, 166, 35, 0.18)'
    },
    sidebarButtonActive: {
      background: 'rgba(245, 166, 35, 0.10)',
      borderColor: 'rgba(245, 166, 35, 0.35)',
      color: 'var(--text-bright)'
    },
    sidebarFooter: {
      padding: '16px',
      borderTop: '1px solid var(--border)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center'
    },
    sidebarBottom: {
      marginTop: 'auto',
      display: 'flex',
      flexDirection: 'column'
    },
    sidebarLogo: {
      width: '100%',
      maxWidth: '300px',
      maxHeight: '160px',
      height: 'auto',
      display: 'block',
      objectFit: 'contain',
      alignSelf: 'center'
    },
    conversationList: {
      flex: 1,
      overflow: 'auto',
      padding: '8px'
    },
    conversationItem: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '6px',
      padding: '12px',
      marginBottom: '8px',
      cursor: 'pointer',
      transition: 'all 0.15s'
    },
    todoItem: {
      background: 'var(--bg3)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '10px',
      padding: '12px',
      transition: 'all 0.15s'
    },
    todoCheck: {
      width: '22px',
      height: '22px',
      borderRadius: '6px',
      border: '1px solid rgba(255,255,255,0.18)',
      background: 'rgba(255,255,255,0.04)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'var(--text-dim)',
      fontSize: '14px',
      flex: '0 0 auto'
    },
    conversationItemActive: {
      borderColor: 'var(--amber)',
      background: 'rgba(245, 166, 35, 0.1)'
    },
    conversationTitle: {
      fontSize: '14px',
      fontWeight: '500',
      color: 'var(--text)',
      marginBottom: '4px',
      fontFamily: 'var(--sans)'
    },
    conversationMeta: {
      fontSize: '11px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)'
    },
    newConversationButton: {
      background: 'var(--amber)',
      border: 'none',
      borderRadius: '6px',
      padding: '10px 16px',
      color: 'var(--bg)',
      fontSize: '12px',
      fontWeight: '600',
      fontFamily: 'var(--mono)',
      cursor: 'pointer',
      transition: 'all 0.15s',
      width: '100%'
    },
    chatArea: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      minWidth: 0
    },
    sidebarRight: {
      width: '320px',
      background: 'var(--bg2)',
      borderLeft: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      minHeight: 0,
      padding: '16px',
      overflowY: 'auto'
    },
    chatToolbar: {
      padding: '12px 24px',
      borderBottom: '1px solid var(--border)',
      background: 'var(--bg2)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '12px'
    },
    toolbarTitleRow: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      minWidth: 0
    },
    toolbarTitleText: {
      fontFamily: 'var(--mono)',
      fontSize: '12px',
      color: 'var(--text-dim)',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    },
    chatSearchInput: {
      width: '320px',
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '10px 12px',
      fontSize: '12px',
      color: 'var(--text-bright)',
      fontFamily: 'var(--mono)',
      outline: 'none'
    },
    chatSearchClear: {
      background: 'transparent',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '10px 12px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      cursor: 'pointer'
    },
    smallIconButton: {
      background: 'transparent',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      width: '34px',
      height: '34px',
      color: 'var(--text)',
      fontSize: '14px',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    },
    listTwoCols: {
      display: 'grid',
      gridTemplateColumns: '1.2fr 0.8fr',
      gap: '12px'
    },
    lightCard: {
      background: 'rgba(255,255,255,0.06)',
      border: '1px solid rgba(255,255,255,0.10)',
      borderRadius: '12px',
      padding: '12px'
    },
    skillGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
      gap: '10px'
    },
    skillCard: {
      background: 'rgba(255,255,255,0.06)',
      border: '1px solid rgba(255,255,255,0.10)',
      borderRadius: '12px',
      padding: '12px',
      cursor: 'pointer'
    },
    skillName: {
      fontSize: '13px',
      color: 'var(--text)',
      fontFamily: 'var(--sans)',
      fontWeight: 600
    },
    skillDesc: {
      marginTop: '6px',
      fontSize: '12px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)',
      lineHeight: 1.5
    },
    connectorGrid: {
      marginTop: '10px',
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
      gap: '10px'
    },
    connectorCard: {
      background: 'rgba(0,0,0,0.18)',
      border: '1px solid rgba(255,255,255,0.10)',
      borderRadius: '12px',
      padding: '12px',
      display: 'grid',
      gap: '10px'
    },
    connectorRow: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '10px'
    },
    connectorTitle: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      minWidth: 0
    },
    connectorDot: {
      width: '10px',
      height: '10px',
      borderRadius: '50%',
      background: 'var(--red)',
      flex: '0 0 auto'
    },
    monoTextarea: {
      width: '100%',
      minHeight: '320px',
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '12px',
      padding: '12px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      outline: 'none',
      resize: 'vertical'
    },
    messagesContainer: {
      flex: 1,
      overflow: 'auto',
      padding: '24px'
    },
    message: {
      marginBottom: '24px',
      display: 'flex',
      gap: '12px'
    },
    messageUser: {
      flexDirection: 'row-reverse'
    },
    messageAvatar: {
      width: '32px',
      height: '32px',
      borderRadius: '6px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '16px',
      flexShrink: 0
    },
    messageAvatarImg: {
      width: '100%',
      height: '100%',
      objectFit: 'cover',
      borderRadius: '6px',
      display: 'block'
    },
    messageContent: {
      flex: 1,
      maxWidth: '600px'
    },
    messageBubble: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '12px',
      padding: '12px 16px',
      fontSize: '14px',
      lineHeight: '1.6',
      fontFamily: 'var(--sans)',
      whiteSpace: 'pre-wrap'
    },
    messageBubbleUser: {
      background: 'var(--amber)',
      color: 'var(--bg)',
      borderColor: 'var(--amber)'
    },
    messageTimestamp: {
      marginTop: '6px',
      fontSize: '11px',
      fontFamily: 'var(--mono)',
      color: 'var(--text-dim)'
    },
    expertTag: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: '16px',
      padding: '4px 8px',
      fontSize: '11px',
      fontFamily: 'var(--mono)',
      color: 'var(--text-dim)',
      marginTop: '8px'
    },
    expertIcon: {
      fontSize: '12px'
    },
    inputArea: {
      padding: '16px 24px',
      borderTop: '1px solid var(--border)',
      background: 'var(--bg2)'
    },
    inputContainer: {
      display: 'flex',
      gap: '12px',
      alignItems: 'flex-end'
    },
    inputWrapper: {
      flex: 1
    },
    input: {
      width: '100%',
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '12px 16px',
      fontSize: '14px',
      color: 'var(--text-bright)',
      fontFamily: 'var(--sans)',
      outline: 'none',
      resize: 'none',
      minHeight: '48px',
      maxHeight: '200px'
    },
    sendButton: {
      background: 'var(--amber)',
      border: 'none',
      borderRadius: '8px',
      padding: '12px 20px',
      color: 'var(--bg)',
      fontSize: '14px',
      fontWeight: '600',
      fontFamily: 'var(--mono)',
      cursor: 'pointer',
      transition: 'all 0.15s',
      height: '48px'
    },
    sendButtonDisabled: {
      opacity: 0.6,
      cursor: 'not-allowed'
    },
    loadingScreen: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: 'var(--bg)',
      color: 'var(--text)',
      fontFamily: 'var(--sans)'
    },
    centerPanel: {
      flex: 1,
      overflow: 'auto',
      padding: '24px'
    },
    centerPanelTitle: {
      fontSize: '14px',
      fontWeight: '600',
      fontFamily: 'var(--mono)',
      color: 'var(--text)',
      marginBottom: '16px'
    },
    emptyState: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '10px',
      padding: '16px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--sans)'
    },
    settingsSection: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '10px',
      padding: '16px',
      marginBottom: '16px'
    },
    settingsSectionTitle: {
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      color: 'var(--text)',
      marginBottom: '12px'
    },
    settingsGrid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '12px'
    },
    settingsField: {
      display: 'flex',
      flexDirection: 'column',
      gap: '6px'
    },
    settingsLabel: {
      fontSize: '11px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)'
    },
    settingsInput: {
      width: '100%',
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '10px 12px',
      fontSize: '12px',
      color: 'var(--text-bright)',
      fontFamily: 'var(--mono)',
      outline: 'none'
    },
    settingsTextarea: {
      width: '100%',
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '10px 12px',
      fontSize: '12px',
      color: 'var(--text-bright)',
      fontFamily: 'var(--mono)',
      outline: 'none',
      resize: 'vertical',
      minHeight: '90px'
    },
    settingsActions: {
      display: 'flex',
      gap: '10px',
      justifyContent: 'flex-end',
      marginTop: '12px'
    },
    settingsPrimaryButton: {
      background: 'var(--amber)',
      border: 'none',
      borderRadius: '8px',
      padding: '10px 14px',
      color: 'var(--bg)',
      fontSize: '12px',
      fontWeight: '600',
      fontFamily: 'var(--mono)',
      cursor: 'pointer'
    },
    settingsSecondaryButton: {
      background: 'transparent',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '10px 14px',
      color: 'var(--text)',
      fontSize: '12px',
      fontFamily: 'var(--mono)',
      cursor: 'pointer'
    },
    settingsHint: {
      fontSize: '11px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--sans)',
      marginTop: '8px'
    },
    settingsError: {
      background: 'rgba(248, 113, 113, 0.12)',
      border: '1px solid rgba(248, 113, 113, 0.4)',
      borderRadius: '10px',
      padding: '12px',
      color: 'var(--text)',
      fontFamily: 'var(--sans)',
      marginBottom: '16px'
    },
    doctorCard: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '10px',
      padding: '14px',
      marginBottom: '16px'
    },
    doctorRow: {
      display: 'flex',
      justifyContent: 'space-between',
      gap: '12px',
      alignItems: 'flex-start',
      padding: '8px 0',
      borderBottom: '1px solid rgba(255,255,255,0.06)'
    },
    doctorRowLast: {
      borderBottom: 'none'
    },
    doctorLabel: {
      fontSize: '12px',
      color: 'var(--text)',
      fontFamily: 'var(--sans)'
    },
    doctorDetail: {
      fontSize: '11px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)',
      marginTop: '4px'
    },
    doctorStatus: {
      fontSize: '11px',
      fontFamily: 'var(--mono)',
      padding: '4px 8px',
      borderRadius: '999px',
      border: '1px solid var(--border)',
      whiteSpace: 'nowrap'
    },
    commandCard: {
      marginTop: '10px',
      border: '1px solid rgba(245, 166, 35, 0.35)',
      background: 'rgba(245, 166, 35, 0.08)',
      borderRadius: '8px',
      padding: '12px'
    },
    commandTitle: {
      fontSize: '12px',
      fontWeight: '600',
      color: 'var(--text)',
      fontFamily: 'var(--sans)'
    },
    commandMeta: {
      marginTop: '6px',
      fontSize: '11px',
      color: 'var(--text-dim)',
      fontFamily: 'var(--mono)',
      whiteSpace: 'pre-wrap'
    },
    commandActions: {
      marginTop: '10px',
      display: 'flex',
      gap: '10px',
      alignItems: 'center'
    },
    modalOverlay: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.55)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '24px'
    },
    modal: {
      width: '100%',
      maxWidth: '640px',
      borderRadius: '10px',
      border: '1px solid var(--border)',
      background: 'var(--bg2)',
      padding: '16px'
    },
    modalHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '12px'
    },
    modalTitle: {
      fontSize: '14px',
      fontWeight: '600',
      color: 'var(--text)',
      fontFamily: 'var(--sans)'
    },
    modalBody: {
      marginTop: '12px',
      fontSize: '12px',
      color: 'var(--text)',
      fontFamily: 'var(--sans)',
      whiteSpace: 'pre-wrap'
    }
  };
}

