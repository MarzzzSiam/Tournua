from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import UserAccount, Tournament, Team, Match
from .forms import SignupForm
from django.views.decorators.cache import never_cache
from django.utils import timezone
from datetime import datetime
import itertools
from django.db.models import Q
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
import random


def signup_save(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if UserAccount.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            request.session['show_modal'] = False
            return redirect("signup")

        verification_code = random.randint(100000, 999999)


        try:
            send_mail(
                "Your Verification Code - Tournua",
                f"Hi {full_name},\n\nYour verification code is: {verification_code}\n\nUse this code to complete your signup.\n\nThank you!",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

        except Exception as e:
            print(e)
            messages.error(request, "Failed to send verification email. Try again later.")
            request.session['show_modal'] = False
            return redirect("signup")

        #Store user info + code in session
        request.session["signup_info"] = {
            "full_name": full_name,
            "email": email,
            "password": password,
            "verification_code": str(verification_code),
        }

        #Modal open only for verification
        request.session['show_modal'] = True
        messages.success(request, "Verification code sent to your email.")
        return redirect("signup")

    # GET request
    return render(request, "signup.html")

def verify_code(request):
    if request.method == "POST":
        user_code = request.POST.get("verification_code")
        session_data = request.session.get("signup_info")

        if not session_data:
            messages.error(request, "Session expired. Please sign up again.")
            request.session['show_modal'] = False
            return redirect("signup")

        correct_code = session_data.get("verification_code")

        if user_code == correct_code:
            # Create user
            UserAccount.objects.create(
                full_name=session_data["full_name"],
                email=session_data["email"],
                password=session_data["password"],
            )
            del request.session["signup_info"]

            #clear modal flag
            request.session['show_modal'] = False
            return redirect("login")
        else:
            messages.error(request, "Incorrect verification code. Try again.")
            request.session['show_modal'] = True  # Keep modal open if code wrong
            return redirect("signup")



# Step 1: Send OTP
def send_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = UserAccount.objects.get(email=email)
        except UserAccount.DoesNotExist:
            return render(request, "login.html", {
                "error": "No account found with this email."
            })

        # OTP Generate
        import random
        otp = str(random.randint(100000, 999999))
        request.session['reset_email'] = email
        request.session['reset_otp'] = otp

        # Send Mail
        from django.core.mail import send_mail
        from django.conf import settings
        send_mail(
            "Your Password Reset OTP",
            f"Hello {user.full_name},\nYour OTP for password reset is: {otp}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )

        # Save flag to session so next load auto shows step2
        request.session['show_step2'] = True

        return redirect("login_view")

    return redirect("login_view")


def reset_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        session_otp = request.session.get("reset_otp")
        session_email = request.session.get("reset_email")

        if email != session_email:
            error = "Email mismatch. Try again."
        elif otp != session_otp:
            error = "Invalid OTP."
        elif new_password != confirm_password:
            error = "Passwords do not match."
        elif len(new_password) < 8:
            error = "Password must be at least 8 characters."
        else:
            # Update user password (hashing optional)
            user = UserAccount.objects.get(email=email)
            user.password = new_password
            user.save()

            # Clear session
            del request.session['reset_email']
            del request.session['reset_otp']


            return redirect("login_view")

        # If any error
        return render(request, "login.html", {
            "show_step2": True,
            "email": email,
            "error": error
        })

    return redirect("login_view")


def login_view(request):
    error = None
    context = {}

    #Handle normal login
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user_obj = UserAccount.objects.filter(email=email, password=password).first()

        if user_obj:
            request.session["user_id"] = user_obj.id
            return redirect("dashboard")
        else:
            error = "Invalid email or password!"

    #Handle forgot password modal state
    if request.session.get("show_step2"):
        context["show_step2"] = True
        context["email"] = request.session.get("reset_email")
        del request.session["show_step2"]  # clear flag so it doesn’t persist

    #Send error (if any)
    context["error"] = error

    return render(request, "login.html", context)




@never_cache
def dashboard(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = UserAccount.objects.get(id=user_id)
    name = user.full_name.split(" ")[0]

    # Tournaments user created
    own_tournaments = Tournament.objects.filter(user=user)

    # Tournaments user joined (excluding own)
    joined_tournaments = Tournament.objects.filter(participants=user).exclude(user=user)

    tournaments = own_tournaments | joined_tournaments
    tournaments = tournaments.order_by('-created_at')

    show_deleted_modal = request.session.pop('tournament_deleted', False)
    show_created_modal = request.session.pop('tournament_created', False)
    show_remove_modal = request.session.pop('participant_removed', False)
    show_join_modal = request.session.pop('tournament_joined', False)


    return render(request, "demo.html", {
        "name": name,
        "tournaments": tournaments,
        "user": user,
        'show_deleted_modal': show_deleted_modal,
        'show_created_modal': show_created_modal,
        'show_remove_modal' : show_remove_modal,
        'show_join_modal' : show_join_modal,
    })


def join_tournament(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = UserAccount.objects.get(id=user_id)
    error = None

    if request.method == "POST":
        code = request.POST.get("tournament_code").strip().upper()
        try:
            tournament = Tournament.objects.get(code=code)

            if tournament.user == user:
                error = "You cannot join your own tournament."
            elif tournament.participants.filter(id=user.id).exists():
                error = "You already joined this tournament."
            else:
                tournament.participants.add(user)
                request.session['tournament_joined'] = True
                return redirect("dashboard")  # success

        except Tournament.DoesNotExist:
            error = "Invalid tournament code."

    # **Fetch created tournaments + joined tournaments**
    created_tournaments = Tournament.objects.filter(user=user).order_by('-created_at')
    joined_tournaments = Tournament.objects.filter(participants=user).exclude(user=user).order_by('-created_at')

    # Combine into one list (optional: keep separate in template)
    tournaments = list(created_tournaments) + list(joined_tournaments)

    return render(request, "demo.html", {
        "error": error,
        "tournaments": tournaments,
        "user": user,
        "name": user.full_name.split(" ")[0]
    })


def logout_view(request):
    # Clear all session data
    request.session.flush()  # This removes all session data
    return redirect("home")



def create_tournament(request):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        user = UserAccount.objects.get(id=user_id)
        name = request.POST.get("tournament_name")
        description = request.POST.get("tournament_descriptions")
        trophy = request.POST.get("trophy")
        t_type = request.POST.get("select_type")
        player_type = request.POST.get("player_type")
        format_choice = request.POST.get("format")
        teams_per_group = request.POST.get("team_num")

        # Save tournament
        tournament = Tournament.objects.create(
            user=user,
            name=name,
            description=description,
            trophy=trophy,
            tournament_type=t_type,
            player_type=player_type,
            format=format_choice,
            teams_per_group=teams_per_group,
        )

        request.session['tournament_created'] = True
        return redirect("dashboard")  # redirect after success

    return render(request, "tournament_form.html")


def add_teams(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    if request.method == "POST":
        num_teams = tournament.teams_per_group

        for i in range(1, num_teams + 1):
            name = request.POST.get(f"team{i}")

            if name:
                logo_filename = f"logo/Logo{i}.png"

                Team.objects.create(
                    tournament=tournament,
                    name=name,
                    logo=logo_filename  # set static path
                )

        # Generate matches if format = League
        if tournament.format.lower() == "league":
            num_matches = generate_league_fixtures(tournament)
            print(f"{num_matches} matches created for tournament '{tournament.name}'")

        return redirect("viewTournament", tournament_id=tournament.id)


def generate_league_fixtures(tournament):
    teams = list(tournament.teams.all())

    # Clear previous matches if any
    tournament.matches.all().delete()

    fixtures = []
    # Generate all possible pairs of teams (home and away)
    for team1, team2 in itertools.combinations(teams, 2):
        fixtures.append(Match(tournament=tournament, team1=team1, team2=team2))
        fixtures.append(Match(tournament=tournament, team1=team2, team2=team1))

    # Bulk create all matches in DB
    Match.objects.bulk_create(fixtures)
    return len(fixtures)


def tournament_view(request, tournament_id):
    user = None
    user_id = request.session.get("user_id")
    if user_id:
        try:
            user = UserAccount.objects.get(id=user_id)
        except UserAccount.DoesNotExist:
            user = None

    tournament = get_object_or_404(Tournament, id=tournament_id)
    matches = Match.objects.filter(tournament=tournament).select_related('team1', 'team2').order_by('created_at')

    # assign permanent display number before filtering
    all_matches = list(matches)
    for idx, match in enumerate(all_matches, start=1):
        match.display_number = idx  # virtual field (not in DB)

    # search logic
    query = request.GET.get('q', '').strip()
    if query:
        filtered_matches = [
            m for m in all_matches
            if query.lower() in m.team1.name.lower() or query.lower() in m.team2.name.lower()
        ]
    else:
        filtered_matches = all_matches

    is_creator = user and tournament.user == user
    teams_count = tournament.teams.count()
    context = {
        'tournament': tournament,
        'matches': filtered_matches,
        'user': user,
        'is_creator': is_creator,
        'query': query,
        'teams_count' : teams_count,
    }
    return render(request, 'view.html', context)



def update_match_date(request):
    if request.method == "POST":
        match_id = request.POST.get("match_id")
        match_date = request.POST.get("match_date")

        if not match_date:
            messages.error(request, "Please select a valid date and time.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        match = get_object_or_404(Match, id=match_id)

        try:
            # Convert string to datetime (naive)
            naive_datetime = datetime.strptime(match_date, "%Y-%m-%dT%H:%M")

            # Make it timezone-aware
            aware_datetime = timezone.make_aware(naive_datetime)

            match.match_date = aware_datetime
            match.save()


        except ValueError:
            messages.error(request, "Invalid date format. Please try again.")

        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('/')


def update_match_score(request):
    if request.method == "POST":
        match_id = request.POST.get("match_id")
        team1_score = request.POST.get("team1_score")
        team2_score = request.POST.get("team2_score")

        # Validate input
        try:
            team1_score = int(team1_score)
            team2_score = int(team2_score)
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid integer scores.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Get the match
        match = get_object_or_404(Match, id=match_id)

        # Update scores and mark as played
        match.team1_score = team1_score
        match.team2_score = team2_score
        match.played = True
        match.save()

        return redirect(request.META.get('HTTP_REFERER', '/'))

    # If someone tries GET request
    return redirect('/')




def leaderboard(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    matches = Match.objects.filter(tournament=tournament, played=True)
    teams = Team.objects.filter(tournament=tournament)  # all teams in tournament

    # Initialize standings for all teams
    standings = {}
    for team in teams:
        standings[team.id] = {
            "team": team,
            "MP": 0,
            "W": 0,
            "D": 0,
            "L": 0,
            "GS": 0,
            "GC": 0,
            "Pts": 0,
            "played": False  # track if played at least one match
        }

    # Update stats for played matches
    for match in matches:
        t1 = match.team1
        t2 = match.team2
        s1 = match.team1_score
        s2 = match.team2_score

        standings[t1.id]["MP"] += 1
        standings[t2.id]["MP"] += 1
        standings[t1.id]["GS"] += s1
        standings[t1.id]["GC"] += s2
        standings[t2.id]["GS"] += s2
        standings[t2.id]["GC"] += s1

        standings[t1.id]["played"] = True
        standings[t2.id]["played"] = True

        if s1 > s2:
            standings[t1.id]["W"] += 1
            standings[t2.id]["L"] += 1
            standings[t1.id]["Pts"] += 3
        elif s1 < s2:
            standings[t2.id]["W"] += 1
            standings[t1.id]["L"] += 1
            standings[t2.id]["Pts"] += 3
        else:
            standings[t1.id]["D"] += 1
            standings[t2.id]["D"] += 1
            standings[t1.id]["Pts"] += 1
            standings[t2.id]["Pts"] += 1

    # Convert to list
    leaderboard = list(standings.values())

    # Sort: first played teams by Pts->GD->GS, then unplayed teams at the bottom
    played_teams = [t for t in leaderboard if t["played"]]
    unplayed_teams = [t for t in leaderboard if not t["played"]]

    # Sort played teams
    played_teams.sort(key=lambda x: (x["Pts"], x["GS"] - x["GC"], x["GS"]), reverse=True)

    # Combine: played first, unplayed at bottom
    leaderboard = played_teams + unplayed_teams

    # Assign position and format values
    for i, row in enumerate(leaderboard, start=1):
        row["P"] = i
        # For unplayed teams, set all numeric stats to "-"
        if not row["played"]:
            for key in ["MP", "W", "D", "L", "GS", "GC", "Pts"]:
                row[key] = "-"

    return render(request, "leaderboard.html", {
        "tournament": tournament,
        "leaderboard": leaderboard
    })






def view_tournament_by_code(request):
    if request.method == "POST":
        code = request.POST.get("tournament_code").strip().upper()

        try:
            tournament = Tournament.objects.get(code=code)
            return redirect("viewTournament", tournament_id=tournament.id)
        except Tournament.DoesNotExist:
            messages.error(request, "Invalid tournament code.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

    return redirect("dashboard")



def delete_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    tournament.delete()
    request.session['tournament_deleted'] = True
    return redirect("dashboard")



def remove_participant(request, tournament_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = get_object_or_404(UserAccount, id=user_id)
    tournament = get_object_or_404(Tournament, id=tournament_id)

    if user in tournament.participants.all():
        tournament.participants.remove(user)
        # set session flag to show success modal
        request.session['participant_removed'] = True

    return redirect("dashboard")








