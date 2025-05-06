import React, { useState, useEffect } from 'react';
import { Badge, Spinner, Alert } from 'reactstrap';
import useWebSocketSync from '../hooks/useWebSocketSync';

/**
 * Component to display WebSocket connection status
 * @param {Object} props - Component props
 * @param {number[]} props.operationIds - Array of operation IDs to subscribe to
 * @param {boolean} props.showNotifications - Whether to show notifications
 * @param {number} props.maxNotifications - Maximum number of notifications to show
 */
const WebSocketStatusIndicator = ({
  operationIds = [],
  showNotifications = true,
  maxNotifications = 3
}) => {
  // Get WebSocket URL from environment or use default
  const wsUrl = '/api/ws';
  
  // Use WebSocket hook
  const {
    isConnected,
    operations,
    notifications,
    connectionError
  } = useWebSocketSync(wsUrl, operationIds);
  
  // Count running operations
  const runningOpsCount = Object.values(operations).filter(
    op => op.status === 'running' || op.status === 'pending'
  ).length;
  
  return (
    <div className="websocket-status-indicator mb-3">
      <div className="d-flex align-items-center">
        {connectionError ? (
          <Badge color="danger" pill className="px-3 py-2">
            Disconnected
          </Badge>
        ) : isConnected ? (
          <Badge color="success" pill className="px-3 py-2 d-flex align-items-center">
            <span className="me-1">Connected</span>
            {runningOpsCount > 0 && (
              <Badge color="light" pill className="ms-1 text-dark">
                {runningOpsCount} active
              </Badge>
            )}
          </Badge>
        ) : (
          <Badge color="warning" pill className="px-3 py-2 d-flex align-items-center">
            <Spinner size="sm" className="me-2" />
            Connecting...
          </Badge>
        )}
      </div>
      
      {showNotifications && notifications.length > 0 && (
        <div className="mt-2">
          {notifications.slice(0, maxNotifications).map((notification, index) => (
            <Alert
              key={index}
              color={
                notification.severity === 'error' || notification.severity === 'critical'
                  ? 'danger'
                  : notification.severity === 'warning'
                  ? 'warning'
                  : 'info'
              }
              className="p-2 mb-2"
            >
              <small>
                {notification.description || notification.event_type}
              </small>
            </Alert>
          ))}
          {notifications.length > maxNotifications && (
            <small className="text-muted">
              +{notifications.length - maxNotifications} more notifications
            </small>
          )}
        </div>
      )}
    </div>
  );
};

export default WebSocketStatusIndicator;