// File Organizer Web Interface JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initializeUI();
    
    // Check services status periodically
    checkStatus();
    setInterval(checkStatus, 30000); // Check every 30 seconds
    
    // Set up live log streaming if on logs page
    if (document.getElementById('logs-container')) {
        setupLogStreaming();
    }
    
    // Set up dark mode toggle
    setupDarkMode();
    
    // Set up file upload drag and drop
    setupDragAndDrop();
    
    // Initialize charts if on dashboard
    if (document.getElementById('stats-charts')) {
        initializeCharts();
    }
    
    // Set up organize form
    setupOrganizeForm();
});

function initializeUI() {
    // Set the current year in the footer
    const footerYear = document.querySelector('.current-year');
    if (footerYear) {
        footerYear.textContent = new Date().getFullYear();
    }
    
    // Initialize tooltips if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
    }
    
    // Initialize toasts if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const toastElList = document.querySelectorAll('.toast');
        toastElList.forEach(el => new bootstrap.Toast(el));
    }
    
    // Show flash messages
    const flashMessages = document.querySelectorAll('.toast.flash-message');
    flashMessages.forEach(toast => {
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    });
}

function checkStatus() {
    // Fetch the current status from the API
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateStatusIndicators(data.services);
            updateSystemInfo(data.system);
            
            // Show toast if status changed
            const apiStatus = document.getElementById('api-status');
            const n8nStatus = document.getElementById('n8n-status');
            
            if (apiStatus && apiStatus.dataset.prevStatus !== data.services.api.toString()) {
                showStatusChangeToast('API Server', data.services.api);
                apiStatus.dataset.prevStatus = data.services.api.toString();
            }
            
            if (n8nStatus && n8nStatus.dataset.prevStatus !== data.services.n8n.toString()) {
                showStatusChangeToast('n8n', data.services.n8n);
                n8nStatus.dataset.prevStatus = data.services.n8n.toString();
            }
        })
        .catch(error => {
            console.error('Error fetching status:', error);
        });
}

function updateStatusIndicators(services) {
    // Update API status indicator
    const apiStatus = document.getElementById('api-status');
    if (apiStatus) {
        apiStatus.className = services.api ? 'status-indicator online' : 'status-indicator offline';
        apiStatus.setAttribute('title', services.api ? 'API Server is online' : 'API Server is offline');
    }
    
    // Update n8n status indicator
    const n8nStatus = document.getElementById('n8n-status');
    if (n8nStatus) {
        n8nStatus.className = services.n8n ? 'status-indicator online' : 'status-indicator offline';
        n8nStatus.setAttribute('title', services.n8n ? 'n8n is online' : 'n8n is offline');
    }
    
    // Update restart buttons availability
    const restartButtons = document.querySelectorAll('.restart-btn');
    restartButtons.forEach(btn => {
        const service = btn.dataset.service;
        if (service === 'api') {
            btn.disabled = services.api;
            btn.title = services.api ? 'API Server is already running' : 'Restart API Server';
        } else if (service === 'n8n') {
            btn.disabled = services.n8n;
            btn.title = services.n8n ? 'n8n is already running' : 'Restart n8n';
        }
    });
}

function updateSystemInfo(systemInfo) {
    // Update system info in the UI
    document.querySelectorAll('[data-system="uptime"]').forEach(el => {
        el.textContent = systemInfo.uptime;
    });
    
    document.querySelectorAll('[data-system="cpu"]').forEach(el => {
        el.textContent = systemInfo.cpu_usage + '%';
    });
    
    document.querySelectorAll('[data-system="memory"]').forEach(el => {
        el.textContent = systemInfo.memory_usage + '%';
    });
    
    document.querySelectorAll('[data-system="disk"]').forEach(el => {
        el.textContent = systemInfo.disk_usage + '%';
    });
    
    document.querySelectorAll('[data-system="disk-free"]').forEach(el => {
        el.textContent = systemInfo.disk_free;
    });
    
    // Update progress bars
    document.querySelectorAll('[data-progress="cpu"]').forEach(el => {
        el.style.width = systemInfo.cpu_usage + '%';
        el.setAttribute('aria-valuenow', systemInfo.cpu_usage);
        
        // Change color based on usage
        if (systemInfo.cpu_usage > 80) {
            el.className = 'progress-bar bg-danger';
        } else if (systemInfo.cpu_usage > 60) {
            el.className = 'progress-bar bg-warning';
        } else {
            el.className = 'progress-bar bg-success';
        }
    });
    
    document.querySelectorAll('[data-progress="memory"]').forEach(el => {
        el.style.width = systemInfo.memory_usage + '%';
        el.setAttribute('aria-valuenow', systemInfo.memory_usage);
        
        // Change color based on usage
        if (systemInfo.memory_usage > 80) {
            el.className = 'progress-bar bg-danger';
        } else if (systemInfo.memory_usage > 60) {
            el.className = 'progress-bar bg-warning';
        } else {
            el.className = 'progress-bar bg-success';
        }
    });
    
    document.querySelectorAll('[data-progress="disk"]').forEach(el => {
        el.style.width = systemInfo.disk_usage + '%';
        el.setAttribute('aria-valuenow', systemInfo.disk_usage);
        
        // Change color based on usage
        if (systemInfo.disk_usage > 80) {
            el.className = 'progress-bar bg-danger';
        } else if (systemInfo.disk_usage > 60) {
            el.className = 'progress-bar bg-warning';
        } else {
            el.className = 'progress-bar bg-success';
        }
    });
    
    // Update charts if they exist
    updateCharts(systemInfo);
}

