// 主JavaScript文件

document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 初始化弹出框
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // 表单验证增强
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // 自动关闭警告框
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 动态更新页面时间
    function updateDateTime() {
        const now = new Date();
        const dateTimeElements = document.querySelectorAll('.current-datetime');
        dateTimeElements.forEach(element => {
            element.textContent = now.toLocaleString('zh-CN');
        });
    }
    setInterval(updateDateTime, 1000);
    updateDateTime();

    // 表格排序
    const sortableHeaders = document.querySelectorAll('.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const columnIndex = Array.from(this.parentElement.children).indexOf(this);
            const isAscending = this.classList.contains('asc');
            
            // 移除所有排序图标
            sortableHeaders.forEach(h => {
                h.classList.remove('asc', 'desc');
            });
            
            // 设置当前排序方向
            this.classList.toggle('asc', !isAscending);
            this.classList.toggle('desc', isAscending);
            
            // 排序表格
            sortTable(table, columnIndex, !isAscending);
        });
    });

    // 搜索功能增强
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            const searchTerm = this.value.toLowerCase();
            const table = this.closest('.table-container').querySelector('table');
            
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            }
        }, 300));
    });

    // 批量操作
    const selectAllCheckbox = document.querySelector('.select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.item-select');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    // 导出功能
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.dataset.format || 'excel';
            const dataType = this.dataset.type || 'students';
            
            // 显示加载状态
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> 导出中...';
            this.disabled = true;
            
            // 模拟API调用
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
                showToast('数据导出成功！', 'success');
            }, 2000);
        });
    });

    // 图表初始化
    initializeCharts();
});

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 表格排序函数
function sortTable(table, column, asc = true) {
    const dirModifier = asc ? 1 : -1;
    const tBody = table.tBodies[0];
    const rows = Array.from(tBody.querySelectorAll('tr'));

    // 排序行
    const sortedRows = rows.sort((a, b) => {
        const aColText = a.querySelector(`td:nth-child(${column + 1})`).textContent.trim();
        const bColText = b.querySelector(`td:nth-child(${column + 1})`).textContent.trim();

        return aColText > bColText ? (1 * dirModifier) : (-1 * dirModifier);
    });

    // 移除所有现有行
    while (tBody.firstChild) {
        tBody.removeChild(tBody.firstChild);
    }

    // 重新添加排序后的行
    tBody.append(...sortedRows);

    // 更新表头指示器
    table.querySelectorAll('th').forEach(th => th.classList.remove('asc', 'desc'));
    table.querySelector(`th:nth-child(${column + 1})`).classList.toggle('asc', asc);
    table.querySelector(`th:nth-child(${column + 1})`).classList.toggle('desc', !asc);
}

// 显示Toast通知
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toastId = 'toast-' + Date.now();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    // 移除隐藏的toast
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// 创建Toast容器
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

// 初始化图表
function initializeCharts() {
    // 如果有图表容器，初始化示例图表
    const chartContainers = document.querySelectorAll('.chart-container');
    
    chartContainers.forEach(container => {
        const canvas = container.querySelector('canvas');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const chartType = canvas.dataset.chartType || 'bar';
        
        // 示例数据
        const sampleData = {
            labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
            datasets: [{
                label: '示例数据',
                data: [12, 19, 3, 5, 2, 3],
                backgroundColor: 'rgba(74, 122, 188, 0.2)',
                borderColor: 'rgba(74, 122, 188, 1)',
                borderWidth: 1
            }]
        };
        
        new Chart(ctx, {
            type: chartType,
            data: sampleData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            }
        });
    });
}

// AJAX表单提交
function submitFormAjax(form, callback) {
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: form.method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (callback && typeof callback === 'function') {
            callback(data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('请求失败，请稍后重试', 'danger');
    });
}

// 文件上传预览
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    const file = input.files[0];
    const reader = new FileReader();
    
    reader.addEventListener('load', function() {
        preview.src = reader.result;
        preview.style.display = 'block';
    }, false);
    
    if (file) {
        reader.readAsDataURL(file);
    }
}

// 复制到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(err => {
        console.error('复制失败:', err);
        showToast('复制失败', 'danger');
    });
}

// 页面加载动画
function showPageLoading() {
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loading-overlay';
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(loadingOverlay);
}

function hidePageLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// 监听页面加载状态
window.addEventListener('beforeunload', showPageLoading);
window.addEventListener('load', hidePageLoading);