"""
智能去重模块
用于检测和移除重复或近似重复的新闻
"""

import re
from typing import List, Set, Dict, Tuple
from collections import defaultdict
from difflib import SequenceMatcher
from urllib.parse import urlparse

from .logger import get_logger


class NewsDeduplicator:
    """新闻去重器"""

    def __init__(self, title_similarity_threshold: float = 0.85, url_similarity_threshold: float = 0.90):
        """
        初始化去重器

        Args:
            title_similarity_threshold: 标题相似度阈值 (0-1)
            url_similarity_threshold: URL相似度阈值 (0-1)
        """
        self.title_threshold = title_similarity_threshold
        self.url_threshold = url_similarity_threshold
        self.logger = get_logger("dedup")

        # 用于追踪已见过的内容
        self.seen_urls: Set[str] = set()
        self.seen_titles: List[str] = []
        self.seen_domains: Dict[str, Set[str]] = defaultdict(set)

        # 统计信息
        self.stats = {
            'total_processed': 0,
            'url_duplicates': 0,
            'title_duplicates': 0,
            'similar_duplicates': 0,
            'kept': 0
        }

    def normalize_text(self, text: str) -> str:
        """
        标准化文本用于比较

        Args:
            text: 原始文本

        Returns:
            标准化后的文本
        """
        # 转小写
        text = text.lower()

        # 移除特殊字符和多余空格
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        # 移除常见的无意义词
        stopwords = {
            'the', 'a', 'an', 'in', 'on', 'at', 'for', 'of', 'and', 'or', 'but',
            '的', '了', '是', '在', '和', '与', '或', '但是', '然而', '因此'
        }
        words = [w for w in text.split() if w not in stopwords and len(w) > 1]

        return ' '.join(words)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度 (使用SequenceMatcher)

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度 (0-1)
        """
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)

        if not norm1 or not norm2:
            return 0.0

        return SequenceMatcher(None, norm1, norm2).ratio()

    def extract_url_fingerprint(self, url: str) -> str:
        """
        提取URL指纹用于识别相同新闻

        Args:
            url: 新闻URL

        Returns:
            URL指纹
        """
        try:
            parsed = urlparse(url)

            # 移除常见参数
            path = re.sub(r'[?&](utm_[^&]*|ref=[^&]*|source=[^&]*|share=[^&]*)', '', parsed.path)

            # 移除文章ID前后的变化部分
            path = re.sub(r'/\d{6,}', '/ID', path)  # 日期ID
            path = re.sub(r'/\d{4}/\d{2}/\d{2}', '/DATE', path)  # 日期路径
            path = re.sub(r'-\d+$', '', path)  # 尾部数字

            # 组合域名和路径
            domain = parsed.netloc.replace('www.', '')
            return f"{domain}{path}"

        except Exception:
            return url

    def is_duplicate_url(self, url: str) -> bool:
        """
        检查URL是否重复

        Args:
            url: 要检查的URL

        Returns:
            是否重复
        """
        fingerprint = self.extract_url_fingerprint(url)

        if fingerprint in self.seen_urls:
            return True

        # 检查相似的URL
        for seen_fp in self.seen_urls:
            if self.calculate_similarity(fingerprint, seen_fp) > self.url_threshold:
                return True

        return False

    def is_duplicate_title(self, title: str) -> bool:
        """
        检查标题是否重复

        Args:
            title: 要检查的标题

        Returns:
            是否重复
        """
        normalized = self.normalize_text(title)

        if not normalized:
            return False

        # 与已见标题比较
        for seen_title in self.seen_titles:
            similarity = self.calculate_similarity(normalized, seen_title)
            if similarity >= self.title_threshold:
                return True

        return False

    def deduplicate_news_list(self, news_list: List) -> List:
        """
        对新闻列表进行去重

        Args:
            news_list: NewsItem对象列表

        Returns:
            去重后的新闻列表
        """
        self.logger.info(f"开始去重，原始新闻数量: {len(news_list)}")

        # 重置统计
        self.stats = {
            'total_processed': len(news_list),
            'url_duplicates': 0,
            'title_duplicates': 0,
            'similar_duplicates': 0,
            'kept': 0
        }

        deduped = []
        seen_by_source: Dict[str, List[str]] = defaultdict(list)

        for news in news_list:
            # 检查URL重复
            if self.is_duplicate_url(news.url):
                self.stats['url_duplicates'] += 1
                self.logger.debug(f"URL重复: {news.title[:50]}...")
                continue

            # 检查标题重复
            if self.is_duplicate_title(news.title):
                self.stats['title_duplicates'] += 1
                self.logger.debug(f"标题重复: {news.title[:50]}...")
                continue

            # 检查同源相似新闻（保留评分更高的）
            same_source_titles = seen_by_source.get(news.source, [])
            is_similar = False

            for existing_title in same_source_titles:
                similarity = self.calculate_similarity(news.title, existing_title)
                if 0.6 <= similarity < self.title_threshold:  # 相似但不完全相同
                    self.stats['similar_duplicates'] += 1
                    self.logger.debug(f"同源相似: {news.title[:50]}... (相似度: {similarity:.2f})")
                    is_similar = True
                    break

            if is_similar:
                continue

            # 保留这条新闻
            deduped.append(news)
            self.stats['kept'] += 1

            # 记录已见内容
            self.seen_urls.add(self.extract_url_fingerprint(news.url))
            self.seen_titles.append(self.normalize_text(news.title))
            seen_by_source[news.source].append(news.title)

        self.logger.info(
            f"去重完成: 保留 {self.stats['kept']}/{self.stats['total_processed']} "
            f"(URL重复: {self.stats['url_duplicates']}, "
            f"标题重复: {self.stats['title_duplicates']}, "
            f"相似重复: {self.stats['similar_duplicates']})"
        )

        return deduped

    def get_stats(self) -> Dict[str, int]:
        """获取去重统计信息"""
        return self.stats.copy()

    def reset(self):
        """重置去重器状态"""
        self.seen_urls.clear()
        self.seen_titles.clear()
        self.seen_domains.clear()
        self.stats = {
            'total_processed': 0,
            'url_duplicates': 0,
            'title_duplicates': 0,
            'similar_duplicates': 0,
            'kept': 0
        }


class ContentQualityScorer:
    """内容质量评分器"""

    def __init__(self):
        self.logger = get_logger("quality_scorer")

        # 质量指标权重
        self.weights = {
            'title_length': 0.15,
            'title_quality': 0.25,
            'source_quality': 0.20,
            'url_quality': 0.15,
            'ai_relevance': 0.15,
            'uniqueness': 0.10
        }

        # 高质量源列表
        self.high_quality_sources = {
            'techcrunch.com', 'venturebeat.com', 'arstechnica.com',
            'wired.com', 'technologyreview.com', 'nature.com',
            'science.org', 'acm.org', 'ieee.org', 'aaai.org',
            'stanford.edu', 'mit.edu', 'deepmind.com', 'openai.com',
            'leiphone.com', '36kr.com', 'huxiu.com', 'jiqizhixin.com'
        }

    def score_title_length(self, title: str) -> float:
        """评分标题长度 (理想长度: 30-80字符)"""
        length = len(title)
        if 30 <= length <= 80:
            return 1.0
        elif 20 <= length < 30 or 80 < length <= 100:
            return 0.7
        elif length < 20:
            return 0.4
        else:
            return 0.3

    def score_title_quality(self, title: str) -> float:
        """评分标题质量"""
        score = 0.5  # 基础分

        # 包含数字和具体信息
        if any(c.isdigit() for c in title):
            score += 0.1

        # 包含大写缩写 (AI, GPT, etc.)
        if re.search(r'\b[A-Z]{2,}\b', title):
            score += 0.1

        # 避免点击诱饵模式
        clickbait_patterns = [
            r'你不会相信', r'震惊', r'必看', r'刚刚',
            r'you won\'t believe', r'shocking', r'must see'
        ]
        title_lower = title.lower()
        for pattern in clickbait_patterns:
            if re.search(pattern, title_lower):
                score -= 0.3
                break

        # 包含具体技术名词
        tech_terms = [
            'gpt', 'llm', 'transformer', 'diffusion', 'reinforcement',
            'neural', 'machine learning', 'deep learning', 'nlp',
            '计算机视觉', '自然语言', '深度学习', '强化学习', '大模型'
        ]
        for term in tech_terms:
            if term in title_lower:
                score += 0.1
                break

        return max(0.0, min(1.0, score))

    def score_source_quality(self, url: str) -> float:
        """评分源质量"""
        url_lower = url.lower()

        # 高质量源
        for source in self.high_quality_sources:
            if source in url_lower:
                return 1.0

        # 判断是否为知名机构
        if any(domain in url_lower for domain in ['.edu', '.org', 'acm.', 'ieee.']):
            return 0.9

        # 判断是否为新闻媒体
        if any(domain in url_lower for domain in ['.com', '.net', '.io']):
            return 0.7

        return 0.5

    def score_url_quality(self, url: str) -> float:
        """评分URL质量"""
        score = 0.5

        # HTTPS
        if url.startswith('https://'):
            score += 0.2

        # 干净的URL (没有太多参数)
        param_count = url.count('&') + url.count('?')
        if param_count <= 1:
            score += 0.2
        elif param_count > 3:
            score -= 0.2

        # 有文章ID或slug
        if re.search(r'/\d{4,}/|/[a-z0-9-]{10,}', url):
            score += 0.1

        return max(0.0, min(1.0, score))

    def score_ai_relevance(self, title: str) -> float:
        """评分AI相关性"""
        ai_terms = [
            'ai', 'artificial intelligence', 'machine learning', 'ml',
            'deep learning', 'neural', 'llm', 'gpt', 'chatgpt',
            'nlp', 'computer vision', 'robotics', 'automation',
            '人工智能', '机器学习', '深度学习', '大模型', 'gpt'
        ]

        title_lower = title.lower()
        count = sum(1 for term in ai_terms if term in title_lower)

        if count >= 2:
            return 1.0
        elif count == 1:
            return 0.8
        else:
            return 0.3

    def score_uniqueness(self, news, all_news: List) -> float:
        """评分新闻独特性 (与其他新闻的差异度)"""
        if not all_news:
            return 1.0

        # 计算与所有其他新闻的平均相似度
        dedup = NewsDeduplicator()
        similarities = []

        for other in all_news:
            if other.url != news.url:
                sim = dedup.calculate_similarity(news.title, other.title)
                similarities.append(sim)

        if not similarities:
            return 1.0

        avg_similarity = sum(similarities) / len(similarities)

        # 相似度越低，独特性越高
        return max(0.0, 1.0 - avg_similarity)

    def calculate_score(self, news, all_news: List = None) -> float:
        """
        计算综合质量评分

        Args:
            news: NewsItem对象
            all_news: 所有新闻列表 (用于计算独特性)

        Returns:
            质量评分 (0-1)
        """
        if all_news is None:
            all_news = []

        scores = {
            'title_length': self.score_title_length(news.title),
            'title_quality': self.score_title_quality(news.title),
            'source_quality': self.score_source_quality(news.url),
            'url_quality': self.score_url_quality(news.url),
            'ai_relevance': self.score_ai_relevance(news.title),
        }

        # 如果提供了所有新闻列表，计算独特性
        if all_news:
            scores['uniqueness'] = self.score_uniqueness(news, all_news)
        else:
            scores['uniqueness'] = 0.5

        # 计算加权总分
        total_score = sum(
            scores[key] * self.weights[key]
            for key in self.weights
        )

        return round(total_score, 3)

    def rank_news(self, news_list: List) -> List:
        """
        对新闻列表按质量评分排序

        Args:
            news_list: NewsItem对象列表

        Returns:
            排序后的新闻列表
        """
        self.logger.info(f"开始质量评分，新闻数量: {len(news_list)}")

        # 计算每条新闻的评分
        scored_news = []
        for news in news_list:
            score = self.calculate_score(news, news_list)
            news.score = score  # 更新新闻对象的评分
            scored_news.append((news, score))

        # 按评分降序排序
        scored_news.sort(key=lambda x: x[1], reverse=True)

        # 返回排序后的新闻列表
        ranked = [news for news, score in scored_news]

        self.logger.info(
            f"质量评分完成: 平均分 {sum(s for _, s in scored_news) / len(scored_news):.3f}, "
            f"最高分 {scored_news[0][1]:.3f}, "
            f"最低分 {scored_news[-1][1]:.3f}"
        )

        return ranked