function showStatusChangeToast(service, isOnline) {
    // Create and show a toast notification
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.setAttribute('data-bs-delay', '3000');
    
    const statusClass = isOnline ? 'text-success' : 'text-danger';
    const statusText = isOnline ? 'online' : 'offline';
    
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${service} Status Change</strong>
            <small>${new Date().toLocaleTimeString()}</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${service} is now <span class="${statusClass}">${statusText}</span>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove the toast from DOM after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
}

function setupLogStreaming() {
    const logsContainer = document.getElementById('logs-content');
    if (!logsContainer) return;
    
    // Create SSE connection
    const evtSource = new EventSource('/logs/stream');
    
    evtSource.onmessage = function(event) {
        const logs = JSON.parse(event.data);
        
        if (logs.length > 0) {
            // Add new logs to the top of the list
            logs.forEach(log => {
                const logRow = document.createElement('tr');
                logRow.className = 'new-log';
                
                // Set row class based on log level
                if (log.level.includes('ERROR')) {
                    logRow.classList.add('table-danger');
                } else if (log.level.includes('WARNING')) {
                    logRow.classList.add('table-warning');
                } else if (log.level.includes('INFO')) {
                    logRow.classList.add('table-info');
                }
                
                logRow.innerHTML = `
                    <td>${log.timestamp}</td>
                    <td>${log.source}</td>
                    <td>${log.level}</td>
                    <td>${log.message}</td>
                `;
                
                logsContainer.prepend(logRow);
                
                // Highlight new log temporarily
                setTimeout(() => {
                    logRow.classList.remove('new-log');
                }, 2000);
            });
            
            // Limit the number of visible logs to prevent performance issues
            const logRows = logsContainer.querySelectorAll('tr');
            if (logRows.length > 200) {
                for (let i = 200; i < logRows.length; i++) {
                    logRows[i].remove();
                }
            }
        }
    };
    
    evtSource.onerror = function() {
        console.error('EventSource failed. Reconnecting in 5 seconds...');
        evtSource.close();
        setTimeout(setupLogStreaming, 5000);
    };
    
    // Clean up when leaving the page
    window.addEventListener('beforeunload', function() {
        evtSource.close();
    });
}

