from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.utils import timezone


# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg',upload_to='profile_pics')
    token_data = models.JSONField(null=True, blank=True)  # or use TextField/CharField if not JSON
    ytd_capital_gain = models.DecimalField(default=0.00,max_digits=5, decimal_places=2)
    
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
    def save(self,**kwargs):
        super().save()
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300,300)
            img.thumbnail(output_size)
            img.save(self.image.path)

class Position(models.Model):
    # relationships
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name="positions")

    # info
    position_id  = models.CharField(max_length=64)
    symbol    = models.CharField(max_length=16)
    qty       = models.FloatField(default=0.0)
    side      = models.CharField(max_length=4)
    filled_at = models.DateTimeField(default=timezone.now)
    buy_price     = models.FloatField(default=0.0)
    current_price     = models.FloatField(default=0.0)

    # performance metrics
    unrealized_gain     = models.FloatField(default=0.0)
    capital_gain     = models.FloatField(default=0.0)

    # flags
    posted    = models.BooleanField(default=False)     # a post already exists
    dismissed = models.BooleanField(default=False)     # user said “nah, don’t ask again”

    class Meta:
        unique_together = ("user", "position_id")         # prevents duplicates
        ordering = ("-filled_at",)
