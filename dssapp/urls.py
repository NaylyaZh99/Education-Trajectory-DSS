from django.urls import path

from . import views

urlpatterns = [
    # ex: /polls/
    path('', views.upload_file, name='upload_file'),
    path('parameters/', views.fill_params, name='fill_params'),
    path('assessment/', views.assessment, name='assessment'),
    path('result/', views.result_trajectory, name='result_trajectory'),
]