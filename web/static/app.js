/* ===== Zeus Frontend — Enterprise Agent UI ===== */

// ===== Particles =====
const canvas = document.getElementById('particles');
const ctx = canvas.getContext('2d');
let particles = [];

function initParticles() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    particles = Array.from({length: 40}, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: Math.random() * 1.5 + 0.5,
        color: ['#ffb552','#ff5873','#b83dff'][Math.floor(Math.random()*3)]
    }));
}
function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = 0.4;
        ctx.fill();
    });
    ctx.globalAlpha = 1;
    requestAnimationFrame(animateParticles);
}
window.addEventListener('resize', initParticles);
initParticles();
animateParticles();

// ===== Session Management =====
let sessions = [];
let activeSessionId = null;

async function loadSessions() {
    try {
        const resp = await fetch('/api/sessions');
        const data = await resp.json();
        // Backend returns {sessions: [...], active: "id"}
        sessions = Array.isArray(data) ? data : (data.sessions || []);
        if (sessions.length === 0) {
            await createSession();
        } else {
            activeSessionId = (data.active && data.active !== '') ? data.active : sessions[0].id;
            renderSessions();
        }
    } catch (e) {
        await createSession();
    }
}

async function createSession() {
    try {
        const resp = await fetch('/api/sessions', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({}) });
        const session = await resp.json();
        sessions.unshift(session);
        activeSessionId = session.id;
        renderSessions();
        clearActivityFeed();
    } catch (e) {
        // Fallback: just use a local ID
        activeSessionId = 'local-' + Date.now();
        sessions.unshift({id: activeSessionId, title: 'New Session', created_at: new Date().toISOString()});
        renderSessions();
        clearActivityFeed();
    }
}

async function deleteSession(id) {
    try { await fetch(`/api/sessions/${id}`, { method: 'DELETE' }); } catch(e) {}
    sessions = sessions.filter(s => s.id !== id);
    if (activeSessionId === id) {
        activeSessionId = sessions.length > 0 ? sessions[0].id : null;
        if (!activeSessionId) await createSession();
    }
    renderSessions();
    clearActivityFeed();
}

function switchSession(id) {
    activeSessionId = id;
    renderSessions();
    clearActivityFeed();
    // TODO: load session history from backend
}

function renderSessions() {
    const list = document.getElementById('sessions-list');
    list.innerHTML = sessions.map(s => `
        <div class="session-item ${s.id === activeSessionId ? 'active' : ''}" onclick="switchSession('${s.id}')">
            <span class="session-dot"></span>
            <span class="session-name">${s.title || 'New Session'}</span>
            <button class="session-delete" onclick="event.stopPropagation(); deleteSession('${s.id}')">×</button>
        </div>
    `).join('');
}

function clearActivityFeed() {
    const feed = document.getElementById('activity-feed');
    feed.innerHTML = document.getElementById('idle-state') ? '' : '';
    // Re-add idle state
    feed.innerHTML = `
        <div class="idle-state" id="idle-state">
            <div class="idle-orb"><div class="orb-ring"></div><div class="orb-ring delay-1"></div><div class="orb-ring delay-2"></div><div class="orb-core"></div></div>
            <h2>Zeus is ready</h2>
            <p>Describe your data goal and watch the autonomous agent orchestrate the workflow.</p>
            <div class="quick-actions">
                <button class="quick-action" onclick="setInput('Analyze my sales pipeline against support tickets')"><span class="qa-icon">📊</span><span class="qa-text">Cross-analyze sales vs support</span></button>
                <button class="quick-action" onclick="setInput('Check health of all Fivetran connectors')"><span class="qa-icon">🩺</span><span class="qa-text">Health check connectors</span></button>
                <button class="quick-action" onclick="setInput('Set up a complete data pipeline from PostgreSQL to BigQuery')"><span class="qa-icon">🚀</span><span class="qa-text">Provision new pipeline</span></button>
            </div>
        </div>`;
}

