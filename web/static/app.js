/* Zeus — AI Data Engineer — Frontend */

const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
let pendingApprovalId = null;
let isProcessing = false;

// Send on Enter
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const message = inputEl.value.trim();
    if (!message || isProcessing) return;

    isProcessing = true;
    sendBtn.disabled = true;
    sendBtn.textContent = '...';

    appendMessage('user', message);
    inputEl.value = '';

    // Show thinking indicator
    const thinkingId = showThinking();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });

        removeThinking(thinkingId);

        // Read SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE lines
            const lines = buffer.split('\n');
            buffer = lines.pop(); // keep incomplete last line

            for (const line of lines) {
                if (line.startsWith('data:')) {
                    const raw = line.slice(5).trim();
                    if (!raw) continue;
                    try {
                        const event = JSON.parse(raw);
                        handleEvent(event);
                    } catch (_) { /* partial JSON, ignore */ }
                }
            }
        }

    } catch (error) {
        removeThinking(thinkingId);
        appendMessage('assistant', `❌ Error: ${error.message}`);
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
    }
}

function handleEvent(event) {
    switch (event.type) {
        case 'message':
            appendMessage('assistant', event.content, event.lineage);
            break;
        case 'status':
            updateMeterFromData(event.status);
            break;
        case 'approval_request':
            showApprovalModal(event.request);
            break;
        case 'step':
            appendStep(event.step, event.status);
            break;
        case 'error':
            appendMessage('assistant', `❌ ${event.content}`);
            break;
    }
}

// --- Chat UI ---

function appendMessage(role, content, lineage) {
    const div = document.createElement('div');
    div.className = `message ${role}`;

    let html = `<div class="message-content"><p>${formatMarkdown(content)}</p>`;
    if (lineage) {
        html += `<div class="lineage-badge" title="${escapeHtml(lineage)}">🔗 lineage</div>`;
    }
    html += '</div>';
    div.innerHTML = html;

    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function appendStep(step, status) {
    const statusIcon = status === 'done' ? '✅' : status === 'error' ? '❌' : '⏳';
    const div = document.createElement('div');
    div.className = 'message assistant step';
    div.innerHTML = `<div class="message-content step-content">${statusIcon} ${escapeHtml(step)}</div>`;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showThinking() {
    const id = 'thinking-' + Date.now();
    const div = document.createElement('div');
    div.className = 'message assistant thinking';
    div.id = id;
    div.innerHTML = '<div class="message-content"><span class="dot-pulse">⏳ Zeus is thinking</span></div>';
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return id;
}

function removeThinking(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function formatMarkdown(text) {
    return escapeHtml(text)
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text || '';
    return d.innerHTML;
}

// --- Readiness Meter ---

async function updateMeter() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        updateMeterFromData(data);
    } catch (_) {}
}

function updateMeterFromData(data) {
    if (!data || !data.pillars) return;

    const overall = data.overall ?? 0;
    const scoreEl = document.getElementById('overall-score');
    scoreEl.textContent = `${Math.round(overall)}%`;
    scoreEl.style.color = pillarColor(overall);

    for (const [name, info] of Object.entries(data.pillars)) {
        const val = info.value ?? info;
        updatePillar(name, typeof val === 'number' ? val : val.value ?? 0, info.label || '');
    }
}

function updatePillar(name, value, label) {
    const pillar = document.getElementById(`pillar-${name}`);
    if (!pillar) return;
    const valueEl = pillar.querySelector('.pillar-value');
    const fillEl = pillar.querySelector('.pillar-fill');
    const labelEl = pillar.querySelector('.pillar-label');

    if (valueEl) valueEl.textContent = `${value}%`;
    if (fillEl) {
        fillEl.style.width = `${value}%`;
        fillEl.style.background = pillarColor(value);
    }
    if (labelEl && label) labelEl.textContent = label;
}

function pillarColor(value) {
    if (value < 34) return '#ef4444';
    if (value < 67) return '#eab308';
    return '#22c55e';
}

// --- Approval Modal ---

function showApprovalModal(request) {
    pendingApprovalId = request.action_id;
    const modal = document.getElementById('approval-modal');
    const body = document.getElementById('approval-body');
    body.innerHTML = `
        <p><strong>Action:</strong> <code>${escapeHtml(request.action)}</code></p>
        <p><strong>Parameters:</strong> ${escapeHtml(request.parameters)}</p>
        <p><strong>Effect:</strong> ${escapeHtml(request.effect)}</p>
    `;
    modal.style.display = 'flex';
}

async function respondApproval(approved) {
    const modal = document.getElementById('approval-modal');
    modal.style.display = 'none';

    if (pendingApprovalId) {
        try {
            await fetch('/api/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action_id: pendingApprovalId, approved }),
            });
        } catch (_) {}
        pendingApprovalId = null;
    }

    const msg = approved ? '✅ Action approved — proceeding...' : '❌ Action rejected.';
    appendMessage('assistant', msg);
}

// --- Demo Presets ---

function setInput(text) {
    inputEl.value = text;
    inputEl.focus();
}

// Init: load meter and poll
updateMeter();
setInterval(updateMeter, 5000);
