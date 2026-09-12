from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.customer_login, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('transfer/', views.transfer_page, name='transfer'),
    path('transfer/submit/', views.transfer_submit, name='transfer_submit'),
    path('my-account/', views.my_account, name='my_account'),
    path('change-password/', views.change_password, name='change_password'),

    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/users/<int:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
]