// ===== Tool activity (compact) + live workflow steps =====
const STEP_META = {
    create_destination: {i:'🎯', l:'Create destination'},
    create_connection: {i:'🔌', l:'Create connection'},
    modify_connection_table_config: {i:'🎚️', l:'Scope tables'},
    run_connection_setup_tests: {i:'🧪', l:'Run setup tests'},
    sync_connection: {i:'🔄', l:'Sync data'},
    resync_connection: {i:'🔄', l:'Re-sync data'},
    get_connection_details: {i:'🔍', l:'Inspect connection'},
    list_connections: {i:'📋', l:'List connections'},
    query_bigquery: {i:'📊', l:'Query BigQuery'},
    create_account_webhook: {i:'🔔', l:'Set freshness webhook'},
    test_webhook: {i:'✅', l:'Test webhook'},
    create_group: {i:'🛡️', l:'Create access group'},
    add_user_to_group: {i:'🛡️', l:'Scope user access'},
    modify_group: {i:'🛡️', l:'Update access controls'},
};

function addToolActivity(tool) {
    const feed = document.getElementById('activity-feed');
    const idle = document.getElementById('idle-state');
    if (idle) idle.remove();
    const el = document.createElement('div');
    el.className = 'tool-activity-line';
    el.innerHTML = `<span class="tool-gear">⚙</span><code>${escapeHtml(tool)}</code><span class="tool-tag">MCP</span>`;
    feed.appendChild(el);
    feed.scrollTop = feed.scrollHeight;
}

function addWorkflowStep(tool) {
    const canvas = document.getElementById('workflow-canvas');
    let steps = canvas.querySelector('.workflow-steps');
    if (!steps) { canvas.innerHTML = '<div class="workflow-steps"></div>'; steps = canvas.querySelector('.workflow-steps'); }
    const m = STEP_META[tool] || {i:'⚙', l: tool};
    const el = document.createElement('div');
    el.className = 'workflow-step done';
    el.innerHTML = `<span class="step-icon">${m.i}</span><span class="step-name">${escapeHtml(m.l)}</span><span class="step-status">✓</span>`;
    steps.appendChild(el);
}

function resetWorkflow() {
    const canvas = document.getElementById('workflow-canvas');
    if (canvas) canvas.innerHTML = '<div class="workflow-empty"><div class="workflow-empty-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg></div><span>No active workflow</span></div>';
}

// ===== Agent State Management =====
function setAgentState(name, state) {
    const node = document.getElementById(`agent-${name}`);
    if (!node) return;
    const pulse = node.querySelector('.agent-pulse');
    pulse.className = 'agent-pulse';
    if (state === 'active') pulse.classList.add('active');
    else if (state === 'working') pulse.classList.add('working');
}

function activateAgent(name) { setAgentState(name, 'working'); }
function deactivateAgent(name) { setAgentState(name, 'idle'); }

// Orchestrator always on
setAgentState('orchestrator', 'active');

// ===== Workflow Animation =====
function runWorkflowAnimation(steps) {
    const canvas = document.getElementById('workflow-canvas');
    canvas.innerHTML = `<div class="workflow-steps">${steps.map((s, i) => `
        <div class="workflow-step" id="wf-step-${i}">
            <span class="step-icon">${s.icon}</span>
            <span class="step-name">${s.name}</span>
            <span class="step-status">waiting</span>
        </div>`).join('')}</div>`;
    
    steps.forEach((s, i) => {
        setTimeout(() => {
            const el = document.getElementById(`wf-step-${i}`);
            if (!el) return;
            el.classList.add('active');
            el.querySelector('.step-status').textContent = 'running';
            if (s.agent) activateAgent(s.agent);
        }, i * 1200);
        setTimeout(() => {
            const el = document.getElementById(`wf-step-${i}`);
            if (!el) return;
            el.classList.remove('active');
            el.classList.add('done');
            el.querySelector('.step-status').textContent = '✓';
            if (s.agent) deactivateAgent(s.agent);
        }, (i + 1) * 1200);
    });

    setTimeout(() => {
        canvas.innerHTML = `<div class="workflow-empty"><div class="workflow-empty-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg></div><span>Complete</span></div>`;
    }, (steps.length + 1) * 1200);
}

// ===== Chat / Activity =====
function setInput(text) {
    document.getElementById('user-input').value = text;
    document.getElementById('user-input').focus();
}

function addActivityEntry(actor, content, isHtml = false) {
    const feed = document.getElementById('activity-feed');
    const idle = document.getElementById('idle-state');
    if (idle) idle.remove();

    const time = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
    const isUser = actor === 'user';
    const entry = document.createElement('div');
    entry.className = 'activity-entry';
    entry.innerHTML = `
        <div class="entry-avatar ${isUser ? 'user' : 'agent'}">${isUser ? '→' : '⚡'}</div>
        <div class="entry-content">
            <div class="entry-header">
                <span class="entry-actor">${isUser ? 'You' : 'Zeus'}</span>
                <span class="entry-time">${time}</span>
            </div>
            <div class="entry-body ${isUser ? 'user-msg' : ''}">${isHtml ? content : escapeHtml(content)}</div>
        </div>`;
    feed.appendChild(entry);
    feed.scrollTop = feed.scrollHeight;
    return entry;
}

