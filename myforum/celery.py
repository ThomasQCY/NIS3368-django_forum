from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
# 设置 Django 的默认设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myforum.settings')

app = Celery('myforum')

# 从 Django 的设置文件中加载 Celery 配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现各 Django 应用中定义的任务
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'fetch-papers-every-day': {
        'task': 'papers.tasks.fetch_papers',
        'schedule': crontab(hour=0, minute=0),  # 每天午夜运行
    },
    'check-news-every-hour': {
        'task': 'your_app.tasks.check_news_updates',
        'schedule': crontab(minute=0, hour='*'),  # 每小时执行一次
    },
}