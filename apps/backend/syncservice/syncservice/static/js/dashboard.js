// Dashboard JavaScript for TerraFusion SyncService
'use strict';

// Chart instances
let cpuChart = null;
let memoryChart = null;
let diskChart = null;
let entitiesChart = null;

// Refresh intervals
const REFRESH_INTERVAL = 30000; // 30 seconds
let refreshInterval = null;

// Color schemes
const CHART_COLORS = {
    blue: 'rgba(54, 162, 235, 0.7)',
    lightBlue: 'rgba(54, 162, 235, 0.3)',
    green: 'rgba(75, 192, 192, 0.7)',
    lightGreen: 'rgba(75, 192, 192, 0.3)',
    red: 'rgba(255, 99, 132, 0.7)',
    lightRed: 'rgba(255, 99, 132, 0.3)',
    yellow: 'rgba(255, 205, 86, 0.7)',
    lightYellow: 'rgba(255, 205, 86, 0.3)',
    purple: 'rgba(153, 102, 255, 0.7)',
    lightPurple: 'rgba(153, 102, 255, 0.3)',
    orange: 'rgba(255, 159, 64, 0.7)',
    lightOrange: 'rgba(255, 159, 64, 0.3)',
    grey: 'rgba(201, 203, 207, 0.7)',
    lightGrey: 'rgba(201, 203, 207, 0.3)'
};

// Format bytes to human-readable format
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Format date to human-readable format
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Format relative time
function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) {
        return 'just now';
    }
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
        return `${minutes}m ago`;
    }
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
        return `${hours}h ago`;
    }
    
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}

// Show error message
function showError(message) {
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    
    errorMessage.textContent = message;
    errorAlert.style.display = 'block';
}

// Initialize charts
function initCharts() {
    // CPU Chart
    const cpuCtx = document.getElementById('cpuChart').getContext('2d');
    cpuChart = new Chart(cpuCtx, {
        type: 'doughnut',
        data: {
            labels: ['User', 'System', 'Idle'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    CHART_COLORS.blue,
                    CHART_COLORS.green,
                    CHART_COLORS.grey
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.formattedValue + '%';
                        }
                    }
                }
            }
        }
    });
    
    // Memory Chart
    const memoryCtx = document.getElementById('memoryChart').getContext('2d');
    memoryChart = new Chart(memoryCtx, {
        type: 'doughnut',
        data: {
            labels: ['Used', 'Available'],
            datasets: [{
                data: [0, 0],
                backgroundColor: [
                    CHART_COLORS.red,
                    CHART_COLORS.green
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            return context.label + ': ' + formatBytes(value);
                        }
                    }
                }
            }
        }
    });
    
    // Disk Chart
    const diskCtx = document.getElementById('diskChart').getContext('2d');
    diskChart = new Chart(diskCtx, {
        type: 'doughnut',
        data: {
            labels: ['Used', 'Free'],
            datasets: [{
                data: [0, 0],
                backgroundColor: [
                    CHART_COLORS.orange,
                    CHART_COLORS.green
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            return context.label + ': ' + formatBytes(value);
                        }
                    }
                }
            }
        }
    });
    
    // Initialize entities chart (with no data yet)
    const entitiesCtx = document.getElementById('entitiesChart').getContext('2d');
    entitiesChart = new Chart(entitiesCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Succeeded',
                    backgroundColor: CHART_COLORS.green,
                    data: []
                },
                {
                    label: 'Failed',
                    backgroundColor: CHART_COLORS.red,
                    data: []
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });
}

// Fetch dashboard summary data
async function fetchDashboardSummary() {
    try {
        const response = await fetch('/dashboard/summary');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        showError(`Failed to fetch dashboard data: ${error.message}`);
        console.error('Error fetching dashboard data:', error);
        return null;
    }
}

