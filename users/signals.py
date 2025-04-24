# invoked after an object is saved
from django.db.models.signals import post_save
# Sender - User
from django.contrib.auth.models import User
from django.dispatch import receiver

from users.utils import get_orders
from .models import Profile
from django.contrib.auth.signals import user_logged_in

# Convert ISO8601 to DateTime
from dateutil import parser

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
def fetch_orders_on_login(sender, user, request, **kwargs):
    # this will run get_orders each time someone logs in
    json_order_dict = get_orders(request)
    latest_post_date = json_order_dict['']
    #converts original ISO8601 string to datetime 
    latest_trade_date = parser.isoparse(json_order_dict['created_at'])
   
     # shows not all orders since last login have been seen   
    if latest_post_date < latest_trade_date:
        # add to list
        
    # shows all orders since last login have been seen   
    elif latest_post_date >= latest_trade_date: