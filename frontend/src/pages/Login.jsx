import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const getLogoSrc = () => {
  if (window.location.protocol === 'file:') {
    const possiblePaths = [
      './open_slap.png',
      '../open_slap.png',
      '../../open_slap.png',
      'open_slap.png'
    ];
    return possiblePaths[0];
  }
  return '/open_slap.png';
};

const OPEN_SLAP_LOGO_SRC = getLogoSrc();

const Login = ({ onLogin, onRegister, onPasswordResetRequest, onPasswordResetConfirm }) => {
  const { t } = useTranslation();
  const [view, setView] = useState('auth');
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resetStep, setResetStep] = useState(1);
  const [resetEmail, setResetEmail] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [resetNewPassword, setResetNewPassword] = useState('');
  const [resetMessage, setResetMessage] = useState('');
  const [focusedField, setFocusedField] = useState(null);
  const [msg, setMsg] = useState({ ok: false, text: '' });
  const navigate = useNavigate();

  const styles = {
    container: {
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'stretch',
      justifyContent: 'center',
      background: 'var(--bg)',
      fontFamily: 'var(--sans)',
      margin: 0,
      padding: 0
    },
    leftColumn: {
      flex: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg)',
      padding: '40px',
      minWidth: '0'
    },
    rightColumn: {
      flex: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#272727',
      padding: '40px',
      minWidth: '0'
    },
    logoContainer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '100%',
      height: '100%'
    },
    logoImage: {
      maxWidth: '400px',
      maxHeight: '400px',
      width: '100%',
      height: 'auto',
      objectFit: 'contain'
    },
    card: {
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: '12px',
      padding: 'clamp(12px, 4vw, 28px)',
      width: '100%',
      maxWidth: '400px',
      boxShadow: '0 20px 40px rgba(0,0,0,0.1)'
    },
    title: {
      color: 'var(--text)',
      fontSize: '20px',
      fontWeight: '600',
      marginBottom: '20px',
      textAlign: 'center',
      fontFamily: 'var(--sans)',
    },
    form: {
      display: 'flex',
      flexDirection: 'column',
      gap: '14px'
    },
    input: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '8px 12px',
      fontSize: '14px',
      color: 'var(--text-bright)',
      fontFamily: 'var(--sans)',
      outline: 'none',
      transition: 'border-color 0.2s',
      width: '100%',
      boxSizing: 'border-box'
    },
    button: {
      background: 'var(--amber)',
      border: 'none',
      borderRadius: '8px',
      padding: '10px 20px',
      fontSize: '15px',
      fontWeight: '600',
      color: 'var(--bg)',
      cursor: 'pointer',
      transition: 'all 0.2s',
      fontFamily: 'var(--sans)'
    },
    toggle: {
      textAlign: 'center',
      marginTop: '14px'
    },
    error: {
      background: 'rgba(248, 113, 113, 0.1)',
      border: '1px solid var(--red)',
      borderRadius: '6px',
      padding: '12px',
      color: 'var(--red)',
      fontSize: '14px',
      fontFamily: 'var(--sans)',
      marginBottom: '12px'
    },
    inputFocus: {
      borderColor: 'var(--amber)'
    },
    buttonDisabled: {
      opacity: 0.6,
      cursor: 'not-allowed'
    },
    toggleLink: {
      color: 'var(--amber)',
      textDecoration: 'none',
      fontSize: '14px',
      fontFamily: 'var(--sans)',
      cursor: 'pointer',
      transition: 'color 0.2s'
    },
    secondaryLink: {
      color: 'var(--text-dim)',
      textDecoration: 'none',
      fontSize: '13px',
      fontFamily: 'var(--sans)',
      cursor: 'pointer',
      transition: 'color 0.2s'
    },
    passwordRules: {
      marginTop: '8px',
      fontSize: '12px',
      fontFamily: 'var(--sans)',
      color: 'var(--text-dim)'
    },
    ruleItem: {
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      marginBottom: '4px'
    },
    ruleValid: {
      color: '#22c55e'
    },
    ruleInvalid: {
      color: 'var(--text-dim)'
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg({ ok: false, text: '' });

    try {
      const result = isLogin
        ? await onLogin(email, password)
        : await onRegister(email, password);

      if (!result.success) {
        const data = result.data || {};
        setMsg({ ok: false, text: data.detail || data.msg || result.error || t('error_unknown') });
      } else {
        if (!isLogin) setMsg({ ok: true, text: t('registration_success') });
        navigate('/');
      }
    } catch (err) {
      console.error('Submit error:', err);
      setMsg({ ok: false, text: t('connection_error') + err.message });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordResetRequest = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg({ ok: false, text: '' });
    setResetMessage('');
    try {
      const result = await onPasswordResetRequest(resetEmail);
      if (!result?.success) {
        let data = null;
        if (result.response) {
          try {
            data = await result.response.json();
            console.log('Password Reset API Response:', data);
          } catch (parseError) {
            console.error('Failed to parse response:', parseError);
          }
        }
        setMsg({ ok: false, text: data?.detail || data?.msg || result?.error || t('password_reset_error') });
      } else {
        const msg = result.recoveryCode
          ? `${t('recovery_code')}: ${result.recoveryCode}`
          : t('follow_instructions');
        setResetMessage(msg);
        setResetStep(2);
      }
    } catch (err) {
      console.error('Password reset error:', err);
      setMsg({ ok: false, text: t('unexpected_error') });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordResetConfirm = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg({ ok: false, text: '' });
    setResetMessage('');
    try {
      const result = await onPasswordResetConfirm(resetEmail, resetCode, resetNewPassword);
      if (!result?.success) {
        let data = null;
        if (result.response) {
          try {
            data = await result.response.json();
            console.log('Password Reset Confirm API Response:', data);
          } catch (parseError) {
            console.error('Failed to parse response:', parseError);
          }
        }
        setMsg({ ok: false, text: data?.detail || data?.msg || result?.error || t('password_reset_confirm_error') });
      } else {
        setResetMessage(t('password_reset_success'));
        setView('auth');
        setIsLogin(true);
        setPassword('');
      }
    } catch (err) {
      console.error('Password reset confirm error:', err);
      setMsg({ ok: false, text: t('unexpected_error') });
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = (field) => ({
    ...styles.input,
    ...(focusedField === field ? styles.inputFocus : {})
  });

  const isPasswordValid = () => {
    if (isLogin) return true;
    return password.length >= 8 &&
           /[A-Z]/.test(password) &&
           /[0-9]/.test(password);
  };

  const passwordRules = [
    { text: t('min_8_chars'), valid: password.length >= 8 },
    { text: t('one_uppercase'), valid: /[A-Z]/.test(password) },
    { text: t('one_number'), valid: /[0-9]/.test(password) }
  ];

  return (
    <div style={styles.container}>
      <div style={styles.leftColumn}>
        <div style={styles.logoContainer}>
          <img src={OPEN_SLAP_LOGO_SRC} alt="Open Slap" style={styles.logoImage} />
        </div>
      </div>

      <div style={styles.rightColumn}>
        <div style={styles.card}>
          <h1 style={styles.title}>
            <span>
              {view === 'auth' ? (isLogin ? t('sign_in') : t('create_account')) : t('reset_password')}
            </span>
          </h1>

        {msg.text && (
          <div style={styles.error}>
            {msg.text}
          </div>
        )}

        {view === 'auth' ? (
          <>
            <form style={styles.form} onSubmit={handleSubmit}>
              <input
                type="email"
                placeholder={t('email')}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={inputStyle('email')}
                onFocus={() => setFocusedField('email')}
                onBlur={() => setFocusedField(null)}
                required
              />

              <input
                type="password"
                placeholder={t('password')}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={inputStyle('password')}
                onFocus={() => setFocusedField('password')}
                onBlur={() => setFocusedField(null)}
                required
              />

              {!isLogin && (
                <div style={styles.passwordRules}>
                  {passwordRules.map((rule, index) => (
                    <div key={index} style={styles.ruleItem}>
                      <span style={rule.valid ? styles.ruleValid : styles.ruleInvalid}>
                        {rule.valid ? '✓' : '○'}
                      </span>
                      <span style={rule.valid ? styles.ruleValid : styles.ruleInvalid}>
                        {rule.text}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || (!isLogin && !isPasswordValid())}
                style={{
                  ...styles.button,
                  ...(loading || (!isLogin && !isPasswordValid()) ? styles.buttonDisabled : {})
                }}
              >
                {loading ? t('processing') : (isLogin ? t('sign_in_btn') : t('create_account_btn'))}
              </button>
            </form>

            <div style={{ textAlign: 'center', marginTop: '14px' }}>
              <a
                href="#"
                style={styles.secondaryLink}
                onClick={(e) => {
                  e.preventDefault();
                  setView('reset');
                  setResetStep(1);
                  setResetEmail(email);
                  setResetCode('');
                  setResetNewPassword('');
                  setResetMessage('');
                  setMsg({ ok: false, text: '' });
                }}
              >
                {t('forgot_password')}
              </a>
            </div>

            <div style={styles.toggle}>
              <span style={{ color: 'var(--text-dim)', marginRight: '8px' }}>
                {isLogin ? t('no_account') : t('have_account')}
              </span>
              <a
                href="#"
                style={styles.toggleLink}
                onClick={(e) => {
                  e.preventDefault();
                  setIsLogin(!isLogin);
                  setMsg({ ok: false, text: '' });
                }}
              >
                {isLogin ? t('create_account') : t('sign_in')}
              </a>
            </div>
          </>
        ) : (
          <>
            {resetMessage && (
              <div style={{ ...styles.error, border: '1px solid var(--border)', color: 'var(--text)', background: 'var(--bg3)' }}>
                {resetMessage}
              </div>
            )}

            {resetStep === 1 ? (
              <form style={styles.form} onSubmit={handlePasswordResetRequest}>
                <input
                  type="email"
                  placeholder={t('email')}
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  style={inputStyle('resetEmail')}
                  onFocus={() => setFocusedField('resetEmail')}
                  onBlur={() => setFocusedField(null)}
                  required
                />

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    ...styles.button,
                    ...(loading ? styles.buttonDisabled : {})
                  }}
                >
                  {loading ? t('processing') : t('send_code')}
                </button>
              </form>
            ) : (
              <form style={styles.form} onSubmit={handlePasswordResetConfirm}>
                <input
                  type="email"
                  placeholder={t('email')}
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  style={inputStyle('resetEmail')}
                  onFocus={() => setFocusedField('resetEmail')}
                  onBlur={() => setFocusedField(null)}
                  required
                />

                <input
                  type="text"
                  placeholder={t('code')}
                  value={resetCode}
                  onChange={(e) => setResetCode(e.target.value)}
                  style={inputStyle('resetCode')}
                  onFocus={() => setFocusedField('resetCode')}
                  onBlur={() => setFocusedField(null)}
                  required
                />

                <input
                  type="password"
                  placeholder={t('new_password')}
                  value={resetNewPassword}
                  onChange={(e) => setResetNewPassword(e.target.value)}
                  style={inputStyle('resetNewPassword')}
                  onFocus={() => setFocusedField('resetNewPassword')}
                  onBlur={() => setFocusedField(null)}
                  required
                />

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    ...styles.button,
                    ...(loading ? styles.buttonDisabled : {})
                  }}
                >
                  {loading ? t('processing') : t('reset_password_btn')}
                </button>

                <div style={{ textAlign: 'center', marginTop: '4px' }}>
                  <a
                    href="#"
                    style={styles.secondaryLink}
                    onClick={(e) => {
                      e.preventDefault();
                      setResetStep(1);
                      setResetCode('');
                      setResetNewPassword('');
                      setResetMessage('');
                      setMsg({ ok: false, text: '' });
                    }}
                  >
                    {t('send_new_code')}
                  </a>
                </div>
              </form>
            )}

            <div style={{ textAlign: 'center', marginTop: '18px' }}>
              <a
                href="#"
                style={styles.toggleLink}
                onClick={(e) => {
                  e.preventDefault();
                  setView('auth');
                  setMsg({ ok: false, text: '' });
                }}
              >
                {t('back')}
              </a>
            </div>
          </>
        )}
        </div>
      </div>
    </div>
  );
};

export default Login;
