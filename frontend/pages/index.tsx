import { useState } from 'react'
import Router from 'next/router'
import { useEffect } from 'react'

import { API_BASE } from '../utils/apiBase'
const API = API_BASE

export default function Login({ setToken }: any) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    // Check if we're in browser before accessing localStorage
    if (typeof window !== 'undefined') {
      const t = localStorage.getItem('token')
      if (t) Router.replace('/dashboard')
    }
  }, [])

  const submit = async (e: any) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const res = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json'
        },
        body: new URLSearchParams({ username: email, password }),
      })
      
      let data
      try {
        data = await res.json()
      } catch (parseError) {
        throw new Error('Failed to parse server response')
      }
      
      if (!res.ok) {
        throw new Error(data.detail || 'Login failed')
      }
      
      if (!data.access_token) {
        throw new Error('No access token received')
      }
      
      localStorage.setItem('token', data.access_token)
      setToken(data.access_token)
      Router.push('/dashboard')
    } catch (err: any) {
      console.error('Login error:', err)
      setError(err.message || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white border rounded-xl p-6 shadow-sm">
        <h1 className="text-lg font-semibold mb-4 text-center">Sign in</h1>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-600">Email</label>
            <input className="mt-1 w-full border rounded-md px-3 py-2" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm text-gray-600">Password</label>
            <input className="mt-1 w-full border rounded-md px-3 py-2" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button className="w-full bg-black text-white py-2 rounded-md" disabled={loading} type="submit">{loading ? 'Loading…' : 'Login'}</button>
        </form>
      </div>
    </div>
  )
}
