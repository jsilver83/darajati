from django.conf.urls import url
from . import views


app_name = 'exam'

urlpatterns = [
    url(r'^subjective-marking/course/(?P<course_offering_id>[0-9]+)/$', views.SubjectiveMarkView.as_view(), name='subjective_marking'),
]
