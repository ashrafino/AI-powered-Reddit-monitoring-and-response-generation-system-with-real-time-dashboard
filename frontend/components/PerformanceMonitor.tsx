import React, { useState, useEffect, useRef } from 'react'

interface PerformanceMetrics {
  renderTime: number
  memoryUsage: number
  componentCount: number
  updateFrequency: number
  lastUpdate: Date
}

interface PerformanceMonitorProps {
  enabled?: boolean
  maxDataPoints?: number
  className?: string
}

const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({ 
  enabled = false, 
  maxDataPoints = 1000,
  className = '' 
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderTime: 0,
    memoryUsage: 0,
    componentCount: 0,
    updateFrequency: 0,
    lastUpdate: new Date()
  })
  const [isVisible, setIsVisible] = useState(false)
  const [performanceHistory, setPerformanceHistory] = useState<PerformanceMetrics[]>([])
  const renderStartTime = useRef<number>(0)
  const updateCount = useRef<number>(0)
  const lastUpdateTime = useRef<number>(Date.now())

  // Performance measurement hooks
  useEffect(() => {
    if (!enabled) return

    renderStartTime.current = performance.now()
    
    return () => {
      const renderTime = performance.now() - renderStartTime.current
      updateMetrics(renderTime)
    }
  })

  const updateMetrics = (renderTime: number) => {
    const now = Date.now()
    const timeSinceLastUpdate = now - lastUpdateTime.current
    updateCount.current++
    
    const newMetrics: PerformanceMetrics = {
      renderTime: Math.round(renderTime * 100) / 100,
      memoryUsage: getMemoryUsage(),
      componentCount: getComponentCount(),
      updateFrequency: timeSinceLastUpdate > 0 ? Math.round(1000 / timeSinceLastUpdate) : 0,
      lastUpdate: new Date()
    }

    setMetrics(newMetrics)
    
    setPerformanceHistory(prev => {
      const updated = [...prev, newMetrics]
      return updated.slice(-maxDataPoints)
    })

    lastUpdateTime.current = now
  }

  const getMemoryUsage = (): number => {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      return Math.round(memory.usedJSHeapSize / 1024 / 1024 * 100) / 100 // MB
    }
    return 0
  }

  const getComponentCount = (): number => {
    // Estimate component count by counting DOM elements with React-like attributes
    const elements = document.querySelectorAll('[data-reactroot], [data-react-*], .react-*')
    return elements.length
  }

  const getAverageMetric = (key: keyof PerformanceMetrics): number => {
    if (performanceHistory.length === 0) return 0
    
    const values = performanceHistory
      .map(m => typeof m[key] === 'number' ? m[key] as number : 0)
      .filter(v => v > 0)
    
    return values.length > 0 
      ? Math.round(values.reduce((sum, val) => sum + val, 0) / values.length * 100) / 100
      : 0
  }

  const getPerformanceStatus = (): { status: string; color: string } => {
    const avgRenderTime = getAverageMetric('renderTime')
    const memoryUsage = metrics.memoryUsage
    
    if (avgRenderTime > 100 || memoryUsage > 100) {
      return { status: 'Poor', color: 'text-red-600' }
    } else if (avgRenderTime > 50 || memoryUsage > 50) {
      return { status: 'Fair', color: 'text-yellow-600' }
    } else {
      return { status: 'Good', color: 'text-green-600' }
    }
  }

  const clearHistory = () => {
    setPerformanceHistory([])
    updateCount.current = 0
  }

  const exportMetrics = () => {
    const data = {
      currentMetrics: metrics,
      history: performanceHistory,
      averages: {
        renderTime: getAverageMetric('renderTime'),
        memoryUsage: getAverageMetric('memoryUsage'),
        componentCount: getAverageMetric('componentCount'),
        updateFrequency: getAverageMetric('updateFrequency')
      },
      timestamp: new Date().toISOString()
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `performance-metrics-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (!enabled) return null

  const performanceStatus = getPerformanceStatus()

  return (
    <div className={`fixed bottom-4 right-4 z-50 ${className}`}>
      {/* Performance Indicator */}
      <div 
        className="bg-white border rounded-lg shadow-lg cursor-pointer"
        onClick={() => setIsVisible(!isVisible)}
      >
        <div className="p-3 flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${
            performanceStatus.status === 'Good' ? 'bg-green-500' :
            performanceStatus.status === 'Fair' ? 'bg-yellow-500' : 'bg-red-500'
          }`}></div>
          <div className="text-sm">
            <div className="font-medium">Performance</div>
            <div className={`text-xs ${performanceStatus.color}`}>
              {performanceStatus.status}
            </div>
          </div>
          <div className="text-xs text-gray-500">
            {metrics.renderTime}ms
          </div>
        </div>
      </div>

      {/* Detailed Metrics Panel */}
      {isVisible && (
        <div className="mt-2 bg-white border rounded-lg shadow-lg p-4 w-80">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Performance Metrics</h3>
            <div className="flex space-x-2">
              <button
                onClick={clearHistory}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Clear
              </button>
              <button
                onClick={exportMetrics}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Export
              </button>
              <button
                onClick={() => setIsVisible(false)}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {/* Current Metrics */}
            <div>
              <h4 className="text-sm font-medium mb-2">Current</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-gray-600">Render Time</div>
                  <div className="font-medium">{metrics.renderTime}ms</div>
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-gray-600">Memory</div>
                  <div className="font-medium">{metrics.memoryUsage}MB</div>
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-gray-600">Components</div>
                  <div className="font-medium">{metrics.componentCount}</div>
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-gray-600">Updates/sec</div>
                  <div className="font-medium">{metrics.updateFrequency}</div>
                </div>
              </div>
            </div>

            {/* Averages */}
            {performanceHistory.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2">
                  Averages ({performanceHistory.length} samples)
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-blue-50 p-2 rounded">
                    <div className="text-gray-600">Avg Render</div>
                    <div className="font-medium">{getAverageMetric('renderTime')}ms</div>
                  </div>
                  <div className="bg-blue-50 p-2 rounded">
                    <div className="text-gray-600">Avg Memory</div>
                    <div className="font-medium">{getAverageMetric('memoryUsage')}MB</div>
                  </div>
                  <div className="bg-blue-50 p-2 rounded">
                    <div className="text-gray-600">Avg Components</div>
                    <div className="font-medium">{getAverageMetric('componentCount')}</div>
                  </div>
                  <div className="bg-blue-50 p-2 rounded">
                    <div className="text-gray-600">Avg Updates</div>
                    <div className="font-medium">{getAverageMetric('updateFrequency')}/sec</div>
                  </div>
                </div>
              </div>
            )}

            {/* Performance Recommendations */}
            <div>
              <h4 className="text-sm font-medium mb-2">Recommendations</h4>
              <div className="text-xs text-gray-600 space-y-1">
                {metrics.renderTime > 100 && (
                  <div className="text-red-600">• Render time is high (&gt;100ms)</div>
                )}
                {metrics.memoryUsage > 100 && (
                  <div className="text-red-600">• Memory usage is high (&gt;100MB)</div>
                )}
                {metrics.updateFrequency > 10 && (
                  <div className="text-yellow-600">• High update frequency detected</div>
                )}
                {performanceStatus.status === 'Good' && (
                  <div className="text-green-600">• Performance is optimal</div>
                )}
              </div>
            </div>

            {/* Mini Chart */}
            {performanceHistory.length > 1 && (
              <div>
                <h4 className="text-sm font-medium mb-2">Render Time Trend</h4>
                <div className="h-16 bg-gray-50 rounded p-2">
                  <div className="flex items-end justify-between h-full space-x-1">
                    {performanceHistory.slice(-20).map((metric, index) => {
                      const maxTime = Math.max(...performanceHistory.map(m => m.renderTime))
                      const height = maxTime > 0 ? (metric.renderTime / maxTime) * 100 : 0
                      
                      return (
                        <div
                          key={index}
                          className="flex-1 bg-blue-500 rounded-t"
                          style={{ height: `${height}%`, minHeight: '2px' }}
                          title={`${metric.renderTime}ms`}
                        ></div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="mt-3 pt-3 border-t text-xs text-gray-500">
            Last update: {metrics.lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  )
}

export default PerformanceMonitor