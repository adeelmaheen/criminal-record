from django.urls import path
from . import views

app_name = 'scraper'

urlpatterns = [
    path('', views.record_list, name='record_list'),
    path('<int:pk>/', views.record_detail, name='record_detail'),
]

