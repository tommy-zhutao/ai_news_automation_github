"""
路由模块初始化
"""

from .main import main_bp
from .news import news_bp
from .stats import stats_bp
from .config import config_bp
from .api import api_bp

__all__ = ['main_bp', 'news_bp', 'stats_bp', 'config_bp', 'api_bp']
