import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardBody, 
  Badge, 
  Button, 
  Alert,
  Spinner,
  Container,
  Row,
  Col
} from 'reactstrap';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AnimatedBadge, 
  AnimatedButton, 
  AnimatedAlert, 
  AnimatedProgress,
  AnimatedSpinner,
  AnimatedCard,
  AnimatedCount,
  DataRefreshIndicator
} from './AnimatedElements';

const statusColors = {
  completed: 'success',
  running: 'primary',
  pending: 'warning',
  failed: 'danger',
  cancelled: 'secondary'
};

const SyncStatus = ({ operationId, refreshInterval = 5000 }) => {
  const [operation, setOperation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState({ show: false, message: '', type: 'info' });

  // Fetch operation data
  const fetchOperation = async () => {
    try {
      // Don't set loading on refresh if we already have data
      if (!operation) {
        setLoading(true);
      } else {
        setIsRefreshing(true);
      }
      
      const response = await fetch(`/api/operations/${operationId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      const data = await response.json();
      
      // Check if the data has actually changed
      const hasChanged = !operation || 
                         operation.status !== data.status || 
                         operation.processed_records !== data.processed_records;
      
      setOperation(data);
      setLastUpdated(new Date());
      setError(null);
      
      // Show a notification if data has changed significantly
      if (operation && hasChanged) {
        if (data.status === 'completed' && operation.status !== 'completed') {
          showNotification('Operation completed successfully!', 'success');
        } else if (data.status === 'failed' && operation.status !== 'failed') {
          showNotification('Operation failed.', 'danger');
        }
      }
    } catch (err) {
      setError(`Failed to fetch operation data: ${err.message}`);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  // Show a notification
  const showNotification = (message, type = 'info') => {
    setNotification({ show: true, message, type });
    // Auto-hide notification after 4 seconds
    setTimeout(() => {
      setNotification(prev => ({ ...prev, show: false }));
    }, 4000);
  };

  // Retry failed operation
  const handleRetry = async () => {
    try {
      setIsRefreshing(true);
      showNotification('Retrying operation...', 'info');
      
      const response = await fetch(`/api/operations/${operationId}/retry`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      // Refresh operation data
      await fetchOperation();
      showNotification('Operation retry initiated successfully', 'success');
    } catch (err) {
      setError(`Failed to retry operation: ${err.message}`);
      showNotification('Failed to retry operation', 'danger');
    } finally {
      setIsRefreshing(false);
    }
  };

  // Cancel running operation
  const handleCancel = async () => {
    try {
      setIsRefreshing(true);
      showNotification('Cancelling operation...', 'warning');
      
      const response = await fetch(`/api/operations/${operationId}/cancel`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      // Refresh operation data
      await fetchOperation();
      showNotification('Operation cancelled successfully', 'success');
    } catch (err) {
      setError(`Failed to cancel operation: ${err.message}`);
      showNotification('Failed to cancel operation', 'danger');
    } finally {
      setIsRefreshing(false);
    }
  };

  // Initial fetch and setup interval for auto-refresh
  useEffect(() => {
    fetchOperation();
    
    // Set up auto-refresh interval
    const intervalId = setInterval(() => {
      if (operation?.status === 'running' || operation?.status === 'pending') {
        fetchOperation();
      }
    }, refreshInterval);
    
    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, [operationId, refreshInterval, operation?.status]);

  if (loading && !operation) {
    return (
      <Container className="d-flex justify-content-center my-5">
        <AnimatedSpinner color="primary" />
      </Container>
    );
  }

  if (error && !operation) {
    return (
      <AnimatedAlert color="danger">
        {error}
        <AnimatedButton color="link" onClick={fetchOperation} className="ms-2">
          Retry
        </AnimatedButton>
      </AnimatedAlert>
    );
  }

  if (!operation) {
    return (
      <AnimatedAlert color="warning">
        Operation not found or data unavailable.
      </AnimatedAlert>
    );
  }

  const progress = operation.processed_records > 0 && operation.total_records > 0
    ? Math.round((operation.processed_records / operation.total_records) * 100)
    : 0;

  return (
    <>
      <DataRefreshIndicator isRefreshing={isRefreshing} />
      
      <AnimatedNotification 
        message={notification.message}
        type={notification.type}
        isVisible={notification.show}
        onClose={() => setNotification(prev => ({ ...prev, show: false }))}
      />
      
      <AnimatedCard className="mb-4">
        <CardHeader className="d-flex justify-content-between align-items-center">
          <motion.h5 
            className="mb-0"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            Sync Operation: {operation.name || operation.operation_id}
          </motion.h5>
          <AnimatedBadge color={statusColors[operation.status] || 'secondary'}>
            {operation.status}
          </AnimatedBadge>
        </CardHeader>
        <CardBody>
          <AnimatePresence>
            {error && (
              <AnimatedAlert color="danger" className="mb-3">
                {error}
              </AnimatedAlert>
            )}
          </AnimatePresence>
          
          <Row className="mb-3">
            <Col md={6}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 }}
              >
                <p className="mb-1">
                  <strong>Sync Type:</strong> {operation.sync_type}
                </p>
                <p className="mb-1">
                  <strong>Started:</strong> {new Date(operation.started_at).toLocaleString()}
                </p>
                <AnimatePresence>
                  {operation.completed_at && (
                    <motion.p 
                      className="mb-1"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <strong>Completed:</strong> {new Date(operation.completed_at).toLocaleString()}
                    </motion.p>
                  )}
                </AnimatePresence>
              </motion.div>
            </Col>
            <Col md={6}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.2 }}
              >
                <p className="mb-1">
                  <strong>Records Processed:</strong>{' '}
                  <AnimatedCount value={operation.processed_records} /> / {operation.total_records}
                </p>
                <p className="mb-1">
                  <strong>Success Rate:</strong>{' '}
                  <AnimatedCount
                    value={
                      operation.processed_records > 0
                        ? Math.round((operation.successful_records / operation.processed_records) * 100)
                        : 0
                    }
                  />%
                </p>
                <p className="mb-1">
                  <strong>Failed Records:</strong>{' '}
                  <AnimatedCount value={operation.failed_records} />
                </p>
              </motion.div>
            </Col>
          </Row>
          
          <motion.div 
            className="mb-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.3 }}
          >
            <div className="d-flex justify-content-between mb-1">
              <span>Progress</span>
              <AnimatedCount value={progress} />%
            </div>
            <AnimatedProgress value={progress} color={statusColors[operation.status] || 'primary'} />
          </motion.div>
          
          <motion.div 
            className="d-flex justify-content-between"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            <div>
              <AnimatePresence>
                {operation.status === 'failed' && (
                  <AnimatedButton color="warning" onClick={handleRetry}>
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    >
                      Retry Operation
                    </motion.span>
                  </AnimatedButton>
                )}
                {(operation.status === 'running' || operation.status === 'pending') && (
                  <AnimatedButton color="danger" onClick={handleCancel}>
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    >
                      Cancel Operation
                    </motion.span>
                  </AnimatedButton>
                )}
              </AnimatePresence>
            </div>
            <div>
              <motion.small 
                className="text-muted"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                Last updated: {lastUpdated ? lastUpdated.toLocaleString() : 'Never'}
              </motion.small>
            </div>
          </motion.div>
        </CardBody>
      </AnimatedCard>
    </>
  );
};

export default SyncStatus;