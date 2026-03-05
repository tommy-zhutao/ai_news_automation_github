"""
配置管理服务
"""

import json
from pathlib import Path
from src.web.models import CustomSource, db
from src.config.settings import get_config_manager


class ConfigService:
    """配置管理服务类"""

    def __init__(self):
        self.config_manager = get_config_manager()
        self.config = self.config_manager.load()

    def get_all_sources(self):
        """
        获取所有新闻源

        Returns:
            dict: 包含系统源和自定义源
        """
        # 系统预设源
        system_sources = []
        if hasattr(self.config, 'fetcher') and hasattr(self.config.fetcher, 'sources'):
            for source_type, sources in self.config.fetcher.sources.items():
                for source in sources:
                    system_sources.append({
                        'id': f"system_{source}",
                        'name': source,
                        'type': source_type,
                        'enabled': True,
                        'is_custom': False
                    })

        # 自定义源
        custom_sources = CustomSource.query.all()
        custom_list = [s.to_dict() for s in custom_sources]
        for s in custom_list:
            s['is_custom'] = True

        return {
            'system': system_sources,
            'custom': custom_list
        }

    def toggle_source(self, source_id, enabled):
        """
        启用/禁用新闻源

        Args:
            source_id: 源ID
            enabled: 是否启用

        Returns:
            bool: 是否成功
        """
        # 这里需要实现具体的启用/禁用逻辑
        # 暂时只处理自定义源
        if isinstance(source_id, int):
            source = CustomSource.query.get(source_id)
            if source:
                source.enabled = enabled
                db.session.commit()
                return True

        return False

    def add_custom_source(self, source_data):
        """
        添加自定义新闻源

        Args:
            source_data: 源数据字典

        Returns:
            CustomSource: 创建的源对象
        """
        try:
            source = CustomSource(
                name=source_data['name'],
                url=source_data['url'],
                type=source_data['type'],
                category=source_data['category'],
                region=source_data['region'],
                selector=source_data.get('selector'),
                enabled=True
            )

            db.session.add(source)
            db.session.commit()

            return source

        except Exception as e:
            db.session.rollback()
            raise e

    def delete_custom_source(self, source_id):
        """
        删除自定义新闻源

        Args:
            source_id: 源ID

        Returns:
            bool: 是否成功
        """
        try:
            source = CustomSource.query.get(source_id)
            if source:
                db.session.delete(source)
                db.session.commit()
                return True

            return False

        except Exception as e:
            db.session.rollback()
            raise e

    def get_settings(self):
        """
        获取系统设置

        Returns:
            dict: 系统设置
        """
        return {
            'ai_enabled': getattr(self.config.ai, 'enabled', True),
            'ai_model_domestic': getattr(self.config.ai, 'domestic_model', 'qwen2.5:7b-instruct'),
            'ai_model_global': getattr(self.config.ai, 'global_model', 'llama3.1:8b'),
            'concurrent_requests': getattr(self.config.fetcher, 'concurrent_requests', 5),
            'enable_github': getattr(self.config.fetcher, 'enable_github', True),
            'enable_huggingface': getattr(self.config.fetcher, 'enable_huggingface', True),
            'email_enabled': self._is_email_configured(),
            'email_recipient': getattr(self.config.email, 'recipient_email', '')
        }

    def _is_email_configured(self):
        """检查邮箱是否配置"""
        return hasattr(self.config.email, 'recipient_email') and self.config.email.recipient_email

    def update_settings(self, settings):
        """
        更新系统设置

        Args:
            settings: 设置字典

        Returns:
            bool: 是否成功
        """
        try:
            # 更新配置文件
            config_path = self.config_manager.config_path

            # 这里简化处理，实际应该更完善的配置更新逻辑
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 更新AI设置
            if 'ai_enabled' in settings:
                config_data['ai']['enabled'] = settings['ai_enabled']

            # 更新抓取设置
            if 'concurrent_requests' in settings:
                config_data['fetcher']['concurrent_requests'] = settings['concurrent_requests']

            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            raise e

    def trigger_refresh(self):
        """
        触发手动抓取

        Returns:
            bool: 是否成功
        """
        # 这里需要实现触发抓取的逻辑
        # 可以通过子进程启动抓取任务，或者使用任务队列
        return True
