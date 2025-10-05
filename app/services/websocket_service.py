from typing import Dict, List, Set, Optional
import json
import asyncio
import logging
import time
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionHealthMonitor:
    """Monitors WebSocket connection health and handles reconnection"""
    
    def __init__(self):
        self.connection_health: Dict[WebSocket, Dict] = {}
        self.ping_interval = 30  # seconds
        self.ping_timeout = 10   # seconds
        self.max_missed_pings = 3
        
    async def start_health_monitoring(self, websocket: WebSocket):
        """Start health monitoring for a connection"""
        self.connection_health[websocket] = {
            'last_ping': time.time(),
            'last_pong': time.time(),
            'missed_pings': 0,
            'is_healthy': True
        }
        
        # Start ping task
        asyncio.create_task(self._ping_connection(websocket))
    
    async def _ping_connection(self, websocket: WebSocket):
        """Send periodic pings to check connection health"""
        try:
            while websocket in self.connection_health:
                await asyncio.sleep(self.ping_interval)
                
                if websocket not in self.connection_health:
                    break
                
                health = self.connection_health[websocket]
                current_time = time.time()
                
                # Check if previous ping was answered
                if current_time - health['last_pong'] > self.ping_timeout:
                    health['missed_pings'] += 1
                    logger.warning(f"Missed ping from WebSocket connection (count: {health['missed_pings']})")
                    
                    if health['missed_pings'] >= self.max_missed_pings:
                        health['is_healthy'] = False
                        logger.error("WebSocket connection marked as unhealthy due to missed pings")
                        break
                else:
                    health['missed_pings'] = 0
                    health['is_healthy'] = True
                
                # Send ping
                try:
                    await websocket.send_json({
                        'type': 'ping',
                        'timestamp': current_time
                    })
                    health['last_ping'] = current_time
                except Exception as e:
                    logger.error(f"Failed to send ping: {e}")
                    health['is_healthy'] = False
                    break
                    
        except Exception as e:
            logger.error(f"Error in ping monitoring: {e}")
    
    def handle_pong(self, websocket: WebSocket, timestamp: Optional[float] = None):
        """Handle pong response from client"""
        if websocket in self.connection_health:
            self.connection_health[websocket]['last_pong'] = timestamp or time.time()
            self.connection_health[websocket]['missed_pings'] = 0
            self.connection_health[websocket]['is_healthy'] = True
    
    def is_healthy(self, websocket: WebSocket) -> bool:
        """Check if connection is healthy"""
        if websocket not in self.connection_health:
            return False
        return self.connection_health[websocket]['is_healthy']
    
    def cleanup_connection(self, websocket: WebSocket):
        """Clean up health monitoring for a connection"""
        self.connection_health.pop(websocket, None)
    
    def get_health_stats(self) -> Dict:
        """Get health statistics for all connections"""
        healthy_count = sum(1 for health in self.connection_health.values() if health['is_healthy'])
        total_count = len(self.connection_health)
        
        return {
            'total_connections': total_count,
            'healthy_connections': healthy_count,
            'unhealthy_connections': total_count - healthy_count,
            'health_percentage': (healthy_count / total_count * 100) if total_count > 0 else 100
        }

