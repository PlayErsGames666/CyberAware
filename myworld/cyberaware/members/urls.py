from django.urls import path
from . import views

urlpatterns = [
    path('', views.members, name='members'),
    path('login/', views.login_view, name='login'),
]


