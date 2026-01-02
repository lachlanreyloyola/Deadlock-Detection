/**
 * Visualization module for Wait-For Graph and FSA states
 */

class DeadlockVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.warn('Canvas element not found');
            return;
        }
        this.ctx = this.canvas.getContext('2d');
        this.nodes = [];
        this.edges = [];
    }

    /**
     * Draw Wait-For Graph
     */
    drawWaitForGraph(wfgData) {
        if (!this.ctx) return;
        
        this.clear();
        
        const nodes = wfgData.nodes || [];
        const edges = wfgData.edges || [];
        
        // Calculate node positions in circle
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const radius = Math.min(centerX, centerY) - 50;
        
        const nodePositions = {};
        nodes.forEach((node, index) => {
            const angle = (2 * Math.PI * index) / nodes.length;
            nodePositions[node] = {
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle)
            };
        });
        
        // Draw edges first
        this.ctx.strokeStyle = '#dc3545';
        this.ctx.lineWidth = 2;
        edges.forEach(edge => {
            const from = nodePositions[edge.from];
            const to = nodePositions[edge.to];
            
            if (from && to) {
                this.drawArrow(from.x, from.y, to.x, to.y);
            }
        });
        
        // Draw nodes
        nodes.forEach(node => {
            const pos = nodePositions[node];
            this.drawNode(pos.x, pos.y, node, '#667eea');
        });
    }

    /**
     * Draw arrow from (x1,y1) to (x2,y2)
     */
    drawArrow(x1, y1, x2, y2) {
        const headLength = 15;
        const angle = Math.atan2(y2 - y1, x2 - x1);
        
        // Shorten line to not overlap with nodes
        const nodeRadius = 25;
        x2 = x2 - nodeRadius * Math.cos(angle);
        y2 = y2 - nodeRadius * Math.sin(angle);
        x1 = x1 + nodeRadius * Math.cos(angle);
        y1 = y1 + nodeRadius * Math.sin(angle);
        
        // Draw line
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.stroke();
        
        // Draw arrowhead
        this.ctx.beginPath();
        this.ctx.moveTo(x2, y2);
        this.ctx.lineTo(
            x2 - headLength * Math.cos(angle - Math.PI / 6),
            y2 - headLength * Math.sin(angle - Math.PI / 6)
        );
        this.ctx.moveTo(x2, y2);
        this.ctx.lineTo(
            x2 - headLength * Math.cos(angle + Math.PI / 6),
            y2 - headLength * Math.sin(angle + Math.PI / 6)
        );
        this.ctx.stroke();
    }

    /**
     * Draw a node (process)
     */
    drawNode(x, y, label, color) {
        const radius = 25;
        
        // Draw circle
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
        this.ctx.fill();
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        // Draw label
        this.ctx.fillStyle = '#fff';
        this.ctx.font = 'bold 14px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(label, x, y);
    }

    /**
     * Clear canvas
     */
    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw background
        this.ctx.fillStyle = '#f8f9fa';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    /**
     * Draw FSA state diagram
     */
    drawFSADiagram(states, currentState) {
        this.clear();
        
        const stateList = Array.isArray(states) ? states : Object.keys(states);
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const radius =Math.min(centerX, centerY) - 50;
    stateList.forEach((state, index) => {
        const angle = (2 * Math.PI * index) / stateList.length;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        
        const color = state === currentState ? '#28a745' : '#6c757d';
        this.drawNode(x, y, state, color);
    });
}
}
// Export for use in main app
window.DeadlockVisualizer = DeadlockVisualizer;
