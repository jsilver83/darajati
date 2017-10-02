from . import views
from django.views.generic import TemplateView
from django.conf.urls import url

app_name = 'banner_integration'

urlpatterns = [
    url(r'^$', views.PopulationRosterView.as_view(), name='home'),
]
