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

const Login = ({ onLogin, onRegister }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
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
      fontFamily: 'var(--sans)'
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
        setError(result.error || 'Erro na autenticação');
      }
    } catch (err) {
      setError('Erro inesperado. Tente novamente.');
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
          {isLogin ? '🔐 Entrar' : '📝 Cadastrar'}
        </h1>

        {error && (
          <div style={styles.error}>
            {error}
          </div>
        )}

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
            placeholder="Senha"
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
            {loading ? '⏳ Processando...' : (isLogin ? '🚀 Entrar' : '📝 Cadastrar')}
          </button>
        </form>

        <div style={styles.toggle}>
          <span style={{ color: 'var(--text-dim)', marginRight: '8px' }}>
            {isLogin ? 'Não tem conta?' : 'Já tem conta?'}
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
            {isLogin ? 'Cadastrar' : 'Entrar'}
          </a>
        </div>
      </div>
    </div>
  );
};

export default Login;
