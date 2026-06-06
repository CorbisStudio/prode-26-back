from rest_framework import permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView

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
