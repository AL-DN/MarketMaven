import copy
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


# generic modular api call for ALPACA
# given the type of api call(subject) account, orders, positions (refer to end of ALpaca OAutho docs)
# returns json response from api good or bad (make sure to validate)
def alpaca_api_call(request, subject):
    
    token_data = getToken(request.user)
    #print(f"Token Data: {token_data}")
    
    # extracts revelevant info
    access_token = token_data.get('alpaca_access_token')
    token_type = token_data.get('alpaca_token_type')
    url = f'https://paper-api.alpaca.markets/v2/{subject}' 
    
    headers = {
    "Authorization": f"{token_type} {access_token}"
    }
    
    # make GET Request
    response = requests.get(url, headers=headers)
    
    return response

# saves into profile and returns the positions from ALPACA
def get_positions(request):
    
    # API Call
    response = alpaca_api_call(request, 'positions')
    
    # validation
    if response.status_code == 200:
        
        # saves powitions to user profile
        positions = response.json()
        
        pprint(positions)
        pprint(alpaca_api_call(request,'account').json())
        # saves data into db
        profile = request.user.profile
        profile.positions = positions
        profile.save()  
        return positions
    else:
        print(f"Failed to fetch orders: {response.status_code} {response.text}")
        return []

# recognizes changes in users positions in order to
# return a dictionary of buys and sells since last login

def filter_positions(request):
    
    # copy of previous positions from last login
    prev = copy.deepcopy(request.user.profile.positions) or []
       
    # gets current positions from Alpaca API
    new = get_positions(request)
    
    # extract their tickers
    prev_syms = {p['symbol'] for p in prev}
    new_syms  = {p['symbol'] for p in new}

    # filter into buy and sell lists
    buys  = [p for p in new  if p['symbol'] not in prev_syms]
    sells = [p for p in prev if p['symbol'] not in new_syms]

    # packages buys/sells and ships to blog view
    return {
        'buys': buys,
        'sell': sells,
    }

