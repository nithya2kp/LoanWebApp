import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loan_management.settings')

app = Celery('loan_management') 

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.task_acks_late = True  
app.conf.task_reject_on_worker_lost = True  