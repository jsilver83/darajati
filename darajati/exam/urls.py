from django.conf.urls import url
from . import views

app_name = 'exam'

urlpatterns = [
    url(r'^course/(?P<course_offering_id>[0-9]+)/fragment/(?P<grade_fragment_id>[0-9]+)/'
        r'examiner-list/$',
        views.ExaminerListView.as_view(),
        name='examiner'
        ),

    url(r'^course/(?P<course_offering_id>[0-9]+)/fragment/(?P<grade_fragment_id>[0-9]+)/'
        r'add-examiner/$',
        views.ExaminerAddView.as_view(),
        name='add_examiner'
        ),

    url(r'^course/(?P<course_offering_id>[0-9]+)/fragment/(?P<grade_fragment_id>[0-9]+)/'
        r'edit-examiner/(?P<pk>[0-9]+)/$',
        views.ExaminerEditView.as_view(),
        name='edit_examiner'
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
