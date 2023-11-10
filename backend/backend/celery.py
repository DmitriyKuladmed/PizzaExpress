import celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = celery.Celery('PExpress')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
