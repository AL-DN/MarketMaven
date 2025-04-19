from django.http import HttpResponse
from django.shortcuts import redirect
import requests
import os
from django.conf import settings
from .models import Profile


def code_for_token(auth_code):
    token_url = "https://api.alpaca.markets/oauth/token"

    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": settings.ALPACA_ID,
        "client_secret": settings.ALPACA_SECRET,
        "redirect_uri": "http://127.0.0.1:8000/callback/"
    }

    # sends POST request and gets response
    response = requests.post(token_url, data=data)
    
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
        return 'WRONG'
    
    
