import random

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from matches.models import Match
from predictions.models import Prediction, League, LeagueMembership
from predictions.services import score_finished_matches


class Command(BaseCommand):
    help = (
        'Carga datos de prueba: marca los primeros N partidos como jugados con '
        'resultados simulados, crea pronósticos variados para varios usuarios, '
        'puntúa todo y arma una liga de ejemplo.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--matches', type=int, default=12, help='Partidos a simular como jugados')
        parser.add_argument('--users', type=int, default=30, help='Usuarios que cargan pronósticos')
        parser.add_argument('--seed', type=int, default=42, help='Semilla aleatoria (reproducible)')

    @transaction.atomic
    def handle(self, *args, **opts):
        rnd = random.Random(opts['seed'])

        # Limpio datos de prueba previos
        Prediction.objects.all().delete()
        LeagueMembership.objects.all().delete()
        League.objects.all().delete()

        users = list(User.objects.filter(is_active=True).order_by('id')[:opts['users']])
        if not users:
            self.stderr.write(self.style.ERROR('No hay usuarios activos. Cargá usuarios primero.'))
            return

        played = list(Match.objects.order_by('utc_date')[:opts['matches']])
        if not played:
            self.stderr.write(self.style.ERROR('No hay partidos. Corré import_worldcup primero.'))
            return

        # 1) Simular resultados reales de los partidos jugados
        for m in played:
            m.status = Match.Status.FINISHED
            m.home_score = rnd.randint(0, 4)
            m.away_score = rnd.randint(0, 3)
            if m.home_score > m.away_score:
                m.winner = Match.Winner.HOME
            elif m.home_score < m.away_score:
                m.winner = Match.Winner.AWAY
            else:
                m.winner = Match.Winner.DRAW
            m.save()
        self.stdout.write(self.style.SUCCESS(f'{len(played)} partidos simulados como FINISHED'))

        # 2) Pronósticos variados por usuario (algunos exactos, otros cerca, otros lejos)
        total_preds = 0
        for user in users:
            for m in played:
                roll = rnd.random()
                if roll < 0.20:
                    # marcador exacto
                    ph, pa = m.home_score, m.away_score
                elif roll < 0.55:
                    # acierta resultado, marcador distinto
                    if m.winner == Match.Winner.HOME:
                        ph, pa = m.home_score + rnd.randint(0, 2), max(0, m.away_score - 1)
                        ph = max(ph, pa + 1)
                    elif m.winner == Match.Winner.AWAY:
                        pa, ph = m.away_score + rnd.randint(0, 2), max(0, m.home_score - 1)
                        pa = max(pa, ph + 1)
                    else:
                        v = rnd.randint(0, 3)
                        ph, pa = v, v
                else:
                    # pronóstico cualquiera
                    ph, pa = rnd.randint(0, 4), rnd.randint(0, 4)

                Prediction.objects.create(
                    user=user, match=m, home_score=ph, away_score=pa
                )
                total_preds += 1
        self.stdout.write(self.style.SUCCESS(f'{total_preds} pronósticos creados'))

        # 3) Puntuar
        scored = score_finished_matches([m.id for m in played])
        self.stdout.write(self.style.SUCCESS(f'{scored} pronósticos puntuados'))

        # 4) Liga de ejemplo con la mitad de los usuarios
        owner = users[0]
        league = League.objects.create(name='Liga de los Pibes', owner=owner)
        for u in users[: max(2, len(users) // 2)]:
            LeagueMembership.objects.get_or_create(league=league, user=u)
        self.stdout.write(self.style.SUCCESS(
            f'Liga "{league.name}" creada (code={league.join_code}, {league.memberships.count()} miembros)'
        ))

        self.stdout.write(self.style.SUCCESS('✓ Seed completo.'))
