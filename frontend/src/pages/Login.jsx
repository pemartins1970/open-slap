/**
 * 🔐 LOGIN - Página de Autenticação
 * Componente de login/register segundo WINDSURF_AGENT.md
 *
 * CORREÇÃO: recebe onLogin/onRegister como props do App_auth.jsx.
 * Instanciar useAuth() aqui criaria um estado isolado — o App pai
 * nunca ficaria sabendo do login e o redirect não dispararia.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Logo path: detecta ambiente e usa caminho apropriado
const getLogoSrc = () => {
  // No Electron, tenta caminhos relativos ao app bundle
  if (window.location.protocol === 'file:') {
    // Caminhos possíveis no Electron empacotado
    const possiblePaths = [
      './open_slap.png',
      '../open_slap.png',
      '../../open_slap.png',
      'open_slap.png'
    ];
    // Retorna o primeiro (mais provável)
    return possiblePaths[0];
  }
  // Web - caminho absoluto do servidor
  return '/open_slap.png';
};

const OPEN_SLAP_LOGO_SRC = getLogoSrc();

const Login = ({ onLogin, onRegister, onPasswordResetRequest, onPasswordResetConfirm, t }) => {
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
      // Chama a função do pai (App_auth.jsx) — mesmo estado, mesmo hook
      const result = isLogin
        ? await onLogin(email, password)
        : await onRegister(email, password);

      if (!result.success) {
        // Se a API retornou erro (ex: 400), exibe o erro real vindo do backend
        const data = result.data || {};
        setMsg({ ok: false, text: data.detail || data.msg || result.error || 'Erro desconhecido' });
      } else {
        if (!isLogin) setMsg({ ok: true, text: 'Cadastro realizado!' });
        // Estado do App pai já foi atualizado → guard de rota redireciona
        navigate('/');
      }
    } catch (err) {
      console.error('Submit error:', err);
      setMsg({ ok: false, text: 'Erro de conexão: ' + err.message });
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
        setMsg({ ok: false, text: data?.detail || data?.msg || result?.error || t ? t('password_reset_error') : 'Could not request password reset' });
      } else {
        const msg = result.recoveryCode
          ? `${t ? t('recovery_code') : 'Recovery code'}: ${result.recoveryCode}`
          : t ? t('follow_instructions') : 'Follow the instructions to continue';
        setResetMessage(msg);
        setResetStep(2);
      }
    } catch (err) {
      console.error('Password reset error:', err);
      setMsg({ ok: false, text: t ? t('unexpected_error') : 'Unexpected error. Please try again.' });
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
        setMsg({ ok: false, text: data?.detail || data?.msg || result?.error || t ? t('password_reset_confirm_error') : 'Could not reset password' });
      } else {
        setResetMessage(t ? t('password_reset_success') : 'Password reset. You can now sign in.');
        setView('auth');
        setIsLogin(true);
        setPassword('');
      }
    } catch (err) {
      console.error('Password reset confirm error:', err);
      setMsg({ ok: false, text: t ? t('unexpected_error') : 'Unexpected error. Please try again.' });
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
    { text: t ? t('min_8_chars') : 'Mínimo 8 caracteres', valid: password.length >= 8 },
    { text: t ? t('one_uppercase') : '1 letra maiúscula', valid: /[A-Z]/.test(password) },
    { text: t ? t('one_number') : '1 número', valid: /[0-9]/.test(password) }
  ];

  return (
    <div style={styles.container}>
      {/* Left Column - Logo with Gradient Background */}
      <div style={styles.leftColumn}>
        <div style={styles.logoContainer}>
          <img src={OPEN_SLAP_LOGO_SRC} alt="Open Slap" style={styles.logoImage} />
        </div>
      </div>

      {/* Right Column - Login Form */}
      <div style={styles.rightColumn}>
        <div style={styles.card}>
          <h1 style={styles.title}>
            <span>
              {view === 'auth' ? (isLogin ? (t ? t('sign_in') : 'Sign in') : (t ? t('create_account') : 'Create account')) : (t ? t('reset_password') : 'Reset password')}
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
                placeholder={t ? t('email') : 'Email'}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={inputStyle('email')}
                onFocus={() => setFocusedField('email')}
                onBlur={() => setFocusedField(null)}
                required
              />

              <input
                type="password"
                placeholder={t ? t('password') : 'Password'}
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
                {loading ? (t ? t('processing') : 'Processing...') : (isLogin ? (t ? t('sign_in_btn') : 'Sign in') : (t ? t('create_account_btn') : 'Create account'))}
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
                {t ? t('forgot_password') : 'Forgot my password'}
              </a>
            </div>

            <div style={styles.toggle}>
              <span style={{ color: 'var(--text-dim)', marginRight: '8px' }}>
                {isLogin ? (t ? t('no_account') : "Don't have an account?") : (t ? t('have_account') : 'Already have an account?')}
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
                {isLogin ? (t ? t('create_account') : 'Create account') : (t ? t('sign_in') : 'Sign in')}
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
                  placeholder={t ? t('email') : 'Email'}
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
                  {loading ? (t ? t('processing') : 'Processing...') : (t ? t('send_code') : 'Send code')}
                </button>
              </form>
            ) : (
              <form style={styles.form} onSubmit={handlePasswordResetConfirm}>
                <input
                  type="email"
                  placeholder={t ? t('email') : 'Email'}
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  style={inputStyle('resetEmail')}
                  onFocus={() => setFocusedField('resetEmail')}
                  onBlur={() => setFocusedField(null)}
                  required
                />

                <input
                  type="text"
                  placeholder={t ? t('code') : 'Code'}
                  value={resetCode}
                  onChange={(e) => setResetCode(e.target.value)}
                  style={inputStyle('resetCode')}
                  onFocus={() => setFocusedField('resetCode')}
                  onBlur={() => setFocusedField(null)}
                  required
                />

                <input
                  type="password"
                  placeholder={t ? t('new_password') : 'New password'}
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
                  {loading ? (t ? t('processing') : 'Processing...') : (t ? t('reset_password_btn') : 'Reset password')}
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
                    {t ? t('send_new_code') : 'Send a new code'}
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
                {t ? t('back') : 'Back'}
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
