import React, { createContext, useContext, useEffect, useState, useRef } from 'react'
import { API_BASE } from '../utils/apiBase'

interface WebSocketContextType {
  isConnected: boolean
  lastMessage: any
  sendMessage: (message: any) => void
  connectionStats: any
  monitoringStatus: any
  connectionHealth: any
  reconnectAttempts: number
  lastPingTime: number | null
}

const WebSocketContext = createContext<WebSocketContextType>({
  isConnected: false,
  lastMessage: null,
  sendMessage: () => {},
  connectionStats: null,
  monitoringStatus: null,
  connectionHealth: null,
  reconnectAttempts: 0,
  lastPingTime: null
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
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5
  const pingTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = () => {
    if (!token || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    try {
      const wsUrl = `${API_BASE.replace('http', 'ws')}/api/ws?token=${encodeURIComponent(token)}`
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        reconnectAttempts.current = 0
        
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
              console.log('WebSocket connection confirmed:', message)
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
              console.log('System status update:', message.data)
              break
            case 'scan_started':
              console.log('Reddit scan started')
              break
            case 'scan_completed':
              console.log('Reddit scan completed:', message.data)
              break
            default:
              // Handle other message types (new_post, new_response, etc.)
              break
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        wsRef.current = null
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, delay)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
      wsRef.current = ws
    } catch (error) {
      console.error('Error creating WebSocket connection:', error)
    }
  }

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      
      // Track ping times for latency calculation
      if (message.type === 'ping') {
        setLastPingTime(Date.now())
      }
    } else {
      console.warn('WebSocket not connected, cannot send message:', message)
    }
  }

  useEffect(() => {
    if (token) {
      connect()
    }

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
        console.warn('WebSocket ping timeout detected')
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
      lastPingTime
    }}>
      {children}
    </WebSocketContext.Provider>
  )
}