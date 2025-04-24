/**
 * TerraFusion SyncService
 * Metrics & Analytics script
 */

// Configuration
const config = {
    api: {
        metrics: '/api/metrics',
        system: '/api/system',
        syncMetrics: '/api/sync/metrics',
        entityStats: '/api/sync/entity-stats',
        syncPairs: '/api/compatibility/pairs'
    },
    refreshInterval: 60000 // 60 seconds
};

// Metrics data store
let metricsData = {
    lastUpdated: null,
    timeRange: 1, // hours
    metrics: [],
    systemMetrics: [],
    syncMetrics: {},
    entityStats: {},
    syncPairs: [],
    syncPairFilter: 'all'
};

// Chart objects
let operationsChart = null;
let recordsChart = null;
let successFailureChart = null;
let durationChart = null;
let resourceChart = null;
let throughputChart = null;

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
    
    // Initialize charts
    initializeCharts();
    
    // Initial data load
    await Promise.all([
        fetchSyncPairs(),
        fetchMetricsData()
    ]);
    
    // Set up periodic refresh
    setInterval(refreshMetrics, config.refreshInterval);
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Time range buttons
    document.querySelectorAll('.time-range-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active button
            document.querySelectorAll('.time-range-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update time range
            metricsData.timeRange = parseInt(btn.dataset.hours, 10);
            
            // Fetch new data
            fetchMetricsData();
        });
    });
    
    // Sync pair filter
    document.getElementById('sync-pair-filter').addEventListener('change', function() {
        metricsData.syncPairFilter = this.value;
        fetchMetricsData();
    });
    
    // Refresh button
    document.getElementById('refresh-metrics').addEventListener('click', refreshMetrics);
    
    // Export button
    document.getElementById('export-metrics').addEventListener('click', exportMetrics);
}

/**
 * Initialize chart objects
 */
function initializeCharts() {
    // Operations chart
    const operationsCtx = document.getElementById('operations-chart').getContext('2d');
    operationsChart = new Chart(operationsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Total Operations',
                    data: [],
                    borderColor: '#0d6efd', // Bootstrap primary
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderWidth: 2,
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
    
    // Records chart
    const recordsCtx = document.getElementById('records-chart').getContext('2d');
    recordsChart = new Chart(recordsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Records Processed',
                    data: [],
                    borderColor: '#198754', // Bootstrap success
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    borderWidth: 2,
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
                        text: 'Records Count'
                    }
                }
            }
        }
    });
    
    // Success/Failure chart
    const successFailureCtx = document.getElementById('success-failure-chart').getContext('2d');
    successFailureChart = new Chart(successFailureCtx, {
        type: 'pie',
        data: {
            labels: ['Success', 'Failure'],
            datasets: [{
                data: [0, 0],
                backgroundColor: [
                    '#198754', // Bootstrap success
                    '#dc3545'  // Bootstrap danger
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
    
    // Duration chart
    const durationCtx = document.getElementById('duration-chart').getContext('2d');
    durationChart = new Chart(durationCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Average Duration (seconds)',
                data: [],
                backgroundColor: 'rgba(13, 202, 240, 0.5)', // Bootstrap info
                borderColor: '#0dcaf0',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Sync Pair'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Duration (seconds)'
                    }
                }
            }
        }
    });
    
    // Resource utilization chart
    const resourceCtx = document.getElementById('resource-chart').getContext('2d');
    resourceChart = new Chart(resourceCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'CPU',
                    data: [],
                    borderColor: '#0d6efd', // Bootstrap primary
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Memory',
                    data: [],
                    borderColor: '#198754', // Bootstrap success
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Disk',
                    data: [],
                    borderColor: '#ffc107', // Bootstrap warning
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false
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
                    max: 100,
                    title: {
                        display: true,
                        text: 'Utilization %'
                    }
                }
            }
        }
    });
    
    // Throughput chart
    const throughputCtx = document.getElementById('throughput-chart').getContext('2d');
    throughputChart = new Chart(throughputCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Records/Minute',
                    data: [],
                    borderColor: '#6f42c1', // Bootstrap purple
                    backgroundColor: 'rgba(111, 66, 193, 0.1)',
                    borderWidth: 2,
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
                        text: 'Records/Minute'
                    }
                }
            }
        }
    });
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
        metricsData.syncPairs = data.pairs || [];
        
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
    const filterSelect = document.getElementById('sync-pair-filter');
    
    // Keep the 'all' option
    filterSelect.innerHTML = '<option value="all">All Sync Pairs</option>';
    
    // Add options for each sync pair
    metricsData.syncPairs.forEach(pair => {
        const option = document.createElement('option');
        option.value = pair.id;
        option.textContent = `${pair.source_system} → ${pair.target_system}`;
        filterSelect.appendChild(option);
    });
}

