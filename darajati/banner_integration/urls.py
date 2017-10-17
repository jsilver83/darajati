from . import views
from django.views.generic import TemplateView
from django.conf.urls import url

app_name = 'banner_integration'

urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^synchronization/$', views.PopulationRosterView.as_view(), name='synchronization'),
    url(r'^grades/$', views.ImportGradesView.as_view(), name='import_grade'),
]
