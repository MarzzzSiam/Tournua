from django.db import models
import random
import string


class UserAccount(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # will store hashed password

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email



class Tournament(models.Model):
    TROPHY_CHOICES = [
        ("Trophy1.png", "Golden Cup"),
        ("Trophy2.png", "Silver Cup"),
        ("Trophy3.png", "Bronze Cup"),
        ("Trophy4.png", "Bronze Cup"),
    ]
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name="tournaments")
    code = models.CharField(max_length=8, unique=True, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trophy = models.CharField(max_length=20, choices=TROPHY_CHOICES, blank=True, null=True)
    tournament_type = models.CharField(max_length=50, choices=[("online", "Online"), ("offline", "Offline")])
    player_type = models.CharField(max_length=50, choices=[("single", "Single"), ("team", "Team")])
    format = models.CharField(max_length=50, choices=[("Knockout", "Knockout"), ("League", "League")])
    num_groups = models.IntegerField(default=1)
    teams_per_group = models.IntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(UserAccount, related_name="joined_tournaments", blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_code():
        """Generate a unique 6-character alphanumeric code."""
        from .models import Tournament  # avoid circular import
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Tournament.objects.filter(code=code).exists():
                return code


class Team(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=200)
    logo = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name


class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="matches")
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team1_matches")
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team2_matches")
    match_date = models.DateTimeField(blank=True, null=True)  # optional
    team1_score = models.IntegerField(default=0)
    team2_score = models.IntegerField(default=0)
    played = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.team1.name} vs {self.team2.name}"
