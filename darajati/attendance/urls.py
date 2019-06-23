from django.urls import path

from . import views

app_name = 'attendance'

urlpatterns = [
    path('section/<int:section_id>/', views.AttendanceView.as_view(),
         {'year': None, 'month': None, 'day': None}, name='section_attendance'),
    path('section/<int:section_id>/<int:year>-<int:month>-<int:day>/',
         views.AttendanceView.as_view(),
         name='section_day_attendance'),

    path('summary/<int:section_id>/<int:enrollment_id>/',
         views.StudentAttendanceSummaryView.as_view(),
         name='attendance_summary'),

    # path('print/section/<int:section_id>/', views.AttendancePrintView.as_view(), name='section_attendance_print'),
    path('print/section/<int:section_id>/', views.attendance_print_sheet, name='section_attendance_print'),

    path('excuses/', views.ExcusesListingView.as_view(), name='excuses_listing'),
    path('excuse-entry/', views.ExcuseEntryView.as_view(), name='excuse_entry'),
    path('excuse-entry-confirm/<int:pk>/', views.ExcuseEntryConfirm.as_view(), name='excuse_entry_confirm'),
]
