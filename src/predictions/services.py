"""
Lógica del juego: cálculo de puntos y rankings.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce

from matches.models import Match
from .models import Prediction

logger = logging.getLogger(__name__)
User = get_user_model()


def compute_points(pred_home, pred_away, real_home, real_away, stage):
    """
    Devuelve los puntos de un pronóstico según las reglas:
      - marcador exacto  → PRODE_POINTS_EXACT  * multiplicador_de_fase
      - acierto 1/X/2    → PRODE_POINTS_RESULT * multiplicador_de_fase
      - error            → 0
    """
    if real_home is None or real_away is None:
        return 0

    multiplier = settings.PRODE_STAGE_MULTIPLIERS.get(stage, 1)

    # Marcador exacto
    if pred_home == real_home and pred_away == real_away:
        return settings.PRODE_POINTS_EXACT * multiplier

    # Mismo resultado (1/X/2)
    def outcome(h, a):
        if h > a:
            return 'H'
        if h < a:
            return 'A'
        return 'D'

    if outcome(pred_home, pred_away) == outcome(real_home, real_away):
        return settings.PRODE_POINTS_RESULT * multiplier

    return 0


def score_match(match):
    """
    Calcula los puntos de todas las predicciones de un partido terminado.
    Idempotente: se puede volver a llamar si se corrige el resultado.
    Devuelve la cantidad de predicciones puntuadas.
    """
    if match.status != Match.Status.FINISHED:
        return 0
    if match.home_score is None or match.away_score is None:
        return 0

    scored = 0
    for pred in match.predictions.all():
        pred.points = compute_points(
            pred.home_score, pred.away_score,
            match.home_score, match.away_score,
            match.stage,
        )
        pred.is_exact = (
            pred.home_score == match.home_score
            and pred.away_score == match.away_score
        )
        pred.is_scored = True
        pred.save(update_fields=['points', 'is_exact', 'is_scored', 'update_date'])
        scored += 1

    logger.info('score_match %s: %s predicciones puntuadas', match.id, scored)
    return scored


def score_finished_matches(match_ids=None):
    """
    Puntúa los partidos terminados. Si se pasan match_ids, sólo esos.
    Devuelve la cantidad total de predicciones puntuadas.
    """
    qs = Match.objects.filter(status=Match.Status.FINISHED)
    if match_ids:
        qs = qs.filter(id__in=match_ids)

    total = 0
    for match in qs:
        total += score_match(match)
    logger.info('score_finished_matches: %s predicciones puntuadas', total)
    return total


# ── Rankings ─────────────────────────────────────────────────────────────────────

def _ranking_queryset(user_qs):
    """Anota puntos totales y aciertos exactos (desempate) sobre un queryset de users."""
    return (
        user_qs
        .annotate(
            total_points=Coalesce(Sum('predictions__points'), 0),
            exact_hits=Count('predictions', filter=Q(predictions__is_exact=True)),
        )
        .order_by('-total_points', '-exact_hits', 'id')
    )


def _serialize_ranking(users):
    rows = []
    for pos, user in enumerate(users, start=1):
        profile = getattr(user, 'profile', None)
        rows.append({
            'position': pos,
            'user_id': user.id,
            'username': user.username,
            'full_name': f'{user.first_name} {user.last_name}'.strip() or user.username,
            'profile_picture_url': profile.profile_picture_url if profile else None,
            'total_points': user.total_points or 0,
            'exact_hits': user.exact_hits or 0,
        })
    return rows


def global_ranking():
    """Ranking de todos los usuarios."""
    users = _ranking_queryset(User.objects.filter(is_staff=False, is_active=True))
    return _serialize_ranking(users)


def league_ranking(league):
    """Ranking restringido a los miembros de una liga."""
    member_ids = league.memberships.values_list('user_id', flat=True)
    users = _ranking_queryset(User.objects.filter(id__in=member_ids, is_staff=False, is_active=True))
    return _serialize_ranking(users)
