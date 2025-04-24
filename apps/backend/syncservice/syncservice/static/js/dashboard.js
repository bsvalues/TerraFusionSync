/**
 * TerraFusion SyncService Dashboard JavaScript
 * 
 * This file contains all the client-side JavaScript for the SyncService monitoring dashboard,
 * including data fetching, visualization, and UI interaction.
 */

// Dashboard configuration
const config = {
    // API endpoints
    api: {
        metrics: '/dashboard/metrics',
        systemStats: '/dashboard/system',
        syncOperations: '/dashboard/syncs',
        entityStats: '/dashboard/entities'
    },
    // Refresh interval in milliseconds (default: 10 seconds)
    refreshInterval: 10000,
    // Chart colors
    chartColors: {
        primary: '#0d6efd',
        success: '#198754',
        danger: '#dc3545',
        warning: '#ffc107',
        info: '#0dcaf0',
        secondary: '#6c757d',
    }
};

// Global chart objects
const charts = {
    cpuMemory: null,
    diskNetwork: null,
    syncOperations: null,
    entitySuccessRate: null
};

// Dashboard data
let dashboardData = {
    lastUpdated: null,
    metrics: {},
    syncOperations: [],
    entityStats: {}
};

// Auto-refresh timer
let refreshTimer = null;

/**
 * Initialize the dashboard when the page loads
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize charts
    initCharts();
    
    // Set up event listeners
    document.getElementById('refreshBtn').addEventListener('click', refreshDashboard);
    
    // Initial data load
    refreshDashboard();
    
    // Set up auto-refresh
    refreshTimer = setInterval(refreshDashboard, config.refreshInterval);
    
    // Handle tab visibility changes (pause refresh when tab is not visible)
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            if (refreshTimer) {
                clearInterval(refreshTimer);
                refreshTimer = null;
            }
        } else {
            if (!refreshTimer) {
                refreshDashboard();
                refreshTimer = setInterval(refreshDashboard, config.refreshInterval);
            }
        }
    });
});

/**
 * Initialize all dashboard charts
 */
