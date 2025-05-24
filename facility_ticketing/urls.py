from django.urls import path
from . import views

app_name = 'facility_ticketing'

urlpatterns = [
    path('manajemen-atraksi/', views.manajemen_atraksi, name='manajemen_atraksi'),
    path('manajemen-atraksi/tambah/', views.tambah_atraksi, name='tambah_atraksi'),
    path('manajemen-atraksi/edit/', views.edit_atraksi, name='edit_atraksi'),
    path('manajemen-atraksi/hapus/', views.hapus_atraksi, name='hapus_atraksi'),
    path('manajemen-wahana/', views.manajemen_wahana, name='manajemen_wahana'),
    path('manajemen-wahana/tambah/', views.tambah_wahana, name='tambah_wahana'),
    path('manajemen-wahana/edit/', views.edit_wahana, name='edit_wahana'),
    path('manajemen-wahana/hapus/', views.hapus_wahana, name='hapus_wahana'),
    path('reservasi-pengunjung/', views.reservasi_pengunjung, name='reservasi_pengunjung'),
    path('admin-reservasi/', views.admin_reservasi, name='admin_reservasi'),
]