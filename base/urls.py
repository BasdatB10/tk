import profile
from django.urls import include, path
from base.views import *
from adoption_management.views import *

app_name = 'base'

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('adoption/', include('adoption_management.urls')),
]