function initCharts() {
    // CPU & Memory chart
    const cpuMemoryCtx = document.getElementById('cpuMemoryChart').getContext('2d');
    charts.cpuMemory = new Chart(cpuMemoryCtx, {
        type: 'line',
        data: {
            labels: Array(10).fill(''),
            datasets: [
                {
                    label: 'CPU Usage',
                    borderColor: config.chartColors.primary,
                    backgroundColor: hexToRgba(config.chartColors.primary, 0.1),
                    borderWidth: 2,
                    data: Array(10).fill(0),
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Memory Usage',
                    borderColor: config.chartColors.warning,
                    backgroundColor: hexToRgba(config.chartColors.warning, 0.1),
                    borderWidth: 2,
                    data: Array(10).fill(0),
                    tension: 0.3,
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
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Usage %'
                    }
                }
            }
        }
    });
    
    // Disk & Network chart
    const diskNetworkCtx = document.getElementById('diskNetworkChart').getContext('2d');
    charts.diskNetwork = new Chart(diskNetworkCtx, {
        type: 'bar',
        data: {
            labels: ['Disk', 'Network TX', 'Network RX'],
            datasets: [
                {
                    label: 'Current',
                    backgroundColor: hexToRgba(config.chartColors.info, 0.7),
                    borderColor: config.chartColors.info,
                    borderWidth: 1,
                    data: [0, 0, 0]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => formatBytes(value)
                    }
                }
            }
        }
    });
    
    // Sync Operations chart
    const syncOpsCtx = document.getElementById('syncOperationsChart').getContext('2d');
    charts.syncOperations = new Chart(syncOpsCtx, {
        type: 'pie',
        data: {
            labels: ['Success', 'In Progress', 'Failed'],
            datasets: [
                {
                    data: [0, 0, 0],
                    backgroundColor: [
                        config.chartColors.success,
                        config.chartColors.warning,
                        config.chartColors.danger
                    ],
                    borderWidth: 0
                }
            ]
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
    
    // Entity Success Rate chart
    const entitySuccessCtx = document.getElementById('entitySuccessChart').getContext('2d');
    charts.entitySuccessRate = new Chart(entitySuccessCtx, {
        type: 'bar',
        data: {
            labels: ['Properties', 'Owners', 'Assessments'],
            datasets: [
                {
                    label: 'Success Rate %',
                    backgroundColor: hexToRgba(config.chartColors.success, 0.7),
                    borderColor: config.chartColors.success,
                    borderWidth: 1,
                    data: [0, 0, 0]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false,
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Success Rate %'
                    }
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
        const [metrics, syncOperations, entityStats] = await Promise.all([
            fetchMetrics(),
            fetchSyncOperations(),
            fetchEntityStats()
        ]);
        
        // Update the dashboard data
        dashboardData = {
            lastUpdated: new Date(),
            metrics,
            syncOperations,
            entityStats
        };
        
        // Update the UI
        updateDashboard();
        
        // Hide any previous errors
        document.getElementById('errorAlert').style.display = 'none';
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        
        // Show error message
        document.getElementById('errorMessage').textContent = `Failed to refresh dashboard: ${error.message}`;
        document.getElementById('errorAlert').style.display = 'block';
    } finally {
        // Remove loading state
        document.body.classList.remove('loading');
    }
}

/**
 * Fetch system metrics from the API
 */
async function fetchMetrics() {
    const response = await fetch(config.api.metrics);
    if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.status} ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch sync operations from the API
 */
async function fetchSyncOperations() {
    const response = await fetch(config.api.syncOperations);
    if (!response.ok) {
        throw new Error(`Failed to fetch sync operations: ${response.status} ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch entity statistics from the API
 */
async function fetchEntityStats() {
    const response = await fetch(config.api.entityStats);
    if (!response.ok) {
        throw new Error(`Failed to fetch entity stats: ${response.status} ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Update the dashboard UI with the latest data
 */
function updateDashboard() {
    // Update last updated timestamp
    const lastUpdated = formatDateTime(dashboardData.lastUpdated);
    document.getElementById('lastUpdated').textContent = `Last updated: ${lastUpdated}`;
    
    // Update system metrics
    updateSystemMetrics();
    
    // Update sync operations
    updateSyncOperations();
    
    // Update entity statistics
    updateEntityStats();
}

/**
 * Update the system metrics section of the dashboard
 */
function updateSystemMetrics() {
    const metrics = dashboardData.metrics;
    
    // Update CPU and memory metrics
    const cpuPercent = getMetricValue(metrics, 'cpu_percent') || 0;
    const memoryPercent = getMetricValue(metrics, 'memory_percent') || 0;
    const diskPercent = getMetricValue(metrics, 'disk_percent') || 0;
    
    document.getElementById('cpuUsage').textContent = `${cpuPercent.toFixed(1)}%`;
    document.getElementById('cpuProgress').style.width = `${cpuPercent}%`;
    
    document.getElementById('memoryUsage').textContent = `${memoryPercent.toFixed(1)}%`;
    document.getElementById('memoryProgress').style.width = `${memoryPercent}%`;
    
    document.getElementById('diskUsage').textContent = `${diskPercent.toFixed(1)}%`;
    document.getElementById('diskProgress').style.width = `${diskPercent}%`;
    
    // Format total and used memory
    const memoryTotal = getMetricValue(metrics, 'memory_total_bytes') || 0;
    const memoryUsed = getMetricValue(metrics, 'memory_used_bytes') || 0;
    document.getElementById('memoryDetails').textContent = 
        `${formatBytes(memoryUsed)} / ${formatBytes(memoryTotal)}`;
    
    // Format total and used disk
    const diskTotal = getMetricValue(metrics, 'disk_total_bytes') || 0;
    const diskUsed = getMetricValue(metrics, 'disk_used_bytes') || 0;
    document.getElementById('diskDetails').textContent = 
        `${formatBytes(diskUsed)} / ${formatBytes(diskTotal)}`;
    
    // Update process metrics
    const processCpu = getMetricValue(metrics, 'process_cpu_percent') || 0;
    const processMemory = getMetricValue(metrics, 'process_memory_rss_bytes') || 0;
    const processThreads = getMetricValue(metrics, 'process_threads') || 0;
    
    document.getElementById('processCpu').textContent = `${processCpu.toFixed(1)}%`;
    document.getElementById('processMemory').textContent = formatBytes(processMemory);
    document.getElementById('processThreads').textContent = processThreads;
    
    // Update network metrics
    const networkSent = getMetricValue(metrics, 'network_bytes_sent') || 0;
    const networkReceived = getMetricValue(metrics, 'network_bytes_recv') || 0;
    
    document.getElementById('networkSent').textContent = formatBytes(networkSent);
    document.getElementById('networkReceived').textContent = formatBytes(networkReceived);
    
    // Update charts with new data
    updateSystemCharts(cpuPercent, memoryPercent, diskUsed, networkSent, networkReceived);
}

/**
 * Update the system metric charts with new data
 */
function updateSystemCharts(cpu, memory, disk, networkTx, networkRx) {
    // Get current timestamp
    const timestamp = formatTime(new Date());
    
    // Update CPU & Memory chart
    const cpuMemoryChart = charts.cpuMemory;
    
    // Add new data points
    cpuMemoryChart.data.labels.push(timestamp);
    cpuMemoryChart.data.datasets[0].data.push(cpu);
    cpuMemoryChart.data.datasets[1].data.push(memory);
    
    // Remove oldest data points if we have more than 10
    if (cpuMemoryChart.data.labels.length > 10) {
        cpuMemoryChart.data.labels.shift();
        cpuMemoryChart.data.datasets[0].data.shift();
        cpuMemoryChart.data.datasets[1].data.shift();
    }
    
    // Update the chart
    cpuMemoryChart.update();
    
    // Update Disk & Network chart
    const diskNetworkChart = charts.diskNetwork;
    
    // Update data
    diskNetworkChart.data.datasets[0].data = [disk, networkTx, networkRx];
    
    // Update the chart
    diskNetworkChart.update();
}

/**
 * Update the sync operations section of the dashboard
 */
function updateSyncOperations() {
    const syncOps = dashboardData.syncOperations;
    
    // Count operations by status
    let success = 0;
    let inProgress = 0;
    let failed = 0;
    let total = 0;
    
    // Get the latest 5 operations for the table
    const latestOps = (syncOps.operations || []).sort((a, b) => {
        return new Date(b.start_time) - new Date(a.start_time);
    }).slice(0, 5);
    
    // Count operations by status
    (syncOps.operations || []).forEach(op => {
        total++;
        if (op.status === 'completed') {
            success++;
        } else if (op.status === 'in_progress') {
            inProgress++;
        } else if (op.status === 'failed') {
            failed++;
        }
    });
    
    // Update operation counts
    document.getElementById('totalSyncs').textContent = total;
    document.getElementById('successfulSyncs').textContent = success;
    document.getElementById('failedSyncs').textContent = failed;
    document.getElementById('activeJobs').textContent = inProgress;
    
    // Update the sync operations table
    const tableBody = document.getElementById('syncOpsTable');
    
    if (latestOps.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No sync operations available</td></tr>';
    } else {
        tableBody.innerHTML = latestOps.map(op => {
            const startTime = formatDateTime(new Date(op.start_time));
            let statusClass = '';
            let statusBadge = '';
            
            if (op.status === 'completed') {
                statusClass = 'bg-success';
                statusBadge = 'Success';
            } else if (op.status === 'in_progress') {
                statusClass = 'bg-warning text-dark';
                statusBadge = 'In Progress';
            } else if (op.status === 'failed') {
                statusClass = 'bg-danger';
                statusBadge = 'Failed';
            }
            
            return `
                <tr>
                    <td>${op.id}</td>
                    <td>${op.sync_type}</td>
                    <td>${startTime}</td>
                    <td>${op.entity_count || 0}</td>
                    <td><span class="badge ${statusClass} badge-status">${statusBadge}</span></td>
                </tr>
            `;
        }).join('');
    }
    
    // Update the sync operations chart
    const syncOpsChart = charts.syncOperations;
    syncOpsChart.data.datasets[0].data = [success, inProgress, failed];
    syncOpsChart.update();
}

/**
 * Update the entity statistics section of the dashboard
 */
function updateEntityStats() {
    const entityStats = dashboardData.entityStats;
    
    // Get entity types and their stats
    const entityTypes = Object.keys(entityStats.entities || {}).sort();
    
    // Update the entity table
    const tableBody = document.getElementById('entityTable');
    
    if (entityTypes.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No entity metrics available</td></tr>';
    } else {
        tableBody.innerHTML = entityTypes.map(entityType => {
            const stats = entityStats.entities[entityType];
            const total = stats.success + stats.failure;
            const successRate = total > 0 ? (stats.success / total) * 100 : 0;
            
            return `
                <tr>
                    <td>${entityType}</td>
                    <td>
                        <div class="progress">
                            <div class="progress-bar bg-success" role="progressbar" 
                                style="width: ${successRate}%" 
                                aria-valuenow="${successRate}" 
                                aria-valuemin="0" 
                                aria-valuemax="100">
                                ${successRate.toFixed(1)}%
                            </div>
                        </div>
                    </td>
                    <td>${stats.success}</td>
                    <td>${stats.failure}</td>
                    <td>${total}</td>
                </tr>
            `;
        }).join('');
    }
    
    // Update the entity success rate chart
    const entitySuccessChart = charts.entitySuccessRate;
    const labels = [];
    const data = [];
    
    entityTypes.forEach(entityType => {
        const stats = entityStats.entities[entityType];
        const total = stats.success + stats.failure;
        const successRate = total > 0 ? (stats.success / total) * 100 : 0;
        
        labels.push(entityType);
        data.push(successRate);
    });
    
    entitySuccessChart.data.labels = labels;
    entitySuccessChart.data.datasets[0].data = data;
    entitySuccessChart.update();
}

/**
 * Get a metric value from the metrics object
 */
function getMetricValue(metrics, metricName) {
    if (!metrics || !metrics[metricName]) {
        return null;
    }
    
    return metrics[metricName].values.default;
}

/**
 * Format a timestamp as a date and time string
 */
function formatDateTime(date) {
    if (!date) return 'N/A';
    
    return date.toLocaleString();
}

/**
 * Format a timestamp as a time string (HH:MM:SS)
 */
function formatTime(date) {
    if (!date) return '';
    
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

/**
 * Format bytes as a human-readable string
 */
function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Convert a hex color to rgba
 */
function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}