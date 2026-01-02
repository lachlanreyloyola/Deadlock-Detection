// Deadlock Detection System - Frontend Controller
// Connects to Flask API in src/interfaces/web_api.py

const API_BASE = '/api';
let currentSimId = null;

// DOM Elements
const dom = {
    btnCreate: document.getElementById('createSimBtn'),
    btnRun: document.getElementById('runSimBtn'),
    btnReset: document.getElementById('resetBtn'),
    btnProcess: document.getElementById('addProcessBtn'),
    btnResource: document.getElementById('addResourceBtn'),
    btnRequest: document.getElementById('requestBtn'),
    
    lblSimId: document.getElementById('simIdDisplay'),
    lblStatus: document.getElementById('systemStateBadge'),
    lblProcCount: document.getElementById('procCount'),
    lblResCount: document.getElementById('resCount'),
    lblIter: document.getElementById('iterValue'),
    lblLastAction: document.getElementById('lastActionValue'), // <--- ADDED: Metrics Panel
    
    listProcess: document.getElementById('processList'),
    listResource: document.getElementById('resourceList'),
    logTerminal: document.getElementById('requestLog'),
    
    // Inputs
    inPid: document.getElementById('pidInput'),
    inPrio: document.getElementById('priorityInput'),
    inRid: document.getElementById('ridInput'),
    inInst: document.getElementById('instancesInput'),
    inReqPid: document.getElementById('reqPidInput'),
    inReqRid: document.getElementById('reqRidInput')
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    log("System initialized. Waiting for user input...", "system");
});

// --- Event Listeners ---

