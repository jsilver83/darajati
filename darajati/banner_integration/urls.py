from . import views
from django.conf.urls import url

app_name = 'banner_integration'

urlpatterns = [
    url(r'^synchronization/$', views.PopulationRosterView.as_view(), name='synchronization'),
    url(r'^grades/$', views.ImportGradesView.as_view(), name='import_grade'),
]
