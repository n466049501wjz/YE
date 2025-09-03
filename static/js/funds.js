// 私募列表页面交互逻辑
document.addEventListener('DOMContentLoaded', function() {
    // 初始化筛选表单交互
    initFilterForm();

    // 初始化排序功能
    initSorting();

    // 初始化高级筛选
    initAdvancedFilters();

    // 添加响应式调整
    window.addEventListener('resize', adjustTableLayout);

    // 初始调整表格布局
    adjustTableLayout();
});

// 初始化筛选表单交互
function initFilterForm() {
    const filterForm = document.getElementById('filter-form');
    if (!filterForm) return;

    // 重置按钮
    const resetBtn = filterForm.querySelector('.btn-reset');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            filterForm.reset();
            // 提交空表单以重置所有筛选
            filterForm.submit();
        });
    }

    // 动态策略标签输入
    const strategyInput = document.getElementById('strategy');
    if (strategyInput) {
        // 可以从服务器获取所有策略标签，这里使用简单实现
        strategyInput.addEventListener('focus', function() {
            this.setAttribute('list', 'strategy-suggestions');
        });
    }

    // 高级筛选切换
    const advancedToggle = document.getElementById('advanced-filter-toggle');
    const advancedFilters = document.getElementById('advanced-filters');

    if (advancedToggle && advancedFilters) {
        advancedToggle.addEventListener('click', function() {
            advancedFilters.classList.toggle('d-none');
            this.textContent = advancedFilters.classList.contains('d-none') ?
                '显示高级筛选' : '隐藏高级筛选';
        });
    }
}

// 初始化排序功能
function initSorting() {
    const sortLinks = document.querySelectorAll('th a[data-sort]');
    sortLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            const sortBy = this.getAttribute('data-sort');
            const currentOrder = this.getAttribute('data-order') || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';

            // 更新所有排序指示器
            sortLinks.forEach(l => {
                l.querySelector('i').className = 'bi bi-arrow-down-up';
            });

            // 设置当前排序指示器
            this.setAttribute('data-order', newOrder);
            this.querySelector('i').className = `bi bi-arrow-${newOrder === 'asc' ? 'up' : 'down'}`;

            // 获取当前筛选参数
            const url = new URL(window.location);
            url.searchParams.set('sort_by', sortBy);
            url.searchParams.set('order', newOrder);

            // 跳转到新URL
            window.location.href = url.toString();
        });
    });
}

// 初始化高级筛选
function initAdvancedFilters() {
    // 日期范围选择器
    const dateRangeInputs = document.querySelectorAll('.date-range-input');
    if (dateRangeInputs.length > 0) {
        // 可以使用第三方日期选择器库，这里使用原生输入
        dateRangeInputs.forEach(input => {
            input.addEventListener('change', applyFilters);
        });
    }

    // 多选策略标签
    const multiStrategySelect = document.getElementById('multi-strategy');
    if (multiStrategySelect) {
        multiStrategySelect.addEventListener('change', applyFilters);
    }
}

// 应用筛选条件
function applyFilters() {
    const form = document.getElementById('filter-form');
    if (form) {
        // 创建FormData对象
        const formData = new FormData(form);

        // 构建查询参数
        const params = new URLSearchParams();

        for (let [key, value] of formData.entries()) {
            if (value) {
                params.append(key, value);
            }
        }

        // 获取当前排序参数
        const currentUrl = new URL(window.location);
        const sortBy = currentUrl.searchParams.get('sort_by');
        const order = currentUrl.searchParams.get('order');

        if (sortBy) params.set('sort_by', sortBy);
        if (order) params.set('order', order);

        // 跳转到筛选后的页面
        window.location.href = `${window.location.pathname}?${params.toString()}`;
    }
}

// 调整表格布局（响应式）
function adjustTableLayout() {
    const table = document.querySelector('.table-responsive');
    if (!table) return;

    if (window.innerWidth < 768) {
        table.classList.add('small-table');
    } else {
        table.classList.remove('small-table');
    }
}

// 导出筛选结果
function exportFilteredData() {
    // 获取当前筛选参数
    const currentUrl = new URL(window.location);
    const params = new URLSearchParams(currentUrl.search);

    fetch(`/api/export_funds?${params.toString()}`)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = '私募筛选结果_' + new Date().toISOString().split('T')[0] + '.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('导出失败:', error);
            alert('导出失败，请重试');
        });
}

// 快速筛选函数
function quickFilter(column, value) {
    const input = document.querySelector(`[name="${column}"]`);
    if (input) {
        input.value = value;
        applyFilters();
    }
}