/**
 * Fetch metrics data from APIs
 */
async function fetchMetricsData() {
    // Show loading state
    document.body.classList.add('loading');
    
    try {
        // Build requests for all data sources
        const metricsPromise = fetch(`${config.api.metrics}?hours=${metricsData.timeRange}`);
        const systemPromise = fetch(config.api.system);
        
        // Build sync metrics request with filter if needed
        let syncMetricsUrl = `${config.api.syncMetrics}?days=${Math.ceil(metricsData.timeRange / 24) || 1}`;
        if (metricsData.syncPairFilter !== 'all') {
            syncMetricsUrl += `&sync_pair_id=${metricsData.syncPairFilter}`;
        }
        const syncMetricsPromise = fetch(syncMetricsUrl);
        
        // Fetch entity stats if available
        const entityStatsPromise = fetch(config.api.entityStats).catch(() => {
            // Return empty response if endpoint not found
            return new Response(JSON.stringify({ entities: {} }));
        });
        
        // Wait for all requests to complete
        const [metricsResponse, systemResponse, syncMetricsResponse, entityStatsResponse] = 
            await Promise.all([metricsPromise, systemPromise, syncMetricsPromise, entityStatsPromise]);
        
        // Check responses
        if (!metricsResponse.ok) {
            throw new Error(`Failed to fetch metrics: ${metricsResponse.status} ${metricsResponse.statusText}`);
        }
        
        if (!systemResponse.ok) {
            throw new Error(`Failed to fetch system info: ${systemResponse.status} ${systemResponse.statusText}`);
        }
        
        if (!syncMetricsResponse.ok) {
            throw new Error(`Failed to fetch sync metrics: ${syncMetricsResponse.status} ${syncMetricsResponse.statusText}`);
        }
        
        // Parse responses
        const metrics = await metricsResponse.json();
        const system = await systemResponse.json();
        const syncMetrics = await syncMetricsResponse.json();
        const entityStats = entityStatsResponse.ok ? await entityStatsResponse.json() : { entities: {} };
        
        // Update data store
        updateMetricsData(metrics, system, syncMetrics, entityStats);
        
        // Update UI
        updateCharts();
        updateMetricsTable();
        
        // Hide any previous errors
        document.getElementById('errorAlert').classList.add('d-none');
    } catch (error) {
        console.error('Error fetching metrics data:', error);
        showError(`Failed to fetch metrics data: ${error.message}`);
    } finally {
        // Update last updated timestamp
        metricsData.lastUpdated = new Date();
        document.getElementById('last-updated').textContent = formatDateTime(metricsData.lastUpdated);
        
        // Remove loading state
        document.body.classList.remove('loading');
    }
}

/**
 * Update metrics data store
 */
function updateMetricsData(metrics, system, syncMetrics, entityStats) {
    metricsData.metrics = metrics || [];
    
    // Extract system metrics history if available
    if (metrics && Array.isArray(metrics)) {
        metricsData.systemMetrics = metrics.filter(m => 
            m.name === 'cpu_percent' || 
            m.name === 'memory_percent' || 
            m.name === 'disk_percent'
        );
    }
    
    // Update current system metrics
    metricsData.system = system || {};
    
    // Update sync metrics
    metricsData.syncMetrics = syncMetrics || {};
    
    // Update entity stats
    metricsData.entityStats = entityStats || { entities: {} };
}