// Update system metrics charts and displays
function updateSystemMetrics(systemMetrics) {
    if (!systemMetrics) return;
    
    // CPU metrics
    const cpuPercent = systemMetrics.cpu.usage_percent || 0;
    const cpuUser = systemMetrics.cpu.user_percent || 0;
    const cpuSystem = systemMetrics.cpu.system_percent || 0;
    const cpuIdle = systemMetrics.cpu.idle_percent || 0;
    
    document.getElementById('cpuMetric').textContent = `${cpuPercent.toFixed(1)}% Used`;
    
    // Update CPU chart
    cpuChart.data.datasets[0].data = [cpuUser, cpuSystem, cpuIdle];
    cpuChart.update();
    
    // Memory metrics
    const memoryTotal = systemMetrics.memory.total_bytes || 0;
    const memoryUsed = systemMetrics.memory.used_bytes || 0;
    const memoryAvailable = systemMetrics.memory.available_bytes || 0;
    const memoryPercent = systemMetrics.memory.usage_percent || 0;
    
    document.getElementById('memoryMetric').textContent = 
        `${formatBytes(memoryUsed)} / ${formatBytes(memoryTotal)} (${memoryPercent.toFixed(1)}%)`;
    
    // Update Memory chart
    memoryChart.data.datasets[0].data = [memoryUsed, memoryAvailable];
    memoryChart.update();
    
    // Disk metrics
    const diskTotal = systemMetrics.disk.total_bytes || 0;
    const diskUsed = systemMetrics.disk.used_bytes || 0;
    const diskFree = systemMetrics.disk.free_bytes || 0;
    const diskPercent = systemMetrics.disk.usage_percent || 0;
    
    document.getElementById('diskMetric').textContent = 
        `${formatBytes(diskUsed)} / ${formatBytes(diskTotal)} (${diskPercent.toFixed(1)}%)`;
    
    // Update Disk chart
    diskChart.data.datasets[0].data = [diskUsed, diskFree];
    diskChart.update();
    
    // Process metrics
    const processCpu = systemMetrics.process.cpu_percent || 0;
    const processMemoryRss = systemMetrics.process.memory_rss_bytes || 0;
    const processThreads = systemMetrics.process.threads || 0;
    const processConnections = systemMetrics.process.connections || 0;
    
    document.getElementById('processCpuUsage').textContent = `${processCpu.toFixed(1)}%`;
    document.getElementById('processCpuBar').style.width = `${processCpu}%`;
    
    document.getElementById('processMemoryRss').textContent = formatBytes(processMemoryRss);
    // Set memory bar as percentage of total system memory
    const memoryRssPercent = (processMemoryRss / memoryTotal) * 100;
    document.getElementById('processMemoryRssBar').style.width = `${memoryRssPercent}%`;
    
    document.getElementById('processThreads').textContent = processThreads;
    document.getElementById('processConnections').textContent = processConnections;
    
    // Process metrics header
    document.getElementById('processMetric').textContent = 
        `CPU: ${processCpu.toFixed(1)}%, Memory: ${formatBytes(processMemoryRss)}`;
}

