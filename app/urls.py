
from django.urls import path
from .views import *
urlpatterns = [
    path('signup/',Signup.as_view()),
    path('login/',Login.as_view()),
    path('search-user/',SearchUser.as_view()),
    path('send-friend-request/',SendFriendRequest.as_view()),
    path('accept-friend-request/',AcceptFriendRequest.as_view()),
    path('reject-friend-request/',RejectFriendRequest.as_view()),
    path('list-friend/',ListFriends.as_view()),
    path('list-pending-request/',ListPendingFriendRequests.as_view()),

    
 


]   