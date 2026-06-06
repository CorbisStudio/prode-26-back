import secrets

from django.conf import settings
from django.db import models

from matches.models import Match


class Prediction(models.Model):
    """Pronóstico de marcador de un usuario para un partido."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='predictions'
    )
    match = models.ForeignKey(
        Match, on_delete=models.CASCADE, related_name='predictions'
    )
    home_score = models.PositiveSmallIntegerField()
    away_score = models.PositiveSmallIntegerField()

    points = models.IntegerField(default=0)
    is_scored = models.BooleanField(default=False)
    is_exact = models.BooleanField(default=False)  # acertó el marcador exacto (desempate)

    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'match')
        ordering = ['match__utc_date', 'id']

    def __str__(self):
        return f'{self.user} → {self.match}: {self.home_score}-{self.away_score}'


def _generate_join_code():
    return secrets.token_urlsafe(6)


class League(models.Model):
    """Liga/grupo privado de amigos con ranking propio."""
    name = models.CharField(max_length=120)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_leagues'
    )
    join_code = models.CharField(max_length=20, unique=True, default=_generate_join_code)

    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class LeagueMembership(models.Model):
    league = models.ForeignKey(
        League, on_delete=models.CASCADE, related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='league_memberships'
    )
    joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('league', 'user')

    def __str__(self):
        return f'{self.user} en {self.league}'
