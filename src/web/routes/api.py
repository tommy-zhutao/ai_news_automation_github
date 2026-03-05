"""
API路由
"""

import threading
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
from src.web.services.news_service import NewsService
from src.web.services.stats_service import StatsService
from src.web.models import RunHistory, db

api_bp = Blueprint('api', __name__)

# 全局变量跟踪抓取状态
fetch_status = {
    'running': False,
    'message': '',
    'success': False,
    'start_time': None,
    'total_fetched': 0,
    'final_selected': 0
}


@api_bp.route('/fetch-news', methods=['POST'])
def fetch_news():
    """API: 立即抓取新闻"""
    global fetch_status

    if fetch_status['running']:
        return jsonify({
            'success': False,
            'message': '抓取任务正在运行中'
        })

    try:
        # 启动后台抓取任务
        fetch_status['running'] = True
        fetch_status['message'] = '正在初始化...'
        fetch_status['success'] = False
        fetch_status['start_time'] = datetime.now()
        fetch_status['total_fetched'] = 0
        fetch_status['final_selected'] = 0

        # 在新线程中运行抓取任务
        thread = threading.Thread(target=run_fetch_task)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': '抓取任务已启动'
        })

    except Exception as e:
        fetch_status['running'] = False
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/fetch-status', methods=['GET'])
def get_fetch_status():
    """API: 获取抓取状态"""
    return jsonify({
        'running': fetch_status['running'],
        'success': fetch_status['success'],
        'message': fetch_status['message'],
        'total_fetched': fetch_status['total_fetched'],
        'final_selected': fetch_status['final_selected']
    })


def run_fetch_task():
    """后台运行抓取任务"""
    global fetch_status

    try:
        from src.main import NewsAutomationApp
        from src.utils.logger import get_logger

        logger = get_logger('fetch_task')

        fetch_status['message'] = '正在加载配置...'
        app = NewsAutomationApp('config.json')

        fetch_status['message'] = '正在初始化模块...'
        app.initialize()

        fetch_status['message'] = '正在抓取新闻...'
        news_list = app.fetcher_manager.fetch_all(concurrent=True)

        if not news_list:
            fetch_status['message'] = '未获取到任何新闻'
            fetch_status['running'] = False
            return

        fetch_status['total_fetched'] = len(news_list)
        fetch_status['message'] = f'已抓取 {len(news_list)} 条新闻，正在AI处理...'

        # AI筛选
        if app.ai_filter and app.ai_filter.is_available():
            original_count = len(news_list)
            news_list = app.ai_filter.filter_news(news_list)
            fetch_status['message'] = f'AI筛选完成：{original_count} -> {len(news_list)} 条'

        # 按评分排序
        news_list = app.fetcher_manager.sort_by_score(news_list)
        fetch_status['final_selected'] = len(news_list)

        # AI处理
        ai_summary = ""
        ai_trends = ""
        if app.ai_processor and app.ai_processor.is_available():
            fetch_status['message'] = '正在进行AI摘要和趋势分析...'
            ai_summary, ai_trends = app.ai_processor.generate_all_separated(news_list)

        # 保存文件
        fetch_status['message'] = '正在保存文件...'
        output_dir = app.config.output.output_dir
        app.email_sender.save_to_file(news_list, ai_summary, ai_trends, output_dir)

        # 发送邮件
        fetch_status['message'] = '正在发送邮件...'
        if app.email_sender._is_email_configured():
            success = app.email_sender.send_news(news_list, ai_summary, ai_trends)
            if success:
                fetch_status['message'] = '邮件发送成功'
            else:
                fetch_status['message'] = '邮件发送失败'
        else:
            fetch_status['message'] = '跳过邮件发送（未配置）'

        # 记录运行历史
        try:
            from src.web.app import create_app
            flask_app = create_app()
            with flask_app.app_context():
                history = RunHistory(
                    start_time=fetch_status['start_time'],
                    end_time=datetime.now(),
                    status='success',
                    total_fetched=fetch_status['total_fetched'],
                    unique_news=fetch_status['total_fetched'],
                    final_selected=fetch_status['final_selected']
                )
                db.session.add(history)
                db.session.commit()
        except:
            pass

        app.cleanup()

        # 导入新数据到数据库
        try:
            from src.web.services.data_importer import DataImporter
            fetch_status['message'] = '正在导入数据到数据库...'
            importer = DataImporter('output')
            stats = importer.sync_from_output()
            fetch_status['message'] = f'完成！导入 {stats["imported_news"]} 条新闻'
        except Exception as e:
            logger.error(f"导入数据失败: {e}")

        fetch_status['running'] = False
        fetch_status['success'] = True
        fetch_status['message'] = '抓取完成！'

    except Exception as e:
        fetch_status['running'] = False
        fetch_status['success'] = False
        fetch_status['message'] = f'抓取失败: {str(e)}'


