"""
Flask应用主文件
"""

import os
from pathlib import Path
from flask import Flask, render_template, send_from_directory
from src.utils.logger import get_logger

from .models import db


def create_app(config_name='default'):
    """
    创建Flask应用工厂

    Args:
        config_name: 配置名称

    Returns:
        Flask应用实例
    """
    app = Flask(__name__,
                template_folder='templates',
                static_folder='../../static')

    # 配置
    configure_app(app)

    # 初始化数据库
    db.init_app(app)

    # 创建数据库表
    with app.app_context():
        init_database(app)

    # 注册蓝图
    register_blueprints(app)

    # 错误处理
    register_error_handlers(app)

    # 日志
    app.logger = get_logger('web')

    return app


def configure_app(app):
    """配置应用"""
    # 基础配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

    # 数据库配置
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / 'news.db'

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False

    # 分页配置
    app.config['ITEMS_PER_PAGE'] = 20

    # JSON配置
    app.config['JSON_AS_ASCII'] = False
    app.config['JSON_SORT_KEYS'] = False


def init_database(app):
    """初始化数据库"""
    try:
        db.create_all()
        app.logger.info(f"数据库初始化成功: {app.config['SQLALCHEMY_DATABASE_URI']}")
    except Exception as e:
        app.logger.error(f"数据库初始化失败: {e}")
        raise


def register_blueprints(app):
    """注册蓝图"""
    from .routes.main import main_bp
    from .routes.news import news_bp
    from .routes.stats import stats_bp
    from .routes.config import config_bp
    from .routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(news_bp, url_prefix='/news')
    app.register_blueprint(stats_bp, url_prefix='/stats')
    app.register_blueprint(config_bp, url_prefix='/config')
    app.register_blueprint(api_bp, url_prefix='/api')


def register_error_handlers(app):
    """注册错误处理器"""

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403


# 创建应用实例
def run_web_server(host='127.0.0.1', port=5000, debug=False):
    """
    运行Web服务器

    Args:
        host: 主机地址
        port: 端口
        debug: 调试模式
    """
    app = create_app()

    print(f"""
    ╔═══════════════════════════════════════════════════════╗
    ║       AI新闻自动化系统 - Web管理界面                   ║
    ╠═══════════════════════════════════════════════════════╣
    ║  访问地址: http://{host}:{port}                      ║
    ║  工作目录: {os.getcwd()}                      ║
    ║  数据库: {app.config['SQLALCHEMY_DATABASE_URI']}   ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    app.run(host=host, port=port, debug=debug)
