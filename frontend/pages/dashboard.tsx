import useSWR from 'swr'
import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/router'
import Layout from '../components/Layout'

import ResponseManager from '../components/ResponseManager'
import SearchAndFilter from '../components/SearchAndFilter'
import MobileResponsiveLayout from '../components/MobileResponsiveLayout'
import { WebSocketProvider } from '../components/WebSocketProvider'
import { useAuth } from '../utils/authContext'
import { apiClient, APIClientError, API_BASE } from '../utils/apiBase'
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

function DashboardContent() {
  const { isAuthenticated, isLoading: authLoading, token, logout, error: authError } = useAuth()
  const [filteredPosts, setFilteredPosts] = useState<any[]>([])
  const [availableSubreddits, setAvailableSubreddits] = useState<string[]>([])
  const [isScanning, setIsScanning] = useState(false)
  const [scanStatus, setScanStatus] = useState<string>('')
  const router = useRouter()
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/')
    }
  }, [isAuthenticated, authLoading, router])
  
  const { data: posts, error: postsError, mutate: mutatePosts } = useSWR(
    isAuthenticated ? '/api/posts' : null, 
    fetcher,
    { 
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      errorRetryCount: 3
    }
  )

  const { data: summary, error: summaryError, mutate: mutateSummary } = useSWR(
    isAuthenticated ? '/api/analytics/summary' : null, 
    fetcher,
    { 
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      errorRetryCount: 3
    }
  )

  const { data: clients } = useSWR(
    isAuthenticated ? '/api/clients' : null,
    fetcher,
    {
      revalidateOnFocus: false,
      errorRetryCount: 3
    }
  )

  // Extract available subreddits from posts
  useEffect(() => {
    if (posts && Array.isArray(posts)) {
      const subreddits = Array.from(new Set(posts.map((p: any) => p.subreddit).filter(Boolean)))
      setAvailableSubreddits(subreddits)
      setFilteredPosts(posts)
    }
  }, [posts])

  // Filter posts based on search and filter criteria
  const handleFilterChange = useCallback((filters: any) => {
    if (!posts || !Array.isArray(posts)) return

    let filtered = [...posts]

    // Search query filter
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase()
      filtered = filtered.filter(post => 
        post.title?.toLowerCase().includes(query) ||
        post.content?.toLowerCase().includes(query) ||
        post.keywords_matched?.toLowerCase().includes(query)
      )
    }

    // Client filter
    if (filters.clientId) {
      filtered = filtered.filter(post => post.client_id === parseInt(filters.clientId))
    }

    // Subreddit filter
    if (filters.subreddit) {
      filtered = filtered.filter(post => post.subreddit === filters.subreddit)
    }

    // Date range filter
    if (filters.dateRange !== 'all') {
      const now = new Date()
      const filterDate = new Date()
      
      switch (filters.dateRange) {
        case 'today':
          filterDate.setHours(0, 0, 0, 0)
          break
        case 'week':
          filterDate.setDate(now.getDate() - 7)
          break
        case 'month':
          filterDate.setMonth(now.getMonth() - 1)
          break
        case 'quarter':
          filterDate.setMonth(now.getMonth() - 3)
          break
      }
      
      filtered = filtered.filter(post => 
        new Date(post.created_at) >= filterDate
      )
    }

    // Response status filter
    if (filters.responseStatus !== 'all') {
      switch (filters.responseStatus) {
        case 'with_responses':
          filtered = filtered.filter(post => post.responses && post.responses.length > 0)
          break
        case 'without_responses':
          filtered = filtered.filter(post => !post.responses || post.responses.length === 0)
          break
        case 'copied':
          filtered = filtered.filter(post => 
            post.responses && post.responses.some((r: any) => r.copied)
          )
          break
        case 'high_score':
          filtered = filtered.filter(post => 
            post.responses && post.responses.some((r: any) => r.score >= 80)
          )
          break
      }
    }

    // Score range filter
    if (filters.scoreRange[0] > 0 || filters.scoreRange[1] < 100) {
      filtered = filtered.filter(post => {
        if (!post.responses || post.responses.length === 0) return false
        const maxScore = Math.max(...post.responses.map((r: any) => r.score || 0))
        return maxScore >= filters.scoreRange[0] && maxScore <= filters.scoreRange[1]
      })
    }

    // Sorting
    filtered.sort((a, b) => {
      let aValue, bValue
      
      switch (filters.sortBy) {
        case 'score':
          aValue = a.score || 0
          bValue = b.score || 0
          break
        case 'response_score':
          aValue = a.responses ? Math.max(...a.responses.map((r: any) => r.score || 0)) : 0
          bValue = b.responses ? Math.max(...b.responses.map((r: any) => r.score || 0)) : 0
          break
        case 'subreddit':
          aValue = a.subreddit || ''
          bValue = b.subreddit || ''
          break
        case 'title':
          aValue = a.title || ''
          bValue = b.title || ''
          break
        default: // created_at
          aValue = new Date(a.created_at).getTime()
          bValue = new Date(b.created_at).getTime()
      }

      if (filters.sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })

    setFilteredPosts(filtered)
  }, [posts])

  const handleResponseUpdate = (responseId: number, updatedResponse: any) => {
    // Update the posts data with the new response
    mutatePosts()
  }

  const generateResponse = async (postId: number) => {
    try {
      const result = await apiClient.post(`/api/posts/${postId}/generate-response`) as any
      
      if (result?.status === 'generated') {
        alert(`✓ Response generated!\n\nScore: ${result.response.score}\nGrade: ${result.response.grade}`)
        // Refresh posts to show new response
        mutatePosts()
      } else if (result?.status === 'exists') {
        alert('ℹ️ Response already exists for this post')
      } else if (result?.status === 'failed') {
        alert(`⚠️ Failed to generate response:\n${result.message}`)
      } else if (result?.status === 'error') {
        alert(`❌ Error generating response:\n${result.message}`)
      }
    } catch (error) {
      console.error('Generate response error:', error)
      if (error instanceof APIClientError) {
        alert(`Failed to generate response: ${error.message}`)
      } else {
        alert('Error generating response. Check console for details.')
      }
    }
  }


  const scan = async () => {
    setIsScanning(true)
    setScanStatus('Starting scan...')
    
    try {
      const result = await apiClient.post('/api/ops/scan') as any
      
      if (result?.method === 'celery') {
        setScanStatus('Scan running in background...')
        alert('✓ Scan started!\n\nThe scan is running in the background.\nNew posts will appear in 30-60 seconds.\n\nRefresh the page to see results.')
        
        // Auto-refresh after 30 seconds
        setTimeout(() => {
          mutatePosts()
          mutateSummary()
          setIsScanning(false)
          setScanStatus('')
        }, 30000)
      } else if (result?.method === 'sync') {
        const posts = result.created_posts || 0
        const responses = result.created_responses || 0
        
        setScanStatus(`Found ${posts} posts, generated ${responses} responses`)
        
        if (result.error) {
          alert(`⚠️ Scan completed with errors:\n${result.error}\n\nCreated: ${posts} posts, ${responses} responses`)
        } else {
          alert(`✓ Scan completed!\n\nFound: ${posts} new posts\nGenerated: ${responses} AI responses`)
        }
        
        // Refresh immediately for sync
        setTimeout(() => {
          mutatePosts()
          mutateSummary()
          setIsScanning(false)
          setScanStatus('')
        }, 1000)
      }
    } catch (error) {
      console.error('Scan error:', error)
      setIsScanning(false)
      setScanStatus('')
      
      if (error instanceof APIClientError) {
        alert(`Failed to start scan: ${error.message}\n\nPossible issues:\n- No active configurations\n- Reddit API not configured\n- Backend service unavailable`)
      } else {
        alert('Error starting scan.\n\nPlease check:\n1. You have at least one active configuration\n2. Reddit API credentials are set\n3. Backend service is running')
      }
    }
  }

  // Safe data handling with proper null checks
  const eventsTotal: number | string = (summary as any)?.events
    ? Object.values((summary as any).events as Record<string, number>).reduce((a: number, b: any) => a + Number(b), 0)
    : '—'

  const copy = async (id: number, content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      await apiClient.post(`/api/posts/responses/${id}/copied`)
    } catch (error) {
      console.error('Copy error:', error)
    }
  }
  
  const ack = async (id: number) => {
    try {
      await apiClient.post(`/api/posts/responses/${id}/compliance`)
    } catch (error) {
      console.error('Ack error:', error)
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
    <MobileResponsiveLayout>
      {/* Authentication Error Display */}
      {authError && (
        <AuthErrorDisplay 
          error={authError}
          onLogin={() => router.push('/')}
          className="mb-4"
        />
      )}
      
      <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">Total Posts Found</div>
          <div className="text-2xl font-semibold">{(summary as any)?.posts ?? '—'}</div>
        </div>
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">AI Responses Generated</div>
          <div className="text-2xl font-semibold">{(summary as any)?.responses ?? '—'}</div>
        </div>
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500 mb-2">Scanning Status</div>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-sm font-medium">Active (Every 5 min)</span>
          </div>
          <div className="text-xs text-gray-600">
            {configs && Array.isArray(configs) && configs.length > 0 ? (
              <>
                <div className="font-medium mb-1">Monitoring:</div>
                {configs.filter((c: any) => c.is_active).map((cfg: any, idx: number) => (
                  <div key={idx} className="mb-1">
                    <div className="text-gray-700">
                      r/{Array.isArray(cfg.reddit_subreddits) ? cfg.reddit_subreddits.join(', r/') : cfg.reddit_subreddits}
                    </div>
                    <div className="text-gray-500">
                      Keywords: {Array.isArray(cfg.keywords) ? cfg.keywords.join(', ') : cfg.keywords}
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <span className="text-gray-500">No active configs</span>
            )}
          </div>
        </div>
      </div>



      {/* Search and Filter */}
      <div className="mt-8 mb-6">
        <SearchAndFilter 
          onFilterChange={handleFilterChange}
          subreddits={availableSubreddits}
          clients={(Array.isArray(clients) ? clients : []) as Array<{id: number; name: string}>}
        />
      </div>

      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Matched Posts</h2>
          <p className="text-sm text-gray-600">
            Showing {filteredPosts.length} of {(posts as any)?.length || 0} posts
          </p>
          {scanStatus && (
            <p className="text-xs text-blue-600 mt-1">
              {scanStatus}
            </p>
          )}
        </div>
        <button 
          onClick={scan} 
          disabled={isScanning}
          className="px-3 py-2 rounded-md bg-black text-white hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isScanning && (
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          {isScanning ? 'Scanning...' : 'Scan now'}
        </button>
      </div>
      
      {/* Error handling */}
      {(postsError || summaryError) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-red-600">
            Error loading data: {postsError?.message || summaryError?.message}
          </p>
        </div>
      )}
      
      {/* Posts loading state */}
      {!posts && !postsError && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading posts...</p>
        </div>
      )}
      
      {/* Posts content */}
      {filteredPosts.length === 0 && posts && Array.isArray(posts) && posts.length > 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No posts match your current filters.</p>
        </div>
      )}

      {posts && Array.isArray(posts) && posts.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No posts yet. Click "Scan now" to start monitoring.</p>
        </div>
      )}
      
      {filteredPosts.length > 0 && (
        <div className="space-y-3">
          {filteredPosts.map((p: any) => {
            const redditUrl = p?.subreddit && p?.reddit_post_id
              ? `https://www.reddit.com/r/${p.subreddit}/comments/${p.reddit_post_id}`
              : (p?.url || '#')
            const formatPostDate = (dateString: string) => {
              if (!dateString) return 'Unknown date'
              
              try {
                const date = new Date(dateString)
                // Check if date is valid
                if (isNaN(date.getTime())) {
                  return 'Unknown date'
                }
                
                return date.toLocaleString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })
              } catch (error) {
                return 'Unknown date'
              }
            }
            
            const formattedDate = formatPostDate(p.created_at)
            
            return (
              <div key={p.id} className="bg-white border rounded-xl p-4 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-gray-700">r/{p.subreddit || 'unknown'}</span>
                    <span className="text-xs text-gray-400">•</span>
                    <span className="text-xs">{formattedDate}</span>
                  </div>
                  <a
                    href={redditUrl}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="shrink-0 inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs hover:bg-gray-50"
                    aria-label="Open on Reddit"
                  >
                    Open on Reddit
                    <span aria-hidden>↗</span>
                  </a>
                </div>
                <a 
                  className="mt-2 block text-lg font-semibold text-gray-900 hover:underline"
                  href={redditUrl}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  {p.title || 'No title'}
                </a>
                <div className="text-sm text-gray-600">
                  Keywords: {p.keywords_matched || 'None'}
                </div>
                <div className="mt-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-medium">AI Responses</div>
                    {(!Array.isArray(p.responses) || p.responses.length === 0) && (
                      <button
                        onClick={() => generateResponse(p.id)}
                        className="px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                      >
                        Generate Response
                      </button>
                    )}
                  </div>
                  {Array.isArray(p.responses) && p.responses.length > 0 ? (
                    <ResponseManager 
                      responses={p.responses}
                      token={token!}
                      onResponseUpdate={handleResponseUpdate}
                    />
                  ) : (
                    <p className="text-sm text-gray-500 italic py-4">No responses generated yet</p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </MobileResponsiveLayout>
  )
}

export default function Dashboard() {
  const { token } = useAuth()

  return (
    <WebSocketProvider token={token}>
      <DashboardContent />
    </WebSocketProvider>
  )
}
