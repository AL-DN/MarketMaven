from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
    
    # Someone would like to update
    if request.method == 'POST':
        u_form= UserUpdateForm(request.POST, instance=request.user)
        p_form= ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your profile has been updated')
            return redirect('profile')

    else:
        # arguements populate form with users data
        u_form= UserUpdateForm(instance=request.user)
        p_form= ProfileUpdateForm(instance=request.user.profile)
        
        context = {
            'u_form': u_form,
            'p_form': p_form
        }

    return render(request, 'users/profile.html', context=context)


# Creates URL for OAuth consent screen
@login_required
def redirect_to_alpaca(request):
    client_id = settings.ALPACA_ID  # Ensure this matches your Alpaca settings
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



    
    