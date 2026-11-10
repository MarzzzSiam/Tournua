from django.contrib import admin
from .models import UserAccount, Tournament, Team, Match

admin.site.register(UserAccount)
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'tournament_type', 'player_type', 'format', 'created_at')
    readonly_fields = ('code',)
admin.site.register(Team)
admin.site.register(Match)