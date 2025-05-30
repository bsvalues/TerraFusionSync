/**
 * TerraFusion SyncService Dashboard
 * Main dashboard script
 */

// Configuration
const config = {
    api: {
        metrics: '/api/metrics',
        system: '/api/system',
        syncOperations: '/api/sync/operations',
        syncActive: '/api/sync/active',
        syncMetrics: '/api/sync/metrics',
        entityStats: '/api/sync/entity-stats',
        compatibility: '/api/compatibility/matrix',
        health: '/health/status'
    },
    refreshInterval: 30000 // 30 seconds
};

// Dashboard data store
let dashboardData = {
    lastUpdated: null,
    metrics: [],
    system: {},
    syncOperations: [],
    activeOperations: [],
    syncMetrics: {},
    entityStats: {},
    errors: []
};

// Chart objects
let performanceChart = null;
let entityChart = null;

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
});

/**
 * Initialize the dashboard components
 */
async function initializeDashboard() {
    // Set up click handlers
    document.getElementById('refresh-health').addEventListener('click', () => refreshSystemHealth());
    document.getElementById('view-all-syncs').addEventListener('click', () => window.location.href = '/sync.html');
    
    // Initialize charts
    initializeCharts();
    
    // Initial data load
    await refreshDashboard();
    
    // Set up periodic refresh
    setInterval(refreshDashboard, config.refreshInterval);
}

/**
 * Initialize chart objects
 */
function initializeCharts() {
    // Performance chart (success/failure over time)
    const perfCtx = document.getElementById('performance-chart').getContext('2d');
    performanceChart = new Chart(perfCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Successful Operations',
                    data: [],
                    borderColor: '#198754', // Bootstrap success color
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Failed Operations',
                    data: [],
                    borderColor: '#dc3545', // Bootstrap danger color
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Operations Count'
                    }
                }
            }
        }
    });
    
    // Entity distribution chart
    const entityCtx = document.getElementById('entity-chart').getContext('2d');
    entityChart = new Chart(entityCtx, {
        type: 'pie',
        data: {
            labels: ['Property', 'Owner', 'Assessment'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    '#198754', // Bootstrap success
                    '#0d6efd', // Bootstrap primary
                    '#ffc107'  // Bootstrap warning
                ],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                }
            }
        }
    });
}

/**
 * Refresh all dashboard data
 */
async function refreshDashboard() {
    // Show loading state
    document.body.classList.add('loading');
    
    try {
        // Fetch dashboard data in parallel
        const [system, syncOperations, activeOperations, syncMetrics, entityStats] = await Promise.all([
            fetchSystemHealth(),
            fetchSyncOperations(),
            fetchActiveSyncOperations(),
            fetchSyncMetrics(),
            fetchEntityStats()
        ]);
        
        // Update the dashboard data
        dashboardData = {
            lastUpdated: new Date(),
            system,
            syncOperations,
            activeOperations,
            syncMetrics,
            entityStats,
            errors: [] // Reset errors
        };
        
        // Update the UI
        updateDashboard();
        
        // Hide any previous errors
        document.getElementById('errorAlert').classList.add('d-none');
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        
        // Show error message
        document.getElementById('errorMessage').textContent = `Failed to refresh dashboard: ${error.message}`;
        document.getElementById('errorAlert').classList.remove('d-none');
    } finally {
        // Remove loading state
        document.body.classList.remove('loading');
    }
}

/**
 * Fetch system health status from the API
 */