/**
 * Update all charts
 */
function updateCharts() {
    updateOperationsChart();
    updateRecordsChart();
    updateSuccessFailureChart();
    updateDurationChart();
    updateResourceChart();
    updateThroughputChart();
}

/**
 * Update operations chart
 */
function updateOperationsChart() {
    const metrics = metricsData.syncMetrics;
    
    if (!metrics || !metrics.time_series) {
        return; // No time series data available
    }
    
    // Extract time series data
    const timePoints = metrics.time_series.map(point => {
        const date = new Date(point.timestamp);
        return formatDateTime(date, true);
    });
    
    const operationsData = metrics.time_series.map(point => 
        (point.success_count || 0) + (point.failure_count || 0)
    );
    
    // Update chart data
    operationsChart.data.labels = timePoints;
    operationsChart.data.datasets[0].data = operationsData;
    operationsChart.update();
}

/**
 * Update records chart
 */
function updateRecordsChart() {
    const metrics = metricsData.syncMetrics;
    
    if (!metrics || !metrics.time_series) {
        return; // No time series data available
    }
    
    // Extract time series data
    const timePoints = metrics.time_series.map(point => {
        const date = new Date(point.timestamp);
        return formatDateTime(date, true);
    });
    
    const recordsData = metrics.time_series.map(point => point.records_processed || 0);
    
    // Update chart data
    recordsChart.data.labels = timePoints;
    recordsChart.data.datasets[0].data = recordsData;
    recordsChart.update();
}

/**
 * Update success/failure chart
 */
function updateSuccessFailureChart() {
    const metrics = metricsData.syncMetrics;
    
    if (!metrics) {
        return; // No metrics data available
    }
    
    const successCount = metrics.total_completed || 0;
    const failureCount = metrics.total_failed || 0;
    
    // Update chart data
    successFailureChart.data.datasets[0].data = [successCount, failureCount];
    successFailureChart.update();
}

/**
 * Update duration chart
 */
function updateDurationChart() {
    const metrics = metricsData.syncMetrics;
    
    if (!metrics || !metrics.by_sync_pair) {
        return; // No sync pair data available
    }
    
    // Extract sync pair data
    const syncPairs = Object.keys(metrics.by_sync_pair);
    const durations = syncPairs.map(pairId => {
        const pairData = metrics.by_sync_pair[pairId];
        return pairData.average_duration_seconds || 0;
    });
    
    // Update chart data
    durationChart.data.labels = syncPairs;
    durationChart.data.datasets[0].data = durations;
    durationChart.update();
}

/**
 * Update resource chart
 */
