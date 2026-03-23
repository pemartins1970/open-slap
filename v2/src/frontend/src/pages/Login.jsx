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

const OPEN_SLAP_LOGO_SRC = '/media/open_slap.png';

const Login = ({ onLogin, onRegister, onPasswordResetRequest, onPasswordResetConfirm }) => {
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
  const navigate = useNavigate();

  const styles = {
    container: {
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg)',
      padding: '20px',
      fontFamily: 'var(--sans)'
    },
    card: {
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: '12px',
      padding: '40px',
      width: '100%',
      maxWidth: '400px',
      boxShadow: '0 20px 40px rgba(0,0,0,0.1)'
    },
    title: {
      color: 'var(--text)',
      fontSize: '24px',
      fontWeight: '600',
      marginBottom: '30px',
      textAlign: 'center',
      fontFamily: 'var(--sans)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '10px'
    },
    titleLogo: {
      width: '28px',
      height: '28px',
      objectFit: 'contain',
      display: 'block'
    },
    form: {
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    },
    input: {
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '12px 16px',
      fontSize: '14px',
      color: 'var(--text-bright)',
      fontFamily: 'var(--sans)',
      outline: 'none',
      transition: 'border-color 0.2s',
      width: '100%',
      boxSizing: 'border-box'
    },
    inputFocus: {
      borderColor: 'var(--amber)'
    },
    button: {
      background: 'var(--amber)',
      border: 'none',
      borderRadius: '8px',
      padding: '14px 24px',
      fontSize: '16px',
      fontWeight: '600',
      color: 'var(--bg)',
      cursor: 'pointer',
      transition: 'all 0.2s',
      fontFamily: 'var(--sans)'
    },
    buttonDisabled: {
      opacity: 0.6,
      cursor: 'not-allowed'
    },
    toggle: {
      textAlign: 'center',
      marginTop: '20px'
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
    error: {
      background: 'rgba(248, 113, 113, 0.1)',
      border: '1px solid var(--red)',
      borderRadius: '6px',
      padding: '12px',
      color: 'var(--red)',
      fontSize: '14px',
      fontFamily: 'var(--sans)',
      marginBottom: '20px'
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Chama a função do pai (App_auth.jsx) — mesmo estado, mesmo hook
      const result = isLogin
        ? await onLogin(email, password)
        : await onRegister(email, password);

      if (result.success) {
        // Estado do App pai já foi atualizado → guard de rota redireciona
        navigate('/');
      } else {
        setError(result.error || 'Authentication error');
      }
    } catch (err) {
      setError('Unexpected error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordResetRequest = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResetMessage('');
    try {
      const result = await onPasswordResetRequest(resetEmail);
      if (!result?.success) {
        setError(result?.error || 'Could not request password reset');
      } else {
        const msg = result.recoveryCode
          ? `Recovery code: ${result.recoveryCode}`
          : 'Follow the instructions to continue';
        setResetMessage(msg);
        setResetStep(2);
      }
    } catch (err) {
      setError('Unexpected error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordResetConfirm = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResetMessage('');
    try {
      const result = await onPasswordResetConfirm(resetEmail, resetCode, resetNewPassword);
      if (!result?.success) {
        setError(result?.error || 'Could not reset password');
      } else {
        setResetMessage('Password reset. You can now sign in.');
        setView('auth');
        setIsLogin(true);
        setPassword('');
      }
    } catch (err) {
      setError('Unexpected error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = (field) => ({
    ...styles.input,
    ...(focusedField === field ? styles.inputFocus : {})
  });

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>
          <img src={OPEN_SLAP_LOGO_SRC} alt="Open Slap" style={styles.titleLogo} />
          <span>
            {view === 'auth' ? (isLogin ? '🔐 Sign in' : '📝 Create account') : '🔑 Reset password'}
          </span>
        </h1>

        {error && (
          <div style={styles.error}>
            {error}
          </div>
        )}

        {view === 'auth' ? (
          <>
            <form style={styles.form} onSubmit={handleSubmit}>
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={inputStyle('email')}
                onFocus={() => setFocusedField('email')}
                onBlur={() => setFocusedField(null)}
                required
              />

              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={inputStyle('password')}
                onFocus={() => setFocusedField('password')}
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
                {loading ? '⏳ Processing...' : (isLogin ? '🚀 Sign in' : '📝 Create account')}
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
                  setError('');
                }}
              >
                Forgot my password
              </a>
            </div>

            <div style={styles.toggle}>
              <span style={{ color: 'var(--text-dim)', marginRight: '8px' }}>
                {isLogin ? "Don't have an account?" : 'Already have an account?'}
              </span>
              <a
                href="#"
                style={styles.toggleLink}
                onClick={(e) => {
                  e.preventDefault();
                  setIsLogin(!isLogin);
                  setError('');
                }}
              >
                {isLogin ? 'Create account' : 'Sign in'}
              </a>
            </div>
          </>
        ) : (
          <>
            {resetMessage && (
              <div style={{ ...styles.error, borderColor: 'var(--border)', color: 'var(--text)', background: 'var(--bg3)' }}>
                {resetMessage}
              </div>
            )}

            {resetStep === 1 ? (
              <form style={styles.form} onSubmit={handlePasswordResetRequest}>
                <input
                  type="email"
                  placeholder="Email"
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
                  {loading ? '⏳ Processing...' : 'Send code'}
                </button>
              </form>
            ) : (
              <form style={styles.form} onSubmit={handlePasswordResetConfirm}>
                <input
                  type="email"
                  placeholder="Email"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  style={inputStyle('resetEmail')}
                  onFocus={() => setFocusedField('resetEmail')}
                  onBlur={() => setFocusedField(null)}
                  required
                />

                <input
                  type="text"
                  placeholder="Code"
                  value={resetCode}
                  onChange={(e) => setResetCode(e.target.value)}
                  style={inputStyle('resetCode')}
                  onFocus={() => setFocusedField('resetCode')}
                  onBlur={() => setFocusedField(null)}
                  required
                />

                <input
                  type="password"
                  placeholder="New password"
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
                  {loading ? '⏳ Processing...' : 'Reset password'}
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
                      setError('');
                    }}
                  >
                    Send a new code
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
                  setError('');
                }}
              >
                Back
              </a>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Login;