@api_bp.route('/news', methods=['GET'])
def get_news():
    """API: 获取新闻列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        filters = {
            'date': request.args.get('date'),
            'category': request.args.get('category'),
            'region': request.args.get('region'),
            'type': request.args.get('type'),
            'source': request.args.get('source')
        }
        filters = {k: v for k, v in filters.items() if v}

        news_service = NewsService()
        result = news_service.get_news_list(page=page, per_page=per_page, filters=filters)

        return jsonify({
            'success': True,
            'data': result['items'],
            'pagination': result['pagination']
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/news/<int:news_id>', methods=['GET'])
def get_news_detail(news_id):
    """API: 获取新闻详情"""
    try:
        news_service = NewsService()
        news_item = news_service.get_news_detail(news_id)

        if news_item:
            return jsonify({'success': True, 'data': news_item})
        else:
            return jsonify({'success': False, 'message': '新闻不存在'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/stats/dashboard', methods=['GET'])
def get_dashboard_stats():
    """API: 获取仪表盘统计"""
    try:
        stats_service = StatsService()
        stats = stats_service.get_dashboard_stats()
        return jsonify({'success': True, 'data': stats})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/stats/trend', methods=['GET'])
def get_trend_stats():
    """API: 获取趋势统计"""
    try:
        days = request.args.get('days', 30, type=int)
        stats_service = StatsService()
        data = stats_service.get_trend_data(days=days)
        return jsonify({'success': True, 'data': data})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI News Automation API',
        'version': '2.3.0'
    })


@api_bp.route('/ai-summary', methods=['GET'])
def get_ai_summary():
    """API: 获取最新AI摘要"""
    try:
        from src.web.app import create_app
        from src.web.models import DailySummary, db

        app = create_app()
        with app.app_context():
            # 获取最新的AI摘要
            latest = DailySummary.query.order_by(DailySummary.date.desc()).first()

            if latest:
                return jsonify({
                    'success': True,
                    'data': {
                        'date': latest.date.isoformat() if latest.date else None,
                        'ai_summary': latest.ai_summary,
                        'ai_trends': latest.ai_trends,
                        'total_news': latest.total_news,
                        'domestic_count': latest.domestic_count,
                        'global_count': latest.global_count
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'data': None
                })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/latest-stats', methods=['GET'])
def get_latest_stats():
    """API: 获取最新统计（用于实时更新）"""
    try:
        stats_service = StatsService()
        stats = stats_service.get_dashboard_stats()

        # 获取AI摘要
        from src.web.app import create_app
        from src.web.models import DailySummary, db

        app = create_app()
        with app.app_context():
            latest = DailySummary.query.order_by(DailySummary.date.desc()).first()

            result = {
                'success': True,
                'stats': stats,
                'ai_summary': None
            }

            if latest:
                result['ai_summary'] = {
                    'date': latest.date.isoformat() if latest.date else None,
                    'ai_summary': latest.ai_summary,
                    'ai_trends': latest.ai_trends
                }

            return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
