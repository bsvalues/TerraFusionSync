/**
 * TerraFusion Platform - Custom JavaScript
 */

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Set up AJAX request headers with CSRF token if available
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  if (csrfToken) {
    // Add CSRF token to all AJAX requests
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
      if (!options.headers) {
        options.headers = {};
      }
      
      if (typeof options.headers.append === 'function') {
        options.headers.append('X-CSRF-Token', csrfToken);
      } else {
        options.headers['X-CSRF-Token'] = csrfToken;
      }
      
      return originalFetch(url, options);
    };
  }
  
  // Initialize tooltips
  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  if (tooltips.length > 0 && typeof bootstrap !== 'undefined') {
    tooltips.forEach(tooltip => {
      new bootstrap.Tooltip(tooltip);
    });
  }
  
  // Initialize popovers
  const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
  if (popovers.length > 0 && typeof bootstrap !== 'undefined') {
    popovers.forEach(popover => {
      new bootstrap.Popover(popover);
    });
  }
  
  // Add active class to sidebar nav links based on current page
  const currentPath = window.location.pathname;
  const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
  sidebarLinks.forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });
  
  // Handle form validation
  const forms = document.querySelectorAll('.needs-validation');
  Array.from(forms).forEach(form => {
    form.addEventListener('submit', event => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    }, false);
  });
  
  // Setup JSON editor for configuration fields
  setupJsonEditors();
  
  // Initialize any charts on the page
  initializeCharts();
});

/**
 * Initialize charts on the dashboard
 */
function initializeCharts() {
  // System metrics chart (if exists)
  const systemMetricsCanvas = document.getElementById('systemMetricsChart');
  if (systemMetricsCanvas && typeof Chart !== 'undefined') {
    fetch('/api/v1/system/metrics')
      .then(response => response.json())
      .then(data => {
        const ctx = systemMetricsCanvas.getContext('2d');
        new Chart(ctx, {
          type: 'line',
          data: {
            labels: data.timestamps,
            datasets: [
              {
                label: 'CPU Usage (%)',
                data: data.cpu,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
                tension: 0.3
              },
              {
                label: 'Memory Usage (%)',
                data: data.memory,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderWidth: 2,
                tension: 0.3
              }
            ]
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: 'top',
              },
              title: {
                display: true,
                text: 'System Resource Usage'
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                max: 100
              }
            }
          }
        });
      })
      .catch(error => {
        console.error('Error fetching system metrics:', error);
        systemMetricsCanvas.parentNode.innerHTML = '<div class="alert alert-danger">Failed to load system metrics</div>';
      });
  }
  
  // Sync operations chart (if exists)
  const syncOperationsCanvas = document.getElementById('syncOperationsChart');
  if (syncOperationsCanvas && typeof Chart !== 'undefined') {
    fetch('/api/v1/sync-operations/stats')
      .then(response => response.json())
      .then(data => {
        const ctx = syncOperationsCanvas.getContext('2d');
        new Chart(ctx, {
          type: 'bar',
          data: {
            labels: data.days,
            datasets: [
              {
                label: 'Completed',
                data: data.completed,
                backgroundColor: 'rgba(40, 167, 69, 0.7)'
              },
              {
                label: 'Failed',
                data: data.failed,
                backgroundColor: 'rgba(220, 53, 69, 0.7)'
              }
            ]
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: 'top',
              },
              title: {
                display: true,
                text: 'Sync Operations (Last 7 Days)'
              }
            },
            scales: {
              x: {
                stacked: true,
              },
              y: {
                stacked: true,
                beginAtZero: true
              }
            }
          }
        });
      })
      .catch(error => {
        console.error('Error fetching sync operation stats:', error);
        syncOperationsCanvas.parentNode.innerHTML = '<div class="alert alert-danger">Failed to load sync statistics</div>';
      });
  }
}

/**
 * Setup JSON editors for configuration fields
 */
function setupJsonEditors() {
  document.querySelectorAll('.json-editor').forEach(textarea => {
    try {
      // Format JSON if it exists
      if (textarea.value && textarea.value.trim() !== '') {
        const parsed = JSON.parse(textarea.value);
        textarea.value = JSON.stringify(parsed, null, 2);
      }
      
      // Add validation on blur
      textarea.addEventListener('blur', function() {
        try {
          if (this.value && this.value.trim() !== '') {
            const parsed = JSON.parse(this.value);
            this.value = JSON.stringify(parsed, null, 2);
            this.classList.remove('is-invalid');
            this.classList.add('is-valid');
          }
        } catch (e) {
          this.classList.remove('is-valid');
          this.classList.add('is-invalid');
          
          // Show error message if there's a feedback element
          const feedback = this.nextElementSibling;
          if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.textContent = 'Invalid JSON: ' + e.message;
          }
        }
      });
    } catch (e) {
      console.error('Error setting up JSON editor:', e);
    }
  });
}

/**
 * Format a date as a relative time string (e.g., "2 hours ago")
 */
function formatRelativeTime(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.round(diffMs / 1000);
  const diffMin = Math.round(diffSec / 60);
  const diffHour = Math.round(diffMin / 60);
  const diffDay = Math.round(diffHour / 24);
  
  if (diffSec < 60) {
    return diffSec + ' seconds ago';
  } else if (diffMin < 60) {
    return diffMin + ' minutes ago';
  } else if (diffHour < 24) {
    return diffHour + ' hours ago';
  } else if (diffDay < 30) {
    return diffDay + ' days ago';
  } else {
    return date.toLocaleDateString();
  }
}

/**
 * Calculate and format success rate percentage
 */
function calculateSuccessRate(succeeded, total) {
  if (!total) return '0';
  const rate = (succeeded / total) * 100;
  return rate.toFixed(1);
}

/**
 * Show a notification toast
 */
function showNotification(message, type = 'info') {
  // Check if we have the toast container, create if not
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(toastContainer);
  }
  
  // Create the toast element
  const toastId = 'toast-' + Date.now();
  const toast = document.createElement('div');
  toast.id = toastId;
  toast.className = `toast align-items-center text-white bg-${type}`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');
  
  // Create toast content
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        ${message}
      </div>
      <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;
  
  // Add the toast to the container
  toastContainer.appendChild(toast);
  
  // Initialize and show the toast
  if (typeof bootstrap !== 'undefined') {
    const toastInstance = new bootstrap.Toast(toast);
    toastInstance.show();
    
    // Remove the toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
      this.remove();
    });
  }
}