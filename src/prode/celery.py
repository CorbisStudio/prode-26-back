import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prode.settings')

app = Celery('prode')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ── Schedule ───────────────────────────────────────────────────────────────────
# Actualiza los resultados de los partidos todas las noches a las 03:00
# (hora del TIME_ZONE configurado en settings).
app.conf.beat_schedule = {
    'update-match-results-nightly': {
        'task': 'matches.tasks.update_match_results',
        'schedule': crontab(hour=2, minute=0),  # 02:00 (antes del apagado de mark1 a las 03:00)
    },
}
