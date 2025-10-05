import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '../utils/authContext'
import { APIClientError } from '../utils/apiBase'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login, isAuthenticated, isLoading, error } = useAuth()
  const router = useRouter()

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/dashboard')
    }
  }, [isAuthenticated, router])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await login(email, password)
      // Navigation is handled by the login function
    } catch (err) {
      // Error is handled by the auth context
      console.error('Login error:', err)
    }
  }

  // Show loading state during initial auth check
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render login form if already authenticated
  if (isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white border rounded-xl p-6 shadow-sm">
        <h1 className="text-lg font-semibold mb-4 text-center">Sign in</h1>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-600">Email</label>
            <input 
              className="mt-1 w-full border rounded-md px-3 py-2" 
              type="email"
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              required 
              disabled={isLoading}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600">Password</label>
            <input 
              className="mt-1 w-full border rounded-md px-3 py-2" 
              type="password" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              required 
              disabled={isLoading}
            />
          </div>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
          <button 
            className="w-full bg-black text-white py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed" 
            disabled={isLoading} 
            type="submit"
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Signing in...
              </span>
            ) : (
              'Sign in'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
