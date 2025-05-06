import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Badge,
  Button,
  Alert,
  Progress,
  Spinner,
  Toast,
  ToastHeader,
  ToastBody,
  ListGroup,
  ListGroupItem
} from 'reactstrap';
import useWebSocketSync from '../hooks/useWebSocketSync';

// Map of status to color for visual indication
const statusColors = {
  completed: 'success',
  running: 'primary',
  pending: 'warning',
  failed: 'danger',
  cancelled: 'secondary'
};

// Map of event type to user-friendly messages
const eventMessages = {
  sync_started: 'Sync operation started',
  sync_completed: 'Sync operation completed successfully',
  sync_failed: 'Sync operation failed',
  record_validation_failed: 'Record validation failed',
  data_transformation_error: 'Error during data transformation'
};

const SyncRealTimeStatus = ({ selectedOperationIds = [] }) => {
  // Get the WebSocket URL from environment or use a default
  const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8081/ws';
  
  // Use our custom WebSocket hook
  const {
    isConnected,
    operations,
    notifications,
    connectionError,
    clearNotifications
  } = useWebSocketSync(wsUrl, selectedOperationIds);
  
  // State for showing/hiding the notifications panel
  const [showNotifications, setShowNotifications] = useState(false);
  
  // Calculate the number of running operations
  const runningOpsCount = Object.values(operations).filter(
    op => op.status === 'running' || op.status === 'pending'
  ).length;
  
  // Calculate the number of failed operations
  const failedOpsCount = Object.values(operations).filter(
    op => op.status === 'failed'
  ).length;
  
  // Function to format time elapsed
  const formatTimeElapsed = (startTime, endTime = null) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diffMs = end - start;
    
    // Convert to hours, minutes, seconds
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);
    
    // Format the output based on duration
    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  };
  
  // Function to toggle notifications panel
  const toggleNotifications = () => {
    setShowNotifications(!showNotifications);
  };
  
  return (
    <div className="sync-real-time-status">
      {/* Connection status */}
      <div className="connection-status mb-3">
        {connectionError ? (
          <Alert color="danger">
            {connectionError}
            <Button
              color="link"
              className="p-0 ms-2"
              onClick={() => window.location.reload()}
            >
              Reconnect
            </Button>
          </Alert>
        ) : isConnected ? (
          <Alert color="success" className="d-flex align-items-center justify-content-between">
            <div>
              <span className="me-2">Connected to sync service</span>
              <Badge color="primary" pill>
                {runningOpsCount} running
              </Badge>
              {failedOpsCount > 0 && (
                <Badge color="danger" pill className="ms-2">
                  {failedOpsCount} failed
                </Badge>
              )}
            </div>
            <Button
              color="link"
              className="p-0"
              onClick={toggleNotifications}
            >
              Notifications ({notifications.length})
            </Button>
          </Alert>
        ) : (
          <Alert color="warning" className="d-flex align-items-center">
            <Spinner size="sm" className="me-2" />
            Connecting to sync service...
          </Alert>
        )}
      </div>
      
      {/* Notifications panel */}
      {showNotifications && (
        <Card className="mb-4 shadow-sm">
          <CardHeader className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Recent Notifications</h5>
            <div>
              <Button
                color="link"
                className="p-0 me-2"
                onClick={clearNotifications}
              >
                Clear All
              </Button>
              <Button
                color="link"
                className="p-0"
                onClick={toggleNotifications}
              >
                Close
              </Button>
            </div>
          </CardHeader>
          <CardBody>
            {notifications.length === 0 ? (
              <Alert color="info">No recent notifications</Alert>
            ) : (
              <ListGroup>
                {notifications.map((notification, index) => (
                  <ListGroupItem
                    key={`${notification.audit_id || index}`}
                    className={`list-group-item-${
                      notification.severity === 'error' || notification.severity === 'critical'
                        ? 'danger'
                        : notification.severity === 'warning'
                        ? 'warning'
                        : 'info'
                    }`}
                  >
                    <div className="d-flex justify-content-between">
                      <strong>
                        {eventMessages[notification.event_type] || notification.event_type}
                      </strong>
                      <small>
                        {new Date(notification.created_at).toLocaleTimeString()}
                      </small>
                    </div>
                    <p className="mb-1">{notification.description}</p>
                    {notification.operation_id && (
                      <small>Operation ID: {notification.operation_id}</small>
                    )}
                  </ListGroupItem>
                ))}
              </ListGroup>
            )}
          </CardBody>
        </Card>
      )}
      
      {/* Real-time operation updates */}
      {Object.values(operations).length > 0 ? (
        <div className="operation-cards">
          {Object.values(operations)
            .sort((a, b) => {
              // Sort by status (running first, then pending, then others)
              const statusOrder = { running: 0, pending: 1 };
              const statusA = statusOrder[a.status] !== undefined ? statusOrder[a.status] : 2;
              const statusB = statusOrder[b.status] !== undefined ? statusOrder[b.status] : 2;
              
              if (statusA !== statusB) {
                return statusA - statusB;
              }
              
              // Then sort by start time (newest first)
              return new Date(b.started_at) - new Date(a.started_at);
            })
            .map(operation => {
              // Calculate progress percentage
              const progress = operation.processed_records > 0 && operation.total_records > 0
                ? Math.round((operation.processed_records / operation.total_records) * 100)
                : 0;
              
              // Calculate success rate
              const successRate = operation.processed_records > 0
                ? Math.round((operation.successful_records / operation.processed_records) * 100)
                : 0;
              
              return (
                <Card key={operation.operation_id} className="mb-3 shadow-sm">
                  <CardHeader className="d-flex justify-content-between align-items-center">
                    <div>
                      <h5 className="mb-0">
                        Operation #{operation.operation_id}
                      </h5>
                      <div>
                        <small className="text-muted">
                          {operation.sync_type} sync
                        </small>
                        {operation.status === 'running' && (
                          <small className="text-muted ms-2">
                            Running for {formatTimeElapsed(operation.started_at)}
                          </small>
                        )}
                        {operation.status === 'completed' && operation.completed_at && (
                          <small className="text-muted ms-2">
                            Completed in {formatTimeElapsed(operation.started_at, operation.completed_at)}
                          </small>
                        )}
                      </div>
                    </div>
                    <Badge color={statusColors[operation.status] || 'secondary'}>
                      {operation.status}
                    </Badge>
                  </CardHeader>
                  <CardBody>
                    <div className="mb-3">
                      <div className="d-flex justify-content-between mb-1">
                        <span>Progress</span>
                        <span>{progress}%</span>
                      </div>
                      <Progress value={progress} animated={operation.status === 'running'} />
                    </div>
                    
                    <div className="d-flex justify-content-between mb-3">
                      <div>
                        <strong>Records:</strong>{' '}
                        {operation.processed_records} / {operation.total_records}
                      </div>
                      <div>
                        <strong>Success Rate:</strong> {successRate}%
                      </div>
                      <div>
                        <strong>Failed:</strong> {operation.failed_records}
                      </div>
                    </div>
                    
                    {operation.error_message && (
                      <Alert color="danger" className="mb-3">
                        {operation.error_message}
                      </Alert>
                    )}
                    
                    <div className="text-end">
                      <small className="text-muted">
                        Last updated: {new Date().toLocaleTimeString()}
                      </small>
                    </div>
                  </CardBody>
                </Card>
              );
            })}
        </div>
      ) : (
        isConnected && (
          <Alert color="info">
            No active operations to display. Start a sync operation to see real-time updates.
          </Alert>
        )
      )}
      
      {/* Floating toast for new notifications */}
      {notifications.length > 0 && !showNotifications && (
        <div className="position-fixed bottom-0 end-0 p-3" style={{ zIndex: 5 }}>
          <Toast isOpen={true}>
            <ToastHeader toggle={toggleNotifications}>
              New Notification
            </ToastHeader>
            <ToastBody>
              {notifications[0].description}
              <Button 
                color="link" 
                className="p-0 d-block mt-2" 
                onClick={toggleNotifications}
              >
                View All Notifications
              </Button>
            </ToastBody>
          </Toast>
        </div>
      )}
    </div>
  );
};

export default SyncRealTimeStatus;