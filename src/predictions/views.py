from django.shortcuts import get_object_or_404

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response

from .models import Prediction, League, LeagueMembership
from .serializers import PredictionSerializer, LeagueSerializer
from .services import global_ranking, league_ranking, eliminatoria_ranking


class PredictionListCreateView(ListCreateAPIView):
    """
    GET  /api/predictions/  → mis pronósticos
    POST /api/predictions/  → crea o actualiza mi pronóstico para un partido (upsert).
    """
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Prediction.objects
            .filter(user=self.request.user)
            .select_related('match', 'match__home_team', 'match__away_team')
        )

    def create(self, request, *args, **kwargs):
        # upsert: si ya existe pronóstico para ese match, lo edita.
        match_id = request.data.get('match')
        instance = Prediction.objects.filter(user=request.user, match_id=match_id).first()
        serializer = self.get_serializer(instance, data=request.data, partial=bool(instance))
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        code = status.HTTP_200_OK if instance else status.HTTP_201_CREATED
        return Response(serializer.data, status=code)


class GlobalRankingView(APIView):
    """GET /api/ranking/ → ranking global."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(global_ranking())


class EliminatoriaRankingView(APIView):
    """GET /api/ranking/eliminatoria/ → ranking contando sólo puntos de eliminatoria."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(eliminatoria_ranking())


class LeagueListCreateView(ListCreateAPIView):
    """
    GET  /api/leagues/  → mis ligas (creadas o donde soy miembro)
    POST /api/leagues/  → crear liga (me agrega como miembro y owner)
    """
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return League.objects.filter(memberships__user=self.request.user).distinct()

    def perform_create(self, serializer):
        league = serializer.save(owner=self.request.user)
        LeagueMembership.objects.get_or_create(league=league, user=self.request.user)


class LeagueJoinView(APIView):
    """POST /api/leagues/join/  body: {join_code} → me une a la liga."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        join_code = request.data.get('join_code')
        if not join_code:
            return Response({'error': 'join_code es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        league = League.objects.filter(join_code=join_code).first()
        if not league:
            return Response({'error': 'Liga no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        LeagueMembership.objects.get_or_create(league=league, user=request.user)
        return Response(LeagueSerializer(league).data, status=status.HTTP_200_OK)


class LeagueRankingView(APIView):
    """GET /api/leagues/<id>/ranking/ → ranking de la liga (sólo miembros)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        league = get_object_or_404(League, pk=pk)
        if not league.memberships.filter(user=request.user).exists():
            return Response({'error': 'No sos miembro de esta liga'}, status=status.HTTP_403_FORBIDDEN)
        return Response(league_ranking(league))
