from . import views
from django.views.generic import TemplateView
from django.conf.urls import url

app_name = 'attendance'

urlpatterns = [
    url(r'^section/(?P<section_id>[0-9]+)/$', views.AttendanceView.as_view(),
        name='section_attendance'),
]
