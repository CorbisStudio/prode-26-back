from django.urls import path

from .views import MatchListView, MatchDetailView

urlpatterns = [
    path('matches/', MatchListView.as_view(), name='matches'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='match-detail'),
]
