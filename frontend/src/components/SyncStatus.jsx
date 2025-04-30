import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardBody, 
  Progress, 
  Badge, 
  Button, 
  Alert,
  Spinner,
  Container,
  Row,
  Col
} from 'reactstrap';

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

  // Fetch operation data
  const fetchOperation = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/operations/${operationId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      const data = await response.json();
      setOperation(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(`Failed to fetch operation data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Retry failed operation
  const handleRetry = async () => {
    try {
      const response = await fetch(`/api/operations/${operationId}/retry`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      // Refresh operation data
      fetchOperation();
    } catch (err) {
      setError(`Failed to retry operation: ${err.message}`);
    }
  };

  // Cancel running operation
  const handleCancel = async () => {
    try {
      const response = await fetch(`/api/operations/${operationId}/cancel`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      // Refresh operation data
      fetchOperation();
    } catch (err) {
      setError(`Failed to cancel operation: ${err.message}`);
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
        <Spinner color="primary" />
      </Container>
    );
  }

  if (error && !operation) {
    return (
      <Alert color="danger">
        {error}
        <Button color="link" onClick={fetchOperation} className="ms-2">
          Retry
        </Button>
      </Alert>
    );
  }

  if (!operation) {
    return (
      <Alert color="warning">
        Operation not found or data unavailable.
      </Alert>
    );
  }

  const progress = operation.processed_records > 0 && operation.total_records > 0
    ? Math.round((operation.processed_records / operation.total_records) * 100)
    : 0;

  return (
    <Card className="mb-4 shadow-sm">
      <CardHeader className="d-flex justify-content-between align-items-center">
        <h5 className="mb-0">Sync Operation: {operation.name || operation.operation_id}</h5>
        <Badge color={statusColors[operation.status] || 'secondary'}>
          {operation.status}
        </Badge>
      </CardHeader>
      <CardBody>
        {error && (
          <Alert color="danger" className="mb-3">
            {error}
          </Alert>
        )}
        
        <Row className="mb-3">
          <Col md={6}>
            <p className="mb-1">
              <strong>Sync Type:</strong> {operation.sync_type}
            </p>
            <p className="mb-1">
              <strong>Started:</strong> {new Date(operation.started_at).toLocaleString()}
            </p>
            {operation.completed_at && (
              <p className="mb-1">
                <strong>Completed:</strong> {new Date(operation.completed_at).toLocaleString()}
              </p>
            )}
          </Col>
          <Col md={6}>
            <p className="mb-1">
              <strong>Records Processed:</strong> {operation.processed_records} / {operation.total_records}
            </p>
            <p className="mb-1">
              <strong>Success Rate:</strong> {
                operation.processed_records > 0
                  ? Math.round((operation.successful_records / operation.processed_records) * 100)
                  : 0
              }%
            </p>
            <p className="mb-1">
              <strong>Failed Records:</strong> {operation.failed_records}
            </p>
          </Col>
        </Row>
        
        <div className="mb-3">
          <div className="d-flex justify-content-between mb-1">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <Progress value={progress} />
        </div>
        
        <div className="d-flex justify-content-between">
          <div>
            {operation.status === 'failed' && (
              <Button color="warning" onClick={handleRetry}>
                Retry Operation
              </Button>
            )}
            {(operation.status === 'running' || operation.status === 'pending') && (
              <Button color="danger" onClick={handleCancel}>
                Cancel Operation
              </Button>
            )}
          </div>
          <div>
            <small className="text-muted">
              Last updated: {lastUpdated ? lastUpdated.toLocaleString() : 'Never'}
            </small>
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default SyncStatus;