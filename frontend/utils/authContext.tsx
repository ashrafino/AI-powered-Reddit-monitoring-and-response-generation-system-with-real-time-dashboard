import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/router';
import { apiClient, APIError, AuthState, AUTH_ERROR_CODES, APIClientError } from './apiBase';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  handleAuthError: (error: APIError) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    token: null,
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  const router = useRouter();

  // Handle authentication errors
  const handleAuthError = useCallback((error: APIError) => {
    console.error('Authentication error:', error);
    
    const errorMessage = error?.error?.message || 'Authentication failed';
    const errorCode = error?.error?.code;
    
    setAuthState(prev => ({
      ...prev,
      error: errorMessage,
      isLoading: false,
    }));

    // Handle specific error types
    switch (errorCode) {
      case AUTH_ERROR_CODES.TOKEN_EXPIRED:
      case AUTH_ERROR_CODES.TOKEN_INVALID:
      case AUTH_ERROR_CODES.TOKEN_MISSING:
        // Clear invalid token and redirect to login
        logout();
        break;
      case AUTH_ERROR_CODES.USER_NOT_FOUND:
      case AUTH_ERROR_CODES.USER_INACTIVE:
        // User account issues - redirect to login with message
        logout();
        break;
      default:
        // Other auth errors - show error message but don't logout
        break;
    }
  }, []);

  // Initialize API client with auth error handler
  useEffect(() => {
    apiClient.setToken(authState.token);
    // Set the auth error handler on the API client
    (apiClient as any).onAuthError = handleAuthError;
  }, [authState.token, handleAuthError]);

  // Load token from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');
      
      if (storedToken) {
        try {
          // Validate token format and expiration
          const parts = storedToken.split('.');
          if (parts.length === 3) {
            const payload = JSON.parse(atob(parts[1]));
            const now = Math.floor(Date.now() / 1000);
            
            if (payload.exp > now) {
              // Token is valid - set it on apiClient immediately
              apiClient.setToken(storedToken);
              setAuthState({
                token: storedToken,
                user: storedUser ? JSON.parse(storedUser) : null,
                isAuthenticated: true,
                isLoading: false,
                error: null,
              });
              return;
            }
          }
        } catch (error) {
          console.error('Error validating stored token:', error);
        }
        
        // Token is invalid, clear it
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    
    setAuthState(prev => ({
      ...prev,
      isLoading: false,
    }));
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    setAuthState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await apiClient.post<{
        access_token: string;
        token_type: string;
      }>('/api/auth/login', undefined, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: email,
          password: password,
        }).toString(),
      });

      const { access_token } = response;

      // Set token on apiClient immediately
      apiClient.setToken(access_token);

      // Decode token to get user info
      const tokenParts = access_token.split('.');
      const payload = JSON.parse(atob(tokenParts[1]));
      
      const user = {
        email: payload.sub,
        id: payload.user_id,
        client_id: payload.client_id,
      };

      // Store token and user info
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user));
      }

      setAuthState({
        token: access_token,
        user: user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      // Redirect to dashboard after successful login
      router.push('/dashboard');
    } catch (error) {
      let errorMessage = 'Login failed';
      
      if (error instanceof APIClientError) {
        errorMessage = error.message;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      
      throw error;
    }
  };

  const logout = useCallback(() => {
    // Clear stored data
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }

    setAuthState({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });

    // Redirect to login page
    router.push('/');
  }, [router]);

  const refreshToken = async (): Promise<void> => {
    if (!authState.token) {
      throw new Error('No token to refresh');
    }

    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));

      const response = await apiClient.post<{
        access_token: string;
        token_type: string;
        user: any;
      }>('/api/auth/refresh');

      const { access_token, user } = response;

      // Store new token
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user));
      }

      setAuthState(prev => ({
        ...prev,
        token: access_token,
        user: user,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      throw error;
    }
  };

  const contextValue: AuthContextType = {
    ...authState,
    login,
    logout,
    refreshToken,
    handleAuthError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};