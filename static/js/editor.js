// ============================================
// Manim Studio — Editor Logic & Rendering
// ============================================

let editor = null;
let currentJobId = null;
let currentVideoUrl = null;
let currentFilename = null;
let cachedExamples = null;
let renderHistory = [];
let syntaxCheckTimeout = null;
let dockerAvailable = false;

// Default Manim code
const DEFAULT_CODE = `from manim import *

class MyAnimation(Scene):
    def construct(self):
        # Create a circle
        circle = Circle()
        circle.set_fill(BLUE, opacity=0.5)
        circle.set_stroke(WHITE, width=4)

        # Create a label
        label = Text("Hello, Manim!", font_size=36)
        label.next_to(circle, DOWN, buff=0.5)

        # Animate
        self.play(Create(circle))
        self.play(Write(label))
        self.wait(2)
`;

// Initialize Monaco Editor
require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });

require(['vs/editor/editor.main'], function () {
    // Define custom dark theme
    monaco.editor.defineTheme('manim-dark', {
        base: 'vs-dark',
        inherit: true,
        rules: [
            { token: 'comment', foreground: '606078', fontStyle: 'italic' },
            { token: 'keyword', foreground: 'c792ea' },
            { token: 'string', foreground: 'c3e88d' },
            { token: 'number', foreground: 'f78c6c' },
            { token: 'type', foreground: 'ffcb6b' },
            { token: 'function', foreground: '82aaff' },
            { token: 'variable', foreground: 'e8e8f0' },
            { token: 'operator', foreground: '89ddff' },
            { token: 'delimiter', foreground: '89ddff' },
            { token: 'class', foreground: 'ffcb6b' },
        ],
        colors: {
            'editor.background': '#0d0d14',
            'editor.foreground': '#e8e8f0',
            'editor.lineHighlightBackground': '#1a1a2e80',
            'editor.selectionBackground': '#3d3d5c40',
            'editorCursor.foreground': '#a78bfa',
            'editorLineNumber.foreground': '#404060',
            'editorLineNumber.activeForeground': '#a78bfa',
            'editor.inactiveSelectionBackground': '#3d3d5c20',
            'editorWidget.background': '#12121a',
            'editorWidget.border': '#2a2a40',
            'editorSuggestWidget.background': '#12121a',
            'editorSuggestWidget.border': '#2a2a40',
            'editorSuggestWidget.selectedBackground': '#1a1a3080',
            'input.background': '#0d0d14',
            'input.border': '#2a2a40',
            'scrollbar.shadow': '#00000000',
            'scrollbarSlider.background': '#2a2a4040',
            'scrollbarSlider.hoverBackground': '#3a3a5060',
        }
    });

    editor = monaco.editor.create(document.getElementById('editor'), {
        value: DEFAULT_CODE,
        language: 'python',
        theme: 'manim-dark',
        fontSize: 14,
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        fontLigatures: true,
        lineNumbers: 'on',
        minimap: { enabled: false },
        padding: { top: 16, bottom: 16 },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 4,
        renderLineHighlight: 'line',
        cursorBlinking: 'smooth',
        cursorSmoothCaretAnimation: 'on',
        smoothScrolling: true,
        wordWrap: 'on',
        bracketPairColorization: { enabled: true },
        suggest: {
            showKeywords: true,
            showSnippets: true,
        },
    });

    // Keyboard shortcut: Ctrl/Cmd + Enter to render
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, function () {
        renderCode();
    });

    // Syntax validation on content change (debounced)
    editor.onDidChangeModelContent(function () {
        clearTimeout(syntaxCheckTimeout);
        syntaxCheckTimeout = setTimeout(() => validateSyntax(), 500);
    });

    // Initial validation
    setTimeout(() => validateSyntax(), 500);

    // Load examples and history
    loadExamples();
    loadHistory();
    checkDockerStatus();
});

// ============================================
// Syntax Validation
// ============================================
async function validateSyntax() {
    if (!editor) return;

    const code = editor.getValue();
    const indicator = document.getElementById('syntax-indicator');
    const statusEl = document.getElementById('syntax-status');

    if (!code.trim()) {
        setSyntaxStatus('ok', 'No code');
        return;
    }

    try {
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });

        const data = await response.json();

        if (data.valid && data.warnings.length === 0) {
            setSyntaxStatus('ok', 'No issues');
        } else if (data.valid && data.warnings.length > 0) {
            setSyntaxStatus('warning', `${data.warnings.length} warning${data.warnings.length > 1 ? 's' : ''}`);
        } else if (!data.valid && data.errors.length > 0) {
            const err = data.errors[0];
            setSyntaxStatus('error', `Line ${err.line}: ${err.message}`);
        } else {
            setSyntaxStatus('ok', 'No issues');
        }
    } catch (err) {
        // Network error during validation - don't show error
        setSyntaxStatus('ok', 'No issues');
    }
}

