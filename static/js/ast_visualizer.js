// AST Visualizer JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // State
    let astData = [];
    let currentTreeIndex = 0;
    
    // DOM elements
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const contentEl = document.getElementById('content');
    const filePathEl = document.getElementById('file-path');
    const linesEl = document.getElementById('lines');
    const nodeTypeEl = document.getElementById('node-type');
    const treeCounterEl = document.getElementById('tree-counter');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const visualizationEl = document.getElementById('visualization');

    // Initialize D3 visualization with zoom and pan
    const margin = {top: 60, right: 120, bottom: 20, left: 120};
    const width = visualizationEl.clientWidth - margin.left - margin.right;
    const height = 600 - margin.top - margin.bottom;
    
    // Create a container for the visualization
    const svg = d3.select(visualizationEl)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .style('overflow', 'hidden');
    
    // Add a group for zoom/pan
    const g = svg.append('g');
    
    // Add a rectangle to capture mouse events for zooming
    svg.append('rect')
        .attr('width', '100%')
        .attr('height', '100%')
        .style('fill', 'none')
        .style('pointer-events', 'all')
        .call(d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            }));
    
    // Add a group for the visualization content
    const visGroup = g.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Event listeners
    prevBtn.addEventListener('click', showPreviousTree);
    nextBtn.addEventListener('click', showNextTree);

    // Initial load
    loadAstData();

    // Functions
    async function loadAstData() {
        try {
            const response = await fetch('/ast');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            astData = await response.json();
            
            if (!astData || astData.length === 0) {
                throw new Error('No AST data available');
            }
            
            // Hide loading, show content
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
            
            // Visualize the first tree
            visualizeTree(0);
            
        } catch (error) {
            console.error('Error loading AST data:', error);
            loadingEl.style.display = 'none';
            showError(`Failed to load AST data: ${error.message}`);
        }
    }

    function showError(message) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }

    function showPreviousTree() {
        if (astData.length <= 1) return;
        currentTreeIndex = (currentTreeIndex - 1 + astData.length) % astData.length;
        visualizeTree(currentTreeIndex);
    }

    function showNextTree() {
        if (astData.length <= 1) return;
        currentTreeIndex = (currentTreeIndex + 1) % astData.length;
        visualizeTree(currentTreeIndex);
    }

    function updateMetadata(metadata) {
        filePathEl.textContent = metadata.file_path || '-';
        linesEl.textContent = metadata.start_line ? 
            `${metadata.start_line}-${metadata.end_line}` : '-';
        nodeTypeEl.textContent = metadata.type || '-';
        
        // Update tree counter
        treeCounterEl.textContent = `${currentTreeIndex + 1} of ${astData.length}`;
        
        // Update button states
        prevBtn.disabled = astData.length <= 1;
        nextBtn.disabled = astData.length <= 1;
    }

    function visualizeTree(index) {
        if (index < 0 || index >= astData.length) return;
        
        const treeItem = astData;
        
        // Update metadata
        if (treeItem.metadata) {
            updateMetadata(treeItem.metadata);
        }
        
        // Process the AST tree for visualization
        const root = processAstNode(treeItem);
        
        // Clear previous visualization
        visGroup.selectAll('*').remove();
        
        // Layout the tree
        const treeLayout = d3.tree().size([height, width - 100]);
        const rootNode = d3.hierarchy(root);
        const treeData = treeLayout(rootNode);
        
        // Calculate bounds for centering
        let minX = Infinity, maxX = -Infinity;
        treeData.descendants().forEach(d => {
            if (d.x < minX) minX = d.x;
            if (d.x > maxX) maxX = d.x;
        });
        
        const treeHeight = maxX - minX;
        const yOffset = (height - treeHeight) / 2 - minX;
        
        // Draw links
        visGroup.selectAll('.link')
            .data(treeData.links())
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', d3.linkHorizontal()
                .x(d => d.y)
                .y(d => d.x + yOffset));
        
        // Create node groups
        const nodes = visGroup.selectAll('.node')
            .data(treeData.descendants())
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.y},${d.x + yOffset})`);
        
        // Add circles to nodes
        nodes.append('circle')
            .attr('r', 4);
        
        // Add text labels
        // nodes.append('text')
        //     .attr('dy', '.31em')
        //     .attr('x', d => d.children ? -13 : 13)
        //     .style('text-anchor', d => d.children ? 'end' : 'start')
        //     .text(d => d.data.name);
        
        // Reset zoom
        const t = d3.zoomIdentity;
        svg.call(d3.zoom().transform, t);
    }
    
    function processAstNode(node) {
        if (!node) return { name: 'undefined' };
        
        // Create a simplified node structure for visualization
        const simpleNode = {
            name: node.type || 'root',
            children: []
        };
        
        // Process child nodes
        for (const key in node) {
            if (key === 'type' || key === 'metadata') continue;
            
            const value = node[key];
            
            if (Array.isArray(value)) {
                // Process array of nodes
                const children = value
                    .filter(item => item && typeof item === 'object')
                    .map(processAstNode);
                
                if (children.length > 0) {
                    simpleNode.children.push({
                        name: `${key} [${children.length}]`,
                        children: children
                    });
                }
            } else if (value && typeof value === 'object') {
                // Process single node
                simpleNode.children.push(processAstNode(value));
            } else if (value !== null && value !== undefined) {
                // Process primitive values
                simpleNode.children.push({
                    name: `${key}: ${value}`
                });
            }
        }
        
        return simpleNode;
    }
});
