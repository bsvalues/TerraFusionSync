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
import SyncStatus from './SyncStatus';

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

  // Fetch operations data
  const fetchOperations = async () => {
    try {
      setLoading(true);
      
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
      setOperations(data.items || data.operations || data);
      
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
    } catch (err) {
      setError(`Failed to fetch operations: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Start a new sync operation
  const startSync = async (syncType, syncPairId) => {
    try {
      setLoading(true);
      
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
      fetchOperations();
      
      // Select the new operation
      setSelectedOperation(data.operation_id);
      
      return data;
    } catch (err) {
      setError(`Failed to start sync operation: ${err.message}`);
      return null;
    } finally {
      setLoading(false);
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
      if (!loading && operations.some(op => op.status === 'running' || op.status === 'pending')) {
        fetchOperations();
      }
    }, 10000); // Refresh every 10 seconds
    
    return () => clearInterval(intervalId);
  }, [pagination.page, pagination.limit]);
  
  // Effect for filter changes
  useEffect(() => {
    if (!loading) {
      fetchOperations();
    }
  }, [pagination.page, pagination.limit]);

  return (
    <Container className="my-4">
      <h2 className="mb-4">Sync Operations</h2>
      
      {/* Error alert */}
      {error && (
        <Alert color="danger" className="mb-4">
          {error}
          <Button color="link" onClick={fetchOperations} className="p-0 ms-2">
            Retry
          </Button>
        </Alert>
      )}
      
      <Row>
        {/* Filters panel */}
        <Col md={4} lg={3}>
          <Card className="mb-4 shadow-sm">
            <CardHeader>
              <h5 className="mb-0">Filters</h5>
            </CardHeader>
            <CardBody>
              <Form onSubmit={applyFilters}>
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
                
                <div className="d-flex justify-content-between">
                  <Button color="primary" type="submit">
                    Apply
                  </Button>
                  <Button color="secondary" type="button" onClick={resetFilters}>
                    Reset
                  </Button>
                </div>
              </Form>
            </CardBody>
          </Card>
          
          {/* Start New Sync card */}
          <Card className="mb-4 shadow-sm">
            <CardHeader>
              <h5 className="mb-0">Start New Sync</h5>
            </CardHeader>
            <CardBody>
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
              
              <Button
                color="success"
                block
                onClick={() => {
                  const syncType = document.getElementById('newSyncType').value;
                  const syncPairId = document.getElementById('syncPair').value;
                  startSync(syncType, syncPairId);
                }}
              >
                Start Sync
              </Button>
            </CardBody>
          </Card>
        </Col>
        
        {/* Main content */}
        <Col md={8} lg={9}>
          {/* Selected operation details */}
          {selectedOperation && (
            <div className="mb-4">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h4>Operation Details</h4>
                <Button 
                  color="link" 
                  className="p-0" 
                  onClick={() => setSelectedOperation(null)}
                >
                  Close
                </Button>
              </div>
              <SyncStatus operationId={selectedOperation} />
            </div>
          )}
          
          {/* Operations list */}
          <Card className="shadow-sm">
            <CardHeader className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Operations List</h5>
              <Button color="primary" size="sm" onClick={fetchOperations}>
                Refresh
              </Button>
            </CardHeader>
            <CardBody>
              {loading && operations.length === 0 ? (
                <div className="d-flex justify-content-center my-5">
                  <Spinner color="primary" />
                </div>
              ) : operations.length === 0 ? (
                <Alert color="info">
                  No operations found. Try adjusting your filters or start a new sync operation.
                </Alert>
              ) : (
                <>
                  <div className="table-responsive">
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
                        {operations.map(op => (
                          <tr key={op.operation_id}>
                            <td>{op.operation_id}</td>
                            <td>
                              <Badge color={statusColors[op.status] || 'secondary'}>
                                {op.status}
                              </Badge>
                            </td>
                            <td>{op.sync_type}</td>
                            <td>{new Date(op.started_at).toLocaleString()}</td>
                            <td>
                              {op.processed_records} / {op.total_records}
                            </td>
                            <td>
                              {op.processed_records > 0
                                ? Math.round((op.successful_records / op.processed_records) * 100)
                                : 0}%
                            </td>
                            <td>
                              <Button
                                color="info"
                                size="sm"
                                onClick={() => setSelectedOperation(op.operation_id)}
                              >
                                Details
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                  
                  {/* Pagination */}
                  {pagination.totalPages > 1 && (
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
                  )}
                </>
              )}
            </CardBody>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default SyncOperations;