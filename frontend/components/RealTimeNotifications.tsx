import React, { useEffect, useState } from 'react'
import { useWebSocket } from './WebSocketProvider'

interface Notification {
  id: string
  type: string
  message: string
  timestamp: number
  data?: any
}

const RealTimeNotifications: React.FC = () => {
  const { lastMessage, isConnected } = useWebSocket()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [showNotifications, setShowNotifications] = useState(false)

  useEffect(() => {
    if (lastMessage) {
      const notification = createNotificationFromMessage(lastMessage)
      if (notification) {
        setNotifications(prev => [notification, ...prev.slice(0, 9)]) // Keep last 10
        
        // Auto-hide notification after 5 seconds
        setTimeout(() => {
          setNotifications(prev => prev.filter(n => n.id !== notification.id))
        }, 5000)
      }
    }
  }, [lastMessage])

  const createNotificationFromMessage = (message: any): Notification | null => {
    const id = `${Date.now()}-${Math.random()}`
    const timestamp = Date.now()

    switch (message.type) {
      case 'new_post':
        return {
          id,
          type: 'success',
          message: `New post matched in r/${message.data.subreddit}: ${message.data.title.substring(0, 50)}...`,
          timestamp,
          data: message.data
        }
      
      case 'new_response':
        return {
          id,
          type: 'info',
          message: `New AI response generated (Score: ${message.data.score})`,
          timestamp,
          data: message.data
        }
      
      case 'response_copied':
        return {
          id,
          type: 'success',
          message: 'Response copied to clipboard',
          timestamp,
          data: message.data
        }
      
      case 'scan_started':
        return {
          id,
          type: 'info',
          message: 'Reddit scan started...',
          timestamp,
          data: message.data
        }
      
      case 'scan_completed':
        return {
          id,
          type: 'success',
          message: `Scan completed: ${message.data.created_posts || 0} new posts, ${message.data.created_responses || 0} responses`,
          timestamp,
          data: message.data
        }
      
      case 'analytics_update':
        return {
          id,
          type: 'info',
          message: 'Analytics updated',
          timestamp,
          data: message.data
        }
      
      case 'system_status':
        return {
          id,
          type: message.data.status === 'error' ? 'error' : 'info',
          message: message.data.message,
          timestamp,
          data: message.data
        }
      
      default:
        return null
    }
  }

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800'
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return '✓'
      case 'error':
        return '✕'
      case 'warning':
        return '⚠'
      default:
        return 'ℹ'
    }
  }

  return (
    <div className="fixed top-4 right-4 z-50">
      {/* Connection Status */}
      <div className={`mb-2 px-3 py-1 rounded-full text-xs font-medium ${
        isConnected 
          ? 'bg-green-100 text-green-800' 
          : 'bg-red-100 text-red-800'
      }`}>
        {isConnected ? '🟢 Live' : '🔴 Disconnected'}
      </div>

      {/* Notifications Toggle */}
      {notifications.length > 0 && (
        <button
          onClick={() => setShowNotifications(!showNotifications)}
          className="mb-2 px-3 py-1 bg-gray-800 text-white rounded-full text-xs font-medium hover:bg-gray-700"
        >
          {notifications.length} notification{notifications.length !== 1 ? 's' : ''}
        </button>
      )}

      {/* Notifications List */}
      {showNotifications && (
        <div className="space-y-2 max-w-sm">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className={`p-3 rounded-lg border shadow-sm ${getNotificationColor(notification.type)}`}
            >
              <div className="flex items-start space-x-2">
                <span className="text-sm font-medium">
                  {getNotificationIcon(notification.type)}
                </span>
                <div className="flex-1">
                  <p className="text-sm">{notification.message}</p>
                  <p className="text-xs opacity-75 mt-1">
                    {new Date(notification.timestamp).toLocaleTimeString()}
                  </p>
                </div>
                <button
                  onClick={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}
                  className="text-xs opacity-50 hover:opacity-100"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Auto-showing latest notification */}
      {!showNotifications && notifications.length > 0 && (
        <div
          className={`p-3 rounded-lg border shadow-lg ${getNotificationColor(notifications[0].type)} animate-slide-in`}
          style={{
            animation: 'slideIn 0.3s ease-out'
          }}
        >
          <div className="flex items-start space-x-2">
            <span className="text-sm font-medium">
              {getNotificationIcon(notifications[0].type)}
            </span>
            <div className="flex-1">
              <p className="text-sm">{notifications[0].message}</p>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  )
}

export default RealTimeNotifications