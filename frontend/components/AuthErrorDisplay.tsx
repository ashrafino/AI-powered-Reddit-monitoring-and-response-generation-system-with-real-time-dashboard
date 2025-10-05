import React from 'react'
import { AUTH_ERROR_CODES } from '../utils/apiBase'

interface AuthErrorDisplayProps {
  error: string | null
  onRetry?: () => void
  onLogin?: () => void
  className?: string
}

export const AuthErrorDisplay: React.FC<AuthErrorDisplayProps> = ({
  error,
  onRetry,
  onLogin,
  className = ''
}) => {
  if (!error) return null

  const getErrorDetails = (error: string) => {
    // Check if error contains specific auth error codes
    if (error.includes(AUTH_ERROR_CODES.TOKEN_EXPIRED)) {
      return {
        title: 'Session Expired',
        message: 'Your session has expired. Please sign in again.',
        action: 'Sign In',
        actionHandler: onLogin,
        icon: (
          <svg className="h-6 w-6 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      }
    }

    if (error.includes(AUTH_ERROR_CODES.TOKEN_INVALID)) {
      return {
        title: 'Invalid Session',
        message: 'Your session is invalid. Please sign in again.',
        action: 'Sign In',
        actionHandler: onLogin,
        icon: (
          <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        )
      }
    }

    if (error.includes(AUTH_ERROR_CODES.USER_NOT_FOUND) || error.includes(AUTH_ERROR_CODES.USER_INACTIVE)) {
      return {
        title: 'Account Issue',
        message: 'There is an issue with your account. Please contact support or try signing in again.',
        action: 'Sign In',
        actionHandler: onLogin,
        icon: (
          <svg className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        )
      }
    }

    if (error.toLowerCase().includes('network') || error.toLowerCase().includes('connection')) {
      return {
        title: 'Connection Error',
        message: 'Unable to connect to the server. Please check your internet connection and try again.',
        action: 'Retry',
        actionHandler: onRetry,
        icon: (
          <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
          </svg>
        )
      }
    }

    // Generic error
    return {
      title: 'Error',
      message: error,
      action: onRetry ? 'Retry' : undefined,
      actionHandler: onRetry,
      icon: (
        <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    }
  }

  const errorDetails = getErrorDetails(error)

  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          {errorDetails.icon}
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            {errorDetails.title}
          </h3>
          <div className="mt-2 text-sm text-red-700">
            <p>{errorDetails.message}</p>
          </div>
          {errorDetails.action && errorDetails.actionHandler && (
            <div className="mt-4">
              <button
                onClick={errorDetails.actionHandler}
                className="bg-red-100 text-red-800 px-3 py-2 rounded-md text-sm font-medium hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                {errorDetails.action}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface ConnectionStatusProps {
  isConnected: boolean
  isReconnecting: boolean
  connectionError: string | null
  reconnectAttempts: number
  onRetry?: () => void
  className?: string
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  isReconnecting,
  connectionError,
  reconnectAttempts,
  onRetry,
  className = ''
}) => {
  if (isConnected) {
    return (
      <div className={`bg-green-50 border border-green-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-center">
          <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="ml-2 text-sm font-medium text-green-800">Connected</span>
        </div>
      </div>
    )
  }

  if (isReconnecting) {
    return (
      <div className={`bg-yellow-50 border border-yellow-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
          <span className="ml-2 text-sm font-medium text-yellow-800">
            Reconnecting... (Attempt {reconnectAttempts})
          </span>
        </div>
      </div>
    )
  }

  if (connectionError) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="ml-2">
              <span className="text-sm font-medium text-red-800">Connection Error</span>
              <p className="text-xs text-red-600 mt-1">{connectionError}</p>
            </div>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="bg-red-100 text-red-800 px-2 py-1 rounded text-xs font-medium hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-gray-50 border border-gray-200 rounded-lg p-3 ${className}`}>
      <div className="flex items-center">
        <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="ml-2 text-sm font-medium text-gray-600">Disconnected</span>
      </div>
    </div>
  )
}