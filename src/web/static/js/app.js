// Deadlock Detection System - Frontend Controller
const API_BASE = '/api';
let currentSimId = null;
let cy = null; // Graph Instance

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
    lblLastAction: document.getElementById('lastActionValue'),
    listProcess: document.getElementById('processList'),
    listResource: document.getElementById('resourceList'),
    logTerminal: document.getElementById('requestLog'),
    inPid: document.getElementById('pidInput'),
    inPrio: document.getElementById('priorityInput'),
    inRid: document.getElementById('ridInput'),
    inInst: document.getElementById('instancesInput'),
    inReqPid: document.getElementById('reqPidInput'),
    inReqRid: document.getElementById('reqRidInput')
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    initGraph(); // Initialize Cytoscape
    log("System initialized. Waiting for user input...", "system");
});

// --- Graph Logic ---
function initGraph() {
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#666',
                    'label': 'data(id)',
                    'color': '#fff',
                    'text-valign': 'center',
                    'font-family': 'JetBrains Mono',
                    'font-size': '12px'
                }
            },
            {
                selector: '.process',
                style: { 'background-color': '#06b6d4', 'shape': 'ellipse', 'width': 40, 'height': 40 }
            },
            {
                selector: '.resource',
                style: { 'background-color': '#f59e0b', 'shape': 'rectangle', 'width': 40, 'height': 40 }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#4b5563',
                    'target-arrow-color': '#4b5563',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier'
                }
            },
            {
                selector: '.allocated', // Edge: Resource -> Process
                style: { 'line-color': '#10b981', 'target-arrow-color': '#10b981' }
            },
            {
                selector: '.blocked', // Edge: Process -> Resource (Waiting)
                style: { 'line-color': '#ef4444', 'target-arrow-color': '#ef4444', 'line-style': 'dashed' }
            }
        ],
        layout: { name: 'circle' }
    });
}

function addToGraph(id, type) {
    if(!cy) return;
    cy.add({
        group: 'nodes',
        data: { id: id },
        classes: type // 'process' or 'resource'
    });
    cy.layout({ name: 'circle' }).run();
}

function addLink(source, target, type) {
    if(!cy) return;
    // Check if edge exists to avoid duplicates
    const edgeId = `${source}-${target}`;
    if(cy.getElementById(edgeId).length === 0) {
        cy.add({
            group: 'edges',
            data: { id: edgeId, source: source, target: target },
            classes: type // 'allocated' or 'blocked'
        });
        cy.layout({ name: 'circle' }).run();
    }
}

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
            updateAction("SIM STARTED");
            cy.elements().remove(); // Clear graph
        }
    } catch (e) { log(`Error creating simulation: ${e}`, "error"); }
});

dom.btnProcess.addEventListener('click', async () => {
    if (!currentSimId) return;
    const pid = dom.inPid.value.trim();
    const prio = parseInt(dom.inPrio.value);
    if (!pid) return alert("Process ID required");

    try {
        const res = await apiPost(`simulation/${currentSimId}/process`, { pid: pid, priority: prio });
        if (res.status === 'success') {
            addProcessToList(pid, prio);
            addToGraph(pid, 'process'); // Add Node
            dom.inPid.value = '';
            log(`Added Process [${pid}]`, "system");
            updateCounts();
            updateAction(`ADD PROC: ${pid}`);
        }
    } catch (e) { log(`Error adding process: ${e.message}`, "error"); }
});

dom.btnResource.addEventListener('click', async () => {
    if (!currentSimId) return;
    const rid = dom.inRid.value.trim();
    const inst = parseInt(dom.inInst.value);
    if (!rid) return alert("Resource ID required");

    try {
        const res = await apiPost(`simulation/${currentSimId}/resource`, { rid: rid, instances: inst });
        if (res.status === 'success') {
            addResourceToList(rid, inst);
            addToGraph(rid, 'resource'); // Add Node
            dom.inRid.value = '';
            log(`Added Resource [${rid}]`, "system");
            updateCounts();
            updateAction(`ADD RES: ${rid}`);
        }
    } catch (e) { log(`Error adding resource: ${e.message}`, "error"); }
});

