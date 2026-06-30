from django.db import models


class Team(models.Model):
    """Selección participante del Mundial."""
    external_id = models.IntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=10, blank=True, null=True)  # TLA / FIFA code (ARG, BRA...)
    group = models.CharField(max_length=20, blank=True, null=True)  # "Group A"
    flag_url = models.URLField(max_length=300, blank=True, null=True)

    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['group', 'name']

    def __str__(self):
        return self.name


class Match(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        TIMED = 'TIMED', 'Timed'
        IN_PLAY = 'IN_PLAY', 'In play'
        PAUSED = 'PAUSED', 'Paused'
        FINISHED = 'FINISHED', 'Finished'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        POSTPONED = 'POSTPONED', 'Postponed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class Winner(models.TextChoices):
        HOME = 'HOME_TEAM', 'Home team'
        AWAY = 'AWAY_TEAM', 'Away team'
        DRAW = 'DRAW', 'Draw'

    class Duration(models.TextChoices):
        REGULAR = 'REGULAR', 'Regular'
        EXTRA_TIME = 'EXTRA_TIME', 'Extra time'
        PENALTY_SHOOTOUT = 'PENALTY_SHOOTOUT', 'Penalty shootout'

    external_id = models.IntegerField(unique=True, null=True, blank=True)

    stage = models.CharField(max_length=40, blank=True, null=True)   # GROUP_STAGE, LAST_16, FINAL...
    group = models.CharField(max_length=20, blank=True, null=True)   # "Group A" o null en eliminatorias
    matchday = models.IntegerField(blank=True, null=True)

    home_team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='home_matches'
    )
    away_team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='away_matches'
    )

    utc_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    winner = models.CharField(max_length=20, choices=Winner.choices, blank=True, null=True)

    # Cómo se definió el partido. En eliminatorias puede ir a alargue o penales.
    duration = models.CharField(
        max_length=20, choices=Duration.choices, default=Duration.REGULAR
    )
    # Resultado de la tanda de penales (sólo si duration == PENALTY_SHOOTOUT).
    penalties_home = models.IntegerField(null=True, blank=True)
    penalties_away = models.IntegerField(null=True, blank=True)

    # Desgloses del marcador tal como los entrega el proveedor (score.*).
    half_time_home = models.IntegerField(null=True, blank=True)
    half_time_away = models.IntegerField(null=True, blank=True)
    regular_time_home = models.IntegerField(null=True, blank=True)
    regular_time_away = models.IntegerField(null=True, blank=True)
    extra_time_home = models.IntegerField(null=True, blank=True)
    extra_time_away = models.IntegerField(null=True, blank=True)

    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['utc_date', 'id']
        verbose_name_plural = 'matches'

    def __str__(self):
        h = self.home_team.name if self.home_team else 'TBD'
        a = self.away_team.name if self.away_team else 'TBD'
        if self.status == self.Status.FINISHED:
            return f'{h} {self.home_score}-{self.away_score} {a}'
        return f'{h} vs {a}'

    @property
    def is_finished(self):
        return self.status == self.Status.FINISHED
