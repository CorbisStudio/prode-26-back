from django.urls import path

from .views import (
    PredictionListCreateView,
    GlobalRankingView,
    EliminatoriaRankingView,
    LeagueListCreateView,
    LeagueJoinView,
    LeagueRankingView,
)

urlpatterns = [
    path('predictions/', PredictionListCreateView.as_view(), name='predictions'),
    path('ranking/', GlobalRankingView.as_view(), name='ranking'),
    path('ranking/eliminatoria/', EliminatoriaRankingView.as_view(), name='ranking-eliminatoria'),
    path('leagues/', LeagueListCreateView.as_view(), name='leagues'),
    path('leagues/join/', LeagueJoinView.as_view(), name='league-join'),
    path('leagues/<int:pk>/ranking/', LeagueRankingView.as_view(), name='league-ranking'),
]
