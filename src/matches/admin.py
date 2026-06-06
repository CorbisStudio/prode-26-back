from django.contrib import admin

from .models import Team, Match


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'group')
    list_filter = ('group',)
    search_fields = ('name', 'code')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'utc_date', 'stage', 'group',
        'home_team', 'home_score', 'away_score', 'away_team', 'status',
    )
    list_filter = ('status', 'stage', 'group')
    search_fields = ('home_team__name', 'away_team__name')
    date_hierarchy = 'utc_date'
