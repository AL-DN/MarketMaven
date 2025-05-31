from pprint import pprint
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User

from users.models import Position
from users.utils import filter_positions
from .models import Post

from django.views.generic import TemplateView

# to overide forms
from django import forms
from .models import Post

# overides the form sidget
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['symbol','side','content']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        
        # sets fields 
        self.fields['symbol'].disabled = True
        self.fields['side'].disabled = True
        


class PostListView(ListView):
    model=Post
    template_name='blog/home.html' #  <app>/<model>_<viewtype>.html
    context_object_name='posts' # context
    ordering=['-date_posted']
    paginate_by = 10

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
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model=Post
    fields = ['title','content']
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