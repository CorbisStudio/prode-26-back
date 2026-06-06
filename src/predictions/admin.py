from django.contrib import admin

from .models import Prediction, League, LeagueMembership


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'match', 'home_score', 'away_score', 'points', 'is_scored', 'is_exact')
    list_filter = ('is_scored', 'is_exact')
    search_fields = ('user__username', 'match__home_team__name', 'match__away_team__name')


class LeagueMembershipInline(admin.TabularInline):
    model = LeagueMembership
    extra = 0


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'join_code', 'create_date')
    search_fields = ('name', 'join_code', 'owner__username')
    inlines = [LeagueMembershipInline]
