from django.conf.urls import url
from . import views

app_name = 'exam'

urlpatterns = [
    url(r'^course/(?P<course_offering_id>[0-9]+)/fragment/(?P<grade_fragment_id>[0-9]+)/'
        r'exam-list/$',
        views.ExamListView.as_view(),
        name='list_exams'
        ),

    url(r'^course/(?P<course_offering_id>[0-9]+)/fragment/(?P<grade_fragment_id>[0-9]+)/'
        r'add-exam/$',
        views.ExamAddView.as_view(),
        name='add_exam'
        ),

    url(r'^course/(?P<course_offering_id>[0-9]+)/fragment/(?P<grade_fragment_id>[0-9]+)/'
        r'edit-exam/(?P<exam_id>[0-9]+)$',
        views.ExamEditView.as_view(),
        name='edit_exam'
        ),

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
]
