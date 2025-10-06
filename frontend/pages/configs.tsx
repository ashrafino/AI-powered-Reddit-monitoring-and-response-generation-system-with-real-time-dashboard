import useSWR from 'swr'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Layout from '../components/Layout'
import ImprovedConfigManager from '../components/ImprovedConfigManager'
import { useAuth } from '../utils/authContext'
import { apiClient, APIClientError } from '../utils/apiBase'
import { AuthErrorDisplay } from '../components/AuthErrorDisplay'

const fetcher = async (url: string) => {
  try {
    return await apiClient.get(url)
  } catch (error) {
    if (error instanceof APIClientError && error.isAuthError) {
      // Auth errors are handled by the auth context
      throw error
    }
    throw error
  }
}

export default function Configs() {
  const { isAuthenticated, isLoading: authLoading, error: authError, user } = useAuth()
  const [clientId, setClientId] = useState('')
  const [subreddits, setSubs] = useState('')
  const [keywords, setKeywords] = useState('')
  const [redditUsername, setRedditUsername] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)
  const router = useRouter()

  // Auto-fill client_id from logged-in user
  useEffect(() => {
    if (user && user.client_id && !clientId) {
      setClientId(String(user.client_id))
    }
  }, [user, clientId])

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/')
    }
  }, [isAuthenticated, authLoading, router])

  const { data: configs, error: configsError, mutate } = useSWR(
    isAuthenticated ? '/api/configs' : null, 
    fetcher,
    { 
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      errorRetryCount: 3
    }
  )

  const create = async () => {
    if (!subreddits || !keywords) {
      alert('Please add at least one subreddit and one keyword')
      return
    }
    
    // Determine client_id: use explicit value, or user's client_id, or require input
    let effectiveClientId: number | null = null
    
    if (clientId) {
      // Explicitly entered client_id (for admins)
      effectiveClientId = Number(clientId)
    } else if (user?.client_id) {
      // Use logged-in user's client_id
      effectiveClientId = user.client_id
    } else {
      // No client_id available - admin must enter it
      alert('Please enter a Client ID')
      return
    }
    
    try {
      await apiClient.post('/api/configs', { 
        client_id: effectiveClientId, 
        reddit_username: redditUsername || null,
        reddit_subreddits: subreddits.split(',').map(s => s.trim()).filter(s => s), 
        keywords: keywords.split(',').map(k => k.trim()).filter(k => k),
        is_active: isActive
      })
      
      // Don't clear client_id if it's from the user
      if (!user?.client_id) {
        setClientId('')
      }
      setSubs('')
      setKeywords('')
      setRedditUsername('')
      setIsActive(true)
      mutate()
      alert('Configuration created successfully!')
    } catch (error) {
      console.error('Create config error:', error)
      if (error instanceof APIClientError) {
        alert(`Failed to create configuration: ${error.message}`)
      } else {
        alert('Error creating configuration')
      }
    }
  }

  const startEdit = (cfg: any) => {
    setEditingId(cfg.id)
    // Don't set client_id for editing - it's not editable
    setRedditUsername(cfg.reddit_username || '')
    setSubs(Array.isArray(cfg.reddit_subreddits) ? cfg.reddit_subreddits.join(',') : '')
    setKeywords(Array.isArray(cfg.keywords) ? cfg.keywords.join(',') : '')
    setIsActive(Boolean(cfg.is_active))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const saveEdit = async () => {
    if (!editingId) return
    
    if (!subreddits || !keywords) {
      alert('Please add at least one subreddit and one keyword')
      return
    }
    
    try {
      await apiClient.put(`/api/configs/${editingId}`, {
        // Don't send client_id - it shouldn't change
        reddit_username: redditUsername || null,
        reddit_subreddits: subreddits.split(',').map(s => s.trim()).filter(Boolean),
        keywords: keywords.split(',').map(k => k.trim()).filter(Boolean),
        is_active: isActive
      })
      
      setEditingId(null)
      setRedditUsername('')
      setSubs('')
      setKeywords('')
      setIsActive(true)
      mutate()
      alert('Configuration updated successfully!')
    } catch (err) {
      console.error('Update config error:', err)
      if (err instanceof APIClientError) {
        alert(`Failed to update configuration: ${err.message}`)
      } else {
        alert('Error updating configuration')
      }
    }
  }

  const cancelEdit = () => {
    setEditingId(null)
    setRedditUsername('')
    setSubs('')
    setKeywords('')
    setIsActive(true)
  }

  const remove = async (id: number) => {
    if (!confirm('Delete this configuration?')) return
    try {
      await apiClient.delete(`/api/configs/${id}`)
      mutate()
      alert('Configuration deleted')
    } catch (err) {
      console.error('Delete config error:', err)
      if (err instanceof APIClientError) {
        alert(`Failed to delete configuration: ${err.message}`)
      } else {
        alert('Error deleting configuration')
      }
    }
  }

  // Show loading state during authentication check
  if (authLoading) {
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

  // Don't render if not authenticated (redirect will happen)
  if (!isAuthenticated) {
    return null
  }

  return (
    <Layout>
      <h2 className="text-lg font-semibold mb-3">Configs</h2>
      
      {/* Authentication Error Display */}
      {authError && (
        <AuthErrorDisplay 
          error={authError}
          onLogin={() => router.push('/')}
          className="mb-4"
        />
      )}
      
      {/* Config Loading Error */}
      {configsError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-red-600">
            Error loading configs: {configsError.message}
          </p>
        </div>
      )}
      
      <div className="bg-white border rounded-xl p-4 shadow-sm mb-4">
        <h3 className="font-medium mb-3">{editingId ? 'Edit Configuration' : 'Add New Configuration'}</h3>
        <div className="grid gap-3">
          {/* Show client_id field only for admins without a client_id */}
          {!user?.client_id && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Client ID <span className="text-red-500">*</span>
              </label>
              <input 
                className="w-full border rounded-md px-3 py-2" 
                placeholder="Enter client ID" 
                value={clientId} 
                onChange={e => setClientId(e.target.value)}
                type="number"
              />
              <p className="text-xs text-gray-500 mt-1">The client this configuration belongs to</p>
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subreddits to Monitor <span className="text-red-500">*</span>
            </label>
            <input 
              className="w-full border rounded-md px-3 py-2" 
              placeholder="e.g., technology, programming, webdev" 
              value={subreddits} 
              onChange={e => setSubs(e.target.value)}
            />
            <p className="text-xs text-gray-500 mt-1">Separate multiple subreddits with commas</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Keywords to Track <span className="text-red-500">*</span>
            </label>
            <input 
              className="w-full border rounded-md px-3 py-2" 
              placeholder="e.g., API, integration, automation" 
              value={keywords} 
              onChange={e => setKeywords(e.target.value)}
            />
            <p className="text-xs text-gray-500 mt-1">Separate multiple keywords with commas</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reddit Username (Optional)
            </label>
            <input 
              className="w-full border rounded-md px-3 py-2" 
              placeholder="Leave empty to monitor all posts" 
              value={redditUsername} 
              onChange={e => setRedditUsername(e.target.value)}
            />
            <p className="text-xs text-gray-500 mt-1">Filter posts by specific Reddit user</p>
          </div>
          
          <div className="flex items-center justify-between">
            <label className="inline-flex items-center gap-2">
              <input 
                type="checkbox" 
                checked={isActive} 
                onChange={e => setIsActive(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm font-medium">Active</span>
            </label>
            
            {editingId ? (
              <div className="flex gap-2">
                <button 
                  className="px-4 py-2 rounded-md bg-black text-white hover:bg-gray-800" 
                  onClick={saveEdit}
                >
                  Save Changes
                </button>
                <button 
                  className="px-4 py-2 rounded-md border hover:bg-gray-50" 
                  onClick={cancelEdit}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button 
                className="px-4 py-2 rounded-md bg-black text-white hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed" 
                onClick={create}
                disabled={!subreddits || !keywords || (!user?.client_id && !clientId)}
              >
                Create Configuration
              </button>
            )}
          </div>
        </div>
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
