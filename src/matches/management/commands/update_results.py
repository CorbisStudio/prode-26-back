from django.core.management.base import BaseCommand
from matches.tasks import update_match_results

class Command(BaseCommand):
    help = 'Actualiza los resultados de los partidos'

    def handle(self, *args, **options):
        self.stdout.write('Actualizando resultados...')
        result = update_match_results()
        self.stdout.write(self.style.SUCCESS(f'Completado: {result}'))
