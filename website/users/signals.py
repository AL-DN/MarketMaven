# invoked after an object is saved
from django.db.models.signals import post_save
# Sender - User
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

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