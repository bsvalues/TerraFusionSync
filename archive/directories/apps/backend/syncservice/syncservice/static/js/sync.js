/**
 * TerraFusion SyncService
 * Sync Operations script
 */

// Configuration
const config = {
    api: {
        syncOperations: '/api/sync/operations',
        syncOperation: '/api/sync/operation',
        syncActive: '/api/sync/active',
        syncStart: '/api/sync',
        syncPairs: '/api/compatibility/pairs',
        syncCancel: '/api/sync/cancel'
    },
    refreshInterval: 10000 // 10 seconds
};

// Operation data store
let operationsData = {
    lastUpdated: null,
    operations: [],
    activeOperations: [],
    syncPairs: [],
    filter: {
        status: 'all',
        syncPair: 'all'
    }
};

// Pagination state
let paginationState = {
    currentPage: 1,
    totalPages: 1,
    pageSize: 10,
    totalResults: 0
};

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    initializePage();
});

/**
 * Initialize the page components
 */
async function initializePage() {
    // Set up event listeners
    setupEventListeners();
    
    // Check for operation query parameter
    const urlParams = new URLSearchParams(window.location.search);
    const operationId = urlParams.get('operation');
    
    // Initial data load
    await Promise.all([
        fetchSyncPairs(),
        fetchSyncOperations()
    ]);
    
    // If operation ID is provided, open the details modal
    if (operationId) {
        showOperationDetails(operationId);
    }
    
    // Set up periodic refresh
    setInterval(refreshOperations, config.refreshInterval);
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Filter change events
    document.getElementById('filter-status').addEventListener('change', handleFilterChange);
    document.getElementById('filter-sync-pair').addEventListener('change', handleFilterChange);
    
    // Refresh button
    document.getElementById('refresh-operations').addEventListener('click', refreshOperations);
    
    // Export buttons
    document.getElementById('export-csv').addEventListener('click', () => exportData('csv'));
    document.getElementById('export-json').addEventListener('click', () => exportData('json'));
    
    // Start sync form events
    document.getElementById('sync-type').addEventListener('change', function() {
        const hoursContainer = document.getElementById('hours-container');
        hoursContainer.style.display = this.value === 'incremental' ? 'block' : 'none';
    });
    
    document.getElementById('submit-sync').addEventListener('click', startNewSync);
    
    // Cancel operation button
    document.getElementById('cancel-operation').addEventListener('click', cancelOperation);
}

/**
 * Handle filter change event
 */
function handleFilterChange() {
    // Update filter state
    operationsData.filter.status = document.getElementById('filter-status').value;
    operationsData.filter.syncPair = document.getElementById('filter-sync-pair').value;
    
    // Reset pagination
    paginationState.currentPage = 1;
    
    // Reload operations with new filter
    fetchSyncOperations();
}

/**
 * Fetch sync pairs from the API
 */
