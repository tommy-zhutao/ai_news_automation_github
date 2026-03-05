"""
新闻相关路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from src.web.models import News, db
from src.web.services.news_service import NewsService

news_bp = Blueprint('news', __name__)


@news_bp.route('/')
def list():
    """新闻列表页"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # 获取筛选参数
        filters = {
            'date': request.args.get('date'),
            'category': request.args.get('category'),
            'region': request.args.get('region'),
            'type': request.args.get('type'),
            'source': request.args.get('source')
        }

        # 移除空值
        filters = {k: v for k, v in filters.items() if v}

        news_service = NewsService()
        result = news_service.get_news_list(page=page, per_page=per_page, filters=filters)

        return render_template('news/list.html',
                             news=result['items'],
                             pagination=result['pagination'],
                             filters=filters)

    except Exception as e:
        return render_template('news/list.html',
                             news=[],
                             pagination=None,
                             filters={},
                             error=str(e))


@news_bp.route('/detail/<int:news_id>')
def detail(news_id):
    """新闻详情页"""
    try:
        news_service = NewsService()
        news_item = news_service.get_news_detail(news_id)

        if not news_item:
            return render_template('errors/404.html'), 404

        return render_template('news/detail.html', news=news_item)

    except Exception as e:
        return render_template('errors/500.html'), 500


@news_bp.route('/search')
def search():
    """搜索新闻"""
    try:
        keyword = request.args.get('q', '')
        page = request.args.get('page', 1, type=int)

        if not keyword:
            return redirect(url_for('news.list'))

        news_service = NewsService()
        result = news_service.search_news(keyword, page=page)

        return render_template('news/search.html',
                             news=result['items'],
                             pagination=result['pagination'],
                             keyword=keyword)

    except Exception as e:
        return render_template('news/search.html',
                             news=[],
                             pagination=None,
                             keyword=request.args.get('q', ''),
                             error=str(e))


@news_bp.route('/delete', methods=['POST'])
def delete():
    """批量删除新闻"""
    try:
        news_ids = request.json.get('ids', [])

        if not news_ids:
            return jsonify({'success': False, 'message': '未选择任何新闻'})

        news_service = NewsService()
        deleted_count = news_service.delete_news(news_ids)

        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 条新闻'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
