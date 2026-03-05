"""
数据导入服务 - 将历史JSON文件导入SQLite数据库
"""

import json
from pathlib import Path
from datetime import datetime, date
from src.web.models import News, DailySummary, db
from src.utils.logger import get_logger


class DataImporter:
    """数据导入服务类"""

    def __init__(self, output_dir='output'):
        """
        初始化数据导入器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.logger = get_logger('data_importer')

    def import_json_files(self, start_date=None, end_date=None):
        """
        导入指定范围的JSON文件

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            dict: 导入统计
        """
        stats = {
            'total_files': 0,
            'success_files': 0,
            'failed_files': 0,
            'total_news': 0,
            'imported_news': 0,
            'skipped_news': 0
        }

        try:
            # 获取JSON文件列表
            json_files = list(self.output_dir.glob('ai_news_*.json'))

            if start_date or end_date:
                # 过滤日期范围
                filtered_files = []
                for file in json_files:
                    # 从文件名提取日期
                    file_date_str = file.stem.replace('ai_news_', '')
                    try:
                        file_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()

                        if start_date and file_date < datetime.strptime(start_date, '%Y-%m-%d').date():
                            continue
                        if end_date and file_date > datetime.strptime(end_date, '%Y-%m-%d').date():
                            continue

                        filtered_files.append(file)
                    except ValueError:
                        continue

                json_files = filtered_files

            stats['total_files'] = len(json_files)
            self.logger.info(f"找到 {len(json_files)} 个JSON文件")

            # 导入每个文件
            for json_file in json_files:
                result = self._import_single_file(json_file)
                if result['success']:
                    stats['success_files'] += 1
                else:
                    stats['failed_files'] += 1
                stats['total_news'] += result['total_news']
                stats['imported_news'] += result['imported_news']
                stats['skipped_news'] += result['skipped_news']

            self.logger.info(f"导入完成: {stats}")

        except Exception as e:
            self.logger.error(f"导入失败: {e}", exc_info=True)

        return stats

    def _import_single_file(self, json_file):
        """
        导入单个JSON文件

        Args:
            json_file: JSON文件路径

        Returns:
            dict: 导入结果
        """
        result = {
            'success': False,
            'total_news': 0,
            'imported_news': 0,
            'skipped_news': 0
        }

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 提取日期
            file_date_str = json_file.stem.replace('ai_news_', '')
            # 支持两种日期格式: 20260304 或 2026-03-04
            try:
                if '-' in file_date_str:
                    news_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()
                else:
                    news_date = datetime.strptime(file_date_str, '%Y%m%d').date()
            except ValueError:
                self.logger.warning(f"无法解析日期: {file_date_str}")
                return result

            # 导入新闻列表 - 支持两种格式
            if isinstance(data, list):
                # 直接是数组
                news_list = data
            elif isinstance(data, dict):
                # 包含 news_list 键的对象
                news_list = data.get('news_list', [])
            else:
                news_list = []

            result['total_news'] = len(news_list)

            for item in news_list:
                # 检查是否已存在
                exists = News.query.filter_by(link=item['link']).first()

                if exists:
                    result['skipped_news'] += 1
                    continue

                # 创建新闻记录
                news_item = News(
                    title=item.get('title', ''),
                    link=item['link'],
                    source=item.get('source', ''),
                    region=item.get('region', 'global'),
                    category=item.get('category', 'AI'),
                    date=news_date,
                    type=item.get('type', 'news'),
                    score=item.get('score', 0)
                )

                db.session.add(news_item)
                result['imported_news'] += 1

            # 尝试从HTML文件中提取AI摘要
            ai_summary, ai_trends = self._extract_ai_summary_from_html(file_date_str)

            # 导入每日汇总
            daily_summary = {}
            if isinstance(data, dict):
                daily_summary = data.get('daily_summary', {})

            summary_exists = DailySummary.query.filter_by(date=news_date).first()

            if not summary_exists and daily_summary:
                summary = DailySummary(
                    date=news_date,
                    total_news=daily_summary.get('total', len(news_list)),
                    domestic_count=daily_summary.get('domestic', 0),
                    global_count=daily_summary.get('global', 0),
                    ai_summary=daily_summary.get('ai_summary', '') or ai_summary,
                    ai_trends=daily_summary.get('ai_trends', '') or ai_trends,
                    github_count=daily_summary.get('github_count', 0),
                    huggingface_count=daily_summary.get('huggingface_count', 0)
                )
                db.session.add(summary)
            elif not summary_exists and isinstance(data, list):
                # 如果是数组格式，创建一个基本的汇总（包含从HTML提取的AI摘要）
                summary = DailySummary(
                    date=news_date,
                    total_news=len(news_list),
                    domestic_count=len([n for n in news_list if n.get('region') == 'domestic']),
                    global_count=len([n for n in news_list if n.get('region') == 'global']),
                    ai_summary=ai_summary,
                    ai_trends=ai_trends,
                    github_count=len([n for n in news_list if n.get('type') == 'github']),
                    huggingface_count=len([n for n in news_list if n.get('type') == 'huggingface'])
                )
                db.session.add(summary)
            elif summary_exists and (ai_summary or ai_trends):
                # 如果汇总已存在但没有AI摘要，更新它
                if not summary_exists.ai_summary or not summary_exists.ai_trends:
                    summary_exists.ai_summary = summary_exists.ai_summary or ai_summary
                    summary_exists.ai_trends = summary_exists.ai_trends or ai_trends
                    self.logger.info(f"更新现有汇总的AI摘要: {news_date}")

            db.session.commit()
            result['success'] = True

            self.logger.info(f"成功导入 {json_file.name}: {result['imported_news']}/{result['total_news']}")

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"导入文件失败 {json_file.name}: {e}")

        return result

    def _extract_ai_summary_from_html(self, date_str):
        """
        从HTML文件中提取AI摘要和趋势

        Args:
            date_str: 日期字符串 (YYYYMMDD 或 YYYY-MM-DD)

        Returns:
            tuple: (ai_summary, ai_trends)
        """
        try:
            # 标准化日期格式为YYYYMMDD（无连字符）
            if '-' in date_str:
                # 将 YYYY-MM-DD 转换为 YYYYMMDD
                date_str = date_str.replace('-', '')

            html_filename = f'ai_news_{date_str}.html'
            html_file = self.output_dir / html_filename

            if not html_file.exists():
                self.logger.debug(f"HTML文件不存在: {html_file}")
                return '', ''

            from bs4 import BeautifulSoup

            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            # 查找今日摘要
            ai_summary = ''
            ai_trends = ''

            # 查找所有h3标签
            for h3 in soup.find_all('h3'):
                text = h3.get_text(strip=True)

                # 匹配"今日摘要"
                if text == '今日摘要':
                    # 获取下一个元素的内容
                    next_elem = h3.find_next(['div', 'p', 'td', 'span'])
                    if next_elem:
                        ai_summary = next_elem.get_text(strip=True)
                        self.logger.info(f"找到AI摘要，长度: {len(ai_summary)}")

                # 匹配"趋势分析"
                elif text == '趋势分析':
                    # 获取下一个元素的内容
                    next_elem = h3.find_next(['div', 'p', 'td', 'span'])
                    if next_elem:
                        ai_trends = next_elem.get_text(strip=True)
                        self.logger.info(f"找到AI趋势，长度: {len(ai_trends)}")

            return ai_summary, ai_trends

        except Exception as e:
            self.logger.warning(f"从HTML提取AI摘要失败: {e}")
            return '', ''

    def sync_from_output(self):
        """
        同步output目录下的所有文件

        Returns:
            dict: 同步统计
        """
        return self.import_json_files()

    def import_daily_summary(self, date_str):
        """
        导入某日的汇总信息

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            bool: 是否成功
        """
        try:
            json_file = self.output_dir / f'ai_news_{date_str}.json'

            if not json_file.exists():
                self.logger.warning(f"文件不存在: {json_file}")
                return False

            result = self._import_single_file(json_file)
            return result['success']

        except Exception as e:
            self.logger.error(f"导入汇总失败: {e}")
            return False
