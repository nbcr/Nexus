/**
 * Admin Logs Module
 * 
 * Handles:
 * - Log viewing (dynamically loaded from logs directory)
 * - Auto-refresh
 * - Log type switching
 */

let logsRefreshInterval = null;

// Initialize logs tab
async function initLogs() {
    await loadAvailableLogs();
    refreshLogs();
    startLogsAutoRefresh();
    
    // Listen for auto-refresh checkbox
    const autoRefreshCheckbox = document.getElementById('auto-refresh-logs');
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', function() {
            if (this.checked) {
                startLogsAutoRefresh();
            } else {
                stopLogsAutoRefresh();
            }
        });
    }
}

// Load available logs from backend
async function loadAvailableLogs() {
    const logTypeSelect = document.getElementById('log-type');
    if (!logTypeSelect) return;
    
    try {
        const response = await fetch('/api/v1/admin/logs/list', {
            credentials: 'include',
            headers: authManager.getAuthHeaders()
        });
        
        console.log('List logs response status:', response.status);
        
        if (!response.ok) {
            console.error('Failed to load available logs, status:', response.status);
            // Fallback to common logs
            loadFallbackLogs(logTypeSelect);
            return;
        }
        
        const data = await response.json();
        console.log('Available logs:', data);
        const logs = data.logs || [];
        
        // Clear existing options
        logTypeSelect.innerHTML = '';
        
        if (logs.length === 0) {
            console.warn('No logs found, using fallback');
            loadFallbackLogs(logTypeSelect);
            return;
        }
        
        // Add log files as options
        logs.forEach(log => {
            const option = document.createElement('option');
            // Use 'name' field as the key (it's the filename without .log)
            option.value = log.name;
            const sizeKB = (log.size / 1024).toFixed(1);
            option.textContent = `${log.filename} (${sizeKB}KB)`;
            logTypeSelect.appendChild(option);
        });
        
        // Set first log as default
        if (logs.length > 0) {
            logTypeSelect.value = logs[0].name;
        }
        
    } catch (error) {
        console.error('Error loading available logs:', error);
        loadFallbackLogs(logTypeSelect);
    }
}

// Fallback: load common log files if API fails
function loadFallbackLogs(logTypeSelect) {
    const commonLogs = [
        { key: 'error', name: 'error.log' },
        { key: 'access', name: 'access.log' },
        { key: 'service', name: 'service.log' },
        { key: 'nexus_service', name: 'nexus_service.log' }
    ];
    
    logTypeSelect.innerHTML = '';
    commonLogs.forEach(log => {
        const option = document.createElement('option');
        option.value = log.key;
        option.textContent = log.name;
        logTypeSelect.appendChild(option);
    });
    
    if (commonLogs.length > 0) {
        logTypeSelect.value = commonLogs[0].key;
    }
}

// Refresh logs
async function refreshLogs() {
    const logTypeSelect = document.getElementById('log-type');
    const logType = logTypeSelect?.value || '';
    const lines = document.getElementById('log-lines')?.value || 100;
    const logText = document.getElementById('log-text');
    
    if (!logText || !logType) {
        if (logText) logText.textContent = 'Please select a log file';
        return;
    }
    
    try {
        logText.textContent = 'Loading logs...';
        logText.classList.add('loading');
        
        // Ensure we have auth headers
        const headers = authManager.getAuthHeaders();
        console.log('Fetching log:', logType, 'Lines:', lines);
        
        const response = await fetch(`/api/v1/admin/logs/${logType}?lines=${lines}`, {
            credentials: 'include',
            headers: {
                ...headers,
                'Accept': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(`Failed to fetch logs (${response.status}): ${errorData.detail || response.statusText}`);
        }
        
        const data = await response.json();
        logText.textContent = data.content || 'No logs available';
        
    } catch (error) {
        console.error('Error fetching logs:', error);
        logText.textContent = `Error loading logs: ${error.message}`;
    } finally {
        logText.classList.remove('loading');
    }
}

// Start auto-refresh
function startLogsAutoRefresh() {
    stopLogsAutoRefresh(); // Clear any existing interval
    logsRefreshInterval = setInterval(refreshLogs, 10000); // 10 seconds
}

// Stop auto-refresh
function stopLogsAutoRefresh() {
    if (logsRefreshInterval) {
        clearInterval(logsRefreshInterval);
        logsRefreshInterval = null;
    }
}

// Export to global scope
globalThis.refreshLogs = refreshLogs;
globalThis.initLogs = initLogs;
