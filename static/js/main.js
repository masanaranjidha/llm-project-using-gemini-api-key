// Initialize markdown-it at the top of the file
const md = window.markdownit({
    html: true,
    linkify: true,
    typographer: true
});

// Debug utility with enhanced functionality
const debug = {
    enabled: true,
    logQueue: [],
    maxLogEntries: 100,

    init: function() {
        if (!this.enabled) return;
        this.setupDebugPanel();
        this.startPerformanceMonitoring();
        this.setupEventListeners();
    },

    setupDebugPanel: function() {
        const debugToggle = document.getElementById('debugToggle');
        const debugPanel = document.getElementById('debugPanel');
        
        if (debugToggle && debugPanel) {
            debugToggle.addEventListener('click', () => {
                debugPanel.classList.toggle('show');
                if (debugPanel.classList.contains('show')) {
                    this.updateSystemStatus();
                }
            });

            // Initialize system status updates
            this.updateSystemStatus();
            setInterval(() => {
                if (debugPanel.classList.contains('show')) {
                    this.updateSystemStatus();
                }
            }, 5000);
        }
    },

    updateSystemStatus: function() {
        fetch('/debug/status')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Debug status request failed');
                }
                return response.json();
            })
            .then(data => {
                const systemStatus = document.getElementById('systemStatus');
                const performanceMetrics = document.getElementById('performanceMetrics');
                
                if (systemStatus) {
                    systemStatus.innerHTML = this.formatSystemStatus(data);
                }
                if (performanceMetrics) {
                    performanceMetrics.innerHTML = this.formatPerformanceMetrics(data);
                }
            })
            .catch(error => {
                console.error('Debug status error:', error);
                const systemStatus = document.getElementById('systemStatus');
                if (systemStatus) {
                    systemStatus.innerHTML = `<div class="debug-error">Error fetching debug status: ${error.message}</div>`;
                }
            });
    },

    formatSystemStatus: function(data) {
        const dfInfo = data.current_data.df_info;
        return `
            <div class="status-item">
                <span class="status-indicator status-ok"></span>
                Environment: ${data.environment.flask_env || 'development'}
            </div>
            <div class="status-item">
                <span class="status-indicator ${data.debug_config.ENABLED ? 'status-ok' : 'status-error'}"></span>
                Debug Mode: ${data.debug_config.ENABLED ? 'Enabled' : 'Disabled'}
            </div>
            ${dfInfo ? `
            <div class="status-item">
                <span class="status-indicator status-ok"></span>
                DataFrame: ${dfInfo.shape[0]} rows × ${dfInfo.shape[1]} columns
            </div>` : ''}
        `;
    },

    formatPerformanceMetrics: function(data) {
        return `
            <div class="performance-metric">
                <span class="metric-label">Memory Usage:</span>
                <span class="metric-value">${this.formatBytes(data.memory_usage.used)}</span>
            </div>
            <div class="performance-metric">
                <span class="metric-label">Python Version:</span>
                <span class="metric-value">${data.environment.python_version.split(' ')[0]}</span>
            </div>
            ${data.current_data.chat_history.length ? `
            <div class="performance-metric">
                <span class="metric-label">Chat Messages:</span>
                <span class="metric-value">${data.current_data.chat_history.length}</span>
            </div>` : ''}
        `;
    },

    log: function(message, data = null) {
        if (this.enabled) {
            const timestamp = new Date().toISOString();
            const logEntry = {
                type: 'info',
                timestamp,
                message,
                data
            };
            
            this.addLogEntry(logEntry);
            console.log(`[${timestamp}] 🔍 ${message}`, data || '');
        }
    },

    error: function(message, error = null) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            type: 'error',
            timestamp,
            message,
            error
        };
        
        this.addLogEntry(logEntry);
        console.error(`[${timestamp}] ❌ ${message}`, error || '');
    },

    warn: function(message, data = null) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            type: 'warn',
            timestamp,
            message,
            data
        };
        
        this.addLogEntry(logEntry);
        console.warn(`[${timestamp}] ⚠️ ${message}`, data || '');
    },

    addLogEntry: function(entry) {
        this.logQueue.unshift(entry);
        if (this.logQueue.length > this.maxLogEntries) {
            this.logQueue.pop();
        }
        
        const logsContainer = document.getElementById('recentLogs');
        if (logsContainer) {
            logsContainer.innerHTML = this.formatLogEntries();
        }
    },

    formatLogEntries: function() {
        return this.logQueue.map(entry => `
            <div class="debug-log-entry">
                <span class="debug-log-time">${new Date(entry.timestamp).toLocaleTimeString()}</span>
                <span class="debug-log-type ${entry.type}">${entry.type.toUpperCase()}</span>
                <span class="debug-log-message">${entry.message}</span>
                ${entry.data ? `<pre class="debug-log-data">${JSON.stringify(entry.data, null, 2)}</pre>` : ''}
            </div>
        `).join('');
    },

    formatBytes: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    startPerformanceMonitoring: function() {
        if (window.performance && window.performance.memory) {
            setInterval(() => {
                const memory = window.performance.memory;
                this.log('Memory Usage', {
                    usedHeapSize: this.formatBytes(memory.usedJSHeapSize),
                    totalHeapSize: this.formatBytes(memory.totalJSHeapSize),
                    limit: this.formatBytes(memory.jsHeapSizeLimit)
                });
            }, 10000);
        }
    },

    setupEventListeners: function() {
        window.addEventListener('error', (event) => {
            this.error('Global error:', {
                message: event.message,
                source: event.filename,
                lineNo: event.lineno,
                colNo: event.colno,
                error: event.error?.stack
            });
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.error('Unhandled Promise rejection:', event.reason);
        });
    }
};

