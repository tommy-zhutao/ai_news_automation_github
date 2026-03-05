/**
 * Chart.js 图表配置和初始化
 */

const Charts = {
    // 默认配置
    defaults: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            }
        }
    },

    // 创建折线图
    createLineChart: function(canvasId, labels, datasets, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const config = {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets.map(ds => ({
                    label: ds.label,
                    data: ds.data,
                    borderColor: ds.color || this.getColor(0),
                    backgroundColor: ds.backgroundColor || this.getColor(0, 0.1),
                    tension: 0.3,
                    fill: ds.fill || false
                }))
            },
            options: {
                ...this.defaults,
                ...options,
                scales: {
                    y: {
                        beginAtZero: true,
                        ...options.scales?.y
                    },
                    x: {
                        ...options.scales?.x
                    }
                }
            }
        };

        return new Chart(ctx, config);
    },

    // 创建柱状图
    createBarChart: function(canvasId, labels, datasets, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const config = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets.map((ds, index) => ({
                    label: ds.label,
                    data: ds.data,
                    backgroundColor: ds.color || this.getColor(index),
                    borderColor: ds.borderColor || this.getColor(index),
                    borderWidth: 1
                }))
            },
            options: {
                ...this.defaults,
                ...options,
                scales: {
                    y: {
                        beginAtZero: true,
                        ...options.scales?.y
                    }
                }
            }
        };

        return new Chart(ctx, config);
    },

    // 创建饼图
    createPieChart: function(canvasId, labels, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const colors = labels.map((_, i) => this.getColor(i));

        const config = {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                ...this.defaults,
                ...options,
                plugins: {
                    legend: {
                        position: 'right',
                        ...options.plugins?.legend
                    }
                }
            }
        };

        return new Chart(ctx, config);
    },

    // 创建环形图
    createDoughnutChart: function(canvasId, labels, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const colors = labels.map((_, i) => this.getColor(i));

        const config = {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                ...this.defaults,
                ...options,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right',
                        ...options.plugins?.legend
                    }
                }
            }
        };

        return new Chart(ctx, config);
    },

    // 获取颜色
    getColor: function(index, alpha = 1) {
        const colors = [
            `rgba(13, 110, 253, ${alpha})`,   // blue
            `rgba(25, 135, 84, ${alpha})`,    // green
            `rgba(255, 193, 7, ${alpha})`,    // yellow
            `rgba(220, 53, 69, ${alpha})`,    // red
            `rgba(13, 202, 240, ${alpha})`,   // cyan
            `rgba(102, 16, 242, ${alpha})`,   // purple
            `rgba(247, 37, 133, ${alpha})`,   // pink
            `rgba(253, 126, 20, ${alpha})`,   // orange
        ];
        return colors[index % colors.length];
    },

    // 更新图表数据
    updateChart: function(chart, labels, datasets) {
        if (!chart) return;

        chart.data.labels = labels;
        chart.data.datasets.forEach((ds, i) => {
            if (datasets[i]) {
                ds.data = datasets[i].data;
            }
        });

        chart.update();
    },

    // 销毁图表
    destroyChart: function(chart) {
        if (chart) {
            chart.destroy();
        }
    }
};

// 导出到全局
window.Charts = Charts;