function setSyntaxStatus(type, message) {
    const indicator = document.getElementById('syntax-indicator');
    const statusEl = document.getElementById('syntax-status');

    indicator.className = 'syntax-indicator' + (type === 'error' ? ' error' : type === 'warning' ? ' warning' : '');

    if (type === 'ok') {
        indicator.innerHTML = '<i class="fas fa-check-circle"></i><span>OK</span>';
    } else if (type === 'error') {
        indicator.innerHTML = '<i class="fas fa-times-circle"></i><span>Error</span>';
    } else if (type === 'warning') {
        indicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i><span>Warn</span>';
    }

    statusEl.className = 'syntax-status' + (type === 'error' ? ' error' : type === 'warning' ? ' warning' : '');
    statusEl.innerHTML = `<i class="fas ${type === 'ok' ? 'fa-check-circle' : type === 'error' ? 'fa-times-circle' : 'fa-exclamation-triangle'}"></i> ${message}`;
}

// ============================================
// Docker Status
// ============================================
async function checkDockerStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        dockerAvailable = data.docker_available;

        const dockerIcon = document.getElementById('docker-status');
        const renderMode = document.getElementById('render-mode');

        if (dockerAvailable) {
            dockerIcon.classList.add('available');
            dockerIcon.title = 'Docker sandboxing available';
            renderMode.textContent = 'Docker';
        } else {
            dockerIcon.classList.remove('available');
            dockerIcon.title = 'Docker not available — using local rendering';
            renderMode.textContent = 'Local';
        }
    } catch (err) {
        // Status check failed
    }
}

// ============================================
// Render Code
// ============================================
async function renderCode() {
    const code = editor.getValue();
    if (!code.trim()) {
        showToast('Please write some code first', 'error');
        return;
    }

    const quality = document.getElementById('quality-select').value;
    const renderBtn = document.getElementById('render-btn');
    const statusText = document.getElementById('status-text');
    const statusInfo = document.getElementById('status-info');

    // Update UI
    renderBtn.classList.add('rendering');
    renderBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Rendering...</span>';
    statusText.textContent = 'Rendering...';
    statusInfo.textContent = dockerAvailable ? 'Docker sandbox' : 'Local render';

    showLoading();

    try {
        const response = await fetch('/api/render', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, quality, use_docker: dockerAvailable })
        });

        const data = await response.json();

        if (data.success) {
            currentJobId = data.job_id;
            currentVideoUrl = data.video_url;
            currentFilename = data.filename;

            showVideo(data.video_url);
            showToast('Animation rendered successfully!', 'success');
            statusText.textContent = 'Ready';
            statusInfo.textContent = data.rendered_in === 'docker' ? 'Docker · Rendered' : 'Local · Rendered';
        } else {
            showError(data.error || 'Render failed', data.details);
            statusText.textContent = 'Render failed';
            statusInfo.textContent = 'Error';
        }

        // Refresh history
        loadHistory();
    } catch (err) {
        showError('Connection error', err.message);
        statusText.textContent = 'Error';
        statusInfo.textContent = 'Connection error';
    } finally {
        renderBtn.classList.remove('rendering');
        renderBtn.innerHTML = '<i class="fas fa-play"></i><span>Render</span>';
    }
}

// ============================================
// UI State Management
// ============================================
function showLoading() {
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('loading-state').style.display = 'flex';
    document.getElementById('error-state').style.display = 'none';
    document.getElementById('video-container').style.display = 'none';
    document.getElementById('output-actions').style.display = 'none';
}

function showVideo(url) {
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('error-state').style.display = 'none';
    document.getElementById('video-container').style.display = 'flex';
    document.getElementById('output-actions').style.display = 'flex';

    const video = document.getElementById('video-player');
    video.onerror = function() {
        showError('Video failed to load', 'The rendered file may be corrupted or still processing.');
    };
    video.src = url;
    video.load();
}

function showError(message, details) {
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('error-state').style.display = 'flex';
    document.getElementById('video-container').style.display = 'none';
    document.getElementById('output-actions').style.display = 'none';

    const errorMsg = document.getElementById('error-message');
    errorMsg.textContent = details ? `${message}\n\n${details}` : message;
}

function clearOutput() {
    document.getElementById('empty-state').style.display = 'flex';
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('error-state').style.display = 'none';
    document.getElementById('video-container').style.display = 'none';
    document.getElementById('output-actions').style.display = 'none';
    document.getElementById('status-text').textContent = 'Ready';
    document.getElementById('status-info').textContent = 'Python 3 · Manim CE';
}

// ============================================
// Download Video
// ============================================
function downloadVideo() {
    if (currentJobId && currentFilename) {
        window.location.href = `/api/download/${currentJobId}/${currentFilename}`;
    }
}

// ============================================
// View Switching
// ============================================
function switchView(view) {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
    document.querySelectorAll('.view-panel').forEach(panel => {
        panel.style.display = 'none';
        panel.classList.remove('active');
    });

    const viewEl = document.getElementById(`${view}-view`);
    if (viewEl) {
        viewEl.style.display = view === 'editor' ? 'flex' : 'flex';
        viewEl.classList.add('active');
    }

    if (editor) editor.layout();

    // Refresh history when switching to history view
    if (view === 'history') {
        loadHistory();
    }
}

