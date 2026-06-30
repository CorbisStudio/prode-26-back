from rest_framework import permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Match
from .serializers import MatchSerializer


class MatchListView(ListAPIView):
    """
    GET /api/matches/ → lista de partidos.
    Filtros opcionales por query param: ?group=Group A  ?stage=GROUP_STAGE  ?status=TIMED
    """
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Match.objects.select_related('home_team', 'away_team').all()
        params = self.request.query_params
        if params.get('group'):
            qs = qs.filter(group=params['group'])
        if params.get('stage'):
            qs = qs.filter(stage=params['stage'])
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        return qs


class MatchDetailView(RetrieveAPIView):
    """GET /api/matches/<id>/ → detalle de un partido."""
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Match.objects.select_related('home_team', 'away_team').all()


class SyncEliminationRoundsView(APIView):
    """
    GET /api/matches/sync-elimination-rounds/?token=<FOOTBALL_DATA_TOKEN>
    Completa los cruces de eliminatorias con los equipos ya definidos por el
    proveedor. Correr manualmente cada vez que termina una fase (16avos,
    octavos, cuartos...). El token es opcional: si no se pasa usa el configurado.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            from .services import FootballDataClient, sync_elimination_rounds

            token = request.query_params.get('token')
            client = FootballDataClient(token=token) if token else FootballDataClient()

            updated, details = sync_elimination_rounds(client=client)

            return Response({'status': 'ok', 'updated': updated, 'matches': details})
        except Exception as exc:
            return Response({'status': 'error', 'detail': str(exc)}, status=500)


class UpdateMatchResultsView(APIView):
    """
    GET /api/matches/update/?token=<FOOTBALL_DATA_TOKEN>
    Endpoint de emergencia para disparar la actualización sin el cron.
    El token es opcional: si no se pasa usa el configurado en settings.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            from .services import FootballDataClient, update_results
            from predictions.services import score_finished_matches

            token = request.query_params.get('token')
            client = FootballDataClient(token=token) if token else FootballDataClient()

            updated, finished_ids = update_results(client=client)
            scored = score_finished_matches(finished_ids) if finished_ids else 0

            return Response({'status': 'ok', 'result': {
                'updated': updated,
                'finished': len(finished_ids),
                'scored': scored,
            }})
        except Exception as exc:
            return Response({'status': 'error', 'detail': str(exc)}, status=500)
