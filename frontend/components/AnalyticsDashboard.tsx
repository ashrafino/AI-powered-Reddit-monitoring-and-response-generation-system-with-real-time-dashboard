import React, { useState, useEffect } from 'react'
import { useWebSocket } from './WebSocketProvider'
import { API_BASE } from '../utils/apiBase'

interface AnalyticsDashboardProps {
  token: string
  className?: string
}

interface DateRange {
  start: string
  end: string
  label: string
}

interface AnalyticsData {
  overview: {
    total_posts: number
    total_responses: number
    avg_response_score: number
    copy_rate: number
    growth_rate: number
  }
  trends: {
    daily_posts: Array<{ date: string; count: number }>
    daily_responses: Array<{ date: string; count: number }>
    daily_copy_rate: Array<{ date: string; rate: number }>
  }
  performance: {
    top_keywords: Array<{ keyword: string; matches: number; avg_score: number; effectiveness: string }>
    top_subreddits: Array<{ subreddit: string; posts: number; avg_score: number; response_rate: number }>
    quality_distribution: Array<{ grade: string; count: number; percentage: number }>
  }
  realtime: {
    active_monitoring: boolean
    last_scan: string
    posts_today: number
    responses_today: number
  }
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ token, className = '' }) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [selectedDateRange, setSelectedDateRange] = useState<DateRange>({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
    label: '7 Days'
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const { lastMessage, isConnected } = useWebSocket()

  const dateRangePresets = [
    {
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0],
      label: '7 Days'
    },
    {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0],
      label: '30 Days'
    },
    {
      start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0],
      label: '90 Days'
    }
  ]

  // Fetch analytics data
  const fetchAnalytics = async (dateRange: DateRange) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch(
        `${API_BASE}/api/analytics/dashboard?start_date=${dateRange.start}&end_date=${dateRange.end}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setAnalyticsData(data)
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Error fetching analytics:', error)
      setError('Failed to load analytics data')
    } finally {
      setIsLoading(false)
    }
  }

  // Initial load and date range changes
  useEffect(() => {
    fetchAnalytics(selectedDateRange)
  }, [selectedDateRange, token])

  // Handle real-time updates
  useEffect(() => {
    if (lastMessage?.type === 'analytics_update' && analyticsData) {
      setAnalyticsData(prev => {
        if (!prev) return prev
        
        return {
          ...prev,
          overview: {
            ...prev.overview,
            ...lastMessage.data.overview
          },
          realtime: {
            ...prev.realtime,
            ...lastMessage.data.realtime,
            posts_today: lastMessage.data.posts_today || prev.realtime.posts_today,
            responses_today: lastMessage.data.responses_today || prev.realtime.responses_today
          }
        }
      })
      setLastUpdated(new Date())
    }
  }, [lastMessage, analyticsData])

  const handleDateRangeChange = (range: DateRange) => {
    setSelectedDateRange(range)
  }

  const handleCustomDateRange = (start: string, end: string) => {
    setSelectedDateRange({
      start,
      end,
      label: 'Custom Range'
    })
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  const formatPercentage = (num: number) => {
    return `${num.toFixed(1)}%`
  }

  const getGrowthColor = (rate: number) => {
    if (rate > 0) return 'text-green-600'
    if (rate < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  const getEffectivenessColor = (effectiveness: string) => {
    switch (effectiveness.toLowerCase()) {
      case 'high': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <div className={`bg-white border rounded-xl p-6 shadow-sm ${className}`}>
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white border rounded-xl p-6 shadow-sm ${className}`}>
        <div className="text-center py-8">
          <p className="text-red-600">{error}</p>
          <button 
            onClick={() => fetchAnalytics(selectedDateRange)}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!analyticsData) {
    return (
      <div className={`bg-white border rounded-xl p-6 shadow-sm ${className}`}>
        <p className="text-center text-gray-500 py-8">No analytics data available</p>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with Date Range Selector */}
      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h2 className="text-xl font-semibold">Analytics Dashboard</h2>
            <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span>{isConnected ? 'Live Updates' : 'Disconnected'}</span>
              </div>
              <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
            </div>
          </div>
          
          <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-4">
            {/* Date Range Presets */}
            <div className="flex space-x-2">
              {dateRangePresets.map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => handleDateRangeChange(preset)}
                  className={`px-3 py-1 text-sm rounded border transition-colors ${
                    selectedDateRange.label === preset.label
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            
            {/* Custom Date Range */}
            <div className="flex space-x-2">
              <input
                type="date"
                value={selectedDateRange.start}
                onChange={(e) => handleCustomDateRange(e.target.value, selectedDateRange.end)}
                className="px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <input
                type="date"
                value={selectedDateRange.end}
                onChange={(e) => handleCustomDateRange(selectedDateRange.start, e.target.value)}
                className="px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">Total Posts</div>
          <div className="text-2xl font-semibold">{formatNumber(analyticsData.overview.total_posts)}</div>
          <div className="text-xs text-gray-400 mt-1">
            Today: {analyticsData.realtime.posts_today}
          </div>
        </div>
        
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">Total Responses</div>
          <div className="text-2xl font-semibold">{formatNumber(analyticsData.overview.total_responses)}</div>
          <div className="text-xs text-gray-400 mt-1">
            Today: {analyticsData.realtime.responses_today}
          </div>
        </div>
        
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">Avg Response Score</div>
          <div className="text-2xl font-semibold">{analyticsData.overview.avg_response_score.toFixed(1)}</div>
          <div className="text-xs text-gray-400 mt-1">Out of 100</div>
        </div>
        
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">Copy Rate</div>
          <div className="text-2xl font-semibold">{formatPercentage(analyticsData.overview.copy_rate)}</div>
          <div className="text-xs text-gray-400 mt-1">Responses copied</div>
        </div>
        
        <div className="bg-white border rounded-xl p-4 shadow-sm">
          <div className="text-sm text-gray-500">Growth Rate</div>
          <div className={`text-2xl font-semibold ${getGrowthColor(analyticsData.overview.growth_rate)}`}>
            {analyticsData.overview.growth_rate > 0 ? '+' : ''}{formatPercentage(analyticsData.overview.growth_rate)}
          </div>
          <div className="text-xs text-gray-400 mt-1">vs previous period</div>
        </div>
      </div>

      {/* Trends Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Posts Trend */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Posts Trend</h3>
          <div className="space-y-2">
            {analyticsData.trends.daily_posts.slice(-7).map((day, index) => {
              const maxCount = Math.max(...analyticsData.trends.daily_posts.map(d => d.count))
              const percentage = maxCount > 0 ? (day.count / maxCount) * 100 : 0
              
              return (
                <div key={day.date} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium w-8 text-right">{day.count}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Responses Trend */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Responses Trend</h3>
          <div className="space-y-2">
            {analyticsData.trends.daily_responses.slice(-7).map((day, index) => {
              const maxCount = Math.max(...analyticsData.trends.daily_responses.map(d => d.count))
              const percentage = maxCount > 0 ? (day.count / maxCount) * 100 : 0
              
              return (
                <div key={day.date} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all duration-300" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium w-8 text-right">{day.count}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Copy Rate Trend */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Copy Rate Trend</h3>
          <div className="space-y-2">
            {analyticsData.trends.daily_copy_rate.slice(-7).map((day, index) => {
              const maxRate = Math.max(...analyticsData.trends.daily_copy_rate.map(d => d.rate))
              const percentage = maxRate > 0 ? (day.rate / maxRate) * 100 : 0
              
              return (
                <div key={day.date} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full transition-all duration-300" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium w-12 text-right">{formatPercentage(day.rate)}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Performance Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Keywords */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Top Keywords</h3>
          <div className="space-y-3">
            {analyticsData.performance.top_keywords.map((keyword, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <span className="font-medium">{keyword.keyword}</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${getEffectivenessColor(keyword.effectiveness)}`}>
                    {keyword.effectiveness}
                  </span>
                </div>
                <div className="text-right text-sm text-gray-600">
                  <div>{keyword.matches} matches</div>
                  <div>Avg: {keyword.avg_score.toFixed(1)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Subreddits */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Top Subreddits</h3>
          <div className="space-y-3">
            {analyticsData.performance.top_subreddits.map((subreddit, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium">r/{subreddit.subreddit}</div>
                  <div className="text-sm text-gray-600">{subreddit.posts} posts</div>
                </div>
                <div className="text-right text-sm text-gray-600">
                  <div>Avg: {subreddit.avg_score.toFixed(1)}</div>
                  <div>{formatPercentage(subreddit.response_rate)} response rate</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quality Distribution */}
      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Response Quality Distribution</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {analyticsData.performance.quality_distribution.map((grade, index) => (
            <div key={index} className="text-center">
              <div className="text-2xl font-bold text-gray-800">{grade.grade}</div>
              <div className="text-sm text-gray-600">{grade.count} responses</div>
              <div className="text-xs text-gray-500">{formatPercentage(grade.percentage)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default AnalyticsDashboard