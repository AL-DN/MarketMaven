from pprint import pprint
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User

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
        fields = ['symbol','type','content']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        
        # sets fields 
        self.fields['symbol'].disabled = True
        self.fields['type'].disabled = True
        


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
    
    def get_initial(self):
        inital = super().get_initial()
        
        # gets query parameters passed thru url
        symbol = self.request.GET.get('symbol')
        type = self.request.GET.get('type')

        if symbol:
            inital['symbol'] = symbol
            #print(f"symbol {inital['symbol']}")
        if type:
            inital['type'] = type
            #print(f"type {inital['type']}")
        #pprint(inital)
        return inital
            
    
    def form_valid(self, form):
        form.instance.symbol = self.request.GET.get('symbol')
        form.instance.type = self.request.GET.get('type')
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


class NewTradesView(TemplateView):
    template_name = "blog/new_trades.html"

    def get(self, request, *args, **kwargs):
        # Either recompute:
        diff = filter_positions(request)
        # …or pull from session if you stored it there in login
        return self.render_to_response(diff)
