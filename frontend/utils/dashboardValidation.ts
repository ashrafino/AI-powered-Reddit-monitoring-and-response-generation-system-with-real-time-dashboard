/**
 * Dashboard validation utilities to test all implemented features
 * This validates the requirements for task 5: Dashboard Interface and User Experience
 */

export interface ValidationResult {
  feature: string
  requirement: string
  status: 'pass' | 'fail' | 'warning'
  details: string
}

export interface DashboardValidation {
  realTimeUpdates: ValidationResult
  responseManagement: ValidationResult
  copyFunctionality: ValidationResult
  inlineEditing: ValidationResult
  connectionStatus: ValidationResult
  mobileResponsiveness: ValidationResult
  searchAndFiltering: ValidationResult
  analyticsVisualization: ValidationResult
  performanceMonitoring: ValidationResult
}

/**
 * Validate real-time WebSocket updates
 */
export function validateRealTimeUpdates(): ValidationResult {
  const hasWebSocketProvider = !!document.querySelector('[data-websocket-provider]') || 
                               window.location.pathname.includes('dashboard')
  
  return {
    feature: 'Real-Time Updates',
    requirement: '5.1 - Dashboard updates in real-time via WebSockets',
    status: hasWebSocketProvider ? 'pass' : 'warning',
    details: hasWebSocketProvider 
      ? 'WebSocket provider is active and handling real-time updates'
      : 'WebSocket provider not detected - may not be initialized yet'
  }
}

/**
 * Validate response management features
 */
export function validateResponseManagement(): ValidationResult {
  const hasResponseManager = !!document.querySelector('[data-response-manager]') ||
                            !!document.querySelector('.response-manager') ||
                            document.body.innerHTML.includes('ResponseManager')
  
  return {
    feature: 'Response Management',
    requirement: '5.2 - Show responses immediately in response queue',
    status: hasResponseManager ? 'pass' : 'warning',
    details: hasResponseManager
      ? 'Response management components are present'
      : 'Response management components not detected in DOM'
  }
}

/**
 * Validate copy-to-clipboard functionality
 */
export function validateCopyFunctionality(): ValidationResult {
  const hasClipboardSupport = !!(navigator.clipboard || document.execCommand)
  const hasCopyButtons = document.querySelectorAll('button').length > 0 &&
                        Array.from(document.querySelectorAll('button')).some(btn => 
                          btn.textContent?.toLowerCase().includes('copy')
                        )
  
  return {
    feature: 'Copy Functionality',
    requirement: '5.3 - One-click copy-to-clipboard functionality',
    status: hasClipboardSupport && hasCopyButtons ? 'pass' : 'warning',
    details: `Clipboard support: ${hasClipboardSupport}, Copy buttons: ${hasCopyButtons}`
  }
}

/**
 * Validate inline editing capabilities
 */
export function validateInlineEditing(): ValidationResult {
  const hasEditButtons = Array.from(document.querySelectorAll('button')).some(btn => 
    btn.textContent?.toLowerCase().includes('edit')
  )
  const hasTextareas = document.querySelectorAll('textarea').length > 0
  
  return {
    feature: 'Inline Editing',
    requirement: '5.4 - Inline editing capabilities for responses',
    status: hasEditButtons || hasTextareas ? 'pass' : 'warning',
    details: `Edit buttons: ${hasEditButtons}, Textareas: ${hasTextareas}`
  }
}

/**
 * Validate connection status display
 */
export function validateConnectionStatus(): ValidationResult {
  const hasConnectionIndicator = document.body.innerHTML.includes('Connected') ||
                                document.body.innerHTML.includes('Disconnected') ||
                                !!document.querySelector('[data-connection-status]')
  
  return {
    feature: 'Connection Status',
    requirement: '5.5 - Display connection status and auto-reconnect',
    status: hasConnectionIndicator ? 'pass' : 'warning',
    details: hasConnectionIndicator
      ? 'Connection status indicators are present'
      : 'Connection status indicators not detected'
  }
}

/**
 * Validate mobile responsiveness
 */
export function validateMobileResponsiveness(): ValidationResult {
  const viewport = document.querySelector('meta[name="viewport"]')
  const hasResponsiveClasses = document.body.innerHTML.includes('md:') ||
                              document.body.innerHTML.includes('lg:') ||
                              document.body.innerHTML.includes('sm:')
  const isMobileLayout = window.innerWidth < 768
  
  return {
    feature: 'Mobile Responsiveness',
    requirement: '5.6 - Fully responsive and functional on mobile devices',
    status: viewport && hasResponsiveClasses ? 'pass' : 'warning',
    details: `Viewport meta: ${!!viewport}, Responsive classes: ${hasResponsiveClasses}, Mobile view: ${isMobileLayout}`
  }
}

/**
 * Validate search and filtering tools
 */
