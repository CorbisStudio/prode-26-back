from django.core.management.base import BaseCommand

from matches.services import import_teams, import_matches, FootballDataError


class Command(BaseCommand):
    help = 'Carga inicial: importa equipos, grupos y todos los partidos del Mundial.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--teams-only', action='store_true',
            help='Importa sólo los equipos (no los partidos).',
        )
        parser.add_argument(
            '--matches-only', action='store_true',
            help='Importa sólo los partidos (no los equipos).',
        )

    def handle(self, *args, **options):
        try:
            if not options['matches_only']:
                self.stdout.write('Importando equipos...')
                c, u = import_teams()
                self.stdout.write(self.style.SUCCESS(f'  Equipos: {c} creados, {u} actualizados'))

            if not options['teams_only']:
                self.stdout.write('Importando partidos...')
                c, u = import_matches()
                self.stdout.write(self.style.SUCCESS(f'  Partidos: {c} creados, {u} actualizados'))

            self.stdout.write(self.style.SUCCESS('Carga inicial completa.'))
        except FootballDataError as exc:
            self.stderr.write(self.style.ERROR(f'Error de la API: {exc}'))
