from . import views
from django.views.generic import TemplateView
from django.conf.urls import url

app_name = 'attendances_and_grades'

urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^instructor/$', views.InstructorView.as_view(), name='instructor'),
    url(r'^section/(?P<section_id>[0-9]+)/$', views.SectionView.as_view(), name='section'),
    url(r'^section/(?P<section_id>[0-9]+)/students/$', views.SectionStudentView.as_view(), name='section_students'),
    url(r'^unauthorized/$', TemplateView.as_view(template_name='unauthorized.html'), name='unauthorized'),
]
