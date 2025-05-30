import React, { useState, useEffect } from 'react';
import { Badge, Spinner, Alert } from 'reactstrap';
import { motion, AnimatePresence } from 'framer-motion';
import useWebSocketSync from '../hooks/useWebSocketSync';
import { AnimatedAlert, AnimatedCount } from './AnimatedElements';

// Animation variants for badges
const badgeVariants = {
  initial: { scale: 0.8, opacity: 0 },
  animate: { scale: 1, opacity: 1, transition: { type: 'spring', stiffness: 300, damping: 20 } },
  exit: { scale: 0.8, opacity: 0 }
};

// Animation variants for alerts/notifications
const notificationVariants = {
  initial: { height: 0, opacity: 0, y: -10, overflow: 'hidden' },
  animate: { height: 'auto', opacity: 1, y: 0, transition: { duration: 0.3 } },
  exit: { height: 0, opacity: 0, y: -10, overflow: 'hidden', transition: { duration: 0.2 } }
};

// Pulse animation for the connection indicator
const pulseVariants = {
  pulse: {
    scale: [1, 1.05, 1],
    opacity: [1, 0.8, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      repeatType: 'reverse'
    }
  }
};

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
  
  // Previous count for animation
  const [prevCount, setPrevCount] = useState(runningOpsCount);
  
  // Update previous count for animation when it changes
  useEffect(() => {
    if (prevCount !== runningOpsCount) {
      setPrevCount(runningOpsCount);
    }
  }, [runningOpsCount]);
  
  return (
    <div className="websocket-status-indicator mb-3">
      <AnimatePresence mode="wait">
        <div className="d-flex align-items-center">
          {connectionError ? (
            <motion.div
              key="disconnected"
              variants={badgeVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <Badge color="danger" pill className="px-3 py-2">
                <motion.span
                  animate={{ x: [0, -3, 3, -3, 0] }}
                  transition={{ duration: 0.5 }}
                >
                  Disconnected
                </motion.span>
              </Badge>
            </motion.div>
          ) : isConnected ? (
            <motion.div
              key="connected"
              variants={badgeVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <Badge color="success" pill className="px-3 py-2 d-flex align-items-center">
                <motion.span
                  className="me-1"
                  variants={pulseVariants}
                  animate="pulse"
                >
                  Connected
                </motion.span>
                <AnimatePresence>
                  {runningOpsCount > 0 && (
                    <motion.div
                      key="active-count"
                      initial={{ scale: 0.5, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.5, opacity: 0 }}
                      transition={{ type: 'spring', stiffness: 400, damping: 10 }}
                    >
                      <Badge color="light" pill className="ms-1 text-dark">
                        <AnimatedCount value={runningOpsCount} /> active
                      </Badge>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Badge>
            </motion.div>
          ) : (
            <motion.div
              key="connecting"
              variants={badgeVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <Badge color="warning" pill className="px-3 py-2 d-flex align-items-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="me-2"
                >
                  <Spinner size="sm" />
                </motion.div>
                Connecting...
              </Badge>
            </motion.div>
          )}
        </div>
      </AnimatePresence>
      
      {showNotifications && (
        <div className="mt-2">
          <AnimatePresence>
            {notifications.slice(0, maxNotifications).map((notification, index) => (
              <motion.div
                key={`${notification.event_id || index}-${notification.timestamp || Date.now()}`}
                variants={notificationVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                layout
              >
                <Alert
                  color={
                    notification.severity === 'error' || notification.severity === 'critical'
                      ? 'danger'
                      : notification.severity === 'warning'
                      ? 'warning'
                      : 'info'
                  }
                  className="p-2 mb-2"
                >
                  <motion.small
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.3, delay: 0.1 }}
                  >
                    {notification.description || notification.event_type}
                  </motion.small>
                </Alert>
              </motion.div>
            ))}
          </AnimatePresence>
          
          <AnimatePresence>
            {notifications.length > maxNotifications && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                transition={{ duration: 0.3 }}
              >
                <small className="text-muted">
                  +<AnimatedCount value={notifications.length - maxNotifications} /> more notifications
                </small>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default WebSocketStatusIndicator;