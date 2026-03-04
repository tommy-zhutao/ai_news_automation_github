"""
HTML新闻抓取器
用于抓取常规HTML页面的新闻
"""

from typing import List
import chardet
import re

from .base import BaseFetcher, NewsItem


class HTMLFetcher(BaseFetcher):
    """HTML页面新闻抓取器"""

    def _decode_response(self, response) -> str:
        """
        正确解码响应内容，处理中文编码

        Args:
            response: requests响应对象

        Returns:
            解码后的HTML文本
        """
        content = response.content

        # 优先使用 chardet 检测编码（最准确）
        detected = chardet.detect(content)
        if detected and detected['encoding'] and detected['confidence'] > 0.7:
            try:
                return content.decode(detected['encoding'], errors='ignore')
            except:
                pass

        # 尝试从HTML meta标签中提取编码
        charset_match = re.search(rb'<meta[^>]+charset=["\']?([^"\'>\s]+)', content, re.IGNORECASE)
        if charset_match:
            charset = charset_match.group(1).decode('ascii', errors='ignore')
            try:
                return content.decode(charset, errors='ignore')
            except:
                pass

        # 使用 response.apparent_encoding（requests的智能检测）
        if response.apparent_encoding:
            try:
                return content.decode(response.apparent_encoding, errors='ignore')
            except:
                pass

        # 最后尝试常见编码
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'iso-8859-1']:
            try:
                return content.decode(encoding, errors='ignore')
            except:
                continue

        # 如果都失败，使用 response.text（最后的选择）
        return response.text

    def fetch(self) -> List[NewsItem]:
        """
        抓取HTML页面新闻

        Returns:
            新闻项列表
        """
        self.logger.info(f"开始抓取: {self.name}")

        response = self._make_request(self.url)
        if not response:
            self.logger.warning(f"抓取失败: {self.name}")
            return []

        try:
            # 使用正确的解码方法
            html_text = self._decode_response(response)
            news_list = self._parse_html(html_text, self.url)
            self.logger.info(f"从 {self.name} 获取到 {len(news_list)} 篇新闻")
            return news_list
        except Exception as e:
            self.logger.error(f"解析失败 {self.name}: {e}")
            return []
