# invoked after an object is saved
from django.db.models.signals import post_save
# Sender - User
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.shortcuts import redirect

from users.utils import get_positions
from .models import Profile
from django.contrib.auth.signals import user_logged_in

# Convert ISO8601 to DateTime
from dateutil import parser

from pprint import pprint

# After a user(sender) is saved(post_save) 
# it passes values and invokes create_profile
@receiver(post_save,sender=User)
def create_profile(sender, instance, created, **kwargs):
    # if user was created
    if created:
        # create a profile attached to the user that was saved
        Profile.objects.create(user=instance)

@receiver(post_save,sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
    
@receiver(user_logged_in)
def fetch_pos_on_login(sender, user, request, **kwargs):
    
    # caches new buys
    buys = []
   
    # copy of previous pos from last login
    previous_positions = request.user.profile.positions
    
    # gets pos from Alpaca API
    new_positions = get_positions(request)
    
    # checks if there are new pos
    for new_pos in new_positions:
        new_pos_ticker = new_pos.get('symbol')
        
        count = 0
        for prev_pos in previous_positions:
            prev_pos_ticker = new_pos.get('symbol')
            
            if prev_pos_ticker == new_pos_ticker:
                # possibly check for amount of shares here too
                break
        
        # remove checked position from previous positions
        previous_positions.pop(count)
        # addeds new position to list for user post prompt
        buys.append(new_pos)
        
        count += 1
        
        
    # at the end of the loop of there is any positions left in previous_positions
    # we can assume they were sold so we must add it to a sell list
    sells = []
    if len(previous_positions) > 0:
        for prev_pos in previous_positions:
            sells.append(prev_pos)
            

    print("BUYYYYYY")
    print(buys)
    print("SEEEEEEEEEEEEEEEEEELLLLLLLLllll")
    print(sells)
  #  if len(buys) > 0 or len(sells) > 0:
 #      redirect('new-posts')