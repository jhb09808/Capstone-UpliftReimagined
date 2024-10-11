from django.urls import path
from . import views
from .views import home

urlpatterns = [
    path('volunteers/', views.volunteer_list, name='volunteer_list'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('', home, name='home'),
]
