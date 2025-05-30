import React, { useState, useEffect } from 'react';
import {
  Container,
  Row,
  Col,
  Card,
  CardHeader,
  CardBody,
  Table,
  Badge,
  Button,
  Alert,
  Spinner,
  Form,
  FormGroup,
  Input,
  Label,
  Pagination,
  PaginationItem,
  PaginationLink
} from 'reactstrap';
import { motion, AnimatePresence } from 'framer-motion';
import SyncStatus from './SyncStatus';
import {
  AnimatedCard,
  AnimatedBadge,
  AnimatedButton,
  AnimatedAlert,
  AnimatedTableRow,
  AnimatedSpinner,
  AnimatedCount,
  DataRefreshIndicator,
  AnimatedNotification
} from './AnimatedElements';

const statusColors = {
  completed: 'success',
  running: 'primary',
  pending: 'warning',
  failed: 'danger',
  cancelled: 'secondary'
};

const SyncOperations = () => {
  const [operations, setOperations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedOperation, setSelectedOperation] = useState(null);
  const [filters, setFilters] = useState({
    status: '',
    syncType: '',
    fromDate: '',
    toDate: ''
  });
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0,
    totalPages: 0
  });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState({ show: false, message: '', type: 'info' });

  // Show a notification
  const showNotification = (message, type = 'info') => {
    setNotification({ show: true, message, type });
    // Auto-hide notification after 4 seconds
    setTimeout(() => {
      setNotification(prev => ({ ...prev, show: false }));
    }, 4000);
  };

  // Fetch operations data
  const fetchOperations = async () => {
    try {
      if (operations.length === 0) {
        setLoading(true);
      } else {
        setIsRefreshing(true);
      }
      
      // Build query parameters
      const queryParams = new URLSearchParams();
      queryParams.append('page', pagination.page);
      queryParams.append('limit', pagination.limit);
      
      if (filters.status) {
        queryParams.append('status', filters.status);
      }
      
      if (filters.syncType) {
        queryParams.append('sync_type', filters.syncType);
      }
      
      if (filters.fromDate) {
        queryParams.append('from_date', filters.fromDate);
      }
      
      if (filters.toDate) {
        queryParams.append('to_date', filters.toDate);
      }
      
      const response = await fetch(`/api/operations?${queryParams.toString()}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      const data = await response.json();
      const newOperations = data.items || data.operations || data;
      
      // Check if there are new operations or status changes
      const hasChanges = operations.length !== newOperations.length || 
                        newOperations.some((newOp, idx) => 
                          idx >= operations.length || 
                          operations[idx].status !== newOp.status ||
                          operations[idx].processed_records !== newOp.processed_records
                        );
      
      setOperations(newOperations);
      
      // Update pagination if provided
      if (data.pagination) {
        setPagination({
          page: data.pagination.page,
          limit: data.pagination.limit,
          total: data.pagination.totalCount,
          totalPages: data.pagination.totalPages
        });
      }
      
      setError(null);
      
      // Show notification if there are significant changes
      if (hasChanges && operations.length > 0) {
        const newCompleted = newOperations.filter(op => op.status === 'completed' && 
          !operations.some(oldOp => oldOp.operation_id === op.operation_id && oldOp.status === 'completed'));
        
        const newFailed = newOperations.filter(op => op.status === 'failed' && 
          !operations.some(oldOp => oldOp.operation_id === op.operation_id && oldOp.status === 'failed'));
        
        if (newCompleted.length > 0) {
          showNotification(`${newCompleted.length} operation(s) completed successfully!`, 'success');
        } else if (newFailed.length > 0) {
          showNotification(`${newFailed.length} operation(s) failed.`, 'danger');
        } else if (hasChanges) {
          showNotification('Operations updated', 'info');
        }
      }
    } catch (err) {
      setError(`Failed to fetch operations: ${err.message}`);
      showNotification(`Failed to fetch operations: ${err.message}`, 'danger');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  // Start a new sync operation
  const startSync = async (syncType, syncPairId) => {
    try {
      setIsRefreshing(true);
      showNotification(`Starting ${syncType} sync...`, 'info');
      
      const response = await fetch(`/api/sync/${syncPairId}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sync_type: syncType,
          hours: syncType === 'incremental' ? 24 : undefined
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      const data = await response.json();
      
      // Refresh operations list
      await fetchOperations();
      
      // Select the new operation
      setSelectedOperation(data.operation_id);
      
      showNotification('Sync operation started successfully!', 'success');
      
      return data;
    } catch (err) {
      setError(`Failed to start sync operation: ${err.message}`);
      showNotification(`Failed to start sync operation: ${err.message}`, 'danger');
      return null;
    } finally {
      setIsRefreshing(false);
    }
  };

  // Handle filter changes
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Apply filters
  const applyFilters = (e) => {
    e.preventDefault();
    setPagination(prev => ({
      ...prev,
      page: 1 // Reset to first page when filtering
    }));
    fetchOperations();
    showNotification('Filters applied', 'info');
  };

  // Reset filters
  const resetFilters = () => {
    setFilters({
      status: '',
      syncType: '',
      fromDate: '',
      toDate: ''
    });
    setPagination(prev => ({
      ...prev,
      page: 1
    }));
    fetchOperations();
    showNotification('Filters reset', 'info');
  };

  // Pagination change handler
  const handlePageChange = (page) => {
    setPagination(prev => ({
      ...prev,
      page
    }));
  };

  // Initial data fetch
  useEffect(() => {
    fetchOperations();
    
    // Set up auto-refresh for active operations
    const intervalId = setInterval(() => {
      // Only auto-refresh if there are running operations and not already loading
      if (!loading && !isRefreshing && operations.some(op => op.status === 'running' || op.status === 'pending')) {
        fetchOperations();
      }
    }, 10000); // Refresh every 10 seconds
    
    return () => clearInterval(intervalId);
  }, [pagination.page, pagination.limit]);
  
  // Effect for filter changes
  useEffect(() => {
    if (!loading && !isRefreshing) {
      fetchOperations();
    }
  }, [pagination.page, pagination.limit]);

  return (
    <Container className="my-4">
      <motion.h2 
        className="mb-4"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        Sync Operations
      </motion.h2>
      
      <DataRefreshIndicator isRefreshing={isRefreshing} />
      
      <AnimatedNotification 
        message={notification.message}
        type={notification.type}
        isVisible={notification.show}
        onClose={() => setNotification(prev => ({ ...prev, show: false }))}
      />
      
      {/* Error alert */}
      <AnimatePresence>
        {error && (
          <AnimatedAlert color="danger" className="mb-4">
            {error}
            <AnimatedButton color="link" onClick={fetchOperations} className="p-0 ms-2">
              Retry
            </AnimatedButton>
          </AnimatedAlert>
        )}
      </AnimatePresence>
      
      <Row>
        {/* Filters panel */}
        <Col md={4} lg={3}>
          <AnimatedCard className="mb-4" delay={0.1}>
            <CardHeader>
              <motion.h5 
                className="mb-0"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                Filters
              </motion.h5>
            </CardHeader>
            <CardBody>
              <Form onSubmit={applyFilters}>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.1 }}
                >
                  <FormGroup>
                    <Label for="status">Status</Label>
                    <Input
                      type="select"
                      name="status"
                      id="status"
                      value={filters.status}
                      onChange={handleFilterChange}
                    >
                      <option value="">All</option>
                      <option value="completed">Completed</option>
                      <option value="running">Running</option>
                      <option value="pending">Pending</option>
                      <option value="failed">Failed</option>
                      <option value="cancelled">Cancelled</option>
                    </Input>
                  </FormGroup>
                </motion.div>
                
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.2 }}
                >
                  <FormGroup>
                    <Label for="syncType">Sync Type</Label>
                    <Input
                      type="select"
                      name="syncType"
                      id="syncType"
                      value={filters.syncType}
                      onChange={handleFilterChange}
                    >
                      <option value="">All</option>
                      <option value="incremental">Incremental</option>
                      <option value="full">Full</option>
                    </Input>
                  </FormGroup>
                </motion.div>
                
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.3 }}
                >
                  <FormGroup>
                    <Label for="fromDate">From Date</Label>
                    <Input
                      type="date"
                      name="fromDate"
                      id="fromDate"
                      value={filters.fromDate}
                      onChange={handleFilterChange}
                    />
                  </FormGroup>
                </motion.div>
                
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.4 }}
                >
                  <FormGroup>
                    <Label for="toDate">To Date</Label>
                    <Input
                      type="date"
                      name="toDate"
                      id="toDate"
                      value={filters.toDate}
                      onChange={handleFilterChange}
                    />
                  </FormGroup>
                </motion.div>
                
                <motion.div 
                  className="d-flex justify-content-between"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.5 }}
                >
                  <AnimatedButton color="primary" type="submit">
                    Apply
                  </AnimatedButton>
                  <AnimatedButton color="secondary" type="button" onClick={resetFilters}>
                    Reset
                  </AnimatedButton>
                </motion.div>
              </Form>
            </CardBody>
          </AnimatedCard>
          
          {/* Start New Sync card */}
          <AnimatedCard className="mb-4" delay={0.3}>
            <CardHeader>
              <motion.h5 
                className="mb-0"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                Start New Sync
              </motion.h5>
            </CardHeader>
            <CardBody>
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 }}
              >
                <FormGroup>
                  <Label for="newSyncType">Sync Type</Label>
                  <Input
                    type="select"
                    name="newSyncType"
                    id="newSyncType"
                  >
                    <option value="incremental">Incremental</option>
                    <option value="full">Full</option>
                  </Input>
                </FormGroup>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.2 }}
              >
                <FormGroup>
                  <Label for="syncPair">Sync Pair</Label>
                  <Input
                    type="select"
                    name="syncPair"
                    id="syncPair"
                  >
                    <option value="1">PACS-CAMA Integration</option>
                    <option value="2">GIS-ERP Integration</option>
                  </Input>
                </FormGroup>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.3 }}
              >
                <AnimatedButton
                  color="success"
                  block
                  onClick={() => {
                    const syncType = document.getElementById('newSyncType').value;
                    const syncPairId = document.getElementById('syncPair').value;
                    startSync(syncType, syncPairId);
                  }}
                >
                  Start Sync
                </AnimatedButton>
              </motion.div>
            </CardBody>
          </AnimatedCard>
        </Col>
        
        {/* Main content */}
        <Col md={8} lg={9}>
          {/* Selected operation details */}
          <AnimatePresence>
            {selectedOperation && (
              <motion.div 
                className="mb-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <motion.h4
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: 0.1 }}
                  >
                    Operation Details
                  </motion.h4>
                  <AnimatedButton
                    color="link" 
                    className="p-0" 
                    onClick={() => setSelectedOperation(null)}
                  >
                    Close
                  </AnimatedButton>
                </div>
                <SyncStatus operationId={selectedOperation} />
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Operations list */}
          <AnimatedCard>
            <CardHeader className="d-flex justify-content-between align-items-center">
              <motion.h5 
                className="mb-0"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                Operations List
              </motion.h5>
              <AnimatedButton color="primary" size="sm" onClick={fetchOperations}>
                Refresh
              </AnimatedButton>
            </CardHeader>
            <CardBody>
              {loading && operations.length === 0 ? (
                <div className="d-flex justify-content-center my-5">
                  <AnimatedSpinner color="primary" />
                </div>
              ) : operations.length === 0 ? (
                <AnimatedAlert color="info">
                  No operations found. Try adjusting your filters or start a new sync operation.
                </AnimatedAlert>
              ) : (
                <>
                  <motion.div 
                    className="table-responsive"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.3 }}
                  >
                    <Table className="table-striped table-hover">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Status</th>
                          <th>Type</th>
                          <th>Started</th>
                          <th>Processed</th>
                          <th>Success Rate</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        <AnimatePresence>
                          {operations.map((op, index) => (
                            <AnimatedTableRow key={op.operation_id} index={index}>
                              <td>{op.operation_id}</td>
                              <td>
                                <AnimatedBadge color={statusColors[op.status] || 'secondary'}>
                                  {op.status}
                                </AnimatedBadge>
                              </td>
                              <td>{op.sync_type}</td>
                              <td>{new Date(op.started_at).toLocaleString()}</td>
                              <td>
                                <AnimatedCount value={op.processed_records} /> / {op.total_records}
                              </td>
                              <td>
                                <AnimatedCount
                                  value={
                                    op.processed_records > 0
                                      ? Math.round((op.successful_records / op.processed_records) * 100)
                                      : 0
                                  }
                                />%
                              </td>
                              <td>
                                <AnimatedButton
                                  color="info"
                                  size="sm"
                                  onClick={() => setSelectedOperation(op.operation_id)}
                                >
                                  Details
                                </AnimatedButton>
                              </td>
                            </AnimatedTableRow>
                          ))}
                        </AnimatePresence>
                      </tbody>
                    </Table>
                  </motion.div>
                  
                  {/* Pagination */}
                  {pagination.totalPages > 1 && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: 0.3 }}
                    >
                      <Pagination className="d-flex justify-content-center mt-4">
                        <PaginationItem disabled={pagination.page === 1}>
                          <PaginationLink previous onClick={() => handlePageChange(pagination.page - 1)} />
                        </PaginationItem>
                        
                        {[...Array(pagination.totalPages).keys()].map(i => (
                          <PaginationItem key={i} active={i + 1 === pagination.page}>
                            <PaginationLink onClick={() => handlePageChange(i + 1)}>
                              {i + 1}
                            </PaginationLink>
                          </PaginationItem>
                        ))}
                        
                        <PaginationItem disabled={pagination.page === pagination.totalPages}>
                          <PaginationLink next onClick={() => handlePageChange(pagination.page + 1)} />
                        </PaginationItem>
                      </Pagination>
                    </motion.div>
                  )}
                </>
              )}
            </CardBody>
          </AnimatedCard>
        </Col>
      </Row>
    </Container>
  );
};

export default SyncOperations;