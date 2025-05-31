from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse

from users.models import Position

class Post(models.Model):

    # relationships
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.OneToOneField(Position, on_delete=models.CASCADE,null=True, blank=True)

    symbol = models.CharField(default='', max_length=4)
    side = models.CharField(default='', max_length=4)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.symbol
    
    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk':self.pk})