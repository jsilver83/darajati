from django.urls import re_path
from . import views

app_name = 'exam'

urlpatterns = [
    re_path(r'^rooms/$',
        views.RoomListView.as_view(),
        name='list_rooms'
        ),

    re_path(r'^rooms/add/$',
        views.RoomAddView.as_view(),
        name='add_room'
        ),

    re_path(r'^rooms/(?P<room_id>[0-9]+)/edit/$',
        views.RoomEditView.as_view(),
        name='edit_room'
        ),

    re_path(r'^settings/(?P<exam_settings_id>[0-9]+)/$',
        views.ExamSettingsView.as_view(),
        name='settings'
        ),

    re_path(r'^shifts/(?P<exam_settings_id>[0-9]+)/$',
        views.ExamShiftsView.as_view(),
        name='shifts'
        ),

    re_path(r'^rooms/(?P<exam_settings_id>[0-9]+)/$',
        views.ExamRoomsView.as_view(),
        name='exam_rooms'
        ),

    re_path(r'^markers/(?P<exam_settings_id>[0-9]+)/$',
        views.MarkersView.as_view(),
        name='markers'
        ),

    re_path(r'^marks/(?P<marker_id>[0-9]+)/$',
        views.StudentMarksView.as_view(),
        name='marks'
        ),

    re_path(r'^unaccepted/(?P<exam_settings_id>[0-9]+)/$',
        views.UnacceptedStudentMarksView.as_view(),
        name='unaccepted_markers'
        ),
]
