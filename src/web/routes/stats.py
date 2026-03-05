"""
统计分析路由
"""

from flask import Blueprint, render_template, jsonify, request
from src.web.services.stats_service import StatsService

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/dashboard')
def dashboard():
    """统计仪表盘"""
    try:
        days = request.args.get('days', 30, type=int)

        stats_service = StatsService()

        # 获取各种统计数据
        dashboard_stats = stats_service.get_dashboard_stats()
        trend_data = stats_service.get_trend_data(days=days)
        category_data = stats_service.get_category_distribution()
        source_data = stats_service.get_source_performance(days=7)

        return render_template('stats/dashboard.html',
                             stats=dashboard_stats,
                             trend_data=trend_data,
                             category_data=category_data,
                             source_data=source_data,
                             days=days)

    except Exception as e:
        return render_template('stats/dashboard.html',
                             error=str(e))


@stats_bp.route('/api/trend')
def api_trend():
    """API: 获取趋势数据"""
    try:
        days = request.args.get('days', 30, type=int)
        stats_service = StatsService()
        data = stats_service.get_trend_data(days=days)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@stats_bp.route('/api/category')
def api_category():
    """API: 获取分类分布"""
    try:
        stats_service = StatsService()
        data = stats_service.get_category_distribution()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@stats_bp.route('/api/source')
def api_source():
    """API: 获取新闻源性能"""
    try:
        days = request.args.get('days', 7, type=int)
        stats_service = StatsService()
        data = stats_service.get_source_performance(days=days)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
