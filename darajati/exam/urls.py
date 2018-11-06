from django.conf.urls import url
from . import views

app_name = 'exam'

urlpatterns = [
    url(r'^rooms/$',
        views.RoomListView.as_view(),
        name='list_rooms'
        ),

    url(r'^rooms/add/$',
        views.RoomAddView.as_view(),
        name='add_room'
        ),

    url(r'^rooms/(?P<room_id>[0-9]+)/edit/$',
        views.RoomEditView.as_view(),
        name='edit_room'
        ),

    url(r'^settings/(?P<grade_fragment_id>[0-9]+)/$',
        views.ExamSettingsView.as_view(),
        name='settings'
        ),

    url(r'^shifts/(?P<grade_fragment_id>[0-9]+)/$',
        views.ExamShiftsView.as_view(),
        name='shifts'
        ),

    url(r'^rooms/(?P<grade_fragment_id>[0-9]+)/$',
        views.ExamRoomsView.as_view(),
        name='exam_rooms'
        ),

    url(r'^markers/(?P<grade_fragment_id>[0-9]+)/$',
        views.MarkersView.as_view(),
        name='markers'
        ),

    url(r'^unaccepted/(?P<grade_fragment_id>[0-9]+)/$',
        views.UnacceptedStudentMarksView.as_view(),
        name='unaccepted_markers'
        ),
]