function setupDarkMode() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (!darkModeToggle) return;
    
    // Check for saved theme preference or use OS preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-bs-theme', 'dark');
        darkModeToggle.checked = true;
    }
    
    // Toggle theme when checkbox changes
    darkModeToggle.addEventListener('change', function() {
        if (this.checked) {
            document.documentElement.setAttribute('data-bs-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-bs-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });
}

function setupDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    if (!dropZone) return;
    
    // Prevent default behavior to enable drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropZone.classList.add('highlight');
    }
    
    function unhighlight() {
        dropZone.classList.remove('highlight');
    }
    
    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        handleFiles(files);
    }
    
    function handleFiles(files) {
        // Display selected files
        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '';
        
        Array.from(files).forEach(file => {
            const fileItem = document.createElement('li');
            fileItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            fileItem.innerHTML = `
                <span>${file.name}</span>
                <span class="badge bg-primary rounded-pill">${formatFileSize(file.size)}</span>
            `;
            fileList.appendChild(fileItem);
        });
        
        // Show organize button
        document.getElementById('organize-files-btn').classList.remove('d-none');
        
        // Prepare form data
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files[]', files[i]);
        }
        
        // Store files in a global variable for later use
        window.filesToOrganize = formData;
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Handle organize button click
    const organizeBtn = document.getElementById('organize-files-btn');
    if (organizeBtn) {
        organizeBtn.addEventListener('click', function() {
            if (!window.filesToOrganize) {
                showMessage('No files selected', 'error');
                return;
            }
            
            // Show loading spinner
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Organizing...';
            this.disabled = true;
            
            // Send files to API
            fetch('/api/organize-files', {
                method: 'POST',
                body: window.filesToOrganize
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('Files organized successfully', 'success');
                    // Clear file list
                    document.getElementById('file-list').innerHTML = '';
                    window.filesToOrganize = null;
                    // Hide organize button
                    organizeBtn.classList.add('d-none');
                } else {
                    showMessage('Error: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showMessage('Error: ' + error.message, 'error');
            })
            .finally(() => {
                // Reset button
                organizeBtn.innerHTML = 'Organize Files';
                organizeBtn.disabled = false;
            });
        });
    }
}

function setupOrganizeForm() {
    const organizeForm = document.getElementById('organize-form');
    if (!organizeForm) return;
    
    organizeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const sourceDir = document.getElementById('source-dir').value;
        const targetDir = document.getElementById('target-dir').value;
        
        // Disable form and show loading
        const submitBtn = organizeForm.querySelector('[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        submitBtn.disabled = true;
        
        // Prepare form data
        const formData = new FormData();
        formData.append('source_dir', sourceDir);
        formData.append('target_dir', targetDir);
        
        // Submit form via AJAX
        fetch('/organize-now', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                showMessage('Organization started successfully', 'success');
            } else {
                throw new Error('Failed to start organization');
            }
        })
        .catch(error => {
            showMessage('Error: ' + error.message, 'error');
        })
        .finally(() => {
            // Reset button
            submitBtn.innerHTML = originalBtnText;
            submitBtn.disabled = false;
        });
    });
}

function showMessage(message, type = 'info') {
    // Create toast notification
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Set toast header color based on message type
    let headerClass = 'bg-info text-white';
    let icon = 'info-circle';
    let title = 'Information';
    
    if (type === 'success') {
        headerClass = 'bg-success text-white';
        icon = 'check-circle';
        title = 'Success';
    } else if (type === 'error') {
        headerClass = 'bg-danger text-white';
        icon = 'exclamation-circle';
        title = 'Error';
    } else if (type === 'warning') {
        headerClass = 'bg-warning text-dark';
        icon = 'exclamation-triangle';
        title = 'Warning';
    }
    
    toast.innerHTML = `
        <div class="toast-header ${headerClass}">
            <i class="bi bi-${icon} me-2"></i>
            <strong class="me-auto">${title}</strong>
            <small>${new Date().toLocaleTimeString()}</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove the toast from DOM after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
}

// Chart functionality
let cpuChart, memoryChart, diskChart;

function initializeCharts() {
    if (typeof Chart === 'undefined') return;
    
    const cpuCtx = document.getElementById('cpu-chart');
    const memoryCtx = document.getElementById('memory-chart');
    const diskCtx = document.getElementById('disk-chart');
    
    if (cpuCtx) {
        cpuChart = new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: Array(10).fill(''),
                datasets: [{
                    label: 'CPU Usage (%)',
                    data: Array(10).fill(0),
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    fill: true,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                animation: {
                    duration: 1000
                }
            }
        });
    }
    
    if (memoryCtx) {
        memoryChart = new Chart(memoryCtx, {
            type: 'line',
            data: {
                labels: Array(10).fill(''),
                datasets: [{
                    label: 'Memory Usage (%)',
                    data: Array(10).fill(0),
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 2,
                    fill: true,
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                animation: {
                    duration: 1000
                }
            }
        });
    }
    
    if (diskCtx) {
        diskChart = new Chart(diskCtx, {
            type: 'doughnut',
            data: {
                labels: ['Used', 'Free'],
                datasets: [{
                    data: [0, 100],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1000
                }
            }
        });
    }
}

function updateCharts(systemInfo) {
    if (typeof Chart === 'undefined') return;
    
    // Update CPU chart
    if (cpuChart) {
        cpuChart.data.datasets[0].data.push(systemInfo.cpu_usage);
        cpuChart.data.datasets[0].data.shift();
        cpuChart.data.labels.push('');
        cpuChart.data.labels.shift();
        cpuChart.update();
    }
    
    // Update Memory chart
    if (memoryChart) {
        memoryChart.data.datasets[0].data.push(systemInfo.memory_usage);
        memoryChart.data.datasets[0].data.shift();
        memoryChart.data.labels.push('');
        memoryChart.data.labels.shift();
        memoryChart.update();
    }
    
    // Update Disk chart
    if (diskChart) {
        diskChart.data.datasets[0].data = [systemInfo.disk_usage, 100 - systemInfo.disk_usage];
        diskChart.update();
    }
} 