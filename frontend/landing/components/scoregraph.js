/**
 * PMBrain AI — Score Graph Renderer
 * Visual opportunity scoring bars
 * Pure CSS + Vanilla JS
 */

const ScoreGraphRenderer = {
    /**
     * Render animated score bars
     * @param {HTMLElement} container
     * @param {Array} scores - [{label, value, max}]
     * @param {Object} options
     */
    render(container, scores, options = {}) {
        if (!container || !scores?.length) return;

        const {
            maxValue = 10,
            animated = true,
            showLabels = true,
            className = ''
        } = options;

        const wrapper = document.createElement('div');
        wrapper.className = `score-graph ${className}`;

        scores.forEach(score => {
            const max = score.max || maxValue;
            const pct = Math.min(100, (score.value / max) * 100);
            const level = pct >= 70 ? 'high' : pct >= 40 ? 'medium' : 'low';

            const row = document.createElement('div');
            row.className = 'score-graph-row';

            row.innerHTML = `
                ${showLabels ? `<div class="score-graph-label">${score.label}</div>` : ''}
                <div class="score-graph-track">
                    <div class="score-graph-fill ${level}" 
                         data-width="${pct}" 
                         style="width: ${animated ? '0' : pct + '%'}">
                    </div>
                </div>
                <div class="score-graph-value">${typeof score.value === 'number' ? score.value.toFixed(1) : score.value}</div>
            `;

            wrapper.appendChild(row);
        });

        container.appendChild(wrapper);

        // Animate bars in
        if (animated) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const fills = wrapper.querySelectorAll('.score-graph-fill');
                        fills.forEach((fill, i) => {
                            const targetWidth = fill.getAttribute('data-width');
                            setTimeout(() => {
                                fill.style.width = targetWidth + '%';
                            }, i * 150 + 100);
                        });
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.3 });

            observer.observe(wrapper);
        }
    },

    /**
     * Render opportunity score breakdown (used in AI response)
     * @param {HTMLElement} container
     * @param {Object} breakdown - {frequency: 8.5, revenue_impact: 7.2, ...}
     */
    renderBreakdown(container, breakdown) {
        if (!container || !breakdown) return;

        const labelMap = {
            frequency_score: 'Frequency',
            frequency: 'Frequency',
            revenue_impact: 'Revenue Impact',
            retention_impact: 'Retention Impact',
            strategic_alignment: 'Strategic Fit',
            strategic_fit: 'Strategic Fit',
            effort_estimate: 'Effort (Low=Better)',
            effort: 'Effort (Low=Better)',
            confidence: 'Confidence',
            total_score: 'Total Score',
            market_demand: 'Market Demand',
            competitive_advantage: 'Competitive Edge',
            technical_feasibility: 'Technical Feasibility'
        };

        const scores = Object.entries(breakdown)
            .filter(([k]) => k !== 'total_score')
            .map(([key, value]) => ({
                label: labelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                value: typeof value === 'number' ? value : parseFloat(value) || 0,
                max: 10
            }));

        this.render(container, scores, { animated: true, maxValue: 10 });
    }
};
