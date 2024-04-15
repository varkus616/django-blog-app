from django.urls import path
from . import views

app_name="blog"
urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('', views.post_list, name='post_list'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/new/', views.post_new, name='post_new'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('register', views.MyRegistrationView.as_view(), name="register"),
    path('login', views.MyLoginView.as_view(), name="login"),
    path('logout', views.user_logout, name="logout"),
    path('users', views.UsersListView.as_view(), name="users"),
    path('profile/<str:username>/', views.ProfileDetailView.as_view(), name='profile'),
    path('profile/<str:username>/remove_friend', views.remove_friend, name='remove_friend'),
    path('profile/<str:username>/send_friend_invite', views.send_friend_invitation, name='send_friend_invitation'),
    path('profile/<str:username>/send_message', views.send_message, name='send_message'),
    path('profile/<str:username>/inbox/', views.InboxView.as_view(), name='inbox'),
    path('profile/inbox/delete_msg/<int:msg_pk>/', views.delete_msg, name='delete_msg'),
    path('profile/inbox/message/<str:username>/', views.accept_invitation, name='accept_invitation'),
]