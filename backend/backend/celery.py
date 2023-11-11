from datetime import timedelta
import random

import celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = celery.Celery('PExpress')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-order-status': {
        'task': 'PExpress.tasks.update_order_status',
        'schedule': timedelta(seconds=30),
    },
    'assign-courier-task': {
        'task': 'PExpress.tasks.assign_courier_and_update_status',
        'schedule': timedelta(minutes=1),
        'options': {'countdown': random.randint(30, 50)},
    },
    'update-order-status-on-delivery': {
        'task': 'PExpress.tasks.update_order_status_on_delivery',
        'schedule': timedelta(minutes=1),
        'options': {'countdown': random.randint(30, 50)},
    },
}

# Use UTC timezone for Celery Beat
app.conf.timezone = 'UTC'