function updateResourceChart() {
    // If we have system metrics history, use it
    if (metricsData.systemMetrics && metricsData.systemMetrics.length > 0) {
        // Group by timestamp
        const timePoints = new Set();
        metricsData.systemMetrics.forEach(m => {
            if (m.timestamp) timePoints.add(m.timestamp);
        });
        
        // Sort timestamps
        const sortedTimePoints = Array.from(timePoints).sort();
        
        // Extract data for each metric
        const cpuData = [];
        const memoryData = [];
        const diskData = [];
        
        sortedTimePoints.forEach(timestamp => {
            const cpuMetric = metricsData.systemMetrics.find(m => 
                m.name === 'cpu_percent' && m.timestamp === timestamp
            );
            
            const memoryMetric = metricsData.systemMetrics.find(m => 
                m.name === 'memory_percent' && m.timestamp === timestamp
            );
            
            const diskMetric = metricsData.systemMetrics.find(m => 
                m.name === 'disk_percent' && m.timestamp === timestamp
            );
            
            cpuData.push(cpuMetric ? cpuMetric.value : null);
            memoryData.push(memoryMetric ? memoryMetric.value : null);
            diskData.push(diskMetric ? diskMetric.value : null);
        });
        
        // Format time points for display
        const formattedTimePoints = sortedTimePoints.map(timestamp => {
            const date = new Date(timestamp);
            return formatDateTime(date, true);
        });
        
        // Update chart data
        resourceChart.data.labels = formattedTimePoints;
        resourceChart.data.datasets[0].data = cpuData;
        resourceChart.data.datasets[1].data = memoryData;
        resourceChart.data.datasets[2].data = diskData;
        resourceChart.update();
    } else if (metricsData.system) {
        // If no history, use current system data
        const currentTime = formatDateTime(new Date(), true);
        
        resourceChart.data.labels = [currentTime];
        resourceChart.data.datasets[0].data = [metricsData.system.cpu_percent || 0];
        resourceChart.data.datasets[1].data = [metricsData.system.memory_percent || 0];
        resourceChart.data.datasets[2].data = [metricsData.system.disk_percent || 0];
        resourceChart.update();
    }
}

/**
 * Update throughput chart
 */
function updateThroughputChart() {
    const metrics = metricsData.syncMetrics;
    
    if (!metrics || !metrics.time_series) {
        return; // No time series data available
    }
    
    // Extract time series data
    const timePoints = metrics.time_series.map(point => {
        const date = new Date(point.timestamp);
        return formatDateTime(date, true);
    });
    
    const throughputData = metrics.time_series.map(point => point.records_per_minute || 0);
    
    // Update chart data
    throughputChart.data.labels = timePoints;
    throughputChart.data.datasets[0].data = throughputData;
    throughputChart.update();
}

/**
 * Update metrics table
 */
function updateMetricsTable() {
    const metricsTable = document.getElementById('metrics-table');
    const metrics = metricsData.metrics;
    
    if (!metrics || metrics.length === 0) {
        metricsTable.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-4">
                    <i class="bi bi-info-circle text-muted me-2"></i>
                    No metrics found for the selected time range.
                </td>
            </tr>
        `;
        document.getElementById('metric-count').textContent = '0';
        return;
    }
    
    // Update metric count
    document.getElementById('metric-count').textContent = metrics.length.toString();
    
    // Build table rows for metrics
    const rowsHTML = metrics.slice(0, 100).map(metric => {
        // Format tags as badges
        const tags = metric.tags ? 
            Object.entries(metric.tags).map(([key, value]) => 
                `<span class="badge bg-secondary me-1">${key}=${value}</span>`
            ).join(' ') : '';
        
        return `
            <tr>
                <td>${formatDateTime(metric.timestamp)}</td>
                <td><code>${metric.name}</code></td>
                <td>${isNaN(metric.value) ? metric.value : metric.value.toFixed(2)}</td>
                <td>${tags || '<span class="text-muted">—</span>'}</td>
            </tr>
        `;
    }).join('');
    
    metricsTable.innerHTML = rowsHTML;
}

/**
 * Export metrics data
 */
function exportMetrics() {
    const metrics = metricsData.metrics;
    
    if (!metrics || metrics.length === 0) {
        alert('No metrics data available to export.');
        return;
    }
    
    // Create JSON data for download
    const jsonData = JSON.stringify(metrics, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    // Create download link
    const a = document.createElement('a');
    a.href = url;
    a.download = `syncservice-metrics-${formatDateForFilename(new Date())}.json`;
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
}

/**
 * Format date for filename
 */
function formatDateForFilename(date) {
    return date.toISOString().split('T')[0];
}

/**
 * Format date/time for display
 */
function formatDateTime(dateString, timeOnly = false) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    
    if (timeOnly) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    return date.toLocaleString();
}

/**
 * Refresh metrics data
 */
function refreshMetrics() {
    fetchMetricsData();
}

/**
 * Show error message
 */
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorAlert').classList.remove('d-none');
}