dom.btnRequest.addEventListener('click', async () => {
    if (!currentSimId) return;
    const pid = dom.inReqPid.value.trim();
    const rid = dom.inReqRid.value.trim();
    if (!pid || !rid) return alert("PID and RID required");

    try {
        const res = await apiPost(`simulation/${currentSimId}/request`, { process: pid, resource: rid });
        if (res.status === 'success') {
            const resultColor = res.allocation_result === 'allocated' ? 'success' : 'error';
            log(`[${pid}] -> [${rid}] : ${res.allocation_result.toUpperCase()}`, resultColor);
            updateSystemStatus(res.system_state);
            updateAction(`REQ: ${pid} ➜ ${rid}`);

            // UPDATE GRAPH EDGES
            if (res.allocation_result === 'allocated') {
                // If allocated: Resource points to Process (R -> P)
                addLink(rid, pid, 'allocated');
            } else {
                // If blocked: Process points to Resource (P -> R)
                addLink(pid, rid, 'blocked');
            }
        }
    } catch (e) {
        if (e.message && e.message.includes("No transition")) {
            log(`DEADLOCK TRAP: Process is stuck! (${e.message})`, "error");
            updateSystemStatus("UNSAFE");
            updateAction("DEADLOCK TRAP");
            // Visualize the deadlock wait
            addLink(pid, rid, 'blocked');
        } else {
            log(`Request Failed: ${e.message || "Unknown error"}`, "error");
        }
    }
});

dom.btnRun.addEventListener('click', async () => {
    if (!currentSimId) return;
    updateAction("DETECTING...");
    try {
        await apiPost(`simulation/${currentSimId}/run`, { steps: 1 });
        const stateRes = await fetch(`${API_BASE}/simulation/${currentSimId}/state`);
        const stateData = await stateRes.json();
        
        if (stateData) {
            const status = stateData.state || stateData.system_state || stateData.status || "Unknown";
            updateSystemStatus(status);
            dom.lblIter.textContent = parseInt(dom.lblIter.textContent) + 1;
            const isSafe = (status.toLowerCase() === 'safe');
            log(`Cycle Complete. System is ${status}`, isSafe ? 'success' : 'error');
            updateAction("CYCLE DONE");
        }
    } catch (e) { log(`Detection Error: ${e.message}`, "error"); }
});

dom.btnReset.addEventListener('click', () => { location.reload(); });

// --- Helpers ---
async function apiPost(endpoint, body) {
    const res = await fetch(`${API_BASE}/${endpoint}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "API Error");
    return data;
}

function updateUIState(isActive) {
    [dom.btnRun, dom.btnReset, dom.btnProcess, dom.btnResource, dom.btnRequest].forEach(el => el.disabled = !isActive);
    dom.btnCreate.disabled = isActive;
}
function log(msg, type="normal") {
    const div = document.createElement('div'); div.className = `log-line ${type}`; div.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
    dom.logTerminal.appendChild(div); dom.logTerminal.scrollTop = dom.logTerminal.scrollHeight;
}
function updateSystemStatus(state) {
    if (!state) state = "Unknown";
    dom.lblStatus.innerText = state.toUpperCase();
    dom.lblStatus.className = `status-badge status-${state.toLowerCase().includes("safe") && !state.toLowerCase().includes("un") ? 'safe' : 'unsafe'}`;
}
function updateAction(text) {
    if (dom.lblLastAction) {
        dom.lblLastAction.textContent = text.toUpperCase();
        dom.lblLastAction.style.color = '#06b6d4'; setTimeout(() => dom.lblLastAction.style.color = '', 500);
    }
}
function addProcessToList(pid, prio) {
    const div = document.createElement('div'); div.className = 'list-item p-item';
    div.innerHTML = `<span><strong>${pid}</strong></span> <span>Prio: ${prio}</span>`; dom.listProcess.appendChild(div);
}
function addResourceToList(rid, inst) {
    const div = document.createElement('div'); div.className = 'list-item r-item';
    div.innerHTML = `<span><strong>${rid}</strong></span> <span>Qty: ${inst}</span>`; dom.listResource.appendChild(div);
}
function updateCounts() {
    dom.lblProcCount.innerText = dom.listProcess.children.length;
    dom.lblResCount.innerText = dom.listResource.children.length;
}
