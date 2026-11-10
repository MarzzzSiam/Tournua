"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
path("signup/", views.signup_save, name="signup_save"),
path("verify-code/", views.verify_code, name="verify_code"),
path("login/", views.login_view, name="login_view"),
path('send-otp/', views.send_otp, name='send_otp'),
path('reset-password/', views.reset_password, name='reset_password'),
path("dashboard/", views.dashboard, name="dashboard"),
path('logout/', views.logout_view, name='logout'),
path("create-tournament/", views.create_tournament, name="create_tournament"),
path("tournament/<int:tournament_id>", views.tournament_view, name="viewTournament"),
path('update-match-score/', views.update_match_score, name='update_match_score'),
path("tournament/<int:tournament_id>/leaderboard/", views.leaderboard, name="leaderboard"),
path('update_match_date/', views.update_match_date, name='update_match_date'),
path('join-tournament/', views.join_tournament, name='join_tournament'),
path("view-by-code/", views.view_tournament_by_code, name="view_tournament_by_code"),
path('tournament/<int:tournament_id>/delete/', views.delete_tournament, name='delete_tournament'),
path('tournament/<int:tournament_id>/remove/', views.remove_participant, name='remove_participant'),
path("tournament/<int:tournament_id>/add-teams/", views.add_teams, name="add_teams"),
]
