/**
 * 🔐 USE AUTH - Hook de Autenticação
 * Gerenciamento de estado de autenticação
 * Segundo WINDSURF_AGENT.md - AUTH-02
 */

import { useState, useEffect, useCallback } from 'react';

const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  // Verificar token ao carregar
  useEffect(() => {
    const initAuth = async () => {
      try {
        const savedToken = localStorage.getItem('agentic_token');
        const savedUser = localStorage.getItem('agentic_user');

        if (savedToken && savedUser) {
          // Sincronizar token state
          setToken(savedToken);
          try {
            const parsedUser = JSON.parse(savedUser);
            if (parsedUser && typeof parsedUser === 'object') {
              setUser(parsedUser);
            }
          } catch {}

          let response = null;
          try {
            response = await fetch('/auth/me', {
              headers: {
                'Authorization': `Bearer ${savedToken}`,
                'Content-Type': 'application/json'
              }
            });
          } catch {
            response = null;
          }

          if (response && response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else if (response && (response.status === 401 || response.status === 403)) {
            localStorage.removeItem('agentic_token');
            localStorage.removeItem('agentic_user');
            setToken(null);
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Auth verification error:', error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (email, password) => {
    try {
      const normalizedEmail = (email || '').trim().toLowerCase();
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: normalizedEmail, password })
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('agentic_token', data.access_token);
        localStorage.setItem('agentic_user', JSON.stringify(data.user));
        setToken(data.access_token);
        setUser(data.user);
        return { success: true };
      } else {
        return { success: false, error: data.detail };
      }
    } catch (error) {
      return { success: false, error: 'Connection error' };
    }
  }, []);

  const register = useCallback(async (email, password) => {
    try {
      const normalizedEmail = (email || '').trim().toLowerCase();
      // 1. Criar o usuário
      const response = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: normalizedEmail, password })
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.detail };
      }

      // 2. Registro ok → fazer login automaticamente para obter o token
      return await login(email, password);

    } catch (error) {
      return { success: false, error: 'Connection error' };
    }
  }, [login]);

  const requestPasswordReset = useCallback(async (email) => {
    try {
      const normalizedEmail = (email || '').trim().toLowerCase();
      const response = await fetch('/auth/password-reset/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: normalizedEmail })
      });
      const data = await response.json();
      if (!response.ok) {
        return { success: false, error: data.detail || 'Could not request password reset' };
      }
      return { success: true, recoveryCode: data.recovery_code };
    } catch (error) {
      return { success: false, error: 'Connection error' };
    }
  }, []);

  const confirmPasswordReset = useCallback(async (email, code, newPassword) => {
    try {
      const normalizedEmail = (email || '').trim().toLowerCase();
      const response = await fetch('/auth/password-reset/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: normalizedEmail, code, new_password: newPassword })
      });
      const data = await response.json();
      if (!response.ok) {
        return { success: false, error: data.detail || 'Could not reset password' };
      }
      return { success: true, message: data.message };
    } catch (error) {
      return { success: false, error: 'Connection error' };
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('agentic_token');
    localStorage.removeItem('agentic_user');
    setToken(null);
    setUser(null);
  }, []);

  const getAuthHeaders = useCallback(() => {
    const currentToken = token || localStorage.getItem('agentic_token');
    return currentToken
      ? { 'Authorization': `Bearer ${currentToken}`, 'Content-Type': 'application/json' }
      : { 'Content-Type': 'application/json' };
  }, [token]);

  return {
    user,
    loading,
    token,
    login,
    register,
    logout,
    getAuthHeaders,
    requestPasswordReset,
    confirmPasswordReset,
    // CORREÇÃO: boolean, não função — () => !!user sempre é truthy como referência de função
    isAuthenticated: !!user
  };
};

export default useAuth;
