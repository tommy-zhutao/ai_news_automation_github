"""
新闻业务逻辑服务
"""

from datetime import datetime, date, timedelta
from sqlalchemy import func
from src.web.models import News, db


class NewsService:
    """新闻服务类"""

    @staticmethod
    def get_news_list(page=1, per_page=20, filters=None):
        """
        获取新闻列表（支持筛选、分页）

        Args:
            page: 页码
            per_page: 每页数量
            filters: 筛选条件

        Returns:
            dict: 包含新闻列表和分页信息
        """
        query = News.query

        # 应用筛选
        if filters:
            if 'date' in filters and filters['date']:
                query = query.filter(News.date == filters['date'])

            if 'category' in filters and filters['category']:
                query = query.filter(News.category == filters['category'])

            if 'region' in filters and filters['region']:
                query = query.filter(News.region == filters['region'])

            if 'type' in filters and filters['type']:
                query = query.filter(News.type == filters['type'])

            if 'source' in filters and filters['source']:
                query = query.filter(News.source == filters['source'])

        # 按日期和评分排序
        query = query.order_by(News.date.desc(), News.score.desc())

        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            'items': [item.to_dict() for item in pagination.items],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }

    @staticmethod
    def get_recent_news(limit=10):
        """
        获取最新新闻

        Args:
            limit: 数量限制

        Returns:
            list: 新闻列表
        """
        news_list = News.query.order_by(News.date.desc(), News.score.desc()).limit(limit).all()
        return [item.to_dict() for item in news_list]

    @staticmethod
    def search_news(keyword, page=1, per_page=20):
        """
        搜索新闻

        Args:
            keyword: 搜索关键词
            page: 页码
            per_page: 每页数量

        Returns:
            dict: 包含搜索结果和分页信息
        """
        # 使用SQLAlchemy的or_进行搜索
        from sqlalchemy import or_

        query = News.query.filter(
            or_(
                News.title.contains(keyword),
                News.link.contains(keyword),
                News.summary.contains(keyword)
            )
        )

        query = query.order_by(News.date.desc(), News.score.desc())

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            'items': [item.to_dict() for item in pagination.items],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }

    @staticmethod
    def get_news_detail(news_id):
        """
        获取新闻详情

        Args:
            news_id: 新闻ID

        Returns:
            dict: 新闻详情
        """
        news_item = News.query.get(news_id)
        return news_item.to_dict() if news_item else None

    @staticmethod
    def delete_news(news_ids):
        """
        批量删除新闻

        Args:
            news_ids: 新闻ID列表

        Returns:
            int: 删除的数量
        """
        try:
            deleted = News.query.filter(News.id.in_(news_ids)).delete(synchronize_session=False)
            db.session.commit()
            return deleted
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_categories():
        """
        获取所有分类

        Returns:
            list: 分类列表
        """
        categories = db.session.query(News.category).distinct().order_by(News.category).all()
        return [c[0] for c in categories]

    @staticmethod
    def get_sources():
        """
        获取所有新闻源

        Returns:
            list: 新闻源列表
        """
        sources = db.session.query(News.source).distinct().order_by(News.source).all()
        return [s[0] for s in sources]

    @staticmethod
    def get_news_by_date_range(start_date, end_date):
        """
        获取指定日期范围的新闻

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            list: 新闻列表
        """
        news_list = News.query.filter(
            News.date >= start_date,
            News.date <= end_date
        ).order_by(News.date.desc(), News.score.desc()).all()

        return [item.to_dict() for item in news_list]
