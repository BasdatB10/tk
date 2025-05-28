from django.urls import path
from adoption_management.views import *

app_name = 'adoption_management'

urlpatterns = [
    path('', manage_adopt, name='manage_adopt'),  # URL default untuk manage_adopt
    path('daftar-adopter/', daftar_adopter, name='daftar_adopter'),
    path('daftar-user/', daftar_user, name='daftar_user'),
    path('cek-adopter/', cek_adopter, name='cek_adopter'),
    path('adopter-page/', show_adopter_page, name='adopter-page'),
    path('adopter-list/', show_adopter_list, name='adopter-list'),
    path('update-adopter-status/', update_adopter_status, name='update_adopter_status'),
    path('stop-adoption/', stop_adoption, name='stop_adoption'),
    path('delete-adopter/', delete_adopter, name='delete_adopter'),
]