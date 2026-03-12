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

          const response = await fetch('http://localhost:8000/auth/me', {
            headers: {
              'Authorization': `Bearer ${savedToken}`,
              'Content-Type': 'application/json'
            }
          });

          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else {
            localStorage.removeItem('agentic_token');
            localStorage.removeItem('agentic_user');
            setToken(null);
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Erro ao verificar autenticação:', error);
        localStorage.removeItem('agentic_token');
        localStorage.removeItem('agentic_user');
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (email, password) => {
    try {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
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
      return { success: false, error: 'Erro de conexão' };
    }
  }, []);

  const register = useCallback(async (email, password) => {
    try {
      // 1. Criar o usuário
      const response = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.detail };
      }

      // 2. Registro ok → fazer login automaticamente para obter o token
      return await login(email, password);

    } catch (error) {
      return { success: false, error: 'Erro de conexão' };
    }
  }, [login]);

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
    // CORREÇÃO: boolean, não função — () => !!user sempre é truthy como referência de função
    isAuthenticated: !!user
  };
};

export default useAuth;