let currentData = null;
let currentDataframe = null;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize debug functionality
    debug.init();

    const dropZone = document.getElementById('dropZone');
    const uploadForm = document.getElementById('uploadForm');
    const csvFile = document.getElementById('csvFile');
    const queryInput = document.getElementById('queryInput');
    const queryBtn = document.getElementById('queryBtn');
    const clearChat = document.getElementById('clearChat');
    const chatMessages = document.getElementById('chatMessages');
    const statsSection = document.getElementById('statsSection');
    
    let currentFile = null;

    // Drag and drop handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleFile(file);
    });

    csvFile.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFile(file);
    });

    function handleFile(file) {
        if (!file || !file.name.endsWith('.csv')) {
            showNotification('Please select a CSV file', 'error');
            return;
        }

        showLoadingSpinner();
        const formData = new FormData();
        formData.append('file', file);
        currentFile = file;

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoadingSpinner();
            if (data.error) {
                throw new Error(data.error);
            }
            handleUploadSuccess(data, file.name);
        })
        .catch(error => {
            hideLoadingSpinner();
            showNotification(error.message, 'error');
        });
    }

    function handleUploadSuccess(data, fileName) {
        statsSection.classList.remove('d-none');
        document.getElementById('rowCount').textContent = data.stats.rows;
        document.getElementById('colCount').textContent = data.stats.columns;
        document.getElementById('previewContent').innerHTML = data.preview;
        
        // Enable chat interface
        queryInput.disabled = false;
        queryBtn.disabled = false;
        clearChat.disabled = false;

        // Add file info and delete button
        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info';
        fileInfo.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span><i class="fas fa-file-csv"></i> ${fileName}</span>
                <button class="delete-file" title="Delete file">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </div>
        `;
        
        const existingFileInfo = dropZone.querySelector('.file-info');
        if (existingFileInfo) {
            existingFileInfo.remove();
        }
        dropZone.appendChild(fileInfo);

        // Add delete handler
        fileInfo.querySelector('.delete-file').addEventListener('click', deleteFile);
        
        showNotification('File uploaded successfully!', 'success');
    }

    function deleteFile() {
        // Reset the interface
        statsSection.classList.add('d-none');
        queryInput.disabled = true;
        queryBtn.disabled = true;
        clearChat.disabled = true;
        
        // Clear the file input
        csvFile.value = '';
        currentFile = null;
        
        // Remove file info
        const fileInfo = dropZone.querySelector('.file-info');
        if (fileInfo) {
            fileInfo.remove();
        }

        // Clear chat messages
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <h4>Welcome! 👋</h4>
                <p>Upload a CSV file to start analyzing your data. I can help you:</p>
                <ul>
                    <li>Analyze trends and patterns</li>
                    <li>Calculate statistics</li>
                    <li>Generate insights</li>
                    <li>Answer questions about your data</li>
                </ul>
            </div>
        `;

        showNotification('File deleted successfully', 'success');
    }

    function showLoadingSpinner() {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.id = 'loadingSpinner';
        dropZone.appendChild(spinner);
    }

    function hideLoadingSpinner() {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.remove();
        }
    }

    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : 'success'} notification`;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '1000';
        notification.style.animation = 'fadeIn 0.3s ease';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Handle chat interaction
    queryBtn.addEventListener('click', sendQuery);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendQuery();
        }
    });

    function sendQuery() {
        const query = queryInput.value.trim();
        if (!query) return;

        // Add user message
        addMessage(query, 'user');
        queryInput.value = '';

        // Show typing indicator
        const typingIndicator = addTypingIndicator();

        // Send query to server
        fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        })
        .then(response => response.json())
        .then(data => {
            typingIndicator.remove();
            if (data.error) {
                throw new Error(data.error);
            }
            addMessage(data.response, 'assistant');
        })
        .catch(error => {
            typingIndicator.remove();
            showNotification(error.message, 'error');
        });
    }

    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        // For assistant messages, render as markdown
        if (type === 'assistant') {
            messageDiv.innerHTML = md.render(content);
        } else {
            // For user messages, keep as plain text
            messageDiv.textContent = content;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'message assistant-message typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return indicator;
    }

    // Handle chat clearing
    clearChat.addEventListener('click', () => {
        while (chatMessages.firstChild) {
            chatMessages.removeChild(chatMessages.firstChild);
        }
    });
});
