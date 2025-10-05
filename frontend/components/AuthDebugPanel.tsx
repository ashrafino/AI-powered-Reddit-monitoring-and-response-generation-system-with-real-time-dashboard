import React, { useState } from 'react'
import { useAuth } from '../utils/authContext'
import { apiClient } from '../utils/apiBase'

interface AuthDebugPanelProps {
  isVisible: boolean
  onClose: () => void
}

export const AuthDebugPanel: React.FC<AuthDebugPanelProps> = ({ isVisible, onClose }) => {
  const { token, user, isAuthenticated, error } = useAuth()
  const [tokenInfo, setTokenInfo] = useState<any>(null)
  const [testResult, setTestResult] = useState<string | null>(null)

  if (!isVisible) return null

  const decodeToken = () => {
    if (!token) {
      setTokenInfo({ error: 'No token available' })
      return
    }

    try {
      const parts = token.split('.')
      if (parts.length !== 3) {
        setTokenInfo({ error: 'Invalid token format' })
        return
      }

      const header = JSON.parse(atob(parts[0]))
      const payload = JSON.parse(atob(parts[1]))
      
      setTokenInfo({
        header,
        payload,
        isExpired: payload.exp < Math.floor(Date.now() / 1000),
        expiresAt: new Date(payload.exp * 1000).toLocaleString(),
        issuedAt: new Date(payload.iat * 1000).toLocaleString()
      })
    } catch (error) {
      setTokenInfo({ error: 'Failed to decode token' })
    }
  }

  const testApiCall = async () => {
    try {
      setTestResult('Testing...')
      const response = await apiClient.get('/api/auth/me')
      setTestResult(`Success: ${JSON.stringify(response, null, 2)}`)
    } catch (error: any) {
      const errorMsg = error?.message || error?.toString() || 'Unknown error'
      setTestResult(`Error: ${errorMsg}`)
    }
  }

  const copyTokenToClipboard = () => {
    if (token) {
      navigator.clipboard.writeText(token)
      alert('Token copied to clipboard')
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Authentication Debug Panel</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4 space-y-6">
          {/* Auth State */}
          <div>
            <h3 className="text-md font-medium mb-2">Authentication State</h3>
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Authenticated:</span>
                  <span className={`ml-2 ${isAuthenticated ? 'text-green-600' : 'text-red-600'}`}>
                    {isAuthenticated ? 'Yes' : 'No'}
                  </span>
                </div>
                <div>
                  <span className="font-medium">Has Token:</span>
                  <span className={`ml-2 ${token ? 'text-green-600' : 'text-red-600'}`}>
                    {token ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="col-span-2">
                  <span className="font-medium">User:</span>
                  <span className="ml-2">{user ? JSON.stringify(user) : 'None'}</span>
                </div>
                {error && (
                  <div className="col-span-2">
                    <span className="font-medium text-red-600">Error:</span>
                    <span className="ml-2 text-red-600">{error}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Token Info */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-md font-medium">Token Information</h3>
              <div className="space-x-2">
                <button
                  onClick={decodeToken}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                  disabled={!token}
                >
                  Decode Token
                </button>
                <button
                  onClick={copyTokenToClipboard}
                  className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
                  disabled={!token}
                >
                  Copy Token
                </button>
              </div>
            </div>
            
            {token ? (
              <div className="bg-gray-50 p-3 rounded-md">
                <div className="text-sm mb-2">
                  <span className="font-medium">Token (first 50 chars):</span>
                  <code className="ml-2 bg-gray-200 px-1 rounded">
                    {token.substring(0, 50)}...
                  </code>
                </div>
                
                {tokenInfo && (
                  <div className="mt-3">
                    {tokenInfo.error ? (
                      <div className="text-red-600">{tokenInfo.error}</div>
                    ) : (
                      <div className="space-y-2">
                        <div className="text-sm">
                          <span className="font-medium">Expires:</span>
                          <span className={`ml-2 ${tokenInfo.isExpired ? 'text-red-600' : 'text-green-600'}`}>
                            {tokenInfo.expiresAt} {tokenInfo.isExpired ? '(EXPIRED)' : '(Valid)'}
                          </span>
                        </div>
                        <div className="text-sm">
                          <span className="font-medium">Issued:</span>
                          <span className="ml-2">{tokenInfo.issuedAt}</span>
                        </div>
                        <details className="text-sm">
                          <summary className="font-medium cursor-pointer">Payload Details</summary>
                          <pre className="mt-2 bg-gray-200 p-2 rounded text-xs overflow-auto">
                            {JSON.stringify(tokenInfo.payload, null, 2)}
                          </pre>
                        </details>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-gray-50 p-3 rounded-md text-gray-600">
                No token available
              </div>
            )}
          </div>

          {/* API Test */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-md font-medium">API Test</h3>
              <button
                onClick={testApiCall}
                className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                disabled={!token}
              >
                Test API Call
              </button>
            </div>
            
            {testResult && (
              <div className="bg-gray-50 p-3 rounded-md">
                <pre className="text-sm overflow-auto whitespace-pre-wrap">
                  {testResult}
                </pre>
              </div>
            )}
          </div>

          {/* Local Storage */}
          <div>
            <h3 className="text-md font-medium mb-2">Local Storage</h3>
            <div className="bg-gray-50 p-3 rounded-md text-sm">
              <div className="space-y-1">
                <div>
                  <span className="font-medium">Token in localStorage:</span>
                  <span className="ml-2">
                    {typeof window !== 'undefined' && localStorage.getItem('token') ? 'Present' : 'Not found'}
                  </span>
                </div>
                <div>
                  <span className="font-medium">User in localStorage:</span>
                  <span className="ml-2">
                    {typeof window !== 'undefined' && localStorage.getItem('user') ? 'Present' : 'Not found'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Debug trigger component
export const AuthDebugTrigger: React.FC = () => {
  const [isVisible, setIsVisible] = useState(false)

  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  return (
    <>
      <button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 bg-purple-600 text-white p-2 rounded-full shadow-lg hover:bg-purple-700 z-40"
        title="Open Auth Debug Panel"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </button>
      
      <AuthDebugPanel 
        isVisible={isVisible} 
        onClose={() => setIsVisible(false)} 
      />
    </>
  )
}