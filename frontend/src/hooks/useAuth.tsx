import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiFetch } from '../hooks/useApi';

type User = {
  id: string;
  email: string;
  name: string;
};

type AuthContextType = {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuth();

    const handleLogout = () => {
      setUser(null);
    };

    window.addEventListener('auth:logout', handleLogout);
    return () => window.removeEventListener('auth:logout', handleLogout);
  }, []);

  async function checkAuth() {
    const token = localStorage.getItem('fairlens_api_key');
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const response = await apiFetch<{ user: User }>('/auth/me', {
        method: 'GET',
      });
      const user = response.user || response;
      setUser(user);
    } catch {
      localStorage.removeItem('fairlens_api_key');
    } finally {
      setIsLoading(false);
    }
  }

  async function login(email: string, password: string) {
    const response = await apiFetch<{ session_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('fairlens_api_key', response.session_token);
    setUser(response.user);
  }

  function logout() {
    localStorage.removeItem('fairlens_api_key');
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}