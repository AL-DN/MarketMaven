import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import requests
from .models import Profile
from users.utils import code_for_token, get_positions, getToken
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.conf import settings
import random
import string
import urllib.parse

def register(request):

    def save(self, *args, **kwargs):  # Accept extra arguments
        super().save(*args, **kwargs)  # Pass them to the parent class

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # saves form fields as user
            form.save()
            messages.success(request, f'Your account has been created! You are now able to login.')
            return redirect('login')
    else:
        form = UserRegisterForm()

    return render(request,'users/register.html', {'form': form}) 

@login_required
def profile(request):
    context = {
        'current_positions': request.user.profile.get_current_positions(),
        'past_trades': request.user.profile.get_past_trades(),
        'user_posts': request.user.profile.get_user_posts()
    }
    return render(request, 'users/profile.html', context=context)

@login_required
def settings(request):
    # Someone would like to update
    if request.method == 'POST':
        u_form= UserUpdateForm(request.POST, instance=request.user)
        p_form= ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your profile has been updated')
            return redirect('settings')

    else:
        # arguements populate form with users data
        u_form= UserUpdateForm(instance=request.user)
        p_form= ProfileUpdateForm(instance=request.user.profile)
        
        context = {
            'u_form': u_form,
            'p_form': p_form,
        }

    return render(request, 'users/settings.html', context=context)


# Creates URL for OAuth consent screen
@login_required
def redirect_to_alpaca(request):
    client_id = os.environ.get("ALPACA_ID")  # Ensure this matches your Alpaca settings
    redirect_uri = "http://127.0.0.1:8000/callback/" # must match one registered / where it redirects once consent is completed
    state = ''.join(random.choices(string.ascii_letters + string.digits, k=16))  # CSRF protection
    scope = "account:write trading"
    env="paper"

    if not client_id:
        messages.error(request, "Alpaca Client ID is missing.")
        return redirect("profile")  # Redirect somewhere useful if there's an error

    oauth_url = (
        f"http://app.alpaca.markets/oauth/authorize?"
        f"response_type=code&client_id={urllib.parse.quote(client_id)}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&state={state}&scope={urllib.parse.quote(scope)}"
        f"&env={urllib.parse.quote(env)}"
    )

    return redirect(oauth_url)

# Once consent is accepte it will return to this view that will:
# Extract the code and save it to backend
@login_required
def oauth_callback(request):
    auth_code = request.GET.get("code")
        
    if not auth_code:
        return HttpResponse("Authorization code was not returned!")

    # does token exhange 
    token_data = code_for_token(auth_code)

    # saves token info in profile model
    if token_data != None:
        profile = Profile.objects.get(user=request.user)
        profile.token_data = token_data
        profile.save()  
        return redirect("profile")
    else:
        return HttpResponse("Exhange of Code for Token was unsuccessful")

@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if user_to_follow != request.user:
        request.user.profile.following.add(user_to_follow)
        messages.success(request, f'You are now following {username}')
    return redirect('user-profile', username=username)

@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    request.user.profile.following.remove(user_to_unfollow)
    messages.success(request, f'You have unfollowed {username}')
    return redirect('user-profile', username=username)

@login_required
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    is_following = request.user.profile.following.filter(id=user.id).exists()
    has_notifications = request.user.profile.has_email_notifications_for(user)
    context = {
        'profile_user': user,
        'is_following': is_following,
        'has_notifications': has_notifications,
        'current_positions': user.profile.get_current_positions(),
        'past_trades': user.profile.get_past_trades(),
        'user_posts': user.profile.get_user_posts()
    }
    return render(request, 'users/user_profile.html', context)

@login_required
def user_search(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)[:10]
    context = {
        'users': users,
        'query': query
    }
    return render(request, 'users/user_search.html', context)

@login_required
def following_list(request):
    following = request.user.profile.following.all()
    context = {
        'following': following
    }
    return render(request, 'users/following_list.html', context)

@login_required
def user_stats(request):
    """Display comprehensive user trading statistics"""
    stats = request.user.profile.get_trading_stats()
    positions = request.user.positions.all().order_by('-filled_at')[:10]  # Recent positions
    
    context = {
        'stats': stats,
        'recent_positions': positions
    }
    return render(request, 'users/user_stats.html', context)

def public_stats(request, username):
    """Display public trading statistics for any user"""
    user = get_object_or_404(User, username=username)
    stats = user.profile.get_trading_stats()
    
    context = {
        'profile_user': user,
        'stats': stats
    }
    return render(request, 'users/public_stats.html', context)

@login_required
def leaderboard(request):
    """Display top performing traders leaderboard"""
    # Get all users with positions
    users_with_positions = User.objects.filter(positions__isnull=False).distinct()
    
    # Calculate stats for each user and create leaderboard
    leaderboard_data = []
    
    for user in users_with_positions:
        stats = user.profile.get_trading_stats()
        if stats['total_positions'] > 0:  # Only include users with actual trades
            # Calculate performance score (average return * win rate / 100)
            performance_score = stats['avg_return_pct'] * stats['win_rate'] / 100
            leaderboard_data.append({
                'user': user,
                'stats': stats,
                'score': performance_score
            })
    
    # Sort by performance score (descending)
    leaderboard_data.sort(key=lambda x: x['score'], reverse=True)
    
    # Get top 20 traders
    top_traders = leaderboard_data[:20]
    
    context = {
        'top_traders': top_traders,
        'total_traders': len(leaderboard_data)
    }
    return render(request, 'users/leaderboard.html', context)

@login_required
def toggle_email_notifications(request, username):
    """Toggle email notifications for a specific user's posts"""
    user_to_notify = get_object_or_404(User, username=username)
    
    # Check if the current user follows this user
    is_following = request.user.profile.following.filter(id=user_to_notify.id).exists()
    
    if not is_following:
        messages.error(request, f'You must follow {username} before enabling email notifications.')
        return redirect('user-profile', username=username)
    
    # Don't allow notifications for yourself
    if user_to_notify == request.user:
        messages.error(request, 'You cannot enable email notifications for yourself.')
        return redirect('profile')
    
    # Toggle notifications
    enabled = request.user.profile.toggle_email_notifications(user_to_notify)
    
    if enabled:
        messages.success(request, f'Email notifications enabled for {username}\'s posts!')
    else:
        messages.success(request, f'Email notifications disabled for {username}\'s posts.')
    
    return redirect('user-profile', username=username)
    