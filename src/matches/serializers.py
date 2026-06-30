from rest_framework import serializers

from .models import Team, Match


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'code', 'group', 'flag_url']


class MatchSerializer(serializers.ModelSerializer):
    home_team = TeamSerializer(read_only=True)
    away_team = TeamSerializer(read_only=True)

    class Meta:
        model = Match
        fields = [
            'id', 'stage', 'group', 'matchday',
            'home_team', 'away_team', 'utc_date', 'status',
            'home_score', 'away_score', 'winner',
            'duration', 'penalties_home', 'penalties_away',
            'half_time_home', 'half_time_away',
            'regular_time_home', 'regular_time_away',
            'extra_time_home', 'extra_time_away',
        ]
