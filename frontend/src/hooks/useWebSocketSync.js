import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for managing WebSocket connections to the SyncService WebSocket server
 * @param {string} url - WebSocket server URL
 * @param {Array<number>} operationIds - Array of operation IDs to subscribe to
 * @param {boolean} autoReconnect - Whether to automatically reconnect (default: true)
 * @returns {Object} - WebSocket state and connection management functions
 */
const useWebSocketSync = (url, operationIds = [], autoReconnect = true) => {
  const [isConnected, setIsConnected] = useState(false);
  const [operations, setOperations] = useState({});
  const [notifications, setNotifications] = useState([]);
  const [connectionError, setConnectionError] = useState(null);
  
  // Use a ref to keep the current WebSocket instance
  const wsRef = useRef(null);
  
  // Use a ref to track reconnection attempts
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelayMs = 3000;
  
  // Keep track of subscribed operation IDs
  const subscribedOpsRef = useRef(new Set());
  
  /**
   * Connect to the WebSocket server
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }
    
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('WebSocket connection established');
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttemptsRef.current = 0;
        
        // Subscribe to specified operation IDs
        operationIds.forEach(opId => {
          subscribeToOperation(opId);
        });
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'operation_update':
            handleOperationUpdate(message.data);
            break;
            
          case 'audit_notification':
            handleAuditNotification(message.data);
            break;
            
          case 'error':
            console.error('WebSocket error:', message.message);
            break;
            
          default:
            console.log('Unknown message type:', message.type);
        }
      };
      
      ws.onclose = (event) => {
        console.log(`WebSocket connection closed: ${event.code} - ${event.reason}`);
        setIsConnected(false);
        
        // Try to reconnect if autoReconnect is enabled
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})...`);
          reconnectAttemptsRef.current += 1;
          setTimeout(connect, reconnectDelayMs);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setConnectionError('Maximum reconnection attempts reached. Please try again later.');
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('Failed to connect to the server. Please check your network connection.');
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      setConnectionError(`Connection error: ${error.message}`);
    }
  }, [url, operationIds, autoReconnect]);
  
  /**
   * Disconnect from the WebSocket server
   */
  const disconnect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }
  }, []);
  
  /**
   * Subscribe to updates for a specific operation
   * @param {number} operationId - ID of the operation to subscribe to
   */
  const subscribeToOperation = useCallback((operationId) => {
    if (!operationId) return;
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Only subscribe if not already subscribed
      if (!subscribedOpsRef.current.has(operationId)) {
        wsRef.current.send(JSON.stringify({
          action: 'subscribe',
          operation_id: operationId
        }));
        subscribedOpsRef.current.add(operationId);
      }
    } else {
      // If not connected, add to the set and it will be subscribed when connected
      subscribedOpsRef.current.add(operationId);
    }
  }, []);
  
  /**
   * Unsubscribe from updates for a specific operation
   * @param {number} operationId - ID of the operation to unsubscribe from
   */
  const unsubscribeFromOperation = useCallback((operationId) => {
    if (!operationId) return;
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        operation_id: operationId
      }));
    }
    
    subscribedOpsRef.current.delete(operationId);
    
    // Remove operation from state
    setOperations(prevOps => {
      const newOps = { ...prevOps };
      delete newOps[operationId];
      return newOps;
    });
  }, []);
  
  /**
   * Handle operation update message
   * @param {Object} data - Operation data from the server
   */
  const handleOperationUpdate = useCallback((data) => {
    setOperations(prevOps => ({
      ...prevOps,
      [data.operation_id]: data
    }));
  }, []);
  
  /**
   * Handle audit notification message
   * @param {Object} data - Audit notification data from the server
   */
  const handleAuditNotification = useCallback((data) => {
    setNotifications(prevNotifications => [data, ...prevNotifications].slice(0, 10));
  }, []);
  
  /**
   * Clear all notifications
   */
  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);
  
  // Connect to the WebSocket server when the component mounts
  useEffect(() => {
    connect();
    
    // Clean up the WebSocket connection when the component unmounts
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);
  
  // Subscribe/unsubscribe to operation IDs when they change
  useEffect(() => {
    const currentSubscribed = subscribedOpsRef.current;
    
    // Subscribe to new operation IDs
    operationIds.forEach(opId => {
      if (!currentSubscribed.has(opId)) {
        subscribeToOperation(opId);
      }
    });
    
    // Unsubscribe from removed operation IDs
    currentSubscribed.forEach(opId => {
      if (!operationIds.includes(opId)) {
        unsubscribeFromOperation(opId);
      }
    });
  }, [operationIds, subscribeToOperation, unsubscribeFromOperation]);
  
  return {
    isConnected,
    operations,
    notifications,
    connectionError,
    connect,
    disconnect,
    subscribeToOperation,
    unsubscribeFromOperation,
    clearNotifications
  };
};

export default useWebSocketSync;