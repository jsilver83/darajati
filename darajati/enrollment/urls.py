from . import views
from django.views.generic import TemplateView
from django.conf.urls import url

app_name = 'enrollment'

urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^instructor/$', views.InstructorView.as_view(), name='instructor'),
    url(r'^student/section/(?P<section_id>[0-9]+)/$', views.SectionStudentView.as_view(),
        name='section_students'),
    url(r'^controls/$', views.AdminControlsView.as_view(), name='controls'),
    url(r'^unauthorized/$', TemplateView.as_view(template_name='unauthorized.html'), name='unauthorized'),

    # Coordinator
    url(r'^coordinator/$', views.CoordinatorView.as_view(), name='coordinator'),
    url(r'^coordinator/course/(?P<course_offering_id>[0-9]+)/$', views.CoordinatorSectionView.as_view(),
        name='course_coordinator'),
    url(r'^coordinator/section/(?P<section_id>[0-9]+)/$', views.CoordinatorView.as_view(), name='section_coordinator'),

]
