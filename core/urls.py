from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('history/', views.history_view, name='history'),
    path('delete-summary/<int:summary_id>/', views.delete_summary, name='delete_summary'),
] 