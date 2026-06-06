"""
Cliente e importador de datos del Mundial.

El cliente está aislado en `FootballDataClient` para poder cambiar de proveedor
(API-Football, openfootball, etc.) sin tocar las tasks ni los comandos.
"""
import logging
from datetime import datetime

import requests
from django.conf import settings
from django.utils.dateparse import parse_datetime

from .models import Team, Match

logger = logging.getLogger(__name__)


class FootballDataError(Exception):
    pass


class FootballDataClient:
    """Cliente para football-data.org (v4)."""

    def __init__(self, token=None, base_url=None, competition=None, timeout=20):
        self.token = token or settings.FOOTBALL_DATA_TOKEN
        self.base_url = (base_url or settings.FOOTBALL_DATA_BASE_URL).rstrip('/') + '/'
        self.competition = competition or settings.WORLD_CUP_COMPETITION_CODE
        self.timeout = timeout

    def _get(self, path):
        if not self.token:
            raise FootballDataError(
                'FOOTBALL_DATA_TOKEN no configurado. Registrate en '
                'https://www.football-data.org/client/register y seteá la variable.'
            )
        url = f'{self.base_url}{path}'
        headers = {'X-Auth-Token': self.token}
        resp = requests.get(url, headers=headers, timeout=self.timeout)
        if resp.status_code != 200:
            raise FootballDataError(f'GET {url} -> HTTP {resp.status_code}: {resp.text[:300]}')
        return resp.json()

    def get_teams(self):
        data = self._get(f'competitions/{self.competition}/teams')
        return data.get('teams', [])

    def get_matches(self):
        data = self._get(f'competitions/{self.competition}/matches')
        return data.get('matches', [])


# ── Importadores ────────────────────────────────────────────────────────────────

def _group_label(raw):
    """'GROUP_A' -> 'Group A'."""
    if not raw:
        return None
    return raw.replace('_', ' ').title()


def import_teams(client=None):
    """Trae y guarda todas las selecciones. Devuelve (creados, actualizados)."""
    client = client or FootballDataClient()
    created = updated = 0
    for t in client.get_teams():
        obj, was_created = Team.objects.update_or_create(
            external_id=t.get('id'),
            defaults={
                'name': t.get('name') or '',
                'code': t.get('tla'),
                'flag_url': t.get('crest'),
            },
        )
        created += int(was_created)
        updated += int(not was_created)
    logger.info('Teams import: %s creados, %s actualizados', created, updated)
    return created, updated


def _team_by_external_id(node):
    """Resuelve (o crea mínimamente) el Team a partir del nodo home/away de un match."""
    if not node or not node.get('id'):
        return None
    team, _ = Team.objects.get_or_create(
        external_id=node['id'],
        defaults={'name': node.get('name') or '', 'code': node.get('tla')},
    )
    return team


def _apply_match_fields(match, m):
    """Vuelca los campos del JSON del proveedor en la instancia Match (sin guardar)."""
    score = m.get('score') or {}
    full_time = score.get('fullTime') or {}

    match.stage = m.get('stage')
    match.group = _group_label(m.get('group'))
    match.matchday = m.get('matchday')
    match.utc_date = parse_datetime(m['utcDate']) if m.get('utcDate') else None
    match.status = m.get('status') or Match.Status.SCHEDULED
    match.home_score = full_time.get('home')
    match.away_score = full_time.get('away')
    match.winner = score.get('winner')


def import_matches(client=None):
    """
    Carga inicial: trae TODOS los partidos y los crea/actualiza.
    Devuelve (creados, actualizados).
    """
    client = client or FootballDataClient()
    created = updated = 0
    for m in client.get_matches():
        match, was_created = Match.objects.get_or_create(external_id=m.get('id'))
        match.home_team = _team_by_external_id(m.get('homeTeam'))
        match.away_team = _team_by_external_id(m.get('awayTeam'))
        _apply_match_fields(match, m)
        match.save()
        created += int(was_created)
        updated += int(not was_created)
    logger.info('Matches import: %s creados, %s actualizados', created, updated)
    # El endpoint de equipos no trae el grupo: lo derivamos de los partidos.
    assign_team_groups()
    return created, updated


def assign_team_groups():
    """
    El grupo no viene en el endpoint de equipos, sólo en los partidos.
    Recorre los partidos de fase de grupos y asigna el grupo a cada equipo.
    Devuelve la cantidad de equipos actualizados.
    """
    updated = 0
    group_matches = Match.objects.filter(group__isnull=False).exclude(group='')
    for match in group_matches:
        for team in (match.home_team, match.away_team):
            if team and team.group != match.group:
                team.group = match.group
                team.save(update_fields=['group'])
                updated += 1
    logger.info('Team groups: %s equipos actualizados', updated)
    return updated


def update_results(client=None):
    """
    Actualización nocturna: sólo refresca el resultado/estado de los partidos
    que ya empezaron o terminaron (no toca los que siguen sin jugarse).
    Devuelve la cantidad de partidos actualizados.
    """
    client = client or FootballDataClient()
    by_external = {m.get('id'): m for m in client.get_matches()}

    updated = 0
    finished_ids = []
    # Sólo nos interesan los que el proveedor marca como ya jugados / en juego.
    relevant = {Match.Status.IN_PLAY, Match.Status.PAUSED, Match.Status.FINISHED}
    for match in Match.objects.exclude(status=Match.Status.FINISHED):
        m = by_external.get(match.external_id)
        if not m:
            continue
        if m.get('status') not in relevant:
            continue
        # asegura equipos resueltos (eliminatorias que se definen)
        if match.home_team is None:
            match.home_team = _team_by_external_id(m.get('homeTeam'))
        if match.away_team is None:
            match.away_team = _team_by_external_id(m.get('awayTeam'))
        _apply_match_fields(match, m)
        match.save()
        updated += 1
        if match.status == Match.Status.FINISHED:
            finished_ids.append(match.id)
    logger.info('Results update: %s partidos actualizados (%s terminados)', updated, len(finished_ids))
    return updated, finished_ids
