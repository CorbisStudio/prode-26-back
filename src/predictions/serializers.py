from django.utils import timezone

from rest_framework import serializers

from matches.models import Match
from .models import Prediction, League, LeagueMembership


class PredictionSerializer(serializers.ModelSerializer):
    match_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Prediction
        fields = [
            'id', 'match', 'match_detail',
            'home_score', 'away_score',
            'points', 'is_scored', 'is_exact',
        ]
        read_only_fields = ['points', 'is_scored', 'is_exact']

    def get_match_detail(self, obj):
        m = obj.match
        return {
            'id': m.id,
            'home_team': m.home_team.name if m.home_team else None,
            'away_team': m.away_team.name if m.away_team else None,
            'utc_date': m.utc_date,
            'stage': m.stage,
            'group': m.group,
            'status': m.status,
            'home_score': m.home_score,
            'away_score': m.away_score,
        }

    def validate(self, attrs):
        match = attrs.get('match') or getattr(self.instance, 'match', None)
        # El pronóstico se bloquea cuando el partido arranca.
        if match and match.utc_date and match.utc_date <= timezone.now():
            raise serializers.ValidationError(
                'El partido ya comenzó: no se puede cargar ni editar el pronóstico.'
            )
        return attrs


class LeagueSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = League
        fields = ['id', 'name', 'join_code', 'owner', 'members_count', 'create_date']
        read_only_fields = ['join_code', 'owner', 'create_date']

    def get_members_count(self, obj):
        return obj.memberships.count()
