"""
主页路由
"""

from flask import Blueprint, render_template, jsonify
from src.web.models import News, DailySummary, RunHistory
from src.web.services.news_service import NewsService
from src.web.services.stats_service import StatsService
from datetime import date, timedelta

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首页仪表盘"""
    try:
        # 获取统计数据
        stats_service = StatsService()
        dashboard_stats = stats_service.get_dashboard_stats()

        # 获取最新新闻
        news_service = NewsService()
        recent_news = news_service.get_recent_news(limit=10)

        # 获取趋势数据（最近7天）
        trend_data = stats_service.get_trend_data(days=7)

        return render_template('index.html',
                             stats=dashboard_stats,
                             recent_news=recent_news,
                             trend_data=trend_data)
    except Exception as e:
        return render_template('index.html',
                             stats=None,
                             recent_news=[],
                             trend_data=None,
                             error=str(e))


@main_bp.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI News Automation'
    })
