from celery import Celery


# 利用导入的Celery创建对象
celery_app = Celery('mall')
celery_app.config_from_object('celery_tasks.config')
celery_app.autodiscover_tasks(['celery_tasks.sms'])
