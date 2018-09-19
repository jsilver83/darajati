from . import views
from django.urls import re_path

app_name = 'attendance'

urlpatterns = [
    re_path(r'^section/(?P<section_id>[0-9]+)/$', views.AttendanceView.as_view(),
        {'year': None, 'month': None, 'day': None}, name='section_attendance'),

    re_path(r'^section/(?P<section_id>[0-9]+)/(?P<year>[0-9]{4})-(?P<month>[0-9]{1,2})-(?P<day>[0-9]{1,2})/$',
        views.AttendanceView.as_view(),
        name='section_day_attendance'),
    re_path(r'summary/(?P<section_id>[0-9]+)/(?P<enrollment_id>[0-9]+)',
        views.StudentAttendanceSummaryView.as_view(),
        name='attendance_summary')
]
