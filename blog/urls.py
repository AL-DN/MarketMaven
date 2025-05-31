from django.urls import path
from . import views
from .views import NewPositionsView, PostListView, PostDetailView, PostCreateView, PostUpdateView, PostDeleteView, UserPostListView

urlpatterns = [
    path('', PostListView.as_view(), name='blog-home'),
    path('user/<str:username>', UserPostListView.as_view(), name='user-post'),
    # uses var to navigate to specific post
    path('post/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('post/new/<int:pk>/', PostCreateView.as_view(), name='post-create'),
    path('about/', views.about, name='blog-about'),
    path('positions/new/', NewPositionsView.as_view(), name='new-positions'),
    path('positions/dismiss/<int:pk>/', views.dismiss_position, name='dismiss-position')
]   