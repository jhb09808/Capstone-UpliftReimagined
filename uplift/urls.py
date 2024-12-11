from django.urls import path
from . import views
from .views import home
from .views import proxy

urlpatterns = [
    path('view_shift_schedule/', views.view_shift_schedule, name='view_shift_schedule'),
    path('apply_for_shift/', views.apply_for_shift, name='apply_for_shift'),
    path('api/get_shifts/', views.get_shifts, name='get_shifts'),
    path('view_inventory/', views.view_inventory, name='view_inventory'),
    path('volunteers/', views.volunteer_list, name='volunteer_list'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('manage_users/', views.manage_users, name='manage_users'),
    path('manage_inventory/', views.manage_inventory, name='manage_inventory'),
    path('confirm_shifts/', views.confirm_shifts, name='confirm_shifts'),
    path('generate_reports/', views.generate_reports, name='generate_reports'),
    path('donate/', views.donate, name='donate'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('route/', views.route, name='route'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('get_volunteers/', views.get_volunteers, name='get_volunteers'),
    path('', home, name='home'),
    path('proxy/<path:path>', proxy, name='proxy'),
    path('shift/<int:shift_id>/edit/', views.edit_shift, name='edit_shift'),
    path('shift/<int:shift_id>/cancel/', views.cancel_shift, name='cancel_shift'),
    path('user/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('user/<int:user_id>/activate/', views.activate_user, name='activate_user'),
    path('user/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
    path('user/<int:user_id>/make_admin/', views.make_admin, name='make_admin'),
    path('user/<int:user_id>/remove_admin/', views.remove_admin, name='remove_admin'),
    path('inventory/update/<int:item_id>/', views.update_inventory_item, name='update_inventory_item'),
    path('inventory/delete/<int:item_id>/', views.delete_inventory_item, name='delete_inventory_item'),
    path('shift/<int:shift_id>/delete/', views.delete_shift, name='delete_shift'),
]