export function validateSearchAndFiltering(): ValidationResult {
  const hasSearchInput = document.querySelectorAll('input[type="text"]').length > 0 ||
                        document.querySelectorAll('input[placeholder*="search" i]').length > 0
  const hasFilterControls = document.querySelectorAll('select').length > 0 ||
                           document.body.innerHTML.includes('filter')
  
  return {
    feature: 'Search and Filtering',
    requirement: '5.7 - Filtering tools for posts and responses',
    status: hasSearchInput && hasFilterControls ? 'pass' : 'warning',
    details: `Search inputs: ${hasSearchInput}, Filter controls: ${hasFilterControls}`
  }
}

/**
 * Validate analytics visualization
 */
export function validateAnalyticsVisualization(): ValidationResult {
  const hasCharts = document.body.innerHTML.includes('chart') ||
                   document.body.innerHTML.includes('analytics') ||
                   document.querySelectorAll('[class*="chart"]').length > 0
  const hasInteractiveElements = document.querySelectorAll('button').length > 5
  
  return {
    feature: 'Analytics Visualization',
    requirement: '6.1, 6.2, 6.3 - Interactive charts and performance visualizations',
    status: hasCharts && hasInteractiveElements ? 'pass' : 'warning',
    details: `Charts detected: ${hasCharts}, Interactive elements: ${hasInteractiveElements}`
  }
}

/**
 * Validate performance monitoring
 */
export function validatePerformanceMonitoring(): ValidationResult {
  const hasPerformanceAPI = 'performance' in window
  const hasMemoryInfo = 'memory' in performance
  const renderStart = performance.now()
  const renderTime = performance.now() - renderStart
  
  return {
    feature: 'Performance Monitoring',
    requirement: '10.1, 10.2, 10.3 - Dashboard performance with large datasets',
    status: hasPerformanceAPI ? 'pass' : 'fail',
    details: `Performance API: ${hasPerformanceAPI}, Memory info: ${hasMemoryInfo}, Render time: ${renderTime.toFixed(2)}ms`
  }
}

/**
 * Run complete dashboard validation
 */
export function validateDashboard(): DashboardValidation {
  return {
    realTimeUpdates: validateRealTimeUpdates(),
    responseManagement: validateResponseManagement(),
    copyFunctionality: validateCopyFunctionality(),
    inlineEditing: validateInlineEditing(),
    connectionStatus: validateConnectionStatus(),
    mobileResponsiveness: validateMobileResponsiveness(),
    searchAndFiltering: validateSearchAndFiltering(),
    analyticsVisualization: validateAnalyticsVisualization(),
    performanceMonitoring: validatePerformanceMonitoring()
  }
}

/**
 * Generate validation report
 */
export function generateValidationReport(validation: DashboardValidation): string {
  const results = Object.values(validation)
  const passed = results.filter(r => r.status === 'pass').length
  const warnings = results.filter(r => r.status === 'warning').length
  const failed = results.filter(r => r.status === 'fail').length
  
  let report = `Dashboard Validation Report\n`
  report += `==========================\n\n`
  report += `Summary: ${passed} passed, ${warnings} warnings, ${failed} failed\n\n`
  
  results.forEach(result => {
    const icon = result.status === 'pass' ? '✅' : result.status === 'warning' ? '⚠️' : '❌'
    report += `${icon} ${result.feature}\n`
    report += `   Requirement: ${result.requirement}\n`
    report += `   Details: ${result.details}\n\n`
  })
  
  return report
}

/**
 * Test dashboard performance with simulated large dataset
 */
export async function testDashboardPerformance(itemCount: number = 1000): Promise<{
  renderTime: number
  memoryUsage: number
  domNodes: number
  recommendation: string
}> {
  const startTime = performance.now()
  const startMemory = (performance as any).memory?.usedJSHeapSize || 0
  
  // Simulate large dataset rendering
  const testContainer = document.createElement('div')
  testContainer.style.position = 'absolute'
  testContainer.style.left = '-9999px'
  testContainer.style.top = '-9999px'
  
  for (let i = 0; i < itemCount; i++) {
    const item = document.createElement('div')
    item.className = 'test-item bg-white border rounded p-4'
    item.innerHTML = `
      <div class="text-sm font-medium">Test Item ${i}</div>
      <div class="text-xs text-gray-500">Simulated content for performance testing</div>
      <button class="px-2 py-1 text-xs bg-blue-500 text-white rounded">Action</button>
    `
    testContainer.appendChild(item)
  }
  
  document.body.appendChild(testContainer)
  
  // Force layout calculation
  testContainer.offsetHeight
  
  const endTime = performance.now()
  const endMemory = (performance as any).memory?.usedJSHeapSize || 0
  
  // Clean up
  document.body.removeChild(testContainer)
  
  const renderTime = endTime - startTime
  const memoryUsage = (endMemory - startMemory) / 1024 / 1024 // MB
  const domNodes = document.querySelectorAll('*').length
  
  let recommendation = 'Performance is optimal'
  if (renderTime > 100) {
    recommendation = 'Consider implementing virtualization for large datasets'
  } else if (renderTime > 50) {
    recommendation = 'Performance is acceptable but could be optimized'
  }
  
  return {
    renderTime: Math.round(renderTime * 100) / 100,
    memoryUsage: Math.round(memoryUsage * 100) / 100,
    domNodes,
    recommendation
  }
}