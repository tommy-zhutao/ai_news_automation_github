"""
AI新闻自动化系统 - Web服务器启动脚本
"""

import sys
import argparse

# 确保可以导入src模块
sys.path.insert(0, '.')

try:
    from src.web.app import run_web_server
except ImportError as e:
    print(f"错误: 无法导入Web模块 - {e}")
    print("\n请先安装依赖:")
    print("  pip install Flask Flask-SQLAlchemy")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="AI新闻自动化系统 - Web服务器")
    parser.add_argument("--host", default="127.0.0.1", help="主机地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="端口 (默认: 5000)")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    print("\n🚀 启动Web服务器...")
    run_web_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
