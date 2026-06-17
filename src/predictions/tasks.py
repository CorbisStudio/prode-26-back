import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def score_match_task(match_id):
    """
    Puntúa las predicciones de un partido. Se dispara cuando se carga/corrige
    su resultado (signal post_save en Match). Idempotente.
    """
    from matches.models import Match
    from .services import score_match

    match = Match.objects.filter(pk=match_id).first()
    if not match:
        logger.warning('score_match_task: match %s no existe', match_id)
        return 0
    scored = score_match(match)
    logger.info('score_match_task: match %s → %s predicciones puntuadas', match_id, scored)
    return scored
