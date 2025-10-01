import React, { useState, useEffect } from 'react'
import { useWebSocket } from './WebSocketProvider'

interface AnalyticsChartsProps {
  data: any
  className?: string
}

interface ChartDataPoint {
  date: string
  posts: number
  responses: number
  copy_rate?: number
}

const EnhancedAnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ data, className = '' }) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d')
  const [selectedMetric, setSelectedMetric] = useState('posts')
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null)
  const { lastMessage } = useWebSocket()

  // Update chart data when analytics data changes
  useEffect(() => {
    if (data?.daily_activity) {
      setChartData(data.daily_activity)
    }
  }, [data])

  // Handle real-time analytics updates
  useEffect(() => {
    if (lastMessage?.type === 'analytics_update') {
      setChartData(prev => {
        const newData = [...prev]
        const today = new Date().toISOString().split('T')[0]
        const todayIndex = newData.findIndex(d => d.date === today)
        
        if (todayIndex >= 0) {
          newData[todayIndex] = { ...newData[todayIndex], ...lastMessage.data }
        } else {
          newData.push({ date: today, ...lastMessage.data })
        }
        
        return newData.slice(-30) // Keep last 30 days
      })
    }
  }, [lastMessage])

  if (!data) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-2 text-gray-600">Loading analytics...</p>
      </div>
    )
  }

  const { daily_activity = [], top_keywords = [], top_subreddits = [] } = data

  const timeRangeOptions = [
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
    { value: '90d', label: '90 Days' }
  ]

  const metricOptions = [
    { value: 'posts', label: 'Posts', color: 'blue' },
    { value: 'responses', label: 'Responses', color: 'green' },
    { value: 'copy_rate', label: 'Copy Rate', color: 'purple' }
  ]

  const getFilteredData = () => {
    const days = parseInt(selectedTimeRange.replace('d', ''))
    return chartData.slice(-days)
  }

  const getMaxValue = (data: ChartDataPoint[], metric: string) => {
    return Math.max(...data.map(d => (d as any)[metric] || 0))
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const getMetricColor = (metric: string) => {
    const colors = {
      posts: 'bg-blue-500',
      responses: 'bg-green-500',
      copy_rate: 'bg-purple-500'
    }
    return colors[metric as keyof typeof colors] || 'bg-gray-500'
  }

  const filteredData = getFilteredData()
  const maxValue = getMaxValue(filteredData, selectedMetric)

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Interactive Activity Chart */}
      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">Activity Trends</h3>
          <div className="flex items-center space-x-4">
            {/* Metric Selector */}
            <div className="flex items-center space-x-2">
              {metricOptions.map(option => (
                <button
                  key={option.value}
                  onClick={() => setSelectedMetric(option.value)}
                  className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                    selectedMetric === option.value
                      ? 'bg-blue-50 border-blue-200 text-blue-700'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-1">
                    <div className={`w-2 h-2 rounded-full ${getMetricColor(option.value)}`}></div>
                    <span>{option.label}</span>
                  </div>
                </button>
              ))}
            </div>
            
            {/* Time Range Selector */}
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              className="px-3 py-1 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {timeRangeOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {filteredData.length > 0 ? (
          <div className="space-y-4">
            {/* Chart */}
            <div className="relative h-64 bg-gray-50 rounded-lg p-4">
              <div className="flex items-end justify-between h-full space-x-1">
                {filteredData.map((day, index) => {
                  const value = (day as any)[selectedMetric] || 0
                  const height = maxValue > 0 ? (value / maxValue) * 100 : 0
                  
                  return (
                    <div
                      key={day.date}
                      className="flex-1 flex flex-col items-center cursor-pointer"
                      onMouseEnter={() => setHoveredPoint(index)}
                      onMouseLeave={() => setHoveredPoint(null)}
                    >
                      <div className="relative flex-1 flex items-end w-full">
                        <div
                          className={`w-full ${getMetricColor(selectedMetric)} rounded-t transition-all duration-200 ${
                            hoveredPoint === index ? 'opacity-80' : 'opacity-60'
                          }`}
                          style={{ height: `${height}%`, minHeight: value > 0 ? '2px' : '0' }}
                        ></div>
                        
                        {/* Tooltip */}
                        {hoveredPoint === index && (
                          <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-black text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                            <div>{formatDate(day.date)}</div>
                            <div className="font-semibold">
                              {selectedMetric === 'copy_rate' ? `${value}%` : value}
                            </div>
                            <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-black"></div>
                          </div>
                        )}
                      </div>
                      
                      <div className="text-xs text-gray-500 mt-2 transform -rotate-45 origin-center">
                        {formatDate(day.date)}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Chart Legend */}
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${getMetricColor(selectedMetric)}`}></div>
                <span className="capitalize">{selectedMetric.replace('_', ' ')}</span>
              </div>
              <div>
                Max: {selectedMetric === 'copy_rate' ? `${maxValue}%` : maxValue}
              </div>
              <div>
                Avg: {selectedMetric === 'copy_rate' 
                  ? `${Math.round(filteredData.reduce((sum, d) => sum + ((d as any)[selectedMetric] || 0), 0) / filteredData.length)}%`
                  : Math.round(filteredData.reduce((sum, d) => sum + ((d as any)[selectedMetric] || 0), 0) / filteredData.length)
                }
              </div>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No activity data available</p>
        )}
      </div>

      {/* Enhanced Keywords Performance */}
      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Keyword Performance</h3>
          <div className="text-sm text-gray-500">
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>
        
        {top_keywords.length > 0 ? (
          <div className="space-y-4">
            {top_keywords.map((item: any, index: number) => {
              const maxCount = Math.max(...top_keywords.map((k: any) => k.count))
              const percentage = maxCount > 0 ? (item.count / maxCount) * 100 : 0
              
              return (
                <div key={index} className="group hover:bg-gray-50 p-3 rounded-lg transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <span className="text-sm font-medium">{item.keyword}</span>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        item.effectiveness === 'high' ? 'bg-green-100 text-green-800' :
                        item.effectiveness === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {item.effectiveness || 'unknown'}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>{item.count} matches</span>
                      <span>{item.avg_score || 0} avg score</span>
                      <span>{item.response_rate || 0}% response rate</span>
                    </div>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300 group-hover:bg-blue-600" 
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                  
                  {item.trend && (
                    <div className="mt-2 text-xs text-gray-500">
                      Trend: <span className={item.trend.direction === 'up' ? 'text-green-600' : 'text-red-600'}>
                        {item.trend.direction === 'up' ? '↗' : '↘'} {item.trend.percentage}%
                      </span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No keyword data available</p>
        )}
      </div>

      {/* Enhanced Subreddits Performance */}
      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Subreddit Performance</h3>
        {top_subreddits.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {top_subreddits.map((item: any, index: number) => {
              const maxCount = Math.max(...top_subreddits.map((s: any) => s.count))
              const percentage = maxCount > 0 ? (item.count / maxCount) * 100 : 0
              
              return (
                <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">r/{item.subreddit}</h4>
                    <a
                      href={`https://reddit.com/r/${item.subreddit}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Visit ↗
                    </a>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Posts</span>
                      <span className="font-medium">{item.count}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Avg Score</span>
                      <span className="font-medium">{item.avg_score}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Response Rate</span>
                      <span className="font-medium">{item.response_rate || 0}%</span>
                    </div>
                    
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all duration-300" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No subreddit data available</p>
        )}
      </div>
    </div>
  )
}

export default EnhancedAnalyticsCharts