async function fetchSyncPairs() {
    try {
        const response = await fetch(config.api.syncPairs);
        if (!response.ok) {
            throw new Error(`Failed to fetch sync pairs: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        operationsData.syncPairs = data.pairs || [];
        
        // Update sync pair dropdown options
        updateSyncPairOptions();
    } catch (error) {
        console.error('Error fetching sync pairs:', error);
        showError(`Failed to fetch sync pairs: ${error.message}`);
    }
}

/**
 * Update sync pair dropdown options
 */
function updateSyncPairOptions() {
    const filterSelect = document.getElementById('filter-sync-pair');
    const startSelect = document.getElementById('sync-pair-id');
    
    // Keep the 'all' option
    filterSelect.innerHTML = '<option value="all">All Sync Pairs</option>';
    
    // Clear start select
    startSelect.innerHTML = '<option value="">Select a sync pair</option>';
    
    // Add options for each sync pair
    operationsData.syncPairs.forEach(pair => {
        // Add to filter dropdown
        const filterOption = document.createElement('option');
        filterOption.value = pair.id;
        filterOption.textContent = `${pair.source_system} → ${pair.target_system}`;
        filterSelect.appendChild(filterOption);
        
        // Add to start sync dropdown
        const startOption = document.createElement('option');
        startOption.value = pair.id;
        startOption.textContent = `${pair.source_system} → ${pair.target_system}`;
        startSelect.appendChild(startOption);
    });
}

/**
 * Fetch sync operations from the API
 */
async function fetchSyncOperations() {
    // Show loading state
    document.body.classList.add('loading');
    
    try {
        // Build query parameters
        const params = new URLSearchParams({
            limit: paginationState.pageSize,
            offset: (paginationState.currentPage - 1) * paginationState.pageSize
        });
        
        // Add filter parameters if not 'all'
        if (operationsData.filter.status !== 'all') {
            params.append('status', operationsData.filter.status);
        }
        
        if (operationsData.filter.syncPair !== 'all') {
            params.append('sync_pair_id', operationsData.filter.syncPair);
        }
        
        // Fetch operations
        const operationsResponse = await fetch(`${config.api.syncOperations}?${params.toString()}`);
        if (!operationsResponse.ok) {
            throw new Error(`Failed to fetch operations: ${operationsResponse.status} ${operationsResponse.statusText}`);
        }
        
        const operationsData = await operationsResponse.json();
        
        // Fetch active operations
        const activeResponse = await fetch(config.api.syncActive);
        if (!activeResponse.ok) {
            throw new Error(`Failed to fetch active operations: ${activeResponse.status} ${activeResponse.statusText}`);
        }
        
        const activeData = await activeResponse.json();
        
        // Update data store
        updateOperationsData(operationsData, activeData);
        
        // Update the UI
        updateOperationsTable();
        updatePagination();
        
        // Hide any previous errors
        document.getElementById('errorAlert').classList.add('d-none');
    } catch (error) {
        console.error('Error fetching operations:', error);
        showError(`Failed to fetch operations: ${error.message}`);
    } finally {
        // Update last updated timestamp
        operationsData.lastUpdated = new Date();
        document.getElementById('last-updated').textContent = formatDateTime(operationsData.lastUpdated);
        
        // Remove loading state
        document.body.classList.remove('loading');
    }
}

/**
 * Update operations data store
 */
function updateOperationsData(operationsData, activeData) {
    // Update operations list
    this.operationsData.operations = operationsData.operations || [];
    
    // Update active operations
    this.operationsData.activeOperations = activeData || [];
    
    // Update pagination state
    paginationState.totalResults = operationsData.total || 0;
    paginationState.totalPages = Math.ceil(paginationState.totalResults / paginationState.pageSize) || 1;
}

/**
 * Update operations table
 */
function updateOperationsTable() {
    const operationsTable = document.getElementById('operations-table');
    const operations = operationsData.operations;
    
    if (operations.length === 0) {
        operationsTable.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-4">
                    <i class="bi bi-info-circle text-muted me-2"></i>
                    No operations found matching the current filters.
                </td>
            </tr>
        `;
        document.getElementById('results-count').textContent = '0';
        return;
    }
    
    // Update results count
    document.getElementById('results-count').textContent = paginationState.totalResults.toString();
    
    // Build the HTML for the table rows
    const rowsHTML = operations.map(op => {
        // Calculate duration
        let duration = 'N/A';
        if (op.completed_at && op.started_at) {
            const startTime = new Date(op.started_at);
            const endTime = new Date(op.completed_at);
            const durationSeconds = (endTime - startTime) / 1000;
            duration = formatDuration(durationSeconds);
        } else if (op.started_at) {
            const startTime = new Date(op.started_at);
            const now = new Date();
            const durationSeconds = (now - startTime) / 1000;
            duration = formatDuration(durationSeconds) + ' (running)';
        }
        
        // Format the records count
        const records = op.records_processed ? op.records_processed.toLocaleString() : 'N/A';
        
        // Determine if the operation is active
        const isActive = operationsData.activeOperations.some(activeOp => activeOp.operation_id === op.operation_id);
        
        // Calculate progress indicator
        let progressHtml = '';
        if (op.status.toLowerCase() === 'running' || op.status.toLowerCase() === 'pending') {
            const progressPercent = op.progress ? Math.round(op.progress * 100) : 0;
            progressHtml = `
                <div class="progress" style="height: 8px;">
                    <div class="progress-bar ${op.status.toLowerCase() === 'pending' ? 'progress-bar-striped' : ''}" 
                         role="progressbar" style="width: ${progressPercent}%"></div>
                </div>
                <div class="small mt-1">${progressPercent}%</div>
            `;
        } else {
            progressHtml = '<span class="text-muted">—</span>';
        }
        
        return `
            <tr>
                <td><a href="#" class="operation-details" data-id="${op.operation_id}">${op.operation_id}</a></td>
                <td>${op.type}</td>
                <td>${op.sync_pair_id}</td>
                <td>${getStatusBadge(op.status)}</td>
                <td>${progressHtml}</td>
                <td>${formatDateTime(op.started_at)}</td>
                <td>${duration}</td>
                <td>${records}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary operation-details" data-id="${op.operation_id}">
                            <i class="bi bi-eye"></i>
                        </button>
                        ${isActive ? `
                            <button class="btn btn-outline-danger cancel-operation" data-id="${op.operation_id}">
                                <i class="bi bi-x-circle"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    operationsTable.innerHTML = rowsHTML;
    
    // Add event listeners to buttons
    document.querySelectorAll('.operation-details').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            showOperationDetails(btn.dataset.id);
        });
    });
    
    document.querySelectorAll('.cancel-operation').forEach(btn => {
        btn.addEventListener('click', () => {
            if (confirm('Are you sure you want to cancel this operation?')) {
                cancelOperationById(btn.dataset.id);
            }
        });
    });
}

