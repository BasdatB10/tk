from django.urls import path
from animal_habitat_management.views import *

app_name = 'animal_habitat_management'

urlpatterns = [
    path('animal/', animal, name='animal'),
    path('habitat/', habitat, name='habitat'),
    path('habitat-detail/', habitat_detail, name='habitat_detail'),
]