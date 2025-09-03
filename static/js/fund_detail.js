// 私募详情页面交互逻辑
document.addEventListener('DOMContentLoaded', function() {
    // 初始化文件上传预览
    initFileUploadPreview();

    // 初始化尽调记录表单验证
    initDueDiligenceForm();

    // 初始化标签编辑功能
    initTagEditing();

    // 初始化图表（如果有）
    initFundCharts();
});

// 初始化文件上传预览
function initFileUploadPreview() {
    const fileInput = document.getElementById('file');
    const filePreview = document.getElementById('file-preview');

    if (fileInput && filePreview) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const fileName = file.name;
                const fileSize = formatFileSize(file.size);
                const fileType = file.type.split('/')[1] || file.type;

                filePreview.innerHTML = `
                    <div class="alert alert-info d-flex align-items-center">
                        <i class="bi bi-file-earmark me-2"></i>
                        <div>
                            <strong>${fileName}</strong> (${fileSize})
                            <div class="small">类型: ${fileType}</div>
                        </div>
                    </div>
                `;
                filePreview.classList.remove('d-none');
            } else {
                filePreview.classList.add('d-none');
            }
        });
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 初始化尽调记录表单验证
function initDueDiligenceForm() {
    const form = document.getElementById('due-diligence-form');

    if (form) {
        form.addEventListener('submit', function(e) {
            const content = document.getElementById('content').value.trim();
            const fileInput = document.getElementById('file');

            if (!content) {
                e.preventDefault();
                alert('尽调内容不能为空');
                document.getElementById('content').focus();
                return false;
            }

            // 检查文件大小
            if (fileInput.files.length > 0) {
                const maxSize = 16 * 1024 * 1024; // 16MB
                if (fileInput.files[0].size > maxSize) {
                    e.preventDefault();
                    alert('文件大小不能超过16MB');
                    return false;
                }
            }

            // 显示提交中状态
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 提交中...';
            }

            return true;
        });
    }
}

// 初始化标签编辑功能
function initTagEditing() {
    const tagsContainer = document.getElementById('strategy-tags');
    const editBtn = document.getElementById('edit-tags-btn');

    if (tagsContainer && editBtn) {
        editBtn.addEventListener('click', function() {
            if (tagsContainer.isContentEditable) {
                // 保存编辑
                tagsContainer.contentEditable = false;
                this.innerHTML = '<i class="bi bi-pencil"></i> 编辑标签';
                this.classList.remove('btn-success');
                this.classList.add('btn-outline-primary');

                // 发送更新请求
                const newTags = tagsContainer.textContent;
                updateFundTags(newTags);
            } else {
                // 开始编辑
                tagsContainer.contentEditable = true;
                tagsContainer.focus();
                this.innerHTML = '<i class="bi bi-check"></i> 保存';
                this.classList.remove('btn-outline-primary');
                this.classList.add('btn-success');
            }
        });
    }
}

// 更新基金标签
function updateFundTags(tags) {
    const fundId = document.getElementById('fund-id').value;

    fetch(`/fund/${fundId}/update_tags`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tags: tags })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('标签更新成功', 'success');
        } else {
            showAlert('标签更新失败: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('标签更新失败', 'danger');
    });
}

// 初始化基金图表
function initFundCharts() {
    const performanceChartEl = document.getElementById('performance-chart');

    if (performanceChartEl) {
        // 如果有性能数据，可以初始化图表
        // 这里只是示例，实际需要从服务器获取数据
        const performanceData = [
            { date: '2023-01', value: 100 },
            { date: '2023-02', value: 105 },
            { date: '2023-03', value: 110 },
            { date: '2023-04', value: 108 },
            { date: '2023-05', value: 115 },
            { date: '2023-06', value: 120 }
        ];

        const dates = performanceData.map(d => d.date);
        const values = performanceData.map(d => d.value);

        const chart = echarts.init(performanceChartEl);
        const option = {
            tooltip: {
                trigger: 'axis'
            },
            xAxis: {
                type: 'category',
                data: dates
            },
            yAxis: {
                type: 'value',
                name: '净值'
            },
            series: [{
                data: values,
                type: 'line',
                smooth: true,
                itemStyle: {
                    color: '#0d6efd'
                }
            }]
        };

        chart.setOption(option);

        // 响应窗口大小变化
        window.addEventListener('resize', function() {
            chart.resize();
        });
    }
}

// 显示提示信息
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);

        // 5秒后自动消失
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.parentNode.removeChild(alertDiv);
                    }
                }, 500);
            }
        }, 5000);
    }
}

// 删除尽调记录
function deleteDueDiligence(ddId) {
    if (!confirm('确定要删除这条尽调记录吗？此操作不可撤销。')) {
        return;
    }

    fetch(`/due_diligence/${ddId}/delete`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('尽调记录已删除', 'success');
            // 刷新页面或移除对应的DOM元素
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert('删除失败: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('删除失败', 'danger');
    });
}

// 下载附件
function downloadAttachment(filePath) {
    window.open(`/uploads/${filePath}`, '_blank');
}