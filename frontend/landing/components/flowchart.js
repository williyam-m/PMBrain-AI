/**
 * PMBrain AI — Flowchart Renderer
 * Creates visual flow diagrams from structured data
 * Pure CSS + Vanilla JS
 */

const FlowchartRenderer = {
    /**
     * Render a vertical flowchart
     * @param {HTMLElement} container
     * @param {Array} nodes - [{icon, title, subtitle}]
     * @param {Object} options
     */
    render(container, nodes, options = {}) {
        if (!container || !nodes?.length) return;

        const {
            className = '',
            animated = true,
            compact = false
        } = options;

        const wrapper = document.createElement('div');
        wrapper.className = `flowchart-container ${className}`;

        nodes.forEach((node, i) => {
            // Node
            const nodeEl = document.createElement('div');
            nodeEl.className = 'flowchart-node fade-in-up';
            if (animated) {
                nodeEl.style.transitionDelay = `${i * 0.12}s`;
            }

            nodeEl.innerHTML = `
                <div class="flowchart-node-icon">${node.icon}</div>
                <div>
                    <div class="flowchart-node-text">${node.title}</div>
                    ${node.subtitle ? `<div class="flowchart-node-sub">${node.subtitle}</div>` : ''}
                </div>
            `;

            // Add tooltip on hover
            if (node.tooltip) {
                nodeEl.title = node.tooltip;
            }

            wrapper.appendChild(nodeEl);

            // Arrow (except after last node)
            if (i < nodes.length - 1) {
                const arrow = document.createElement('div');
                arrow.className = 'flowchart-arrow';
                if (compact) arrow.style.height = '16px';
                wrapper.appendChild(arrow);
            }
        });

        container.appendChild(wrapper);

        // Trigger reveal animation after DOM insertion
        if (animated) {
            requestAnimationFrame(() => {
                wrapper.querySelectorAll('.fade-in-up').forEach(el => {
                    el.classList.add('visible');
                });
            });
        }
    },

    /**
     * Render an execution plan flowchart (enhanced for AI results)
     * @param {HTMLElement} container
     * @param {Array} steps - [{phase, tasks, estimate}]
     */
    renderExecutionPlan(container, steps) {
        if (!container || !steps?.length) return;

        const nodes = steps.map((step, i) => ({
            icon: ['🎯', '⚙️', '🔌', '🎨', '🧪', '🚀'][i % 6],
            title: step.phase || step.title || step.task || `Step ${i + 1}`,
            subtitle: [
                step.estimate ? `Est: ${step.estimate}` : '',
                step.tasks ? `${step.tasks.length} tasks` : '',
                step.priority ? `Priority: ${step.priority}` : ''
            ].filter(Boolean).join(' · ')
        }));

        this.render(container, nodes, { animated: true });
    }
};
