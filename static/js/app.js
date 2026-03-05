/**
 * AI新闻自动化系统 - 主要JavaScript
 */

// 全局配置
const App = {
    apiBase: '',
    refreshInterval: null,

    // 初始化
    init: function() {
        this.initTooltips();
        this.initPopovers();
        this.handleAjaxErrors();
    },

    // 初始化工具提示
    initTooltips: function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    // 初始化弹出框
    initPopovers: function() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    },

    // 处理AJAX错误
    handleAjaxErrors: function() {
        $(document).ajaxError(function(event, jqXHR, settings, thrownError) {
            console.error('AJAX Error:', thrownError);
            App.showError('请求失败: ' + (jqXHR.responseJSON?.message || thrownError));
        });
    },

    // 显示成功消息
    showSuccess: function(message) {
        this.showToast(message, 'success');
    },

    // 显示错误消息
    showError: function(message) {
        this.showToast(message, 'danger');
    },

    // 显示警告消息
    showWarning: function(message) {
        this.showToast(message, 'warning');
    },

    // 显示信息消息
    showInfo: function(message) {
        this.showToast(message, 'info');
    },

    // 显示Toast通知
    showToast: function(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            // 创建toast容器
            const container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast" role="alert" data-bs-autohide="true" data-bs-delay="3000">
                <div class="toast-header bg-${type} text-white">
                    <strong class="me-auto">${this.getToastTitle(type)}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        const container = document.querySelector('.toast-container');
        container.insertAdjacentHTML('beforeend', toastHtml);

        const toastEl = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastEl);
        toast.show();

        // 移除已关闭的toast
        toastEl.addEventListener('hidden.bs.toast', function() {
            toastEl.remove();
        });
    },

    // 获取Toast标题
    getToastTitle: function(type) {
        const titles = {
            'success': '<i class="bi bi-check-circle"></i> 成功',
            'danger': '<i class="bi bi-x-circle"></i> 错误',
            'warning': '<i class="bi bi-exclamation-triangle"></i> 警告',
            'info': '<i class="bi bi-info-circle"></i> 信息'
        };
        return titles[type] || titles['info'];
    },

    // 确认对话框
    confirm: function(message, callback) {
        if (window.confirm(message)) {
            callback();
        }
    },

    // 格式化日期
    formatDate: function(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    },

    // 格式化日期时间
    formatDateTime: function(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // 复制到剪贴板
    copyToClipboard: function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                App.showSuccess('已复制到剪贴板');
            }).catch(function() {
                App.showError('复制失败');
            });
        } else {
            // 降级方案
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                App.showSuccess('已复制到剪贴板');
            } catch (e) {
                App.showError('复制失败');
            }
            document.body.removeChild(textarea);
        }
    },

    // 加载指示器
    showLoading: function(target) {
        const loadingHtml = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2 text-muted">加载中...</p>
            </div>
        `;
        $(target).html(loadingHtml);
    },

    // 隐藏加载指示器
    hideLoading: function(target) {
        $(target).find('.spinner-border').parent().remove();
    },

    // API请求封装
    api: {
        get: function(url, data = {}) {
            return $.ajax({
                url: App.apiBase + url,
                method: 'GET',
                data: data,
                dataType: 'json'
            });
        },

        post: function(url, data = {}) {
            return $.ajax({
                url: App.apiBase + url,
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(data),
                dataType: 'json'
            });
        },

        delete: function(url, data = {}) {
            return $.ajax({
                url: App.apiBase + url,
                method: 'DELETE',
                contentType: 'application/json',
                data: JSON.stringify(data),
                dataType: 'json'
            });
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

// 导出到全局
window.App = App;
