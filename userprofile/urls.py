from django.urls import path
from userprofile.views import *

app_name = 'userprofile'

urlpatterns = [
    path('profile_view/', profile_view, name='profile_view'),
    path('change_password/', change_password_view, name='change_password'),
]