// Update sync metrics and status
function updateSyncMetrics(syncMetrics, syncStatus) {
    if (!syncMetrics || !syncStatus) return;
    
    // Overview stats
    document.getElementById('totalSyncs').textContent = syncStatus.total_syncs || 0;
    document.getElementById('successRate').textContent = `${syncMetrics.success_rate || 0}%`;
    document.getElementById('activeJobs').textContent = (syncStatus.active_syncs || []).length;
    document.getElementById('avgDuration').textContent = syncMetrics.average_duration || 0;
    
    // Active syncs table
    const activeSyncTable = document.getElementById('activeSyncTable');
    const activeSyncs = syncStatus.active_syncs || [];
    
    if (activeSyncs.length === 0) {
        activeSyncTable.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">No active sync operations</td>
            </tr>
        `;
    } else {
        activeSyncTable.innerHTML = '';
        
        activeSyncs.forEach(sync => {
            const row = document.createElement('tr');
            
            // Format sync ID as truncated string
            const syncId = sync.sync_id.substring(0, 8) + '...';
            
            // Calculate time since started
            const startedAt = sync.started_at ? timeAgo(sync.started_at) : 'N/A';
            
            row.innerHTML = `
                <td>${syncId}</td>
                <td>${sync.sync_type}</td>
                <td>${sync.source_system} → ${sync.target_system}</td>
                <td>
                    <div class="progress">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" 
                             style="width: ${sync.progress_percent}%">
                            ${sync.progress_percent}%
                        </div>
                    </div>
                </td>
                <td>${sync.processed_records} / ${sync.total_records}</td>
                <td>${startedAt}</td>
                <td><span class="badge bg-info badge-status">${sync.status}</span></td>
            `;
            
            activeSyncTable.appendChild(row);
        });
    }
    
    // Completed syncs table
    const completedSyncTable = document.getElementById('completedSyncTable');
    const completedSyncs = syncStatus.recently_completed || [];
    
    if (completedSyncs.length === 0) {
        completedSyncTable.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">No completed sync operations</td>
            </tr>
        `;
    } else {
        completedSyncTable.innerHTML = '';
        
        completedSyncs.forEach(sync => {
            const row = document.createElement('tr');
            
            // Format sync ID as truncated string
            const syncId = sync.sync_id.substring(0, 8) + '...';
            
            // Calculate duration
            const duration = sync.duration_seconds ? 
                `${Math.round(sync.duration_seconds)}s` : 'N/A';
            
            // Time completed
            const completedAt = sync.completed_at ? 
                timeAgo(sync.completed_at) : 'N/A';
            
            row.innerHTML = `
                <td>${syncId}</td>
                <td>${sync.sync_type}</td>
                <td>${sync.succeeded_records}/${sync.total_records}</td>
                <td>${duration}</td>
                <td>${completedAt}</td>
            `;
            
            completedSyncTable.appendChild(row);
        });
    }
    
    // Failed syncs table
    const failedSyncTable = document.getElementById('failedSyncTable');
    const failedSyncs = syncStatus.recently_failed || [];
    
    if (failedSyncs.length === 0) {
        failedSyncTable.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">No failed sync operations</td>
            </tr>
        `;
    } else {
        failedSyncTable.innerHTML = '';
        
        failedSyncs.forEach(sync => {
            const row = document.createElement('tr');
            
            // Format sync ID as truncated string
            const syncId = sync.sync_id.substring(0, 8) + '...';
            
            // Truncate error message
            const errorMessage = sync.error_message ? 
                (sync.error_message.length > 50 ? 
                    sync.error_message.substring(0, 50) + '...' : 
                    sync.error_message) : 
                'Unknown error';
            
            // Time failed
            const failedAt = sync.completed_at ? 
                timeAgo(sync.completed_at) : 'N/A';
            
            row.innerHTML = `
                <td>${syncId}</td>
                <td>${sync.sync_type}</td>
                <td>${errorMessage}</td>
                <td>${failedAt}</td>
            `;
            
            failedSyncTable.appendChild(row);
        });
    }
}

// Update entity metrics
function updateEntityMetrics(syncMetrics) {
    if (!syncMetrics || !syncMetrics.entity_metrics) return;
    
    const entityMetrics = syncMetrics.entity_metrics;
    const entityTypes = Object.keys(entityMetrics);
    
    if (entityTypes.length === 0) {
        document.getElementById('entityTable').innerHTML = `
            <tr>
                <td colspan="5" class="text-center">No entity metrics available</td>
            </tr>
        `;
        return;
    }
    
    // Update entity table
    const entityTable = document.getElementById('entityTable');
    entityTable.innerHTML = '';
    
    entityTypes.forEach(type => {
        const metrics = entityMetrics[type];
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${type}</td>
            <td>
                <div class="progress">
                    <div class="progress-bar bg-success" 
                         role="progressbar" 
                         style="width: ${metrics.success_rate}%">
                        ${metrics.success_rate}%
                    </div>
                </div>
            </td>
            <td>${metrics.succeeded_records}</td>
            <td>${metrics.failed_records}</td>
            <td>${metrics.total_records}</td>
        `;
        
        entityTable.appendChild(row);
    });
    
    // Update entities chart
    const labels = entityTypes;
    const succeededData = entityTypes.map(type => entityMetrics[type].succeeded_records);
    const failedData = entityTypes.map(type => entityMetrics[type].failed_records);
    
    entitiesChart.data.labels = labels;
    entitiesChart.data.datasets[0].data = succeededData;
    entitiesChart.data.datasets[1].data = failedData;
    entitiesChart.update();
}

// Refresh all dashboard data
async function refreshDashboard() {
    // Mark last updated time
    const now = new Date();
    document.getElementById('lastUpdated').textContent = 
        `Last updated: ${now.toLocaleTimeString()}`;
    
    // Fetch dashboard summary
    const data = await fetchDashboardSummary();
    
    if (data) {
        // Update system metrics
        updateSystemMetrics(data.system_metrics);
        
        // Update sync metrics and status
        updateSyncMetrics(data.sync_metrics, data.sync_status);
        
        // Update entity metrics
        updateEntityMetrics(data.sync_metrics);
    }
}

// Document ready event
document.addEventListener('DOMContentLoaded', () => {
    // Initialize charts
    initCharts();
    
    // Initial data load
    refreshDashboard();
    
    // Set up refresh interval
    refreshInterval = setInterval(refreshDashboard, REFRESH_INTERVAL);
    
    // Add event listener for manual refresh
    document.getElementById('refreshBtn').addEventListener('click', () => {
        refreshDashboard();
    });
    
    // Add event listener for sync refresh
    document.getElementById('refreshSyncBtn').addEventListener('click', () => {
        refreshDashboard();
    });
});