from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView


app_name = 'accounts'
urlpatterns = [
    path('signup/', UserRegistrationView.as_view()),
    path('signin/', UserLoginView.as_view()),
    path('signout/', LogoutView.as_view()),
]
