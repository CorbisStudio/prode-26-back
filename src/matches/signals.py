from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Match


@receiver(post_save, sender=Match)
def score_on_result_loaded(sender, instance, **kwargs):
    """
    Cuando un partido queda FINISHED con marcador cargado, encola el scoring
    de sus predicciones para que el ranking refleje el cambio al instante.
    Se usa transaction.on_commit para que el worker lea el Match ya commiteado.
    """
    if (
        instance.status == Match.Status.FINISHED
        and instance.home_score is not None
        and instance.away_score is not None
    ):
        match_id = instance.id

        def _enqueue():
            from predictions.tasks import score_match_task
            score_match_task.delay(match_id)

        transaction.on_commit(_enqueue)
