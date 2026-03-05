"""
数据库模型定义
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class News(db.Model):
    """新闻表"""
    __tablename__ = 'news'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(500), nullable=False)
    link = db.Column(db.String(1000), unique=True, nullable=False, index=True)
    source = db.Column(db.String(100), nullable=False, index=True)
    region = db.Column(db.String(20), nullable=False, index=True)  # domestic/global
    category = db.Column(db.String(50), nullable=False, default='AI', index=True)
    summary = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False)  # news/rss/github/huggingface
    score = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'link': self.link,
            'source': self.source,
            'region': self.region,
            'category': self.category,
            'summary': self.summary,
            'date': self.date.isoformat() if self.date else None,
            'type': self.type,
            'score': self.score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<News {self.id}: {self.title[:30]}...>'


class DailySummary(db.Model):
    """每日汇总表"""
    __tablename__ = 'daily_summary'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, unique=True, nullable=False, index=True)
    total_news = db.Column(db.Integer, default=0)
    domestic_count = db.Column(db.Integer, default=0)
    global_count = db.Column(db.Integer, default=0)
    ai_summary = db.Column(db.Text)
    ai_trends = db.Column(db.Text)
    github_count = db.Column(db.Integer, default=0)
    huggingface_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'total_news': self.total_news,
            'domestic_count': self.domestic_count,
            'global_count': self.global_count,
            'ai_summary': self.ai_summary,
            'ai_trends': self.ai_trends,
            'github_count': self.github_count,
            'huggingface_count': self.huggingface_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<DailySummary {self.date}: {self.total_news} news>'


class CustomSource(db.Model):
    """自定义新闻源表"""
    __tablename__ = 'custom_sources'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # html/rss
    category = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(20), nullable=False)  # domestic/global
    selector = db.Column(db.String(500))  # HTML选择器（可选）
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'type': self.type,
            'category': self.category,
            'region': self.region,
            'selector': self.selector,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<CustomSource {self.name}: {self.url}>'


class RunHistory(db.Model):
    """运行历史表"""
    __tablename__ = 'run_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)  # success/failed/error
    total_fetched = db.Column(db.Integer, default=0)
    unique_news = db.Column(db.Integer, default=0)
    final_selected = db.Column(db.Integer, default=0)
    sources_success = db.Column(db.Integer, default=0)
    sources_total = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    duration_seconds = db.Column(db.Integer)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'total_fetched': self.total_fetched,
            'unique_news': self.unique_news,
            'final_selected': self.final_selected,
            'sources_success': self.sources_success,
            'sources_total': self.sources_total,
            'error_message': self.error_message,
            'duration_seconds': self.duration_seconds
        }

    def __repr__(self):
        return f'<RunHistory {self.id}: {self.status}>'


class SourceStats(db.Model):
    """新闻源统计表"""
    __tablename__ = 'source_stats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    news_count = db.Column(db.Integer, default=0)
    success = db.Column(db.Boolean, default=True)
    avg_score = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('source_name', 'date', name='unique_source_date'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'source_name': self.source_name,
            'date': self.date.isoformat() if self.date else None,
            'news_count': self.news_count,
            'success': self.success,
            'avg_score': self.avg_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<SourceStats {self.source_name} {self.date}: {self.news_count}>'
