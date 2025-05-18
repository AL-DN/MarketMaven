from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
import requests
import os
from django.conf import settings
from .models import Profile
from pprint import pprint

def code_for_token(auth_code):
    token_url = "https://api.alpaca.markets/oauth/token"

    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": settings.ALPACA_ID,
        "client_secret": settings.ALPACA_SECRET,
        "redirect_uri": "http://127.0.0.1:8000/callback/"
    }
     # for security purpose specified in part 5 of Usign OAuth2 Docs
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"  # Alpaca requires this
    }
    # TESTING
    #print("Sending token exchange request with:")
    #print("Data:", data)
    #print("Headers:", headers)


    # sends POST request and gets response
    response = requests.post(token_url, data=data, headers=headers)
    
    # checks if post request was successful
    if response.status_code == 200:
        token_data = response.json()
        
        token_data={
        "alpaca_access_token": token_data.get("access_token"),
        "alpaca_scope": token_data.get("scope"),
        "alpaca_token_type": token_data.get("token_type"),
        }
        return token_data 
    else:
        print("Token exchange failed!")
        print("Status Code:", response.status_code)
        print("Response Text:", response.text) 
        return None
    
# gets token info
def getToken(user):
    return user.profile.token_data


def get_positions(request):

    # returns dict with token data from DB
    token_data = getToken(request.user)
    print(f"Token Data: {token_data}")
    
    access_token = token_data.get('alpaca_access_token')
    token_type = token_data.get('alpaca_token_type')
    url = 'https://paper-api.alpaca.markets/v2/positions' 
    
    headers = {
    "Authorization": f"{token_type} {access_token}"
    }
    
    # make GET Request
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # saves orders to user profile
        orders = response.json()
        profile = Profile.objects.get(user=request.user)
        profile.orders = orders
        profile.save()  
        
        return orders
    else:
        print(f"Failed to fetch orders: {response.status_code} {response.text}")
        return []



