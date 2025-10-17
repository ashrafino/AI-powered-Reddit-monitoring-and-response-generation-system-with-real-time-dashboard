import React, { useState, useEffect } from 'react'

interface FilterOptions {
  searchQuery: string
  subreddit: string
  clientId: string
  scoreRange: [number, number]
  dateRange: string
  responseStatus: string
  sortBy: string
  sortOrder: 'asc' | 'desc'
}

interface SearchAndFilterProps {
  onFilterChange: (filters: FilterOptions) => void
  subreddits?: string[]
  clients?: Array<{ id: number; name: string }>
  className?: string
}

const SearchAndFilter: React.FC<SearchAndFilterProps> = ({ 
  onFilterChange, 
  subreddits = [],
  clients = [],
  className = ''
}) => {
  const [filters, setFilters] = useState<FilterOptions>({
    searchQuery: '',
    subreddit: '',
    clientId: '',
    scoreRange: [0, 100],
    dateRange: 'all',
    responseStatus: 'all',
    sortBy: 'created_at',
    sortOrder: 'desc'
  })

  const [isExpanded, setIsExpanded] = useState(true)
  const [activeFiltersCount, setActiveFiltersCount] = useState(0)

  // Update active filters count
  useEffect(() => {
    let count = 0
    if (filters.searchQuery) count++
    if (filters.subreddit) count++
    if (filters.clientId) count++
    if (filters.scoreRange[0] > 0 || filters.scoreRange[1] < 100) count++
    if (filters.dateRange !== 'all') count++
    if (filters.responseStatus !== 'all') count++
    setActiveFiltersCount(count)
  }, [filters])

  // Notify parent of filter changes
  useEffect(() => {
    onFilterChange(filters)
  }, [filters])

  const updateFilter = (key: keyof FilterOptions, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const clearAllFilters = () => {
    setFilters({
      searchQuery: '',
      subreddit: '',
      clientId: '',
      scoreRange: [0, 100],
      dateRange: 'all',
      responseStatus: 'all',
      sortBy: 'created_at',
      sortOrder: 'desc'
    })
  }

  const dateRangeOptions = [
    { value: 'all', label: 'All Time' },
    { value: 'today', label: 'Today' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' },
    { value: 'quarter', label: 'This Quarter' }
  ]

  const responseStatusOptions = [
    { value: 'all', label: 'All Posts' },
    { value: 'with_responses', label: 'With Responses' },
    { value: 'without_responses', label: 'Without Responses' },
    { value: 'copied', label: 'Copied Responses' },
    { value: 'high_score', label: 'High Score (80+)' }
  ]

  const sortOptions = [
    { value: 'created_at', label: 'Date Created' },
    { value: 'score', label: 'Reddit Score' },
    { value: 'response_score', label: 'AI Response Score' },
    { value: 'subreddit', label: 'Subreddit' },
    { value: 'title', label: 'Title' }
  ]

  return (
    <div className={`bg-white border rounded-lg shadow-sm ${className}`}>
      {/* Search Bar and Quick Filters */}
      <div className="p-4">
        <div className="flex items-center space-x-3">
          {/* Search Input */}
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Search posts, keywords, or content..."
              value={filters.searchQuery}
              onChange={(e) => updateFilter('searchQuery', e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <div className="absolute left-3 top-2.5 text-gray-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          {/* Quick Sort */}
          <select
            value={`${filters.sortBy}-${filters.sortOrder}`}
            onChange={(e) => {
              const [sortBy, sortOrder] = e.target.value.split('-')
              updateFilter('sortBy', sortBy)
              updateFilter('sortOrder', sortOrder)
            }}
            className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {sortOptions.map(option => (
              <React.Fragment key={option.value}>
                <option value={`${option.value}-desc`}>{option.label} (Newest)</option>
                <option value={`${option.value}-asc`}>{option.label} (Oldest)</option>
              </React.Fragment>
            ))}
          </select>

          {/* Advanced Filters Toggle */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={`px-3 py-2 border rounded-lg hover:bg-gray-50 flex items-center space-x-2 ${
              activeFiltersCount > 0 ? 'bg-blue-50 border-blue-200 text-blue-700' : ''
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            <span>Filters</span>
            {activeFiltersCount > 0 && (
              <span className="bg-blue-600 text-white text-xs rounded-full px-2 py-0.5">
                {activeFiltersCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Advanced Filters */}
      {isExpanded && (
        <div className="border-t bg-gray-50 p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Client Filter */}
            {clients.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Client
                </label>
                <select
                  value={filters.clientId}
                  onChange={(e) => updateFilter('clientId', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Clients</option>
                  {clients.map(client => (
                    <option key={client.id} value={client.id}>
                      {client.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Subreddit Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subreddit
              </label>
              <select
                value={filters.subreddit}
                onChange={(e) => updateFilter('subreddit', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Subreddits</option>
                {subreddits.map(subreddit => (
                  <option key={subreddit} value={subreddit}>
                    r/{subreddit}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Range Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date Range
              </label>
              <select
                value={filters.dateRange}
                onChange={(e) => updateFilter('dateRange', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {dateRangeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Response Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Response Status
              </label>
              <select
                value={filters.responseStatus}
                onChange={(e) => updateFilter('responseStatus', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {responseStatusOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Score Range Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                AI Score Range
              </label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={filters.scoreRange[0]}
                    onChange={(e) => updateFilter('scoreRange', [parseInt(e.target.value), filters.scoreRange[1]])}
                    className="flex-1"
                  />
                  <span className="text-sm text-gray-600 w-8">{filters.scoreRange[0]}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={filters.scoreRange[1]}
                    onChange={(e) => updateFilter('scoreRange', [filters.scoreRange[0], parseInt(e.target.value)])}
                    className="flex-1"
                  />
                  <span className="text-sm text-gray-600 w-8">{filters.scoreRange[1]}</span>
                </div>
                <div className="text-xs text-gray-500 text-center">
                  {filters.scoreRange[0]} - {filters.scoreRange[1]}
                </div>
              </div>
            </div>
          </div>

          {/* Filter Actions */}
          <div className="flex items-center justify-between mt-4 pt-4 border-t">
            <div className="text-sm text-gray-600">
              {activeFiltersCount > 0 && (
                <span>{activeFiltersCount} filter{activeFiltersCount !== 1 ? 's' : ''} active</span>
              )}
            </div>
            <div className="space-x-2">
              <button
                onClick={clearAllFilters}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
              >
                Clear All
              </button>
              <button
                onClick={() => setIsExpanded(false)}
                className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SearchAndFilter