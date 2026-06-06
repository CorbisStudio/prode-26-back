import logging

from celery import shared_task

from .services import update_results, FootballDataError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def update_match_results(self):
    """
    Tarea nocturna (Celery Beat):
      1. Actualiza los resultados de los partidos que ya se jugaron.
      2. Puntúa las predicciones de los partidos recién terminados (ranking al día).
    Reintenta hasta 3 veces si falla la API.
    """
    try:
        updated, finished_ids = update_results()

        scored = 0
        if finished_ids:
            # import local para evitar dependencia circular entre apps
            from predictions.services import score_finished_matches
            scored = score_finished_matches(finished_ids)

        logger.info(
            'update_match_results OK: %s partidos actualizados, %s predicciones puntuadas',
            updated, scored,
        )
        return {'updated': updated, 'finished': len(finished_ids), 'scored': scored}
    except FootballDataError as exc:
        logger.error('update_match_results error de API: %s', exc)
        raise self.retry(exc=exc)
