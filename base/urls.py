from django.urls import path
from base.views import *

app_name = 'base'

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('profile/', profile, name='profile'),
    path('profile_dokter/', profile_dokter, name='profile_dokter'),
    path('profile_pengunjung/', profile_pengunjung, name='profile_pengunjung'),
    path('profile_staff/', profile_staff, name='profile_staff'),
]