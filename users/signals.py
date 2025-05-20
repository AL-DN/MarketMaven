# invoked after an object is saved
import copy
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