/**
 * Update pagination controls
 */
function updatePagination() {
    const pagination = document.querySelector('.pagination');
    
    // If only one page, simplify the pagination
    if (paginationState.totalPages <= 1) {
        pagination.innerHTML = `
            <li class="page-item disabled">
                <a class="page-link" href="#">Previous</a>
            </li>
            <li class="page-item active">
                <a class="page-link" href="#">1</a>
            </li>
            <li class="page-item disabled">
                <a class="page-link" href="#">Next</a>
            </li>
        `;
        return;
    }
    
    // Otherwise, build full pagination
    let paginationHTML = `
        <li class="page-item ${paginationState.currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${paginationState.currentPage - 1}">Previous</a>
        </li>
    `;
    
    // Add page numbers
    for (let i = 1; i <= paginationState.totalPages; i++) {
        // Show current page, first page, last page, and pages around current
        if (i === 1 || i === paginationState.totalPages || 
            (i >= paginationState.currentPage - 1 && i <= paginationState.currentPage + 1)) {
            paginationHTML += `
                <li class="page-item ${i === paginationState.currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        } else if (i === 2 || i === paginationState.totalPages - 1) {
            // Add ellipsis
            paginationHTML += `
                <li class="page-item disabled">
                    <a class="page-link" href="#">...</a>
                </li>
            `;
        }
    }
    
    paginationHTML += `
        <li class="page-item ${paginationState.currentPage === paginationState.totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${paginationState.currentPage + 1}">Next</a>
        </li>
    `;
    
    pagination.innerHTML = paginationHTML;
    
    // Add event listeners to pagination links
    document.querySelectorAll('.pagination .page-link').forEach(link => {
        if (link.hasAttribute('data-page')) {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.dataset.page, 10);
                if (page !== paginationState.currentPage) {
                    paginationState.currentPage = page;
                    fetchSyncOperations();
                }
            });
        }
    });
}

/**
 * Show operation details in modal
 */
async function showOperationDetails(operationId) {
    // Show loading state
    document.body.classList.add('loading');
    
    try {
        // Fetch operation details
        const response = await fetch(`${config.api.syncOperation}/${operationId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch operation details: ${response.status} ${response.statusText}`);
        }
        
        const operation = await response.json();
        
        // Update modal content
        updateOperationDetailsModal(operation);
        
        // Show the modal
        const detailModal = new bootstrap.Modal(document.getElementById('operationDetailModal'));
        detailModal.show();
    } catch (error) {
        console.error('Error fetching operation details:', error);
        showError(`Failed to fetch operation details: ${error.message}`);
    } finally {
        // Remove loading state
        document.body.classList.remove('loading');
    }
}

/**
 * Update operation details modal content
 */
function updateOperationDetailsModal(operation) {
    // Update basic information
    document.getElementById('detail-id').textContent = operation.operation_id;
    document.getElementById('detail-sync-pair').textContent = operation.sync_pair_id;
    document.getElementById('detail-type').textContent = operation.type;
    document.getElementById('detail-status').innerHTML = getStatusBadge(operation.status);
    
    // Update time information
    document.getElementById('detail-started').textContent = formatDateTime(operation.started_at);
    document.getElementById('detail-completed').textContent = operation.completed_at ? formatDateTime(operation.completed_at) : 'In progress';
    
    // Calculate duration
    let duration = 'N/A';
    if (operation.completed_at && operation.started_at) {
        const startTime = new Date(operation.started_at);
        const endTime = new Date(operation.completed_at);
        const durationSeconds = (endTime - startTime) / 1000;
        duration = formatDuration(durationSeconds);
    } else if (operation.started_at) {
        const startTime = new Date(operation.started_at);
        const now = new Date();
        const durationSeconds = (now - startTime) / 1000;
        duration = formatDuration(durationSeconds) + ' (in progress)';
    }
    document.getElementById('detail-duration').textContent = duration;
    
    // Update entity statistics
    updateEntityStatistics(operation);
    
    // Update operation timeline
    updateOperationTimeline(operation);
    
    // Show/hide cancel button
    const cancelBtn = document.getElementById('cancel-operation');
    const isActive = operation.status.toLowerCase() === 'running' || operation.status.toLowerCase() === 'pending';
    cancelBtn.style.display = isActive ? 'inline-block' : 'none';
    
    // Store operation ID in cancel button
    cancelBtn.dataset.id = operation.operation_id;
}

/**
 * Update entity statistics table
 */
function updateEntityStatistics(operation) {
    const entitiesTable = document.getElementById('detail-entities');
    
    if (!operation.entities || Object.keys(operation.entities).length === 0) {
        entitiesTable.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No entity statistics available</td>
            </tr>
        `;
        return;
    }
    
    // Build table rows for each entity type
    const rowsHTML = Object.entries(operation.entities).map(([entityType, stats]) => {
        const processed = stats.processed || 0;
        const created = stats.created || 0;
        const updated = stats.updated || 0;
        const failed = stats.failed || 0;
        const successRate = processed > 0 ? ((processed - failed) / processed * 100).toFixed(1) : '0.0';
        
        return `
            <tr>
                <td>${entityType}</td>
                <td>${processed.toLocaleString()}</td>
                <td>${created.toLocaleString()}</td>
                <td>${updated.toLocaleString()}</td>
                <td>${failed.toLocaleString()}</td>
                <td>${successRate}%</td>
            </tr>
        `;
    }).join('');
    
    // Add total row
    const totalProcessed = Object.values(operation.entities).reduce((sum, stats) => sum + (stats.processed || 0), 0);
    const totalCreated = Object.values(operation.entities).reduce((sum, stats) => sum + (stats.created || 0), 0);
    const totalUpdated = Object.values(operation.entities).reduce((sum, stats) => sum + (stats.updated || 0), 0);
    const totalFailed = Object.values(operation.entities).reduce((sum, stats) => sum + (stats.failed || 0), 0);
    const totalSuccessRate = totalProcessed > 0 ? ((totalProcessed - totalFailed) / totalProcessed * 100).toFixed(1) : '0.0';
    
    const totalRow = `
        <tr class="table-secondary">
            <td><strong>Total</strong></td>
            <td><strong>${totalProcessed.toLocaleString()}</strong></td>
            <td><strong>${totalCreated.toLocaleString()}</strong></td>
            <td><strong>${totalUpdated.toLocaleString()}</strong></td>
            <td><strong>${totalFailed.toLocaleString()}</strong></td>
            <td><strong>${totalSuccessRate}%</strong></td>
        </tr>
    `;
    
    entitiesTable.innerHTML = rowsHTML + totalRow;
}

/**
 * Update operation timeline
 */
function updateOperationTimeline(operation) {
    const timelineContainer = document.getElementById('operation-timeline');
    
    if (!operation.events || operation.events.length === 0) {
        timelineContainer.innerHTML = '<div class="text-center text-muted py-3">No timeline events available</div>';
        return;
    }
    
    // Sort events by timestamp
    const sortedEvents = [...operation.events].sort((a, b) => {
        return new Date(a.timestamp) - new Date(b.timestamp);
    });
    
    // Build timeline HTML
    const timelineHTML = sortedEvents.map(event => {
        // Determine icon and color based on event type
        let iconClass = 'info';
        let icon = 'info-circle';
        
        switch (event.type.toLowerCase()) {
            case 'start':
                iconClass = 'primary';
                icon = 'play-circle';
                break;
            case 'complete':
                iconClass = 'success';
                icon = 'check-circle';
                break;
            case 'error':
                iconClass = 'danger';
                icon = 'exclamation-circle';
                break;
            case 'warning':
                iconClass = 'warning';
                icon = 'exclamation-triangle';
                break;
            case 'progress':
                iconClass = 'info';
                icon = 'arrow-repeat';
                break;
        }
        
        return `
            <div class="timeline-item">
                <div class="timeline-icon bg-${iconClass}">
                    <i class="bi bi-${icon} text-white"></i>
                </div>
                <div class="card mb-0">
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <h6 class="mb-0">${event.title || event.type}</h6>
                            <small class="text-muted">${formatDateTime(event.timestamp)}</small>
                        </div>
                        <p class="mb-0">${event.message || ''}</p>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    timelineContainer.innerHTML = timelineHTML;
}

/**
 * Start a new sync operation
 */
async function startNewSync() {
    // Get form values
    const syncPairId = document.getElementById('sync-pair-id').value;
    const syncType = document.getElementById('sync-type').value;
    const hours = document.getElementById('hours').value;
    
    // Get selected entity types
    const entityTypes = [];
    if (document.getElementById('entity-property').checked) entityTypes.push('property');
    if (document.getElementById('entity-owner').checked) entityTypes.push('owner');
    if (document.getElementById('entity-assessment').checked) entityTypes.push('assessment');
    
    // Validate form
    if (!syncPairId) {
        alert('Please select a sync pair.');
        return;
    }
    
    if (entityTypes.length === 0) {
        alert('Please select at least one entity type.');
        return;
    }
    
    // Prepare request data
    const requestData = {
        sync_pair_id: syncPairId,
        entity_types: entityTypes,
        params: {}
    };
    
    // Add type-specific parameters
    if (syncType === 'incremental') {
        requestData.params.hours = parseInt(hours, 10);
    }
    
    // Show loading state
    document.body.classList.add('loading');
    
    try {
        // Send request to start sync
        const response = await fetch(`${config.api.syncStart}/${syncType}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to start sync: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('startSyncModal'));
        modal.hide();
        
        // Show success message
        alert(`Sync operation started successfully. Operation ID: ${result.operation_id}`);
        
        // Refresh the operations list
        refreshOperations();
    } catch (error) {
        console.error('Error starting sync:', error);
        alert(`Failed to start sync: ${error.message}`);
    } finally {
        // Remove loading state
        document.body.classList.remove('loading');
    }
}

/**
 * Cancel the current operation
 */
function cancelOperation() {
    const operationId = document.getElementById('cancel-operation').dataset.id;
    if (confirm(`Are you sure you want to cancel operation ${operationId}?`)) {
        cancelOperationById(operationId);
        
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('operationDetailModal'));
        modal.hide();
    }
}

/**
 * Cancel an operation by ID
 */
async function cancelOperationById(operationId) {
    // Show loading state
    document.body.classList.add('loading');
    
    try {
        // Send request to cancel operation
        const response = await fetch(`${config.api.syncCancel}/${operationId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to cancel operation: ${response.status} ${response.statusText}`);
        }
        
        // Refresh the operations list
        refreshOperations();
        
        // Show success message
        alert(`Operation ${operationId} has been cancelled.`);
    } catch (error) {
        console.error('Error cancelling operation:', error);
        alert(`Failed to cancel operation: ${error.message}`);
    } finally {
        // Remove loading state
        document.body.classList.remove('loading');
    }
}

