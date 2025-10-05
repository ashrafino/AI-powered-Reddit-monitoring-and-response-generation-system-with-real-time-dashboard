import useSWR from 'swr'
import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/router'
import Layout from '../components/Layout'
import AnalyticsDashboard from '../components/AnalyticsDashboard'
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

  const { data: trends, error: trendsError } = useSWR(
    token ? `${API_BASE}/api/analytics/trends` : null, 
    fetcher,
    { 
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      errorRetryCount: 3
    }
  )

  const { data: keywordInsights, error: keywordError } = useSWR(
    token ? `${API_BASE}/api/analytics/keywords` : null, 
    fetcher,
    { 
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      errorRetryCount: 3
    }
  )
  const scan = async () => {
    try {
      const result = await apiClient.post('/api/ops/scan') as any
      
      if (result?.method === 'celery') {
        alert('✓ Scan started!\n\nThe scan is running in the background.\nNew posts will appear in 30-60 seconds.\n\nRefresh the page to see results.')
        
        // Auto-refresh after 30 seconds
        setTimeout(() => {
          mutatePosts()
          mutateSummary()
        }, 30000)
      } else if (result?.method === 'sync') {
        const posts = result.created_posts || 0
        const responses = result.created_responses || 0
        if (result.error) {
          alert(`⚠️ Scan completed with errors:\n${result.error}\n\nCreated: ${posts} posts, ${responses} responses`)
        } else {
          alert(`✓ Scan completed!\n\nFound: ${posts} new posts\nGenerated: ${responses} AI responses`)
        }
        
        // Refresh immediately for sync
        setTimeout(() => {
          mutatePosts()
          mutateSummary()
        }, 1000)
      }
    } catch (error) {
      console.error('Scan error:', error)
      if (error instanceof APIClientError) {
        alert(`Failed to start scan: ${error.message}`)
      } else {
        alert('Error starting scan. Check console for details.')
      }
    }
  }

  // Safe data handling with proper null checks
  const eventsTotal: number | string = summary?.events
    ? Object.values(summary.events as Record<string, number>).reduce((a: number, b: any) => a + Number(b), 0)
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
      
      <div className="grid gap-4 grid-cols-1 md:grid-cols-4">
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">Posts</div>
          <div className="text-2xl font-semibold">{summary?.posts ?? '—'}</div>
        </div>
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">Responses</div>
          <div className="text-2xl font-semibold">{summary?.responses ?? '—'}</div>
        </div>
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">Copy Rate</div>
          <div className="text-2xl font-semibold">{summary?.copy_rate ?? '—'}%</div>
        </div>
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">Growth</div>
          <div className="text-2xl font-semibold">
            {trends?.growth_rate ? (
              <span className={trends.growth_rate >= 0 ? 'text-green-600' : 'text-red-600'}>
                {trends.growth_rate > 0 ? '+' : ''}{trends.growth_rate}%
              </span>
            ) : '—'}
          </div>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="mt-8 mb-8">
        <div className="mb-4">
          <h2 className="text-lg font-semibold">Analytics Overview</h2>
        </div>
        
        <AnalyticsDashboard token={token!} />
      </div>

      {/* Keyword Insights */}
      {keywordInsights && keywordInsights.length > 0 && (
        <div className="mt-8 mb-8">
          <h2 className="text-lg font-semibold mb-4">Keyword Performance</h2>
          <div className="bg-white border rounded-xl p-6 shadow-sm">
            <div className="space-y-4">
              {keywordInsights.slice(0, 5).map((insight: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <span className="font-medium">{insight.keyword}</span>
                    <div className="text-sm text-gray-600">
                      {insight.matches} matches • {insight.avg_engagement} avg engagement
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      insight.category === 'high_performer' ? 'bg-green-100 text-green-800' :
                      insight.category === 'moderate_performer' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {insight.category.replace('_', ' ')}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{insight.response_rate}% response rate</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Search and Filter */}
      <div className="mt-8 mb-6">
        <SearchAndFilter 
          onFilterChange={handleFilterChange}
          subreddits={availableSubreddits}
        />
      </div>

      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Matched Posts</h2>
          <p className="text-sm text-gray-600">
            Showing {filteredPosts.length} of {posts?.length || 0} posts
          </p>
        </div>
        <button onClick={scan} className="px-3 py-2 rounded-md bg-black text-white hover:bg-gray-800 transition-colors">
          Scan now
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
            return (
              <div key={p.id} className="bg-white border rounded-xl p-4 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div className="text-sm text-gray-500">
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-gray-700">r/{p.subreddit || 'unknown'}</span>
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
                  <div className="text-sm font-medium mb-1">AI Responses</div>
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
