from django.urls import path
from medical_checkup_feeding.views import *

app_name = 'medical_checkup_feeding'

urlpatterns = [
    path('medical_record/', medical_record, name='medical_record'),
    path('medical_checkup/', medical_checkup, name='medical_checkup'),
    path('feeding_schedule/', feeding_schedule, name='feeding_schedule'),
    path('feeding_history/', feeding_history, name='feeding_history'),
]