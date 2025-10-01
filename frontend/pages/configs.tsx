import useSWR from 'swr'
import { useEffect, useState } from 'react'
import Router from 'next/router'
import Layout from '../components/Layout'
import { API_BASE } from '../utils/apiBase'

const API = API_BASE

const fetcher = async (url: string, token: string) => {
  const response = await fetch(url, { 
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    } 
  })
  
  if (!response.ok) {
    if (response.status === 401) {
      // Token expired or invalid, redirect to login
      localStorage.removeItem('token')
      window.location.href = '/'
      throw new Error('Unauthorized')
    }
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  
  return response.json()
}

export default function Configs() {
  const [token, setToken] = useState<string | null>(null)
  const [clientId, setClientId] = useState('')
  const [subreddits, setSubs] = useState('')
  const [keywords, setKeywords] = useState('')
  const [redditUsername, setRedditUsername] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)
  useEffect(() => {
    // Check if we're in browser before accessing localStorage
    if (typeof window !== 'undefined') {
      const t = localStorage.getItem('token')
      setToken(t)
      if (!t) {
        Router.replace('/')
      }
    }
  }, [])
  const { data: configs, error: configsError, mutate } = useSWR(
    token ? [`${API}/api/configs`, token] : null, 
    ([url, t]) => fetcher(url, t),
    { 
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      errorRetryCount: 3
    }
  )

  const create = async () => {
    if (!clientId || !subreddits || !keywords) {
      alert('Please fill in all fields')
      return
    }
    
    try {
      const response = await fetch(`${API}/api/configs`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ 
          client_id: Number(clientId), 
          reddit_username: redditUsername || null,
          reddit_subreddits: subreddits.split(',').map(s => s.trim()).filter(s => s), 
          keywords: keywords.split(',').map(k => k.trim()).filter(k => k),
          is_active: isActive
        })
      })
      
      if (response.ok) {
        setClientId('')
        setSubs('')
        setKeywords('')
        setRedditUsername('')
        setIsActive(true)
        mutate()
        alert('Configuration created successfully')
      } else {
        const errorText = await response.text()
        alert(`Failed to create configuration: ${errorText}`)
      }
    } catch (error) {
      console.error('Create config error:', error)
      alert('Error creating configuration')
    }
  }

  const startEdit = (cfg: any) => {
    setEditingId(cfg.id)
    setClientId(String(cfg.client_id))
    setRedditUsername(cfg.reddit_username || '')
    setSubs(Array.isArray(cfg.reddit_subreddits) ? cfg.reddit_subreddits.join(',') : '')
    setKeywords(Array.isArray(cfg.keywords) ? cfg.keywords.join(',') : '')
    setIsActive(Boolean(cfg.is_active))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const saveEdit = async () => {
    if (!editingId) return
    try {
      const response = await fetch(`${API}/api/configs/${editingId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          client_id: clientId ? Number(clientId) : undefined,
          reddit_username: redditUsername || null,
          reddit_subreddits: subreddits ? subreddits.split(',').map(s => s.trim()).filter(Boolean) : undefined,
          keywords: keywords ? keywords.split(',').map(k => k.trim()).filter(Boolean) : undefined,
          is_active: isActive
        })
      })
      if (!response.ok) {
        const errorText = await response.text()
        alert(`Failed to update configuration: ${errorText}`)
        return
      }
      setEditingId(null)
      setClientId('')
      setRedditUsername('')
      setSubs('')
      setKeywords('')
      setIsActive(true)
      mutate()
      alert('Configuration updated')
    } catch (err) {
      console.error('Update config error:', err)
      alert('Error updating configuration')
    }
  }

  const cancelEdit = () => {
    setEditingId(null)
    setClientId('')
    setRedditUsername('')
    setSubs('')
    setKeywords('')
    setIsActive(true)
  }

  const remove = async (id: number) => {
    if (!confirm('Delete this configuration?')) return
    try {
      const response = await fetch(`${API}/api/configs/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) {
        const errorText = await response.text()
        alert(`Failed to delete configuration: ${errorText}`)
        return
      }
      mutate()
      alert('Configuration deleted')
    } catch (err) {
      console.error('Delete config error:', err)
      alert('Error deleting configuration')
    }
  }

  if (!token) {
    return (
      <Layout>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <h2 className="text-lg font-semibold mb-3">Configs</h2>
      
      {/* Error handling */}
      {configsError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-red-600">
            Error loading configs: {configsError.message}
          </p>
        </div>
      )}
      
      <div className="bg-white border rounded-xl p-4 shadow-sm mb-4 grid gap-2 md:grid-cols-6">
        <input 
          className="border rounded-md px-3 py-2" 
          placeholder="client_id" 
          value={clientId} 
          onChange={e => setClientId(e.target.value)}
          type="number"
        />
        <input 
          className="border rounded-md px-3 py-2" 
          placeholder="reddit_username (optional)" 
          value={redditUsername} 
          onChange={e => setRedditUsername(e.target.value)}
        />
        <input 
          className="border rounded-md px-3 py-2" 
          placeholder="subreddits (csv)" 
          value={subreddits} 
          onChange={e => setSubs(e.target.value)}
        />
        <input 
          className="border rounded-md px-3 py-2" 
          placeholder="keywords (csv)" 
          value={keywords} 
          onChange={e => setKeywords(e.target.value)}
        />
        <label className="inline-flex items-center gap-2 text-sm px-2">
          <input type="checkbox" checked={isActive} onChange={e => setIsActive(e.target.checked)} />
          Active
        </label>
        {editingId ? (
          <div className="flex gap-2">
            <button 
              className="px-3 py-2 rounded-md bg-black text-white hover:bg-gray-800" 
              onClick={saveEdit}
            >
              Save
            </button>
            <button 
              className="px-3 py-2 rounded-md border hover:bg-gray-50" 
              onClick={cancelEdit}
            >
              Cancel
            </button>
          </div>
        ) : (
          <button 
            className="px-3 py-2 rounded-md bg-black text-white hover:bg-gray-800" 
            onClick={create}
            disabled={!clientId || !subreddits || !keywords}
          >
            Create
          </button>
        )}
      </div>
      
      <div className="bg-white border rounded-xl p-4 shadow-sm">
        {!configs ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading configs...</p>
          </div>
        ) : Array.isArray(configs) && configs.length > 0 ? (
          <div className="grid gap-3">
            {configs.map((cfg: any) => (
              <div key={cfg.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="font-medium">Config #{cfg.id} for client {cfg.client_id}</div>
                  <div className="flex gap-2">
                    <button className="px-2 py-1 text-sm rounded-md border hover:bg-gray-50" onClick={() => startEdit(cfg)}>Edit</button>
                    <button className="px-2 py-1 text-sm rounded-md border hover:bg-red-50 text-red-700" onClick={() => remove(cfg.id)}>Delete</button>
                  </div>
                </div>
                <div className="mt-2 grid gap-2 md:grid-cols-2">
                  <div>
                    <div className="text-xs text-gray-500">Reddit Username</div>
                    <div className="text-sm">{cfg.reddit_username || '—'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Active</div>
                    <div className="text-sm">{cfg.is_active ? 'Yes' : 'No'}</div>
                  </div>
                  <div className="md:col-span-2">
                    <div className="text-xs text-gray-500">Subreddits</div>
                    <div className="text-sm break-words">{Array.isArray(cfg.reddit_subreddits) ? cfg.reddit_subreddits.join(', ') : '—'}</div>
                  </div>
                  <div className="md:col-span-2">
                    <div className="text-xs text-gray-500">Keywords</div>
                    <div className="text-sm break-words">{Array.isArray(cfg.keywords) ? cfg.keywords.join(', ') : '—'}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-4 text-gray-600">No configs yet.</div>
        )}
      </div>
    </Layout>
  )
}
