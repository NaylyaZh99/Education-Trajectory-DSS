from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

from . import views

urlpatterns = [
    # ex: /polls/
    path('', views.upload_file, name='upload_file'),
    # path('parameters/', views.fill_params, name='fill_params'),
    path('assessment/', views.assessment, name='assessment'),
    path('result/', views.result_trajectory, name='result_trajectory'),
    path('i18n/', include('django.conf.urls.i18n')),
]