/**
 * Export operations data
 */
function exportData(format) {
    // Implement export functionality
    alert(`Export functionality not implemented yet. Format: ${format}`);
}

/**
 * Format date/time for display
 */
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleString();
}

/**
 * Format duration in seconds to human-readable format
 */
function formatDuration(seconds) {
    if (seconds === null || seconds === undefined) return 'N/A';
    
    if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.round(seconds % 60);
        return `${minutes}m ${remainingSeconds}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

/**
 * Generate status badge HTML
 */
function getStatusBadge(status) {
    let badgeClass = 'bg-secondary';
    let icon = 'question-circle';
    
    switch (status.toLowerCase()) {
        case 'pending':
            badgeClass = 'bg-info';
            icon = 'hourglass-split';
            break;
        case 'running':
            badgeClass = 'bg-primary';
            icon = 'arrow-repeat';
            break;
        case 'completed':
            badgeClass = 'bg-success';
            icon = 'check-circle';
            break;
        case 'failed':
            badgeClass = 'bg-danger';
            icon = 'x-circle';
            break;
        case 'cancelled':
            badgeClass = 'bg-warning';
            icon = 'slash-circle';
            break;
    }
    
    return `<span class="badge ${badgeClass}"><i class="bi bi-${icon}"></i> ${status}</span>`;
}

/**
 * Refresh operations data
 */
function refreshOperations() {
    fetchSyncOperations();
}

/**
 * Show error message
 */
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorAlert').classList.remove('d-none');
}