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
    path('manage-adopt/', manage_adopt, name='manage-adopt'),
    path('adopter-page/', show_adopter_page, name='adopter-page'),
    path('adopter-list/', show_adopter_list, name='adopter-list'),
]