function addThinking() {
    const feed = document.getElementById('activity-feed');
    const idle = document.getElementById('idle-state');
    if (idle) idle.remove();

    const entry = document.createElement('div');
    entry.className = 'activity-entry';
    entry.id = 'thinking-entry';
    entry.innerHTML = `
        <div class="entry-avatar agent">⚡</div>
        <div class="entry-content">
            <div class="entry-header"><span class="entry-actor">Zeus</span><span class="entry-time">processing</span></div>
            <div class="entry-body"><div class="thinking-dots"><span></span><span></span><span></span></div></div>
        </div>`;
    feed.appendChild(entry);
    feed.scrollTop = feed.scrollHeight;
    return entry;
}

function removeThinking() {
    const el = document.getElementById('thinking-entry');
    if (el && el.isConnected) el.remove();
}

function setStatus(text, working = false) {
    const pill = document.getElementById('agent-status');
    pill.querySelector('.status-text').textContent = text;
    pill.className = 'status-pill' + (working ? ' working' : '');
}

function updateContextMeter(pct) {
    const fill = document.getElementById('ctx-fill');
    const label = document.getElementById('ctx-label');
    const offset = 62.8 * (1 - pct / 100);
    fill.style.strokeDashoffset = offset;
    label.textContent = Math.round(pct) + '%';
}

function updateMeter(freshness, lineage, governance, interop) {
    const overall = Math.round((freshness + lineage + governance + interop) / 4);
    document.getElementById('overall-score').innerHTML = `${overall}<span class="score-unit">%</span>`;
    const offset = 326.7 * (1 - overall / 100);
    document.getElementById('ring-fill').style.strokeDashoffset = offset;

    const pillars = [{id:'freshness',val:freshness},{id:'lineage',val:lineage},{id:'governance',val:governance},{id:'interoperability',val:interop}];
    pillars.forEach(p => {
        const el = document.getElementById(`pillar-${p.id}`);
        if (!el) return;
        el.querySelector('.pillar-value').textContent = p.val + '%';
        el.querySelector('.pillar-fill').style.width = p.val + '%';
    });
}

function resetMeter() { updateMeter(0, 0, 10, 25); }

// ===== Send Message =====
let isSending = false;

async function sendMessage() {
    const input = document.getElementById('user-input');
    const text = input.value.trim();
    if (!text || isSending) return;

    isSending = true;
    input.value = '';
    document.getElementById('send-btn').disabled = true;
    setStatus('Orchestrating...', true);

    addActivityEntry('user', text);
    resetWorkflow();
    const thinkingEl = addThinking();

    try {
        const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: text, session_id: activeSessionId })
        });

        if (resp.headers.get('content-type')?.includes('text/event-stream')) {
            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let agentText = '';
            let buffer = '';

            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, {stream: true});
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'token') {
                                agentText += data.content;
                            } else if (data.type === 'approval_request') {
                                showApproval(data);
                            } else if (data.type === 'agent_state') {
                                setAgentState(data.agent, data.state || 'working');
                            } else if (data.type === 'tool_activity') {
                                addToolActivity(data.tool);
                                addWorkflowStep(data.tool);
                            } else if (data.type === 'context_update') {
                                updateContextMeter(data.context_remaining_pct || 100);
                            } else if (data.type === 'meter_update') {
                                updateMeter(data.freshness, data.lineage, data.governance, data.interoperability);
                            } else if (data.type === 'done') {
                                if (data.content) agentText = data.content;
                            } else if (data.type === 'error') {
                                agentText = '⚠️ ' + (data.content || 'An error occurred');
                            }
                        } catch(e) {}
                    }
                }
            }

            removeThinking();
            if (agentText) addActivityEntry('agent', formatMarkdown(agentText), true);
        } else {
            const data = await resp.json();
            removeThinking();
            addActivityEntry('agent', formatMarkdown(data.response || data.error || 'No response'), true);
        }
    } catch (err) {
        removeThinking();
        addActivityEntry('agent', '⚠️ Connection error: ' + err.message);
    }

    isSending = false;
    document.getElementById('send-btn').disabled = false;
    setStatus('Awaiting Instructions', false);
    setAgentState('orchestrator', 'active');
    ['planner', 'provisioner', 'healer', 'analyst'].forEach(a => setAgentState(a, 'idle'));
}

