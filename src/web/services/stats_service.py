"""
统计分析服务
"""

from datetime import date, timedelta, datetime as dt
from sqlalchemy import func
from src.web.models import News, DailySummary, RunHistory, SourceStats, db


class StatsService:
    """统计分析服务类"""

    @staticmethod
    def get_dashboard_stats():
        """
        获取仪表盘统计数据

        Returns:
            dict: 统计数据
        """
        today = date.today()

        # 总新闻数
        total_news = News.query.count()

        # 今日新闻数
        today_news = News.query.filter(News.date == today).count()

        # 国内/国际新闻数
        domestic_count = News.query.filter(News.region == 'domestic').count()
        global_count = News.query.filter(News.region == 'global').count()

        # 最新运行记录
        latest_run = RunHistory.query.order_by(RunHistory.start_time.desc()).first()

        # 新闻源数量
        source_count = len(News.query.with_entities(News.source).distinct().all())

        # 平均评分
        avg_score = db.session.query(func.avg(News.score)).scalar() or 0

        return {
            'total_news': total_news,
            'today_news': today_news,
            'domestic_count': domestic_count,
            'global_count': global_count,
            'source_count': source_count,
            'avg_score': round(avg_score, 2),
            'latest_run': latest_run.to_dict() if latest_run else None
        }

    @staticmethod
    def get_trend_data(days=30):
        """
        获取趋势数据

        Args:
            days: 天数

        Returns:
            dict: 趋势数据
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)

        # 从daily_summary表获取数据
        summaries = DailySummary.query.filter(
            DailySummary.date >= start_date,
            DailySummary.date <= end_date
        ).order_by(DailySummary.date).all()

        # 如果没有汇总数据，从news表统计
        if not summaries:
            dates = []
            counts = []
            domestic = []
            global_ = []

            current_date = start_date
            while current_date <= end_date:
                dates.append(current_date.isoformat())

                count = News.query.filter(News.date == current_date).count()
                counts.append(count)

                d_count = News.query.filter(
                    News.date == current_date,
                    News.region == 'domestic'
                ).count()
                domestic.append(d_count)

                g_count = News.query.filter(
                    News.date == current_date,
                    News.region == 'global'
                ).count()
                global_.append(g_count)

                current_date += timedelta(days=1)

            return {
                'dates': dates,
                'total': counts,
                'domestic': domestic,
                'global': global_
            }

        # 使用汇总数据
        return {
            'dates': [s.date.isoformat() for s in summaries],
            'total': [s.total_news for s in summaries],
            'domestic': [s.domestic_count for s in summaries],
            'global': [s.global_count for s in summaries]
        }

    @staticmethod
    def get_category_distribution():
        """
        获取分类分布

        Returns:
            dict: 分类分布数据
        """
        result = db.session.query(
            News.category,
            func.count(News.id).label('count')
        ).group_by(News.category).order_by(func.count(News.id).desc()).all()

        categories = [r[0] for r in result]
        counts = [r[1] for r in result]

        return {
            'categories': categories,
            'counts': counts
        }

    @staticmethod
    def get_source_performance(days=7):
        """
        获取新闻源性能

        Args:
            days: 天数

        Returns:
            dict: 新闻源性能数据
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)

        # 从source_stats表获取
        stats = SourceStats.query.filter(
            SourceStats.date >= start_date,
            SourceStats.date <= end_date
        ).all()

        if stats:
            # 按源聚合数据
            source_data = {}
            for stat in stats:
                if stat.source_name not in source_data:
                    source_data[stat.source_name] = {
                        'total': 0,
                        'success': 0,
                        'avg_score': []
                    }

                source_data[stat.source_name]['total'] += stat.news_count
                if stat.success:
                    source_data[stat.source_name]['success'] += stat.news_count
                if stat.avg_score > 0:
                    source_data[stat.source_name]['avg_score'].append(stat.avg_score)

            sources = []
            success_rates = []
            counts = []

            for source, data in source_data.items():
                sources.append(source)
                success_rates.append(
                    round(data['success'] / data['total'] * 100, 2) if data['total'] > 0 else 0
                )
                counts.append(data['total'])

            return {
                'sources': sources,
                'success_rates': success_rates,
                'counts': counts
            }

        # 如果没有统计数据，从news表计算
        result = db.session.query(
            News.source,
            func.count(News.id).label('count')
        ).filter(
            News.date >= start_date
        ).group_by(News.source).order_by(func.count(News.id).desc()).limit(15).all()

        return {
            'sources': [r[0] for r in result],
            'success_rates': [100] * len(result),  # 假设都成功
            'counts': [r[1] for r in result]
        }

    @staticmethod
    def get_run_history(limit=20):
        """
        获取运行历史

        Args:
            limit: 数量限制

        Returns:
            list: 运行历史列表
        """
        history = RunHistory.query.order_by(RunHistory.start_time.desc()).limit(limit).all()
        return [h.to_dict() for h in history]