dom.btnCreate.addEventListener('click', async () => {
    try {
        const res = await fetch(`${API_BASE}/simulation/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ detection_strategy: 'periodic' })
        });
        const data = await res.json();
        
        if (data.simulation_id) {
            currentSimId = data.simulation_id;
            updateUIState(true);
            dom.lblSimId.textContent = `ACTIVE: ${currentSimId}`;
            log(`Simulation created: ${currentSimId}`, "success");
            updateSystemStatus("SAFE");
            updateAction("SIM STARTED"); // <--- ADDED
        }
    } catch (e) {
        log(`Error creating simulation: ${e}`, "error");
    }
});

dom.btnProcess.addEventListener('click', async () => {
    if (!currentSimId) return;
    const pid = dom.inPid.value.trim();
    const prio = parseInt(dom.inPrio.value);

    if (!pid) return alert("Process ID required");

    try {
        const res = await apiPost(`simulation/${currentSimId}/process`, {
            pid: pid, priority: prio
        });

        if (res.status === 'success') {
            addProcessToList(pid, prio);
            dom.inPid.value = '';
            log(`Added Process [${pid}] (Priority: ${prio})`, "system");
            updateCounts();
            updateAction(`ADD PROC: ${pid}`); // <--- ADDED
        }
    } catch (e) {
        log(`Error adding process: ${e.message}`, "error");
    }
});

dom.btnResource.addEventListener('click', async () => {
    if (!currentSimId) return;
    const rid = dom.inRid.value.trim();
    const inst = parseInt(dom.inInst.value);

    if (!rid) return alert("Resource ID required");

    try {
        const res = await apiPost(`simulation/${currentSimId}/resource`, {
            rid: rid, instances: inst
        });

        if (res.status === 'success') {
            addResourceToList(rid, inst);
            dom.inRid.value = '';
            log(`Added Resource [${rid}] (${inst} instances)`, "system");
            updateCounts();
            updateAction(`ADD RES: ${rid}`); // <--- ADDED
        }
    } catch (e) {
        log(`Error adding resource: ${e.message}`, "error");
    }
});

dom.btnRequest.addEventListener('click', async () => {
    if (!currentSimId) return;
    const pid = dom.inReqPid.value.trim();
    const rid = dom.inReqRid.value.trim();

    if (!pid || !rid) return alert("PID and RID required");

    try {
        const res = await apiPost(`simulation/${currentSimId}/request`, {
            process: pid, resource: rid
        });

        // 200 OK
        if (res.status === 'success') {
            const resultColor = res.allocation_result === 'allocated' ? 'success' : 'error';
            log(`[${pid}] requested [${rid}] -> ${res.allocation_result.toUpperCase()}`, resultColor);
            
            // Update System Status based on response
            updateSystemStatus(res.system_state);
            updateAction(`REQ: ${pid} ➜ ${rid}`); // <--- ADDED
        }
    } catch (e) {
        // ERROR HANDLING: Check for specific FSA Deadlock crash
        if (e.message && e.message.includes("No transition")) {
            log(`DEADLOCK TRAP: Process is stuck! (${e.message})`, "error");
            updateSystemStatus("UNSAFE"); // Force UI to show unsafe/deadlock state
            updateAction("DEADLOCK TRAP"); // <--- ADDED
        } else {
            log(`Request Failed: ${e.message || "Unknown error"}`, "error");
        }
    }
});

dom.btnRun.addEventListener('click', async () => {
    if (!currentSimId) return;
    log("Running detection cycle...", "system");
    updateAction("DETECTING..."); // <--- ADDED
    
    try {
        // 1. Run the detection logic
        await apiPost(`simulation/${currentSimId}/run`, { steps: 1 });
        
        // 2. Fetch the new state
        const stateRes = await fetch(`${API_BASE}/simulation/${currentSimId}/state`);
        const stateData = await stateRes.json();
        
        // DEBUGGING: Print exact API response to console for verification
        console.log("DEBUG - API RESPONSE:", stateData);

        if (stateData) {
            // ROBUST CHECK: Look for 'state', 'system_state', or 'status'
            const status = stateData.state || stateData.system_state || stateData.status || "Unknown";
            
            updateSystemStatus(status);
            dom.lblIter.textContent = parseInt(dom.lblIter.textContent) + 1;
            
            const isSafe = (status.toLowerCase() === 'safe');
            log(`Cycle Complete. System is ${status}`, isSafe ? 'success' : 'error');
            updateAction("CYCLE DONE"); // <--- ADDED
        }
    } catch (e) {
        log(`Detection Error: ${e.message}`, "error");
    }
});

dom.btnReset.addEventListener('click', () => {
    location.reload(); 
});

// --- Helper Functions ---

async function apiPost(endpoint, body) {
    const res = await fetch(`${API_BASE}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "API Error");
    return data;
}

function updateUIState(isActive) {
    const elements = [dom.btnRun, dom.btnReset, dom.btnProcess, dom.btnResource, dom.btnRequest];
    elements.forEach(el => el.disabled = !isActive);
    dom.btnCreate.disabled = isActive;
}

function log(msg, type = "normal") {
    const div = document.createElement('div');
    div.className = `log-line ${type}`;
    div.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
    dom.logTerminal.appendChild(div);
    dom.logTerminal.scrollTop = dom.logTerminal.scrollHeight;
}

function updateSystemStatus(state) {
    if (!state) state = "Unknown";
    dom.lblStatus.innerText = state.toUpperCase();
    
    const lowerState = state.toLowerCase();
    if (lowerState.includes("safe") && !lowerState.includes("un")) {
        dom.lblStatus.className = `status-badge status-safe`;
    } else {
        dom.lblStatus.className = `status-badge status-unsafe`;
    }
}

// --- ADDED: Updates the Last Action Metric ---
function updateAction(text) {
    if (dom.lblLastAction) {
        dom.lblLastAction.textContent = text.toUpperCase();
        // Visual flash effect
        dom.lblLastAction.style.color = '#06b6d4'; // Cyan
        setTimeout(() => dom.lblLastAction.style.color = '', 500);
    }
}

function addProcessToList(pid, prio) {
    const div = document.createElement('div');
    div.className = 'list-item p-item';
    div.innerHTML = `<span><strong>${pid}</strong></span> <span>Prio: ${prio}</span>`;
    dom.listProcess.appendChild(div);
}

function addResourceToList(rid, inst) {
    const div = document.createElement('div');
    div.className = 'list-item r-item';
    div.innerHTML = `<span><strong>${rid}</strong></span> <span>Qty: ${inst}</span>`;
    dom.listResource.appendChild(div);
}

function updateCounts() {
    dom.lblProcCount.innerText = dom.listProcess.children.length;
    dom.lblResCount.innerText = dom.listResource.children.length;
}