class ConnectionManager:
    """Enhanced WebSocket connection manager with health monitoring and status indicators"""
    
    def __init__(self):
        # Store active connections by client_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Store user info for each connection
        self.connection_info: Dict[WebSocket, Dict] = {}
        # Redis client for pub/sub
        self.redis_client = None
        # Health monitor
        self.health_monitor = ConnectionHealthMonitor()
        # Connection statistics
        self.connection_stats = {
            'total_connections_ever': 0,
            'current_connections': 0,
            'disconnections': 0,
            'failed_connections': 0,
            'last_connection_time': None,
            'uptime_start': datetime.utcnow()
        }
    
    async def initialize_redis(self):
        """Initialize Redis connection for pub/sub with retry logic"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.redis_client = redis.from_url(settings.redis_url)
                # Test the connection
                await self.redis_client.ping()
                logger.info("Redis connection established for WebSocket service")
                
                # Start listening for Redis pub/sub messages
                asyncio.create_task(self._listen_for_updates())
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize Redis (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        logger.error("Failed to establish Redis connection after all retries")
        return False
    
    async def connect(self, websocket: WebSocket, client_id: int, user_id: int):
        """Accept a new WebSocket connection with enhanced monitoring and authentication confirmation"""
        try:
            await websocket.accept()
            
            if client_id not in self.active_connections:
                self.active_connections[client_id] = set()
            
            self.active_connections[client_id].add(websocket)
            connection_time = datetime.utcnow()
            connection_id = id(websocket)
            
            self.connection_info[websocket] = {
                'client_id': client_id,
                'user_id': user_id,
                'connected_at': connection_time,
                'last_activity': connection_time,
                'messages_sent': 0,
                'messages_received': 0,
                'connection_id': connection_id,
                'authentication_confirmed': True,
                'health_status': 'healthy'
            }
            
            # Update statistics
            self.connection_stats['total_connections_ever'] += 1
            self.connection_stats['current_connections'] += 1
            self.connection_stats['last_connection_time'] = connection_time
            
            # Start health monitoring
            await self.health_monitor.start_health_monitoring(websocket)
            
            # Send initial connection confirmation with comprehensive status
            connection_status = {
                'type': 'connection_established',
                'client_id': client_id,
                'user_id': user_id,
                'connection_id': connection_id,
                'server_time': connection_time.isoformat(),
                'authentication': {
                    'status': 'confirmed',
                    'client_scoped': True,
                    'user_verified': True
                },
                'service_status': {
                    'redis_connected': self.redis_client is not None,
                    'health_monitoring_active': True,
                    'ping_interval_seconds': self.health_monitor.ping_interval,
                    'ping_timeout_seconds': self.health_monitor.ping_timeout,
                    'max_missed_pings': self.health_monitor.max_missed_pings
                },
                'connection_info': {
                    'total_connections': self.connection_stats['current_connections'],
                    'client_connections': len(self.active_connections[client_id]),
                    'uptime_start': self.connection_stats['uptime_start'].isoformat()
                }
            }
            
            await self.send_personal_message(connection_status, websocket)
            
            # Send welcome message with available features
            welcome_message = {
                'type': 'welcome',
                'message': 'WebSocket connection established successfully',
                'available_features': [
                    'real_time_notifications',
                    'health_monitoring',
                    'connection_statistics',
                    'ping_pong_heartbeat',
                    'automatic_reconnection_support'
                ],
                'supported_message_types': [
                    'ping', 'pong', 'subscribe', 'get_stats', 
                    'get_monitoring_status', 'health_check'
                ]
            }
            
            await self.send_personal_message(welcome_message, websocket)
            
            logger.info(f"WebSocket connected and authenticated: client_id={client_id}, user_id={user_id}, connection_id={connection_id}")
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            self.connection_stats['failed_connections'] += 1
            raise
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection with cleanup"""
        if websocket in self.connection_info:
            connection_info = self.connection_info[websocket]
            client_id = connection_info['client_id']
            user_id = connection_info['user_id']
            
            if client_id in self.active_connections:
                self.active_connections[client_id].discard(websocket)
                
                # Clean up empty client groups
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]
            
            # Update statistics
            self.connection_stats['current_connections'] -= 1
            self.connection_stats['disconnections'] += 1
            
            # Clean up health monitoring
            self.health_monitor.cleanup_connection(websocket)
            
            # Remove connection info
            del self.connection_info[websocket]
            
            logger.info(f"WebSocket disconnected: client_id={client_id}, user_id={user_id}")
        else:
            logger.warning("Attempted to disconnect unknown WebSocket connection")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection with error handling"""
        try:
            # Add timestamp to all messages
            message['server_timestamp'] = datetime.utcnow().isoformat()
            
            await websocket.send_text(json.dumps(message))
            
            # Update connection statistics
            if websocket in self.connection_info:
                self.connection_info[websocket]['messages_sent'] += 1
                self.connection_info[websocket]['last_activity'] = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_client(self, message: dict, client_id: int):
        """Broadcast a message to all connections for a specific client with health checks"""
        if client_id not in self.active_connections:
            logger.debug(f"No active connections for client {client_id}")
            return
        
        # Add timestamp and client info to message
        message['server_timestamp'] = datetime.utcnow().isoformat()
        message['target_client_id'] = client_id
        
        disconnected = set()
        healthy_connections = 0
        
        for connection in self.active_connections[client_id].copy():
            try:
                # Check connection health before sending
                if not self.health_monitor.is_healthy(connection):
                    logger.warning(f"Skipping unhealthy connection for client {client_id}")
                    disconnected.add(connection)
                    continue
                
                await connection.send_text(json.dumps(message))
                healthy_connections += 1
                
                # Update connection statistics
                if connection in self.connection_info:
                    self.connection_info[connection]['messages_sent'] += 1
                    self.connection_info[connection]['last_activity'] = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
        
        logger.debug(f"Broadcast to client {client_id}: {healthy_connections} connections reached")
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all active connections"""
        for client_id in list(self.active_connections.keys()):
            await self.broadcast_to_client(message, client_id)
    
    async def publish_update(self, event_type: str, data: dict, client_id: int = None):
        """Publish an update to Redis for distribution"""
        if not self.redis_client:
            return
        
        message = {
            'type': event_type,
            'data': data,
            'client_id': client_id,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        try:
            channel = f"updates:{client_id}" if client_id else "updates:all"
            await self.redis_client.publish(channel, json.dumps(message))
        except Exception as e:
            print(f"Error publishing update: {e}")
    
    async def _listen_for_updates(self):
        """Listen for Redis pub/sub messages and broadcast to WebSocket clients"""
        if not self.redis_client:
            return
        
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.psubscribe("updates:*")
            
            async for message in pubsub.listen():
                if message['type'] == 'pmessage':
                    try:
                        data = json.loads(message['data'])
                        client_id = data.get('client_id')
                        
                        if client_id:
                            await self.broadcast_to_client(data, client_id)
                        else:
                            await self.broadcast_to_all(data)
                    except Exception as e:
                        print(f"Error processing Redis message: {e}")
        except Exception as e:
            print(f"Error in Redis listener: {e}")
    
    def get_connection_stats(self) -> dict:
        """Get comprehensive statistics about active connections"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        health_stats = self.health_monitor.get_health_stats()
        
        # Calculate uptime
        uptime = datetime.utcnow() - self.connection_stats['uptime_start']
        
        # Get per-client statistics
        client_stats = {}
        for client_id, connections in self.active_connections.items():
            healthy_count = sum(1 for conn in connections if self.health_monitor.is_healthy(conn))
            client_stats[client_id] = {
                'total_connections': len(connections),
                'healthy_connections': healthy_count,
                'unhealthy_connections': len(connections) - healthy_count
            }
        
        return {
            'current_connections': total_connections,
            'clients_connected': len(self.active_connections),
            'connections_per_client': client_stats,
            'health': health_stats,
            'lifetime_stats': {
                'total_connections_ever': self.connection_stats['total_connections_ever'],
                'disconnections': self.connection_stats['disconnections'],
                'failed_connections': self.connection_stats['failed_connections'],
                'last_connection_time': self.connection_stats['last_connection_time'].isoformat() if self.connection_stats['last_connection_time'] else None,
                'uptime_seconds': uptime.total_seconds(),
                'uptime_formatted': str(uptime)
            },
            'redis_status': {
                'connected': self.redis_client is not None,
                'pub_sub_active': hasattr(self, '_pubsub_task') and not self._pubsub_task.done() if hasattr(self, '_pubsub_task') else False
            }
        }
    
    def get_monitoring_status(self) -> dict:
        """Get monitoring and health status for dashboard display"""
        stats = self.get_connection_stats()
        
        # Determine overall system health
        health_percentage = stats['health']['health_percentage']
        if health_percentage >= 95:
            status = "excellent"
        elif health_percentage >= 80:
            status = "good"
        elif health_percentage >= 60:
            status = "fair"
        else:
            status = "poor"
        
        return {
            'status': status,
            'health_percentage': health_percentage,
            'active_connections': stats['current_connections'],
            'clients_connected': stats['clients_connected'],
            'redis_connected': stats['redis_status']['connected'],
            'uptime_seconds': stats['lifetime_stats']['uptime_seconds'],
            'last_updated': datetime.utcnow().isoformat()
        }


# Global connection manager instance
manager = ConnectionManager()


class WebSocketNotifier:
    """Service for sending real-time notifications via WebSocket"""
    
    @staticmethod
    async def notify_new_post(client_id: int, post_data: dict):
        """Notify about a new matched post"""
        await manager.publish_update('new_post', post_data, client_id)
    
    @staticmethod
    async def notify_new_response(client_id: int, response_data: dict):
        """Notify about a new AI response"""
        await manager.publish_update('new_response', response_data, client_id)
    
    @staticmethod
    async def notify_response_copied(client_id: int, response_id: int):
        """Notify when a response is copied"""
        await manager.publish_update('response_copied', {'response_id': response_id}, client_id)
    
    @staticmethod
    async def notify_scan_started(client_id: int = None):
        """Notify when a Reddit scan starts"""
        await manager.publish_update('scan_started', {}, client_id)
    
    @staticmethod
    async def notify_scan_completed(client_id: int, results: dict):
        """Notify when a Reddit scan completes"""
        await manager.publish_update('scan_completed', results, client_id)
    
    @staticmethod
    async def notify_analytics_update(client_id: int, analytics_data: dict):
        """Notify about analytics updates"""
        await manager.publish_update('analytics_update', analytics_data, client_id)
    
    @staticmethod
    async def notify_system_status(status: str, message: str):
        """Notify about system-wide status changes"""
        await manager.publish_update('system_status', {
            'status': status,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def notify_monitoring_status_update(client_id: int = None):
        """Notify about monitoring status updates"""
        status = manager.get_monitoring_status()
        await manager.publish_update('monitoring_status_update', status, client_id)
    
    @staticmethod
    async def notify_connection_health_update(client_id: int):
        """Notify about connection health changes"""
        health_stats = manager.health_monitor.get_health_stats()
        await manager.publish_update('connection_health_update', health_stats, client_id)
    
    @staticmethod
    async def notify_reddit_api_status(status: str, message: str, client_id: int = None):
        """Notify about Reddit API status changes"""
        await manager.publish_update('reddit_api_status', {
            'status': status,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }, client_id)


async def websocket_endpoint(websocket: WebSocket, client_id: int, user_id: int):
    """WebSocket endpoint handler"""
    await manager.connect(websocket, client_id, user_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, message, client_id, user_id)
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def handle_websocket_message(websocket: WebSocket, message: dict, client_id: int, user_id: int):
    """Handle incoming WebSocket messages from clients with enhanced functionality and lifecycle management"""
    message_type = message.get('type')
    
    # Update connection activity
    if websocket in manager.connection_info:
        manager.connection_info[websocket]['messages_received'] += 1
        manager.connection_info[websocket]['last_activity'] = datetime.utcnow()
    
    if message_type == 'ping':
        # Handle client ping with enhanced response
        client_timestamp = message.get('timestamp', time.time())
        server_timestamp = time.time()
        
        await manager.send_personal_message({
            'type': 'pong',
            'client_timestamp': client_timestamp,
            'server_timestamp': server_timestamp,
            'round_trip_time': server_timestamp - client_timestamp if isinstance(client_timestamp, (int, float)) else None,
            'connection_healthy': manager.health_monitor.is_healthy(websocket)
        }, websocket)
    
    elif message_type == 'pong':
        # Handle pong response for health monitoring
        timestamp = message.get('timestamp') or message.get('server_timestamp')
        manager.health_monitor.handle_pong(websocket, timestamp)
        
        # Send acknowledgment
        await manager.send_personal_message({
            'type': 'pong_acknowledged',
            'timestamp': datetime.utcnow().isoformat(),
            'health_status': 'healthy'
        }, websocket)
        
    elif message_type == 'subscribe':
        # Handle subscription to specific event types
        event_types = message.get('events', [])
        await manager.send_personal_message({
            'type': 'subscribed',
            'events': event_types,
            'client_id': client_id,
            'subscription_active': True,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
    
    elif message_type == 'get_stats':
        # Send connection statistics
        stats = manager.get_connection_stats()
        await manager.send_personal_message({
            'type': 'stats',
            'data': stats,
            'requested_by': {
                'client_id': client_id,
                'user_id': user_id,
                'connection_id': manager.connection_info[websocket].get('connection_id', id(websocket))
            }
        }, websocket)
    
    elif message_type == 'get_monitoring_status':
        # Send monitoring status for dashboard
        status = manager.get_monitoring_status()
        await manager.send_personal_message({
            'type': 'monitoring_status',
            'data': status,
            'requested_by': {
                'client_id': client_id,
                'user_id': user_id
            }
        }, websocket)
    
    elif message_type == 'health_check':
        # Respond with comprehensive connection health information
        connection_info = manager.connection_info.get(websocket, {})
        health_info = manager.health_monitor.connection_health.get(websocket, {})
        
        health_response = {
            'connection_healthy': manager.health_monitor.is_healthy(websocket),
            'server_time': datetime.utcnow().isoformat(),
            'connection_info': {
                'connection_id': connection_info.get('connection_id', id(websocket)),
                'connected_at': connection_info.get('connected_at', datetime.utcnow()).isoformat(),
                'uptime_seconds': (datetime.utcnow() - connection_info.get('connected_at', datetime.utcnow())).total_seconds(),
                'messages_sent': connection_info.get('messages_sent', 0),
                'messages_received': connection_info.get('messages_received', 0),
                'last_activity': connection_info.get('last_activity', datetime.utcnow()).isoformat()
            },
            'health_metrics': {
                'last_ping': datetime.fromtimestamp(health_info['last_ping']).isoformat() if health_info.get('last_ping') else None,
                'last_pong': datetime.fromtimestamp(health_info['last_pong']).isoformat() if health_info.get('last_pong') else None,
                'missed_pings': health_info.get('missed_pings', 0),
                'ping_interval_seconds': manager.health_monitor.ping_interval,
                'ping_timeout_seconds': manager.health_monitor.ping_timeout
            },
            'client_info': {
                'client_id': client_id,
                'user_id': user_id,
                'authentication_confirmed': connection_info.get('authentication_confirmed', False)
            }
        }
        
        await manager.send_personal_message({
            'type': 'health_response',
            'data': health_response
        }, websocket)
    
    elif message_type == 'connection_test':
        # Handle connection test requests
        test_data = message.get('test_data', {})
        
        await manager.send_personal_message({
            'type': 'connection_test_response',
            'original_data': test_data,
            'server_response': {
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'connection_id': manager.connection_info[websocket].get('connection_id', id(websocket)),
                'echo_test': 'Connection test successful'
            }
        }, websocket)
    
    elif message_type == 'get_connection_info':
        # Send detailed connection information
        connection_info = manager.connection_info.get(websocket, {})
        
        await manager.send_personal_message({
            'type': 'connection_info',
            'data': {
                'connection_id': connection_info.get('connection_id', id(websocket)),
                'client_id': client_id,
                'user_id': user_id,
                'connected_at': connection_info.get('connected_at', datetime.utcnow()).isoformat(),
                'authentication_status': 'confirmed',
                'service_features': {
                    'health_monitoring': True,
                    'real_time_notifications': True,
                    'redis_pub_sub': manager.redis_client is not None,
                    'connection_statistics': True
                }
            }
        }, websocket)
    
    else:
        # Handle unknown message types with helpful error response
        await manager.send_personal_message({
            'type': 'error',
            'error_code': 'UNKNOWN_MESSAGE_TYPE',
            'message': f'Unknown message type: {message_type}',
            'received_message': message,
            'supported_types': [
                'ping', 'pong', 'subscribe', 'get_stats', 
                'get_monitoring_status', 'health_check', 
                'connection_test', 'get_connection_info'
            ],
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)