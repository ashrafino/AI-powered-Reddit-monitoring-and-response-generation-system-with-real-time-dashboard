import React from 'react'

interface AnalyticsChartsProps {
  data: any
}

const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-2 text-gray-600">Loading analytics...</p>
      </div>
    )
  }

  const { daily_activity = [], top_keywords = [], top_subreddits = [] } = data

  return (
    <div className="space-y-6">
      {/* Daily Activity Chart */}
      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Daily Activity (Last 30 Days)</h3>
        {daily_activity.length > 0 ? (
          <div className="space-y-2">
            {daily_activity.slice(-7).map((day: any, index: number) => (
              <div key={day.date} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{day.date}</span>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <span className="text-sm">{day.posts} posts</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm">{day.responses} responses</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No activity data available</p>
        )}
      </div>

      {/* Top Keywords */}
      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Top Performing Keywords</h3>
        {top_keywords.length > 0 ? (
          <div className="space-y-3">
            {top_keywords.map((item: any, index: number) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm font-medium">{item.keyword}</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">{item.count} matches</span>
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full" 
                      style={{ width: `${Math.min(100, (item.count / Math.max(...top_keywords.map((k: any) => k.count))) * 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No keyword data available</p>
        )}
      </div>

      {/* Top Subreddits */}
      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Top Subreddits</h3>
        {top_subreddits.length > 0 ? (
          <div className="space-y-3">
            {top_subreddits.map((item: any, index: number) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm font-medium">r/{item.subreddit}</span>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-600">{item.count} posts</span>
                  <span className="text-sm text-gray-600">Avg: {item.avg_score}</span>
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full" 
                      style={{ width: `${Math.min(100, (item.count / Math.max(...top_subreddits.map((s: any) => s.count))) * 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No subreddit data available</p>
        )}
      </div>
    </div>
  )
}

export default AnalyticsCharts