import copy
from datetime import timedelta
import pprint
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
import requests
import os
from django.conf import settings
from .models import Profile, Position
import json
from .models import Position

from django.utils import timezone

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
    
    if token_data is None:
        return {
            "status_code": 401,
            "message": "Unauthorized: No token data found."
        }
    
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
    # with open("account.json", "w") as f:
    #             json.dump(response.json(), f, indent=4)
    # validation
    try:
        if response.status_code == 200:
            
            # saves positions to user profile
            positions = response.json()
            
            # with open("positions.json", "w") as f:
            #     json.dump(positions, f, indent=4)
                
            #pprint(alpaca_api_call(request,'account').json())
            # saves data into db
            profile = request.user.profile
            profile.positions = positions
            profile.save()  
            return positions
        else:
            return []
    except Exception as e:
        return []

# filter_positon helper functions
def calculate_gain(current_price, buy_price, qty):
    
    return (float(current_price) - float(buy_price)) * float(qty)

def _to_float(val, default = 0.0):
    try:
        return float(val)
    except(TypeError, ValueError):
        return default

# recognizes changes in users positions in order to
# return a dictionary of buys and sells since last login
def filter_positions(request):
    
    # gets (list of Position objects) Positions saved from last login in DB
    prev = list(request.user.positions.all())    

    # gets (list of dicts) current positions from Alpaca API
    new = get_positions(request)
    
    # extract their tickers
    prev_syms = {p.symbol for p in prev}
    new_syms  = {p['symbol'] for p in new}

    # filter into buy and sell lists
    buys  = [p for p in new  if p['symbol'] not in prev_syms]
    sells = [p for p in prev if p.symbol not in new_syms]
    holds = [p for p in new if p['symbol'] in prev_syms]


    for buy in buys:

        # converts json strings to floats
        qty             = _to_float(buy.get("qty"))
        buy_price       = _to_float(buy.get("avg_entry_price"))
        current_price   = _to_float(buy.get("current_price"))


        # this function will ensure changes in qty,cost,price are recorded
        Position.objects.update_or_create(
            #lookup fields (unique)
            user=request.user,
            position_id=buy['asset_id'],
            # saves defaults to row
            defaults={
                "symbol": buy["symbol"],
                "qty":    qty,
                "side":   buy["side"],
                "buy_price":  buy_price,
                "current_price": current_price
            }
        )

    # updates the current price of stocks that are currently held / unrealized gain
    for hold in holds:

        # updates buy and current prices for stock
        try:
            # get position to update
            position = Position.objects.get( user=request.user, symbol=hold["symbol"] )

            # values to update
            position.current_price = float(hold.get('current_price', 0.0))
            position.buy_price = float(hold.get("avg_entry_price", 0.0))
            position.unrealized_gain = calculate_gain(hold['current_price'], hold["avg_entry_price"], hold['qty'])
            position.buy_date = timezone.now()
            position.save(update_fields=["current_price", "buy_price", "unrealized_gain","buy_date"])

        except Position.DoesNotExist:
            pass

    for sell in sells:
        # marks positions as sold
        sell.side = 'sell'
        # updates capital gain
        sell.capital_gain = calculate_gain(sell.current_price, sell.buy_price, sell.qty)
        # caches when it was sold (for ytd calculations)
        sell.sell_date = timezone.now()

        sell.save(update_fields=["side", "capital_gain", "sell_date"])


# def update_performance(request):
     
#     one_year_ago = timezone.now() + timedelta(days=365)

#     # gets users positions
#     # filtering by filled_at is filter by positions that were bought at most a year ago.
#     positions = Position.objects.filter(
#         user = request.user,
#         filled_at__gte=one_year_ago
#     )    
    
#     # sums important data for calculation
#     total_unrealized_gains = 0
#     total_cost = 0
#     total_capital_gains = 0
#     for position in positions:
#         total_cost += position.buy_price * position.qty

#         if position.side == 'sell':
#             total_capital_gains += position.capital_gain
#         else:
#             total_unrealized_gains += position.unrealized_gain        


#     # TODO: we must handle the cases that were boought more than a year ago

#     # calculation
#     ytd_returns = ((total_unrealized_gains + total_capital_gains) / total_cost) * 100

#     # saves metric to profile
#     profile = Profile.objects.get(
#         user=request.user
#     )

#     profile.ytd_return = ytd_returns
#     profile.save()