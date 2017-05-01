from . import views
from django.conf.urls import url

app_name = 'attendance'

urlpatterns = [
    url(r'^section/(?P<section_id>[0-9]+)/$', views.AttendanceView.as_view(),
        {'day': None}, name='section_attendance'),

    url(r'^section/(?P<section_id>[0-9]+)/(?P<day>[A-Za-z]+)/$', views.AttendanceView.as_view(),
        name='section_day_attendance'),
]
