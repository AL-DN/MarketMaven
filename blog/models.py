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
    
    def get_comment_count(self):
        """Get the number of comments on this post"""
        return self.comments.count()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['date_posted']
    
    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.symbol}'