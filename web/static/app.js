/* Zeus — AI Data Engineer — Frontend Logic */

const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('user-input');
let pendingApprovalId = null;

// Send message on Enter
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const message = inputEl.value.trim();
    if (!message) return;

    // Add user message to chat
    appendMessage('user', message);
    inputEl.value = '';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });

        // Handle SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            // Parse SSE data lines
            const lines = chunk.split('\n');
            for (const line of lines) {
                if (line.startsWith('data:')) {
                    try {
                        const data = JSON.parse(line.slice(5));
                        if (data.content) {
                            assistantMessage = data.content;
                        }
                        // Check for approval requests
                        if (data.approval_request) {
                            showApprovalModal(data.approval_request);
                        }
                    } catch (e) {
                        // Partial data, continue
                    }
                }
            }
        }

        if (assistantMessage) {
            appendMessage('assistant', assistantMessage);
        }

        // Update readiness meter
        updateMeter();
    } catch (error) {
        appendMessage('assistant', `Error: ${error.message}`);
    }
}

function appendMessage(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="message-content"><p>${escapeHtml(content)}</p></div>`;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Readiness Meter
async function updateMeter() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        const pillars = data.pillars;
        const overall = data.overall;

        // Update overall score
        const scoreEl = document.getElementById('overall-score');
        scoreEl.textContent = `${Math.round(overall)}%`;
        scoreEl.style.color = getColor(overall);

        // Update each pillar
        for (const [name, value] of Object.entries(pillars)) {
            const pillar = document.getElementById(`pillar-${name}`);
            if (!pillar) continue;

            const valueEl = pillar.querySelector('.pillar-value');
            const fillEl = pillar.querySelector('.pillar-fill');

            valueEl.textContent = `${value}%`;
            fillEl.style.width = `${value}%`;
            fillEl.style.background = getColor(value);
        }
    } catch (e) {
        // Status endpoint not available yet
    }
}

function getColor(value) {
    if (value < 34) return '#ef4444';      // Red
    if (value < 67) return '#eab308';      // Yellow
    return '#22c55e';                       // Green
}

// Approval Modal
function showApprovalModal(request) {
    pendingApprovalId = request.action_id;
    const modal = document.getElementById('approval-modal');
    const body = document.getElementById('approval-body');

    body.innerHTML = `
        <p><strong>Action:</strong> ${escapeHtml(request.action)}</p>
        <p><strong>Parameters:</strong> ${escapeHtml(request.parameters)}</p>
        <p><strong>Effect:</strong> ${escapeHtml(request.effect)}</p>
    `;

    modal.style.display = 'flex';
}

async function respondApproval(approved) {
    const modal = document.getElementById('approval-modal');
    modal.style.display = 'none';

    if (pendingApprovalId) {
        await fetch('/api/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action_id: pendingApprovalId,
                approved,
            }),
        });
        pendingApprovalId = null;
    }

    appendMessage('assistant', approved ? '✅ Action approved. Proceeding...' : '❌ Action rejected.');
}

// Poll meter on load
updateMeter();
setInterval(updateMeter, 5000);
