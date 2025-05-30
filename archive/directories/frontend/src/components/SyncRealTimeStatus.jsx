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
import { motion, AnimatePresence } from 'framer-motion';
import useWebSocketSync from '../hooks/useWebSocketSync';
import {
  AnimatedBadge,
  AnimatedButton,
  AnimatedAlert,
  AnimatedProgress,
  AnimatedCard,
  AnimatedCount,
  DataRefreshIndicator
} from './AnimatedElements';

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

// Animation variants
const listItemVariants = {
  initial: { opacity: 0, y: 20, height: 0 },
  animate: { opacity: 1, y: 0, height: 'auto', transition: { duration: 0.3 } },
  exit: { opacity: 0, height: 0, transition: { duration: 0.2 } }
};

const cardVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } },
  exit: { opacity: 0, y: -20, transition: { duration: 0.3 } }
};

const toastVariants = {
  initial: { opacity: 0, x: 100 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.3, type: 'spring', stiffness: 300, damping: 25 } },
  exit: { opacity: 0, x: 100, transition: { duration: 0.2 } }
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
  // State for tracking if we're refreshing data
  const [isRefreshing, setIsRefreshing] = useState(false);
  // State for tracking previously viewed operations to animate changes
  const [prevOperations, setPrevOperations] = useState({});
  
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
  
  // Update prevOperations when operations change to track changes for animations
  useEffect(() => {
    // If this is a change, mark we're refreshing
    if (Object.keys(prevOperations).length > 0) {
      setIsRefreshing(true);
      // Reset refreshing state after animation completes
      setTimeout(() => setIsRefreshing(false), 700);
    }
    
    setPrevOperations(operations);
  }, [operations]);
  
  // Determine if an operation has changed significantly for animations
  const hasOperationChanged = (operation) => {
    const prev = prevOperations[operation.operation_id];
    if (!prev) return true;
    
    return (
      prev.status !== operation.status ||
      prev.processed_records !== operation.processed_records ||
      prev.failed_records !== operation.failed_records
    );
  };
  
  return (
    <div className="sync-real-time-status">
      <DataRefreshIndicator isRefreshing={isRefreshing} />
      
      {/* Connection status */}
      <div className="connection-status mb-3">
        <AnimatePresence mode="wait">
          {connectionError ? (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.3 }}
            >
              <AnimatedAlert color="danger">
                {connectionError}
                <AnimatedButton
                  color="link"
                  className="p-0 ms-2"
                  onClick={() => window.location.reload()}
                >
                  Reconnect
                </AnimatedButton>
              </AnimatedAlert>
            </motion.div>
          ) : isConnected ? (
            <motion.div
              key="connected"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.3 }}
            >
              <Alert color="success" className="d-flex align-items-center justify-content-between">
                <div className="d-flex align-items-center">
                  <motion.span 
                    className="me-2"
                    animate={{ 
                      color: ['#28a745', '#43b860', '#28a745'],
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    Connected to sync service
                  </motion.span>
                  
                  <AnimatePresence>
                    {runningOpsCount > 0 && (
                      <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.8, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Badge color="primary" pill>
                          <AnimatedCount value={runningOpsCount} /> running
                        </Badge>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  <AnimatePresence>
                    {failedOpsCount > 0 && (
                      <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.8, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="ms-2"
                      >
                        <Badge color="danger" pill>
                          <AnimatedCount value={failedOpsCount} /> failed
                        </Badge>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
                
                <AnimatedButton
                  color="link"
                  className="p-0"
                  onClick={toggleNotifications}
                >
                  Notifications (<AnimatedCount value={notifications.length} />)
                </AnimatedButton>
              </Alert>
            </motion.div>
          ) : (
            <motion.div
              key="connecting"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.3 }}
            >
              <Alert color="warning" className="d-flex align-items-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="me-2"
                >
                  <Spinner size="sm" />
                </motion.div>
                Connecting to sync service...
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {/* Notifications panel */}
      <AnimatePresence>
        {showNotifications && (
          <motion.div
            variants={cardVariants}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            <Card className="mb-4 shadow-sm">
              <CardHeader className="d-flex justify-content-between align-items-center">
                <motion.h5 
                  className="mb-0"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: 0.1 }}
                >
                  Recent Notifications
                </motion.h5>
                <div>
                  <AnimatedButton
                    color="link"
                    className="p-0 me-2"
                    onClick={clearNotifications}
                  >
                    Clear All
                  </AnimatedButton>
                  <AnimatedButton
                    color="link"
                    className="p-0"
                    onClick={toggleNotifications}
                  >
                    Close
                  </AnimatedButton>
                </div>
              </CardHeader>
              <CardBody>
                {notifications.length === 0 ? (
                  <AnimatedAlert color="info">No recent notifications</AnimatedAlert>
                ) : (
                  <ListGroup>
                    <AnimatePresence>
                      {notifications.map((notification, index) => (
                        <motion.div
                          key={`${notification.audit_id || index}-${notification.timestamp || Date.now()}`}
                          variants={listItemVariants}
                          initial="initial"
                          animate="animate"
                          exit="exit"
                          layout
                        >
                          <ListGroupItem
                            className={`list-group-item-${
                              notification.severity === 'error' || notification.severity === 'critical'
                                ? 'danger'
                                : notification.severity === 'warning'
                                ? 'warning'
                                : 'info'
                            }`}
                          >
                            <div className="d-flex justify-content-between">
                              <motion.strong
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ duration: 0.3, delay: 0.1 }}
                              >
                                {eventMessages[notification.event_type] || notification.event_type}
                              </motion.strong>
                              <motion.small
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ duration: 0.3, delay: 0.2 }}
                              >
                                {new Date(notification.created_at).toLocaleTimeString()}
                              </motion.small>
                            </div>
                            <motion.p 
                              className="mb-1"
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ duration: 0.3, delay: 0.3 }}
                            >
                              {notification.description}
                            </motion.p>
                            {notification.operation_id && (
                              <motion.small
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ duration: 0.3, delay: 0.4 }}
                              >
                                Operation ID: {notification.operation_id}
                              </motion.small>
                            )}
                          </ListGroupItem>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </ListGroup>
                )}
              </CardBody>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Real-time operation updates */}
      <AnimatePresence>
        {Object.values(operations).length > 0 ? (
          <motion.div 
            className="operation-cards"
            initial={{ opacity: 1 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
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
              .map((operation, index) => {
                // Calculate progress percentage
                const progress = operation.processed_records > 0 && operation.total_records > 0
                  ? Math.round((operation.processed_records / operation.total_records) * 100)
                  : 0;
                
                // Calculate success rate
                const successRate = operation.processed_records > 0
                  ? Math.round((operation.successful_records / operation.processed_records) * 100)
                  : 0;
                
                // Check if this operation has changed since last render
                const changed = hasOperationChanged(operation);
                
                return (
                  <motion.div
                    key={operation.operation_id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ 
                      opacity: 1, 
                      y: 0,
                      scale: changed ? [1, 1.02, 1] : 1,
                      boxShadow: changed ? 
                        ['0 4px 6px rgba(0,0,0,0.1)', '0 6px 10px rgba(0,0,0,0.15)', '0 4px 6px rgba(0,0,0,0.1)'] : 
                        '0 4px 6px rgba(0,0,0,0.1)'
                    }}
                    transition={{ 
                      duration: 0.4, 
                      delay: index * 0.1,
                      scale: { duration: 0.5 },
                      boxShadow: { duration: 0.5 }
                    }}
                    layout
                  >
                    <Card className="mb-3 shadow-sm">
                      <CardHeader className="d-flex justify-content-between align-items-center">
                        <div>
                          <motion.h5 
                            className="mb-0"
                            animate={{ 
                              color: operation.status === 'running' ? 
                                ['#212529', '#0056b3', '#212529'] : '#212529'
                            }}
                            transition={{ duration: 3, repeat: operation.status === 'running' ? Infinity : 0 }}
                          >
                            Operation #{operation.operation_id}
                          </motion.h5>
                          <div>
                            <small className="text-muted">
                              {operation.sync_type} sync
                            </small>
                            {operation.status === 'running' && (
                              <motion.small 
                                className="text-muted ms-2"
                                key={`running-${operation.operation_id}`}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                              >
                                Running for {formatTimeElapsed(operation.started_at)}
                              </motion.small>
                            )}
                            {operation.status === 'completed' && operation.completed_at && (
                              <motion.small 
                                className="text-muted ms-2"
                                key={`completed-${operation.operation_id}`}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                              >
                                Completed in {formatTimeElapsed(operation.started_at, operation.completed_at)}
                              </motion.small>
                            )}
                          </div>
                        </div>
                        <AnimatedBadge color={statusColors[operation.status] || 'secondary'}>
                          {operation.status}
                        </AnimatedBadge>
                      </CardHeader>
                      <CardBody>
                        <motion.div 
                          className="mb-3"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ duration: 0.4, delay: 0.2 }}
                        >
                          <div className="d-flex justify-content-between mb-1">
                            <span>Progress</span>
                            <AnimatedCount value={progress} />%
                          </div>
                          <AnimatedProgress 
                            value={progress} 
                            color={statusColors[operation.status]}
                          />
                        </motion.div>
                        
                        <motion.div 
                          className="d-flex justify-content-between mb-3"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.4, delay: 0.3 }}
                        >
                          <div>
                            <strong>Records:</strong>{' '}
                            <AnimatedCount value={operation.processed_records} /> / {operation.total_records}
                          </div>
                          <div>
                            <strong>Success Rate:</strong> <AnimatedCount value={successRate} />%
                          </div>
                          <div>
                            <strong>Failed:</strong> <AnimatedCount value={operation.failed_records} />
                          </div>
                        </motion.div>
                        
                        <AnimatePresence>
                          {operation.error_message && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              exit={{ opacity: 0, height: 0 }}
                              transition={{ duration: 0.3 }}
                            >
                              <AnimatedAlert color="danger" className="mb-3">
                                {operation.error_message}
                              </AnimatedAlert>
                            </motion.div>
                          )}
                        </AnimatePresence>
                        
                        <motion.div 
                          className="text-end"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ duration: 0.4, delay: 0.4 }}
                        >
                          <small className="text-muted">
                            Last updated: {new Date().toLocaleTimeString()}
                          </small>
                        </motion.div>
                      </CardBody>
                    </Card>
                  </motion.div>
                );
              })}
          </motion.div>
        ) : (
          isConnected && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <AnimatedAlert color="info">
                No active operations to display. Start a sync operation to see real-time updates.
              </AnimatedAlert>
            </motion.div>
          )
        )}
      </AnimatePresence>
      
      {/* Floating toast for new notifications */}
      <AnimatePresence>
        {notifications.length > 0 && !showNotifications && (
          <motion.div
            className="position-fixed bottom-0 end-0 p-3"
            style={{ zIndex: 5 }}
            variants={toastVariants}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            <Toast isOpen={true}>
              <ToastHeader toggle={toggleNotifications}>
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.2 }}
                >
                  New Notification
                </motion.span>
              </ToastHeader>
              <ToastBody>
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.3 }}
                >
                  {notifications[0].description}
                  <AnimatedButton 
                    color="link" 
                    className="p-0 d-block mt-2" 
                    onClick={toggleNotifications}
                  >
                    View All Notifications
                  </AnimatedButton>
                </motion.div>
              </ToastBody>
            </Toast>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SyncRealTimeStatus;