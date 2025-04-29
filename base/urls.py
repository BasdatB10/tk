from django.urls import path
from base.views import *
from adoption_management.views import *

app_name = 'base'

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('dashboard/', dashboard,name='dashboard') , 
    path('profile/', profile, name='profile'),
    path('profile_dokter/', profile_dokter, name='profile_dokter'),
    path('profile_pengunjung/', profile_pengunjung, name='profile_pengunjung'),
    path('profile_staff/', profile_staff, name='profile_staff'),
    path('manage-adopt/', manage_adopt, name='manage-adopt'),
    path('adopter-page/', show_adopter_page, name='adopter-page'),
    path('adopter-list/', show_adopter_list, name='adopter-list'),
]