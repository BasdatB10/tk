from django.urls import path
from animal_habitat_management.views import *

app_name = 'animal_habitat_management'

urlpatterns = [
    path('animal/', animal, name='animal'),
    path('animal_delete/', animal_delete, name='animal_delete'),
    path('habitat/', habitat, name='habitat'),
    path('habitat_delete/', habitat_delete, name='habitat_delete'),
    path('habitat/detail/', habitat_detail, name='habitat_detail'),
]