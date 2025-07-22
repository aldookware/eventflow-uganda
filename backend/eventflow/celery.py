import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventflow.settings')

app = Celery('eventflow')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'send-daily-notifications': {
        'task': 'notifications.tasks.send_daily_notifications',
        'schedule': 86400.0,  # 24 hours
    },
    'process-pending-settlements': {
        'task': 'payments.tasks.process_pending_settlements',
        'schedule': 3600.0,  # 1 hour
    },
    'cleanup-expired-otp': {
        'task': 'users.tasks.cleanup_expired_otp',
        'schedule': 1800.0,  # 30 minutes
    },
}

app.conf.timezone = 'Africa/Kampala'