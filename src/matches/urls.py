from django.urls import path

from .views import MatchListView, MatchDetailView, UpdateMatchResultsView

urlpatterns = [
    path('matches/', MatchListView.as_view(), name='matches'),
    path('matches/update/', UpdateMatchResultsView.as_view(), name='matches-update'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='match-detail'),
]
