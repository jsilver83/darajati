from . import views
from django.urls import re_path

app_name = 'banner_integration'

urlpatterns = [
    re_path(r'^synchronization/$', views.PopulationRosterView.as_view(), name='synchronization'),
    re_path(r'^grades/$', views.ImportGradesView.as_view(), name='import_grade'),
]
