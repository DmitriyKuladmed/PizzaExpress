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

app.conf.timezone = 'UTC'

app.conf.task_queues = {
    'email_queue': {'exchange': 'email_queue'},
    'processing_status_queue': {'exchange': 'processing_status_queue'},
    'courier_status_queue': {'exchange': 'courier_status_queue'},
    'expectation_status_queue': {'exchange': 'expectation_status_queue'},
}

app.conf.task_routes = {
    'tasks.send_order_confirmation_email': {'queue': 'email_queue'},
    'tasks.update_order_status': {'queue': 'processing_status_queue'},
    'tasks.assign_courier_and_update_status': {'queue': 'courier_status_queue'},
    'tasks.update_order_status_on_delivery': {'queue': 'expectation_status_queue'},
}
