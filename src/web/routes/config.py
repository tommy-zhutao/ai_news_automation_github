"""
配置管理路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from src.web.models import CustomSource, db
from src.web.services.config_service import ConfigService

config_bp = Blueprint('config', __name__)


@config_bp.route('/sources')
def sources():
    """新闻源管理"""
    try:
        config_service = ConfigService()
        sources = config_service.get_all_sources()
        return render_template('config/sources.html', sources=sources)
    except Exception as e:
        return render_template('config/sources.html', sources=[], error=str(e))


@config_bp.route('/sources/toggle', methods=['POST'])
def toggle_source():
    """启用/禁用新闻源"""
    try:
        source_id = request.json.get('id')
        enabled = request.json.get('enabled', True)

        config_service = ConfigService()
        success = config_service.toggle_source(source_id, enabled)

        if success:
            return jsonify({'success': True, 'message': '设置成功'})
        else:
            return jsonify({'success': False, 'message': '源不存在'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@config_bp.route('/sources/add', methods=['GET', 'POST'])
def add_source():
    """添加自定义新闻源"""
    if request.method == 'POST':
        try:
            source_data = {
                'name': request.form.get('name'),
                'url': request.form.get('url'),
                'type': request.form.get('type'),
                'category': request.form.get('category'),
                'region': request.form.get('region'),
                'selector': request.form.get('selector')
            }

            config_service = ConfigService()
            source = config_service.add_custom_source(source_data)

            if source:
                flash('自定义新闻源添加成功', 'success')
                return redirect(url_for('config.sources'))
            else:
                flash('添加失败', 'error')
                return render_template('config/add_source.html', data=source_data)

        except Exception as e:
            flash(f'添加失败: {str(e)}', 'error')
            return render_template('config/add_source.html', data=request.form)

    return render_template('config/add_source.html')


@config_bp.route('/sources/<int:source_id>/delete', methods=['POST'])
def delete_source(source_id):
    """删除自定义新闻源"""
    try:
        config_service = ConfigService()
        success = config_service.delete_custom_source(source_id)

        if success:
            flash('删除成功', 'success')
        else:
            flash('删除失败', 'error')

        return redirect(url_for('config.sources'))

    except Exception as e:
        flash(f'删除失败: {str(e)}', 'error')
        return redirect(url_for('config.sources'))


@config_bp.route('/settings')
def settings():
    """系统设置"""
    try:
        config_service = ConfigService()
        settings = config_service.get_settings()
        return render_template('config/settings.html', settings=settings)
    except Exception as e:
        return render_template('config/settings.html', settings={}, error=str(e))


@config_bp.route('/settings/update', methods=['POST'])
def update_settings():
    """更新系统设置"""
    try:
        settings = request.json
        config_service = ConfigService()
        success = config_service.update_settings(settings)

        if success:
            return jsonify({'success': True, 'message': '设置保存成功'})
        else:
            return jsonify({'success': False, 'message': '保存失败'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@config_bp.route('/trigger', methods=['POST'])
def trigger_refresh():
    """触发手动抓取"""
    try:
        config_service = ConfigService()
        success = config_service.trigger_refresh()

        if success:
            return jsonify({'success': True, 'message': '抓取任务已启动'})
        else:
            return jsonify({'success': False, 'message': '启动失败'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
