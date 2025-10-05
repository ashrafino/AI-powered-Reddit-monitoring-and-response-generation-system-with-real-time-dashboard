import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react'
import { API_BASE, AUTH_ERROR_CODES } from '../utils/apiBase'

// WebSocket close codes for authentication errors
const WS_AUTH_ERROR_CODES = {
  4001: 'Invalid or expired token',
  4002: 'User not found',
  4003: 'User account inactive', 
  4004: 'Client not found',
  4005: 'Internal server error'
} as const

interface WebSocketContextType {
  isConnected: boolean
  lastMessage: any
  sendMessage: (message: any) => void
  connectionStats: any
  monitoringStatus: any
  connectionHealth: any
  reconnectAttempts: number
  lastPingTime: number | null
  connectionError: string | null
  isReconnecting: boolean
}

const WebSocketContext = createContext<WebSocketContextType>({
  isConnected: false,
  lastMessage: null,
  sendMessage: () => {},
  connectionStats: null,
  monitoringStatus: null,
  connectionHealth: null,
  reconnectAttempts: 0,
  lastPingTime: null,
  connectionError: null,
  isReconnecting: false
})

export const useWebSocket = () => useContext(WebSocketContext)

interface WebSocketProviderProps {
  children: React.ReactNode
  token: string | null
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children, token }) => {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any>(null)
  const [connectionStats, setConnectionStats] = useState<any>(null)
  const [monitoringStatus, setMonitoringStatus] = useState<any>(null)
  const [connectionHealth, setConnectionHealth] = useState<any>(null)
  const [lastPingTime, setLastPingTime] = useState<number | null>(null)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const [isReconnecting, setIsReconnecting] = useState(false)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5
  const pingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const connectionAttemptRef = useRef(false)

  const connect = useCallback(() => {
    // WebSocket is optional - skip if not available
    if (!token || connectionAttemptRef.current || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    // Validate token format before attempting connection
    if (!isValidTokenFormat(token)) {
      // Silently fail - WebSocket is optional
      return
    }

    connectionAttemptRef.current = true
    setConnectionError(null)
    setIsReconnecting(reconnectAttempts.current > 0)

    try {
      const wsUrl = `${API_BASE.replace('http', 'ws')}/api/ws?token=${encodeURIComponent(token)}`
      // Silently attempt connection - no console logs
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        // WebSocket connected - silently
        setIsConnected(true)
        setIsReconnecting(false)
        setConnectionError(null)
        reconnectAttempts.current = 0
        connectionAttemptRef.current = false
        
        // Send initial ping and request monitoring status
        ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }))
        ws.send(JSON.stringify({ type: 'get_monitoring_status' }))
        ws.send(JSON.stringify({ type: 'health_check' }))
        
        setLastPingTime(Date.now())
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          setLastMessage(message)
          
          // Handle specific message types
          switch (message.type) {
            case 'stats':
              setConnectionStats(message.data)
              break
            case 'monitoring_status':
              setMonitoringStatus(message.data)
              break
            case 'health_response':
              setConnectionHealth(message.data)
              break
            case 'ping':
              // Respond to server ping with pong
              ws.send(JSON.stringify({ 
                type: 'pong', 
                timestamp: message.timestamp 
              }))
              break
            case 'pong':
              // Handle pong response - calculate latency
              if (message.timestamp && lastPingTime) {
                const latency = Date.now() - message.timestamp
                setConnectionHealth(prev => ({
                  ...prev,
                  latency_ms: latency,
                  last_pong: Date.now()
                }))
              }
              break
            case 'connection_confirmed':
              setConnectionHealth(prev => ({
                ...prev,
                server_status: message.status,
                connection_id: message.connection_id
              }))
              break
            case 'monitoring_status_update':
              setMonitoringStatus(message.data)
              break
            case 'connection_health_update':
              setConnectionHealth(prev => ({
                ...prev,
                server_health: message.data
              }))
              break
            case 'system_status':
            case 'scan_started':
            case 'scan_completed':
              // Silently handle these events
              break
            default:
              // Handle other message types (new_post, new_response, etc.)
              break
          }
        } catch (error) {
          // Silently ignore parsing errors
        }
      }
      
      ws.onclose = (event) => {
        // WebSocket disconnected - handle silently
        setIsConnected(false)
        setIsReconnecting(false)
        connectionAttemptRef.current = false
        wsRef.current = null
        
        // Don't reconnect - WebSocket is optional
        // The app works fine without it
      }
      
      ws.onerror = (error) => {
        // Silently handle WebSocket errors - it's optional
        connectionAttemptRef.current = false
      }
      
      wsRef.current = ws
    } catch (error) {
      // Silently handle connection errors - WebSocket is optional
      connectionAttemptRef.current = false
      setConnectionError('Failed to create WebSocket connection')
    }
  }, [token])

  // Helper function to validate token format
  const isValidTokenFormat = (token: string): boolean => {
    if (!token) return false
    
    try {
      const parts = token.split('.')
      if (parts.length !== 3) return false
      
      // Try to decode the payload to check if it's valid JWT
      const payload = JSON.parse(atob(parts[1]))
      return payload && typeof payload === 'object'
    } catch (error) {
      return false
    }
  }

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      
      // Track ping times for latency calculation
      if (message.type === 'ping') {
        setLastPingTime(Date.now())
      }
    }
    // Silently ignore if not connected
  }

  useEffect(() => {
    // WebSocket disabled - backend doesn't support it yet
    // Uncomment below when backend WebSocket is implemented:
    // if (token) {
    //   connect()
    // }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting')
      }
    }
  }, [token])

  // Periodic ping to keep connection alive and monitor health
  useEffect(() => {
    if (isConnected) {
      const pingInterval = setInterval(() => {
        sendMessage({ type: 'ping', timestamp: Date.now() })
      }, 30000) // Ping every 30 seconds

      // Request monitoring status updates periodically
      const statusInterval = setInterval(() => {
        sendMessage({ type: 'get_monitoring_status' })
      }, 60000) // Every minute

      return () => {
        clearInterval(pingInterval)
        clearInterval(statusInterval)
      }
    }
  }, [isConnected])

  // Ping timeout detection
  useEffect(() => {
    if (lastPingTime && isConnected) {
      // Clear existing timeout
      if (pingTimeoutRef.current) {
        clearTimeout(pingTimeoutRef.current)
      }
      
      // Set new timeout - if no pong received in 10 seconds, mark as unhealthy
      pingTimeoutRef.current = setTimeout(() => {
        setConnectionHealth(prev => ({
          ...prev,
          ping_timeout: true,
          last_timeout: Date.now()
        }))
        // Silently handle ping timeout
      }, 10000)
    }
    
    return () => {
      if (pingTimeoutRef.current) {
        clearTimeout(pingTimeoutRef.current)
      }
    }
  }, [lastPingTime, isConnected])

  return (
    <WebSocketContext.Provider value={{
      isConnected,
      lastMessage,
      sendMessage,
      connectionStats,
      monitoringStatus,
      connectionHealth,
      reconnectAttempts: reconnectAttempts.current,
      lastPingTime,
      connectionError,
      isReconnecting
    }}>
      {children}
    </WebSocketContext.Provider>
  )
}