async function fetchSystemHealth() {
    const response = await fetch(config.api.system);
    if (!response.ok) {
        throw new Error(`Failed to fetch system health: ${response.status} ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch sync operations from the API
 */
async function fetchSyncOperations() {
    const response = await fetch(`${config.api.syncOperations}?limit=5`);
    if (!response.ok) {
        throw new Error(`Failed to fetch sync operations: ${response.status} ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch active sync operations from the API
 */
async function fetchActiveSyncOperations() {
    const response = await fetch(config.api.syncActive);
    if (!response.ok) {
        throw new Error(`Failed to fetch active operations: ${response.status} ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch sync metrics from the API
 */
async function fetchSyncMetrics() {
    const response = await fetch(`${config.api.syncMetrics}?days=7`);
    if (!response.ok) {
        throw new Error(`Failed to fetch sync metrics: ${response.status} ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch entity statistics from the API
 */
async function fetchEntityStats() {
    // This endpoint may not exist yet, so handle the 404 gracefully
    try {
        const response = await fetch(config.api.entityStats);
        if (response.ok) {
            return await response.json();
        }
        return { entities: {} };
    } catch (error) {
        console.warn('Entity stats endpoint not implemented yet:', error);
        return { entities: {} };
    }
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
 * Update the dashboard UI with the latest data
 */
function updateDashboard() {
    // Update last updated timestamp
    document.getElementById('last-updated').textContent = formatDateTime(dashboardData.lastUpdated);
    
    // Update system health section
    updateSystemHealth();
    
    // Update stats cards
    updateStatsCards();
    
    // Update recent syncs table
    updateRecentSyncs();
    
    // Update charts
    updateCharts();
    
    // Update error list
    updateErrorList();
}

/**
 * Update system health display
 */
function updateSystemHealth() {
    const system = dashboardData.system;
    
    if (!system || !system.cpu_percent) {
        return; // No system data available
    }
    
    // Update CPU usage
    const cpuPercent = document.getElementById('cpu-percent');
    const cpuProgress = document.getElementById('cpu-progress');
    cpuPercent.textContent = `${system.cpu_percent.toFixed(1)}%`;
    cpuProgress.style.width = `${system.cpu_percent}%`;
    
    // Update memory usage
    const memoryPercent = document.getElementById('memory-percent');
    const memoryProgress = document.getElementById('memory-progress');
    memoryPercent.textContent = `${system.memory_percent.toFixed(1)}%`;
    memoryProgress.style.width = `${system.memory_percent}%`;
    
    // Update disk usage
    const diskPercent = document.getElementById('disk-percent');
    const diskProgress = document.getElementById('disk-progress');
    diskPercent.textContent = `${system.disk_percent.toFixed(1)}%`;
    diskProgress.style.width = `${system.disk_percent}%`;
    
    // Update system status
    const systemStatus = document.getElementById('system-status');
    const isHealthy = system.cpu_percent < 90 && system.memory_percent < 90 && system.disk_percent < 90;
    systemStatus.textContent = isHealthy ? 'Healthy' : 'Warning';
    systemStatus.className = isHealthy ? 'badge bg-success' : 'badge bg-warning';
    
    // Update uptime if available
    if (system.uptime_seconds) {
        document.getElementById('service-uptime').textContent = formatDuration(system.uptime_seconds);
    }
    
    // Update last checked timestamp
    document.getElementById('system-last-updated').textContent = `Last checked: ${formatDateTime(system.timestamp)}`;
}

/**
 * Update stats cards with metrics data
 */
function updateStatsCards() {
    const metrics = dashboardData.syncMetrics;
    const activeOps = dashboardData.activeOperations || [];
    
    // If we don't have metrics data yet, use default values
    const successfulSyncs = metrics.total_completed || 0;
    const failedOperations = metrics.total_failed || 0;
    const totalRecords = metrics.total_records_processed || 0;
    
    // Update successful syncs card
    document.getElementById('successful-syncs').textContent = successfulSyncs;
    const successRate = metrics.success_rate ? metrics.success_rate.toFixed(1) : '0';
    document.getElementById('success-rate').textContent = `${successRate}%`;
    
    // Update active operations card
    document.getElementById('active-operations').textContent = activeOps.length;
    const avgDuration = metrics.average_duration_seconds 
        ? formatDuration(metrics.average_duration_seconds)
        : 'N/A';
    document.getElementById('avg-duration').textContent = avgDuration;
    
    // Update failed operations card
    document.getElementById('failed-operations').textContent = failedOperations;
    const failureRate = metrics.failure_rate ? metrics.failure_rate.toFixed(1) : '0';
    document.getElementById('failure-rate').textContent = `${failureRate}%`;
    
    // Update total records card
    document.getElementById('total-records').textContent = totalRecords.toLocaleString();
    const recordsPerMinute = metrics.records_per_minute ? metrics.records_per_minute.toFixed(1) : '0';
    document.getElementById('records-per-minute').textContent = `${recordsPerMinute}/min`;
}

/**
 * Update recent syncs table
 */
function updateRecentSyncs() {
    const recentSyncsTable = document.getElementById('recent-syncs');
    const operations = dashboardData.syncOperations || [];
    
    if (operations.length === 0) {
        recentSyncsTable.innerHTML = '<tr><td colspan="6" class="text-center">No sync operations found</td></tr>';
        return;
    }
    
    // Build the HTML for the table rows
    const rowsHTML = operations.map(op => {
        // Calculate duration
        let duration = 'N/A';
        if (op.end_time && op.start_time) {
            const startTime = new Date(op.start_time);
            const endTime = new Date(op.end_time);
            const durationSeconds = (endTime - startTime) / 1000;
            duration = formatDuration(durationSeconds);
        } else if (op.start_time) {
            const startTime = new Date(op.start_time);
            const now = new Date();
            const durationSeconds = (now - startTime) / 1000;
            duration = formatDuration(durationSeconds) + ' (running)';
        }
        
        // Format the records count
        const records = op.entity_count ? op.entity_count.toLocaleString() : 'N/A';
        
        return `
            <tr>
                <td><a href="#" class="operation-link" data-id="${op.id}">${op.id}</a></td>
                <td>${op.sync_type}</td>
                <td>${op.sync_pair_id}</td>
                <td>${getStatusBadge(op.status)}</td>
                <td>${duration}</td>
                <td>${records}</td>
            </tr>
        `;
    }).join('');
    
    recentSyncsTable.innerHTML = rowsHTML;
    
    // Add event listeners to the operation links
    document.querySelectorAll('.operation-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = `/sync.html?operation=${link.dataset.id}`;
        });
    });
}

/**
 * Update chart displays
 */
function updateCharts() {
    updatePerformanceChart();
    updateEntityChart();
}

/**
 * Update the performance chart with time series data
 */
function updatePerformanceChart() {
    const metrics = dashboardData.syncMetrics;
    
    if (!metrics || !metrics.time_series) {
        return; // No time series data available
    }
    
    // Extract time series data
    const timePoints = metrics.time_series.map(point => {
        const date = new Date(point.timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });
    
    const successData = metrics.time_series.map(point => point.success_count || 0);
    const failureData = metrics.time_series.map(point => point.failure_count || 0);
    
    // Update chart data
    performanceChart.data.labels = timePoints;
    performanceChart.data.datasets[0].data = successData;
    performanceChart.data.datasets[1].data = failureData;
    performanceChart.update();
}

/**
 * Update the entity distribution chart
 */
function updateEntityChart() {
    const entityStats = dashboardData.entityStats;
    
    if (!entityStats || !entityStats.entities) {
        return; // No entity data available
    }
    
    // Extract entity data
    const propertyCount = (entityStats.entities.property?.success || 0);
    const ownerCount = (entityStats.entities.owner?.success || 0);
    const assessmentCount = (entityStats.entities.assessment?.success || 0);
    
    // Update chart data
    entityChart.data.datasets[0].data = [propertyCount, ownerCount, assessmentCount];
    entityChart.update();
}

/**
 * Update the error list
 */
function updateErrorList() {
    const errorList = document.getElementById('error-list');
    const errors = dashboardData.errors || [];
    
    if (errors.length === 0) {
        errorList.innerHTML = '<div class="list-group-item text-center text-muted py-4">No errors found.</div>';
        document.getElementById('error-count').textContent = '0';
        return;
    }
    
    // Update error count badge
    document.getElementById('error-count').textContent = errors.length.toString();
    
    // Build the HTML for the errors
    const errorsHTML = errors.map(error => `
        <div class="list-group-item">
            <div class="d-flex justify-content-between align-items-center">
                <h6 class="mb-1">${error.message || 'Unknown error'}</h6>
                <small class="text-muted">${formatDateTime(error.timestamp)}</small>
            </div>
            <p class="mb-1">${error.details || ''}</p>
            <small>
                <span class="badge bg-secondary">${error.operation_id || 'N/A'}</span>
                <span class="badge bg-secondary">${error.sync_pair_id || 'N/A'}</span>
            </small>
        </div>
    `).join('');
    
    errorList.innerHTML = errorsHTML;
}

/**
 * Manually refresh system health
 */
function refreshSystemHealth() {
    // Add loading state to the button
    const button = document.getElementById('refresh-health');
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
    button.disabled = true;
    
    // Fetch the latest system health
    fetchSystemHealth()
        .then(systemData => {
            // Update system health section
            dashboardData.system = systemData;
            updateSystemHealth();
        })
        .catch(error => {
            console.error('Error refreshing system health:', error);
            
            // Show error message
            document.getElementById('errorMessage').textContent = `Failed to refresh system health: ${error.message}`;
            document.getElementById('errorAlert').classList.remove('d-none');
        })
        .finally(() => {
            // Restore button state
            button.innerHTML = '<i class="bi bi-arrow-clockwise"></i>';
            button.disabled = false;
        });
}