// API base URL configuration
// In development, this should point to the backend API
// In production with Docker, this should be set via environment variables

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8001';

// Authentication error codes from backend
export const AUTH_ERROR_CODES = {
  TOKEN_MISSING: 'TOKEN_MISSING',
  TOKEN_INVALID: 'TOKEN_INVALID',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  USER_NOT_FOUND: 'USER_NOT_FOUND',
  USER_INACTIVE: 'USER_INACTIVE',
  CLIENT_NOT_FOUND: 'CLIENT_NOT_FOUND'
} as const;

// API response types
export interface APIError {
  error: {
    code: string;
    message: string;
    details?: string;
    debug_info?: any;
    timestamp: string;
  };
}

export interface AuthState {
  token: string | null;
  user: any | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Enhanced API Client class
export class APIClient {
  private token: string | null = null;
  private baseURL: string;
  private onAuthError?: (error: APIError) => void;

  constructor(baseURL: string = API_BASE, onAuthError?: (error: APIError) => void) {
    this.baseURL = baseURL;
    this.onAuthError = onAuthError;
  }

  setToken(token: string | null): void {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
      console.log('Adding Authorization header with token:', this.token.substring(0, 20) + '...');
    } else {
      console.log('No token available for request');
    }

    return headers;
  }

  private isTokenValid(): boolean {
    if (!this.token) return false;
    
    try {
      // Basic JWT structure validation
      const parts = this.token.split('.');
      if (parts.length !== 3) return false;
      
      // Decode payload to check expiration
      const payload = JSON.parse(atob(parts[1]));
      const now = Math.floor(Date.now() / 1000);
      
      return payload.exp > now;
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    
    if (!response.ok) {
      let errorData: APIError;
      
      if (isJson) {
        errorData = await response.json();
      } else {
        errorData = {
          error: {
            code: 'HTTP_ERROR',
            message: `HTTP ${response.status}: ${response.statusText}`,
            timestamp: new Date().toISOString()
          }
        };
      }

      // Handle authentication errors
      if (response.status === 401) {
        console.error('Authentication error:', errorData);
        if (this.onAuthError) {
          this.onAuthError(errorData);
        }
      }

      throw new APIClientError(errorData, response.status);
    }

    if (isJson) {
      return await response.json();
    } else {
      return response.text() as unknown as T;
    }
  }

  async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    // Validate token before making request
    if (this.token && !this.isTokenValid()) {
      const error: APIError = {
        error: {
          code: AUTH_ERROR_CODES.TOKEN_EXPIRED,
          message: 'Token has expired',
          timestamp: new Date().toISOString()
        }
      };
      
      if (this.onAuthError) {
        this.onAuthError(error);
      }
      
      throw new APIClientError(error, 401);
    }

    const url = `${this.baseURL}${endpoint}`;
    const authHeaders = this.getAuthHeaders();
    const config: RequestInit = {
      ...options,
      headers: {
        ...options.headers,
        ...authHeaders,
      },
    };

    try {
      const response = await fetch(url, config);
      return await this.handleResponse<T>(response);
    } catch (error) {
      if (error instanceof APIClientError) {
        throw error;
      }
      
      // Network or other errors
      const apiError: APIError = {
        error: {
          code: 'NETWORK_ERROR',
          message: error instanceof Error ? error.message : 'Network request failed',
          timestamp: new Date().toISOString()
        }
      };
      
      throw new APIClientError(apiError, 0);
    }
  }

  // Convenience methods
  async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
    const requestOptions: RequestInit = {
      ...options,
      method: 'POST',
    };
    
    // Use body from options if provided, otherwise stringify data
    if (!requestOptions.body && data) {
      requestOptions.body = JSON.stringify(data);
    }
    
    return this.request<T>(endpoint, requestOptions);
  }

  async put<T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

// Custom error class for API errors
export class APIClientError extends Error {
  public apiError: APIError;
  public status: number;

  constructor(apiError: APIError, status: number) {
    super(apiError.error.message);
    this.name = 'APIClientError';
    this.apiError = apiError;
    this.status = status;
  }

  get errorCode(): string {
    return this.apiError.error.code;
  }

  get isAuthError(): boolean {
    return this.status === 401;
  }

  get isTokenExpired(): boolean {
    return this.errorCode === AUTH_ERROR_CODES.TOKEN_EXPIRED;
  }
}

// Create a default API client instance
export const apiClient = new APIClient();
