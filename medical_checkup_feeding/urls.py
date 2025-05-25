from django.urls import path
from medical_checkup_feeding.views import *

app_name = 'medical_checkup_feeding'

urlpatterns = [
    path('medical_record/', medical_record, name='medical_record'),
    path('medical_checkup/', medical_checkup, name='medical_checkup'),
    path('feeding_schedule/', feeding_schedule, name='feeding_schedule'),
    path('add_medical_record/', add_medical_record, name='add_medical_record'),
    path('edit_medical_record/<str:id_hewan>/<str:tanggal_pemeriksaan>/', edit_medical_record, name='edit_medical_record'),
    path('delete_medical_record/<str:id_hewan>/<str:tanggal_pemeriksaan>/', delete_medical_record, name='delete_medical_record'),
    path('add_checkup_schedule/', add_checkup_schedule, name='add_checkup_schedule'),
    path('edit_checkup_schedule/<str:id_hewan>/<str:tgl_pemeriksaan_selanjutnya>/', edit_checkup_schedule, name='edit_checkup_schedule'),
    path('edit_checkup_frequency/<str:id_hewan>/<str:tgl_pemeriksaan_selanjutnya>/', edit_checkup_frequency, name='edit_checkup_frequency'),
    path('delete_checkup_schedule/<str:id_hewan>/<str:tgl_pemeriksaan_selanjutnya>/', delete_checkup_schedule, name='delete_checkup_schedule'),
    path('add_feeding_schedule/', add_feeding_schedule, name='add_feeding_schedule'),
    path('edit_feeding_schedule/<str:id_hewan>/<str:jadwal>/', edit_feeding_schedule, name='edit_feeding_schedule'),
    path('delete_feeding_schedule/<str:id_hewan>/<str:jadwal>/', delete_feeding_schedule, name='delete_feeding_schedule'),
    path('give_feeding/<str:id_hewan>/<str:jadwal>/', give_feeding, name='give_feeding'),
    
]