// ============================================
// Render History
// ============================================
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        renderHistory = await response.json();
        renderHistoryList();
    } catch (err) {
        // History load failed silently
    }
}

function renderHistoryList() {
    const list = document.getElementById('history-list');

    if (renderHistory.length === 0) {
        list.innerHTML = '<p class="history-empty">No renders yet. Start creating!</p>';
        return;
    }

    list.innerHTML = renderHistory.map(entry => {
        const time = new Date(entry.timestamp).toLocaleString();
        const statusClass = entry.status === 'success' ? 'success' : 'error';
        const statusIcon = entry.status === 'success' ? 'fa-check' : 'fa-times';
        const title = entry.code_preview.split('\n')[0].replace(/^class\s+/, '').replace(/\(.*\):.*/, '').trim() || 'Untitled';

        return `
            <div class="history-item" data-job-id="${entry.job_id}">
                <div class="history-item-icon ${statusClass}">
                    <i class="fas ${statusIcon}"></i>
                </div>
                <div class="history-item-info">
                    <div class="history-item-title">${escapeHtml(title)}</div>
                    <div class="history-item-meta">
                        <span>${time}</span>
                        <span class="dot"></span>
                        <span>${entry.status === 'success' ? 'Rendered' : entry.error || 'Failed'}</span>
                    </div>
                </div>
                <div class="history-item-actions">
                    ${entry.status === 'success' ? `
                        <button class="history-action-btn" onclick="playFromHistory('${entry.job_id}')" title="Play">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="history-action-btn" onclick="downloadFromHistory('${entry.job_id}', '${entry.filename || ''}')" title="Download">
                            <i class="fas fa-download"></i>
                        </button>
                    ` : ''}
                    <button class="history-action-btn" onclick="loadCodeFromHistory('${entry.job_id}')" title="Load code">
                        <i class="fas fa-code"></i>
                    </button>
                    <button class="history-action-btn delete" onclick="deleteHistoryEntry('${entry.job_id}')" title="Delete">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function playFromHistory(jobId) {
    const entry = renderHistory.find(h => h.job_id === jobId);
    if (entry && entry.video_url) {
        currentJobId = entry.job_id;
        currentFilename = entry.filename;
        switchView('editor');
        showVideo(entry.video_url);
    }
}

function downloadFromHistory(jobId, filename) {
    if (jobId && filename) {
        window.location.href = `/api/download/${jobId}/${filename}`;
    }
}

function loadCodeFromHistory(jobId) {
    const entry = renderHistory.find(h => h.job_id === jobId);
    if (entry && entry.full_code) {
        editor.setValue(entry.full_code);
        switchView('editor');
        showToast('Code loaded from history', 'success');
    }
}

async function deleteHistoryEntry(jobId) {
    try {
        await fetch(`/api/history/${jobId}`, { method: 'DELETE' });
        renderHistory = renderHistory.filter(h => h.job_id !== jobId);
        renderHistoryList();
        showToast('Entry deleted', 'success');
    } catch (err) {
        showToast('Failed to delete entry', 'error');
    }
}

async function clearAllHistory() {
    if (!confirm('Clear all render history?')) return;
    try {
        await fetch('/api/history', { method: 'DELETE' });
        renderHistory = [];
        renderHistoryList();
        showToast('History cleared', 'success');
    } catch (err) {
        showToast('Failed to clear history', 'error');
    }
}

// ============================================
// Load Examples
// ============================================
async function loadExamples() {
    try {
        const response = await fetch('/api/examples');
        const examples = await response.json();
        const grid = document.getElementById('examples-grid');
        grid.innerHTML = '';

        Object.entries(examples).forEach(([name, code]) => {
            const card = document.createElement('div');
            card.className = 'example-card';
            card.innerHTML = `
                <div class="example-card-header">
                    <span class="example-card-title">${name}</span>
                    <span class="example-card-badge">Example</span>
                </div>
                <div class="example-card-body">
                    <pre class="example-card-code">${escapeHtml(code)}</pre>
                </div>
                <div class="example-card-footer">
                    <button class="example-use-btn" onclick="useExample('${name}')">
                        <i class="fas fa-arrow-right"></i> Use this
                    </button>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (err) {
        document.getElementById('examples-grid').innerHTML =
            '<p class="examples-loading">Failed to load examples</p>';
    }
}

async function useExample(name) {
    try {
        if (!cachedExamples) {
            const response = await fetch('/api/examples');
            cachedExamples = await response.json();
        }
        if (cachedExamples[name]) {
            editor.setValue(cachedExamples[name]);
            switchView('editor');
            showToast(`Loaded "${name}" example`, 'success');
        }
    } catch (err) {
        showToast('Failed to load example', 'error');
    }
}

// ============================================
// Utility Functions
// ============================================
function formatCode() {
    if (editor) {
        editor.getAction('editor.action.formatDocument')?.run();
    }
}

function clearEditor() {
    if (editor) {
        editor.setValue('');
    }
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} toast-icon"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
