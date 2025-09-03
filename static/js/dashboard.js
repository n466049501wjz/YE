// 仪表盘页面交互逻辑
document.addEventListener('DOMContentLoaded', function() {
    // 初始化ECharts图表
    initRegionChart();

    // 添加响应式调整
    window.addEventListener('resize', function() {
        if (window.regionChart) {
            window.regionChart.resize();
        }
    });
});

// 初始化地区分布图表
function initRegionChart() {
    // 从隐藏元素获取数据
    const regionDataElement = document.getElementById('region-data');
    if (!regionDataElement) return;

    const regionData = JSON.parse(regionDataElement.textContent);
    const chartDom = document.getElementById('region-chart');

    if (!chartDom) return;

    window.regionChart = echarts.init(chartDom);

    const regions = Object.keys(regionData);
    const values = Object.values(regionData);

    const option = {
        tooltip: {
            trigger: 'axis',
            formatter: '{b}: {c} 家私募'
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '10%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: regions,
            axisLabel: {
                rotate: 45,
                interval: 0
            }
        },
        yAxis: {
            type: 'value',
            name: '数量'
        },
        series: [{
            data: values,
            type: 'bar',
            itemStyle: {
                color: function(params) {
                    // 使用渐变色
                    const colorList = [
                        '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
                        '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#6e7079'
                    ];
                    return colorList[params.dataIndex % colorList.length];
                }
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };

    window.regionChart.setOption(option);
}

// 刷新图表数据
function refreshChartData() {
    fetch('/api/region_stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('region-data').textContent = JSON.stringify(data);

            if (window.regionChart) {
                const regions = Object.keys(data);
                const values = Object.values(data);

                window.regionChart.setOption({
                    xAxis: {
                        data: regions
                    },
                    series: [{
                        data: values
                    }]
                });
            }
        })
        .catch(error => {
            console.error('Error fetching region stats:', error);
        });
}

// 导出功能
function exportDashboardData() {
    fetch('/api/export_dashboard')
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = '私募数据仪表盘_' + new Date().toISOString().split('T')[0] + '.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('导出失败:', error);
            alert('导出失败，请重试');
        });
}