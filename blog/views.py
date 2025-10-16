from pprint import pprint
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User
from django.contrib import messages

from blog.forms import PostForm, CommentForm
from users.models import Position
from users.utils import filter_positions
from .models import Post, Comment

from django.contrib.auth.decorators import login_required


      
class PostListView(ListView):
    model=Post
    template_name='blog/home.html' #  <app>/<model>_<viewtype>.html
    context_object_name='posts' # context
    ordering=['-date_posted']
    paginate_by = 10

    def get_queryset(self):
        queryset =  super().get_queryset()
        symbol = self.request.GET.get('symbol')

        if symbol:
            queryset = queryset.filter(position__symbol__iexact=symbol)
        
        return queryset

class UserPostListView(ListView):
    model=Post
    template_name='blog/user_posts.html' #  <app>/<model>_<viewtype>.html
    context_object_name='posts' # context
    paginate_by = 10

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')

class PostDetailView(DetailView):
    model=Post
    # context_object_name=object
    # template_name = post_detail.html
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        context['comment_form'] = CommentForm()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.author = request.user
            comment.save()
            messages.success(request, 'Your comment has been posted!')
            return redirect('post-detail', pk=self.object.pk)
        
        context = self.get_context_data()
        context['comment_form'] = form
        return self.render_to_response(context)

class PostCreateView(LoginRequiredMixin, CreateView):
    model=Post
    form_class = PostForm

    # central override point (executes before any function)
    def dispatch(self, request, *args, **kwargs):
        self.position = get_object_or_404(Position, pk=kwargs['pk'], user=request.user)
        return super().dispatch(request,*args,**kwargs)

    # prefills the form
    def get_initial(self):
        initial = super().get_initial()

        # values
        initial['symbol'] = self.position.symbol
        initial['side'] = self.position.side
        return initial     
    
    def form_valid(self, form):
        # form.instance == Post 
        form.instance.position = self.position
        form.instance.author = self.request.user
        
        self.position.posted = True
        self.position.save()
        
        response = super().form_valid(form)
        
        # Send email notifications to subscribers
        self.send_email_notifications(form.instance)
        
        return response
    
    def send_email_notifications(self, post):
        """Send email notifications to users who subscribed to this author's posts"""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        # Get all users who have email notifications enabled for this author
        subscribers = self.request.user.email_subscribers.all()
        
        if not subscribers.exists():
            return
        
        # Prepare email content
        subject = f"New post from {self.request.user.username} on MarketMaven"
        post_url = self.request.build_absolute_uri(post.get_absolute_url())
        
        for subscriber in subscribers:
            # Create personalized message
            message = f"""
Hello {subscriber.username},

{self.request.user.username} just posted about {post.symbol} ({post.side.upper()}).

{post.content[:200]}{'...' if len(post.content) > 200 else ''}

View the full post here: {post_url}

---
To manage your notification settings, visit your profile on MarketMaven.

This email was sent because you enabled email notifications for {self.request.user.username}'s posts.
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [subscriber.email],
                    fail_silently=True,
                )
            except Exception as e:
                # Log error but don't prevent post creation
                print(f"Failed to send email to {subscriber.email}: {e}")


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model=Post
    fields = ['content']
    # context_object_name=object
    # template_name = post_detail.html

    # overrides method so that
    # for the current form user is trying to submit
    # make its author the current logged in user
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        else: return False

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model=Post
    success_url='/'
    
    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        else: return False

def about(request):
    return render(request, 'blog/about.html',context= {'title': 'About'})


class NewPositionsView(LoginRequiredMixin, ListView):
    model = Position

    # template config
    template_name = "blog/new_positions.html"
    context_object_name = "positions"

    def get(self, request, *args, **kwargs):
        
        # updates positions
        filter_positions(request)
        return super().get(request,*args,**kwargs)
        
    def get_queryset(self):
        return Position.objects.filter(
            user = self.request.user,
            posted = False,
            dismissed = False,
        )

@login_required
def dismiss_position(request, pk):
    position = get_object_or_404(Position, pk=pk, user=request.user)
    position.dismissed = True
    position.save()
    return redirect('new-positions')