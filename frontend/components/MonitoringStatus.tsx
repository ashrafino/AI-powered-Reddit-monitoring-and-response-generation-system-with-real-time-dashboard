import React, { useEffect, useState } from 'react'
import { useWebSocket } from './WebSocketProvider'

interface MonitoringStatusProps {
  className?: string
}

const MonitoringStatus: React.FC<MonitoringStatusProps> = ({ className = '' }) => {
  const { 
    isConnected, 
    monitoringStatus, 
    connectionHealth, 
    reconnectAttempts,
    lastPingTime 
  } = useWebSocket()
  
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  useEffect(() => {
    if (monitoringStatus || connectionHealth) {
      setLastUpdate(new Date())
    }
  }, [monitoringStatus, connectionHealth])

  const getConnectionStatusColor = () => {
    if (!isConnected) return 'text-red-500'
    if (connectionHealth?.ping_timeout) return 'text-yellow-500'
    if (reconnectAttempts > 0) return 'text-yellow-500'
    return 'text-green-500'
  }

  const getConnectionStatusText = () => {
    if (!isConnected) return 'Disconnected'
    if (connectionHealth?.ping_timeout) return 'Connection Issues'
    if (reconnectAttempts > 0) return 'Reconnecting'
    return 'Connected'
  }

  const getSystemHealthColor = () => {
    if (!monitoringStatus) return 'text-gray-500'
    
    switch (monitoringStatus.status) {
      case 'excellent': return 'text-green-500'
      case 'good': return 'text-green-400'
      case 'fair': return 'text-yellow-500'
      case 'poor': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const formatUptime = (seconds: number) => {
    if (!seconds) return 'Unknown'
    
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  const formatLatency = (ms: number) => {
    if (ms < 50) return { text: `${ms}ms`, color: 'text-green-500' }
    if (ms < 100) return { text: `${ms}ms`, color: 'text-yellow-500' }
    return { text: `${ms}ms`, color: 'text-red-500' }
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
        {lastUpdate && (
          <span className="text-sm text-gray-500">
            Updated {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Connection Status */}
        <div className="flex flex-col">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm font-medium text-gray-700">Connection</span>
          </div>
          <span className={`text-sm ${getConnectionStatusColor()}`}>
            {getConnectionStatusText()}
          </span>
          {connectionHealth?.latency_ms && (
            <span className={`text-xs ${formatLatency(connectionHealth.latency_ms).color}`}>
              {formatLatency(connectionHealth.latency_ms).text}
            </span>
          )}
        </div>

        {/* System Health */}
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-700">System Health</span>
          <span className={`text-sm ${getSystemHealthColor()}`}>
            {monitoringStatus?.status ? 
              monitoringStatus.status.charAt(0).toUpperCase() + monitoringStatus.status.slice(1) : 
              'Unknown'
            }
          </span>
          {monitoringStatus?.health_percentage && (
            <span className="text-xs text-gray-500">
              {monitoringStatus.health_percentage.toFixed(1)}%
            </span>
          )}
        </div>

        {/* Active Connections */}
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-700">Connections</span>
          <span className="text-sm text-gray-900">
            {monitoringStatus?.active_connections || 0}
          </span>
          <span className="text-xs text-gray-500">
            {monitoringStatus?.clients_connected || 0} clients
          </span>
        </div>

        {/* Uptime */}
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-700">Uptime</span>
          <span className="text-sm text-gray-900">
            {monitoringStatus?.uptime_seconds ? 
              formatUptime(monitoringStatus.uptime_seconds) : 
              'Unknown'
            }
          </span>
          {monitoringStatus?.redis_connected !== undefined && (
            <span className={`text-xs ${monitoringStatus.redis_connected ? 'text-green-500' : 'text-red-500'}`}>
              Redis {monitoringStatus.redis_connected ? 'Connected' : 'Disconnected'}
            </span>
          )}
        </div>
      </div>

      {/* Additional Details */}
      {(connectionHealth || monitoringStatus) && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-gray-600">
            {connectionHealth?.connection_uptime && (
              <div>
                <span className="font-medium">Session: </span>
                {formatUptime(connectionHealth.connection_uptime)}
              </div>
            )}
            {connectionHealth?.messages_sent && (
              <div>
                <span className="font-medium">Messages: </span>
                {connectionHealth.messages_sent} sent, {connectionHealth.messages_received || 0} received
              </div>
            )}
            {lastPingTime && (
              <div>
                <span className="font-medium">Last Ping: </span>
                {Math.floor((Date.now() - lastPingTime) / 1000)}s ago
              </div>
            )}
            {reconnectAttempts > 0 && (
              <div>
                <span className="font-medium text-yellow-600">Reconnect Attempts: </span>
                {reconnectAttempts}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Connection Issues Warning */}
      {(!isConnected || connectionHealth?.ping_timeout) && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Connection Issue Detected
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                {!isConnected ? 
                  'Real-time updates are currently unavailable. The system will attempt to reconnect automatically.' :
                  'Connection latency is high. Some real-time updates may be delayed.'
                }
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MonitoringStatus