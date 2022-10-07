import os
import decouple

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'config.settings.{decouple.config("CONFIGURATION_FILE_TYPE")}_settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


# Celery beat schedule

app.conf.beat_schedule = {
    'periodic-check-credit-status': {
        'task': 'bank_controller.tasks.periodic_check_credit_status',
        'schedule': 60.0,
    },
}