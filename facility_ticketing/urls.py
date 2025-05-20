from django.urls import path
from facility_ticketing.views import *

app_name = 'facility_ticketing'

from django.urls import path
from . import views

urlpatterns = [
    path('manajemen-atraksi/', views.manajemen_atraksi, name='manajemen_atraksi'),
    path('manajemen-wahana/', views.manajemen_wahana, name='manajemen_wahana'),
    path('reservasi-pengunjung/', views.reservasi_pengunjung, name='reservasi_pengunjung'),
    path('admin-reservasi/', views.admin_reservasi, name='admin_reservasi'),
]