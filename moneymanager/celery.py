import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')

app = Celery('moneymanager')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Import periodic tasks from core.tasks
from moneymanager.apps.core.tasks import CELERY_BEAT_SCHEDULE

app.conf.beat_schedule = CELERY_BEAT_SCHEDULE


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')