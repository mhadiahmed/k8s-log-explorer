// Kubernetes Log Explorer Web App JavaScript

let socket;
let currentPod = null;
let currentContainer = null;
let currentNamespace = null;
let isFollowing = false;
let logLines = [];
let searchResults = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    loadNamespaces();
    setupEventListeners();
});

function initializeSocket() {
    // Check if Socket.IO is available
    if (typeof io === 'undefined') {
        console.error('Socket.IO library not loaded. Real-time features will be disabled.');
        showToast('WebSocket unavailable - real-time features disabled', 'warning');
        return;
    }
    
    try {
        socket = io();
        
        socket.on('connect', function() {
            console.log('Socket connected');
            showToast('Connected to server', 'success');
        });
    
    socket.on('disconnect', function() {
        console.log('Socket disconnected');
        showToast('Disconnected from server', 'error');
    });
    
    socket.on('connect_error', function(error) {
        console.error('Socket connection error:', error);
        showToast('Connection error', 'error');
    });
    
    socket.on('log_line', function(data) {
        appendLogLine(data.line, data.line_number);
    });
    
    socket.on('log_error', function(data) {
        showToast(`Log error: ${data.error}`, 'error');
    });
    
    socket.on('stream_started', function(data) {
        showToast(`Started following logs for ${data.pod_name}`, 'success');
    });
    
    socket.on('stream_stopped', function(data) {
        showToast(`Stopped following logs for ${data.pod_name}`, 'info');
    });
    
    } catch (error) {
        console.error('Error initializing Socket.IO:', error);
        showToast('Failed to initialize WebSocket connection', 'error');
    }
}

function setupEventListeners() {
    // Enter key in search modal
    document.getElementById('searchTerm').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Auto-scroll when following logs
    const logContainer = document.getElementById('logContainer');
    logContainer.addEventListener('scroll', function() {
        // If user scrolls up while following, temporarily disable auto-scroll
        if (isFollowing && logContainer.scrollTop < logContainer.scrollHeight - logContainer.clientHeight - 100) {
            // User has scrolled up, they might want to read something
        }
    });
}

