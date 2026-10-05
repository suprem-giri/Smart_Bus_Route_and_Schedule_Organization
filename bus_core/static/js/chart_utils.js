/**
 * Chart.js Visualization Utilities for Transit Demand & Optimization Metrics
 */

const TransitCharts = {
    renderDemandChart: function(canvasId, labels, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Passenger Demand (Count)',
                    data: data,
                    backgroundColor: 'rgba(37, 99, 235, 0.7)',
                    borderColor: 'rgb(37, 99, 235)',
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleFont: { size: 13, weight: 'bold' },
                        bodyFont: { size: 12 },
                        padding: 10
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Total Passengers' },
                        grid: { color: '#f1f5f9' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    },

    renderComparisonChart: function(canvasId, labels, baselineData, optimizedData, title, unit) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Baseline (Uniform Schedule)',
                        data: baselineData,
                        backgroundColor: 'rgba(148, 163, 184, 0.7)',
                        borderColor: 'rgb(148, 163, 184)',
                        borderWidth: 1.5,
                        borderRadius: 6
                    },
                    {
                        label: 'Optimized (Demand-Allocated)',
                        data: optimizedData,
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderColor: 'rgb(16, 185, 129)',
                        borderWidth: 1.5,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { boxWidth: 14, font: { weight: '600' } }
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        padding: 10,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.raw} ${unit}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: `${title} (${unit})` },
                        grid: { color: '#f1f5f9' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
};