// Enter to send
document.getElementById('user-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// ===== Approval =====
let pendingApprovalId = null;

function showApproval(data) {
    pendingApprovalId = data.approval_id;
    const modal = document.getElementById('approval-modal');
    document.getElementById('approval-body').innerHTML = `
        <div style="margin-bottom:8px"><strong>Action:</strong> ${escapeHtml(data.action || 'Unknown')}</div>
        <div style="margin-bottom:8px"><strong>Impact:</strong> ${escapeHtml(data.impact || 'N/A')}</div>
        <div><strong>Parameters:</strong><pre>${escapeHtml(JSON.stringify(data.params || {}, null, 2))}</pre></div>`;
    modal.style.display = 'flex';
}

async function respondApproval(approved) {
    document.getElementById('approval-modal').style.display = 'none';
    try {
        await fetch('/api/approve', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ approval_id: pendingApprovalId, approved })
        });
    } catch(e) {}
    addActivityEntry('agent', approved ? '✅ Action approved — executing...' : '❌ Action rejected by operator');
}

// ===== Audio Input =====
let mediaRecorder = null;
let isRecording = false;

function toggleAudio() {
    if (isRecording) stopRecording();
    else startRecording();
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        const chunks = [];
        mediaRecorder.ondataavailable = e => chunks.push(e.data);
        mediaRecorder.onstop = () => {
            stream.getTracks().forEach(t => t.stop());
            // Use Web Speech API for transcription
            transcribeAudio(chunks);
        };
        mediaRecorder.start();
        isRecording = true;
        document.getElementById('audio-btn').classList.add('recording');
    } catch(e) {
        // Fallback: use SpeechRecognition API
        startSpeechRecognition();
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    isRecording = false;
    document.getElementById('audio-btn').classList.remove('recording');
}

function startSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        addActivityEntry('agent', '⚠️ Speech recognition not supported in this browser');
        return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.onresult = (e) => {
        const text = e.results[0][0].transcript;
        document.getElementById('user-input').value = text;
    };
    recognition.onerror = () => {
        document.getElementById('audio-btn').classList.remove('recording');
        isRecording = false;
    };
    recognition.onend = () => {
        document.getElementById('audio-btn').classList.remove('recording');
        isRecording = false;
    };
    recognition.start();
    isRecording = true;
    document.getElementById('audio-btn').classList.add('recording');
}

function transcribeAudio(chunks) {
    // For now, fallback to SpeechRecognition
    startSpeechRecognition();
}

// ===== Panel Collapse/Expand =====
let leftCollapsed = false;
let rightCollapsed = false;

function toggleLeftPanel() {
    leftCollapsed = !leftCollapsed;
    const panel = document.querySelector('.orchestration-panel');
    const btn = document.getElementById('toggle-left-btn');
    const layout = document.querySelector('.main-layout');
    panel.classList.toggle('collapsed', leftCollapsed);
    btn.title = leftCollapsed ? 'Expand left panel' : 'Collapse left panel';
    btn.innerHTML = leftCollapsed
        ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>`
        : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>`;
    updateLayoutGrid();
}

function toggleRightPanel() {
    rightCollapsed = !rightCollapsed;
    const panel = document.querySelector('.meter-panel');
    const btn = document.getElementById('toggle-right-btn');
    panel.classList.toggle('collapsed', rightCollapsed);
    btn.title = rightCollapsed ? 'Expand right panel' : 'Collapse right panel';
    btn.innerHTML = rightCollapsed
        ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>`
        : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>`;
    updateLayoutGrid();
}

function updateLayoutGrid() {
    const layout = document.querySelector('.main-layout');
    const lw = leftCollapsed ? '36px' : '260px';
    const rw = rightCollapsed ? '36px' : '260px';
    layout.style.gridTemplateColumns = `${lw} 1fr ${rw}`;
}

// ===== Helpers =====
function escapeHtml(s) {
    if (!s) return '';
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatMarkdown(text) {
    if (!text) return '';
    let html = escapeHtml(text);
    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    return html;
}

// ===== Init =====
loadSessions();