async function loadNamespaces() {
    try {
        console.log('Loading namespaces...');
        const response = await fetch('/api/namespaces');
        const data = await response.json();
        console.log('Namespaces response:', data);
        
        if (data.success) {
            const namespaceSelect = document.getElementById('namespaceSelect');
            if (!namespaceSelect) {
                console.error('namespaceSelect element not found');
                return;
            }
            
            namespaceSelect.innerHTML = '';
            
            data.namespaces.forEach(namespace => {
                const option = document.createElement('option');
                option.value = namespace;
                option.textContent = namespace;
                if (namespace === data.current) {
                    option.selected = true;
                    currentNamespace = namespace;
                }
                namespaceSelect.appendChild(option);
            });
            
            console.log(`Loaded ${data.namespaces.length} namespaces, current: ${currentNamespace}`);
            
            // Load pods for the current namespace
            loadPods();
        } else {
            console.error('Failed to load namespaces:', data.error);
            showToast(`Error loading namespaces: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Network error loading namespaces:', error);
        showToast(`Network error: ${error.message}`, 'error');
    }
}

async function loadPods() {
    try {
        showLoading();
        const namespace = currentNamespace || document.getElementById('namespaceSelect').value;
        console.log(`Loading pods for namespace: ${namespace}`);
        
        if (!namespace) {
            console.warn('No namespace selected, using default');
            currentNamespace = 'default';
        }
        
        const response = await fetch(`/api/pods?namespace=${namespace || 'default'}`);
        const data = await response.json();
        console.log('Pods response:', data);
        
        if (data.success) {
            displayPods(data.pods);
            showToast(`Loaded ${data.pods.length} pods from namespace: ${namespace || 'default'}`, 'info');
        } else {
            console.error('Failed to load pods:', data.error);
            showToast(`Error loading pods: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Network error loading pods:', error);
        showToast(`Network error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function onNamespaceChange() {
    const namespaceSelect = document.getElementById('namespaceSelect');
    currentNamespace = namespaceSelect.value;
    
    // Clear current selection and logs
    currentPod = null;
    document.getElementById('selectedPod').value = '';
    clearLogs();
    
    // Load pods for new namespace
    loadPods();
    
    showToast(`Switched to namespace: ${currentNamespace}`, 'info');
}

function displayPods(pods) {
    const podsList = document.getElementById('podsList');
    podsList.innerHTML = '';
    
    pods.forEach(pod => {
        const podItem = document.createElement('div');
        podItem.className = 'list-group-item list-group-item-action pod-item bg-dark text-light';
        podItem.onclick = () => selectPod(pod.name);
        
        const statusClass = pod.status.toLowerCase();
        const readyColor = pod.ready === pod.total_containers ? 'success' : 'warning';
        
        podItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${pod.name}</h6>
                    <small class="text-muted">Age: ${pod.age}</small>
                </div>
                <div class="text-end">
                    <span class="pod-status ${statusClass}">${pod.status}</span><br>
                    <small class="text-${readyColor}">${pod.ready}/${pod.total_containers} Ready</small>
                </div>
            </div>
        `;
        
        podsList.appendChild(podItem);
    });
}

async function selectPod(podName) {
    // Update UI
    document.querySelectorAll('.pod-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.pod-item').classList.add('active');
    
    currentPod = podName;
    document.getElementById('selectedPod').value = podName;
    
    // Load containers for this pod
    try {
        const namespace = currentNamespace || document.getElementById('namespaceSelect').value;
        const response = await fetch(`/api/pods/${podName}/containers?namespace=${namespace}`);
        const data = await response.json();
        
        if (data.success) {
            const containerSelect = document.getElementById('containerSelect');
            containerSelect.innerHTML = '<option value="">Default</option>';
            
            data.containers.forEach(container => {
                const option = document.createElement('option');
                option.value = container;
                option.textContent = container;
                containerSelect.appendChild(option);
            });
        }
    } catch (error) {
        showToast(`Error loading containers: ${error.message}`, 'error');
    }
    
    // Clear logs
    clearLogs();
}

async function loadLogs() {
    if (!currentPod) {
        showToast('Please select a pod first', 'warning');
        return;
    }
    
    const container = document.getElementById('containerSelect').value;
    const lines = document.getElementById('linesInput').value;
    const namespace = currentNamespace || document.getElementById('namespaceSelect').value;
    
    try {
        showLoading();
        const response = await fetch(`/api/pods/${currentPod}/logs?container=${container}&lines=${lines}&namespace=${namespace}`);
        const data = await response.json();
        
        if (data.success) {
            displayLogs(data.logs);
            showToast(`Loaded ${data.logs.length} log lines`, 'success');
        } else {
            showToast(`Error loading logs: ${data.error}`, 'error');
        }
    } catch (error) {
        showToast(`Network error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displayLogs(logs) {
    const logContent = document.getElementById('logContent');
    logContent.innerHTML = '';
    logLines = logs;
    
    logs.forEach((line, index) => {
        appendLogLine(line, index + 1);
    });
}

function appendLogLine(line, lineNumber) {
    const logContent = document.getElementById('logContent');
    const logLine = document.createElement('div');
    logLine.className = 'log-line';
    
    // Detect log level for styling
    let logLevel = '';
    if (line.toUpperCase().includes('ERROR')) {
        logLevel = 'log-error';
    } else if (line.toUpperCase().includes('WARN')) {
        logLevel = 'log-warn';
    } else if (line.toUpperCase().includes('INFO')) {
        logLevel = 'log-info';
    } else if (line.toUpperCase().includes('DEBUG')) {
        logLevel = 'log-debug';
    }
    
    if (logLevel) {
        logLine.classList.add(logLevel);
    }
    
    logLine.innerHTML = `
        <span class="log-line-number">${lineNumber}</span>
        <span class="log-content">${escapeHtml(line)}</span>
    `;
    
    logContent.appendChild(logLine);
    
    // Auto-scroll if following
    if (isFollowing) {
        const logContainer = document.getElementById('logContainer');
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

function toggleFollow() {
    if (!currentPod) {
        showToast('Please select a pod first', 'warning');
        return;
    }
    
    if (!socket) {
        showToast('WebSocket not available - cannot follow logs in real-time', 'error');
        return;
    }
    
    const followBtn = document.getElementById('followBtn');
    const container = document.getElementById('containerSelect').value;
    const namespace = currentNamespace || document.getElementById('namespaceSelect').value;
    
    if (isFollowing) {
        // Stop following
        socket.emit('stop_log_stream', {
            pod_name: currentPod,
            container: container,
            namespace: namespace
        });
        
        isFollowing = false;
        followBtn.innerHTML = '<i class="bi bi-play"></i> Follow';
        followBtn.classList.remove('btn-danger');
        followBtn.classList.add('btn-success');
        
        // Remove following indicator
        const indicator = document.querySelector('.following-indicator');
        if (indicator) {
            indicator.remove();
        }
    } else {
        // Start following
        socket.emit('start_log_stream', {
            pod_name: currentPod,
            container: container,
            namespace: namespace
        });
        
        isFollowing = true;
        followBtn.innerHTML = '<i class="bi bi-stop"></i> Stop';
        followBtn.classList.remove('btn-success');
        followBtn.classList.add('btn-danger');
        
        // Add following indicator
        const logContainer = document.getElementById('logContainer');
        const indicator = document.createElement('div');
        indicator.className = 'following-indicator';
        indicator.innerHTML = '<i class="bi bi-broadcast"></i> Following...';
        logContainer.style.position = 'relative';
        logContainer.appendChild(indicator);
        
        // Clear existing logs and start fresh
        clearLogs();
    }
}

function showSearchModal() {
    if (!currentPod) {
        showToast('Please select a pod first', 'warning');
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('searchModal'));
    modal.show();
    document.getElementById('searchTerm').focus();
}

async function performSearch() {
    const searchTerm = document.getElementById('searchTerm').value.trim();
    if (!searchTerm) {
        showToast('Please enter a search term', 'warning');
        return;
    }
    
    const container = document.getElementById('containerSelect').value;
    const contextLines = document.getElementById('contextLines').value;
    const maxLines = document.getElementById('maxSearchLines').value;
    const sinceHours = document.getElementById('sinceHours').value;
    const javaStack = document.getElementById('javaStack').checked;
    const namespace = currentNamespace || document.getElementById('namespaceSelect').value;
    
    try {
        showLoading();
        
        const params = new URLSearchParams({
            term: searchTerm,
            container: container,
            context: contextLines,
            max_lines: maxLines,
            java_stack: javaStack,
            namespace: namespace
        });
        
        if (sinceHours) {
            params.append('since_hours', sinceHours);
        }
        
        const response = await fetch(`/api/pods/${currentPod}/search?${params}`);
        const data = await response.json();
        
        if (data.success) {
            displaySearchResults(data);
            // Close the modal
            bootstrap.Modal.getInstance(document.getElementById('searchModal')).hide();
            showToast(`Found ${data.total_matches} matches for "${searchTerm}"`, 'success');
        } else {
            showToast(`Search error: ${data.error}`, 'error');
        }
    } catch (error) {
        showToast(`Network error: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

function displaySearchResults(data) {
    const logContent = document.getElementById('logContent');
    logContent.innerHTML = '';
    
    if (data.matches.length === 0) {
        logContent.innerHTML = `
            <div class="text-center p-4">
                <h5>No matches found</h5>
                <p class="text-muted">Try adjusting your search term or parameters.</p>
            </div>
        `;
        return;
    }
    
    data.matches.forEach((match, index) => {
        const matchBlock = document.createElement('div');
        matchBlock.className = 'search-match-block';
        
        const header = document.createElement('div');
        header.className = 'search-match-header';
        header.innerHTML = `Match ${index + 1} - Line ${match.line_number + 1}`;
        
        const content = document.createElement('div');
        content.className = 'search-match-content';
        
        match.context.forEach((line, lineIndex) => {
            const logLine = document.createElement('div');
            logLine.className = 'log-line';
            
            // Highlight the search term
            let displayLine = escapeHtml(line);
            const regex = new RegExp(`(${escapeRegex(data.search_term)})`, 'gi');
            displayLine = displayLine.replace(regex, '<span class="search-highlight">$1</span>');
            
            const actualLineNum = match.line_number + lineIndex - Math.floor(match.context.length / 2);
            
            logLine.innerHTML = `
                <span class="log-line-number">${actualLineNum + 1}</span>
                <span class="log-content">${displayLine}</span>
            `;
            
            content.appendChild(logLine);
        });
        
        matchBlock.appendChild(header);
        matchBlock.appendChild(content);
        logContent.appendChild(matchBlock);
    });
}

function clearLogs() {
    document.getElementById('logContent').innerHTML = '<p class="text-muted p-3">Logs cleared.</p>';
    logLines = [];
}

function downloadLogs() {
    if (logLines.length === 0) {
        showToast('No logs to download', 'warning');
        return;
    }
    
    const blob = new Blob([logLines.join('\n')], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentPod}_logs_${new Date().toISOString().slice(0, 19)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    showToast('Logs downloaded', 'success');
}

function filterPods() {
    const filter = document.getElementById('podFilter').value.toLowerCase();
    const podItems = document.querySelectorAll('.pod-item');
    
    podItems.forEach(item => {
        const podName = item.querySelector('h6').textContent.toLowerCase();
        if (podName.includes(filter)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

function clearFilter() {
    document.getElementById('podFilter').value = '';
    filterPods();
}

function refreshPods() {
    loadPods();
}

function refreshNamespaces() {
    loadNamespaces();
}

function showLoading() {
    // Add loading state to relevant buttons
    const buttons = document.querySelectorAll('button');
    buttons.forEach(btn => {
        if (!btn.disabled) {
            btn.disabled = true;
            btn.dataset.originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading-spinner"></span>';
        }
    });
}

function hideLoading() {
    const buttons = document.querySelectorAll('button');
    buttons.forEach(btn => {
        if (btn.dataset.originalText) {
            btn.disabled = false;
            btn.innerHTML = btn.dataset.originalText;
            delete btn.dataset.originalText;
        }
    });
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('statusToast');
    const toastBody = document.getElementById('toastBody');
    
    // Set toast color based on type
    toast.className = 'toast';
    switch (type) {
        case 'success':
            toast.classList.add('text-bg-success');
            break;
        case 'error':
            toast.classList.add('text-bg-danger');
            break;
        case 'warning':
            toast.classList.add('text-bg-warning');
            break;
        default:
            toast.classList.add('text-bg-info');
    }
    
    toastBody.textContent = message;
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}