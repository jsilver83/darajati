from . import views
from django.views.generic import TemplateView
from django.conf.urls import url

app_name = 'enrollment'

# Instructor
urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^instructor/$', views.InstructorView.as_view(), name='instructor'),
    url(r'^student/section/(?P<section_id>[0-9]+)/$', views.SectionStudentView.as_view(),
        name='section_students'),
]

# Coordinator
urlpatterns += [
    url(r'^coordinator/$', views.CoordinatorView.as_view(), name='coordinator'),
    url(r'^coordinator/course/(?P<course_offering_id>[0-9]+)/$', views.CoordinatorSectionView.as_view(),
        name='course_coordinator'),
    url(r'^coordinator/grade-fragment/(?P<course_offering_id>[0-9]+)/$', views.CoordinatorGradeFragmentView.as_view(),
        name='grade_fragment_coordinator'),
    url(r'^coordinator/grade-fragment/(?P<course_offering_id>[0-9]+)/edit/(?P<pk>[0-9]+)/$',
        views.CoordinatorEditGradeFragmentView.as_view(),
        name='update_grade_fragment_coordinator'),
    url(r'^coordinator/grade-fragment/(?P<course_offering_id>[0-9]+)/create/$',
        views.CoordinatorCreateGradeFragmentView.as_view(),
        name='create_grade_fragment_coordinator'),
    url(r'^coordinator/section/(?P<section_id>[0-9]+)/$', views.CoordinatorView.as_view(), name='section_coordinator'),

]

# Admin
urlpatterns += [
    url(r'^controls/$', views.AdminControlsView.as_view(), name='controls'),
]

# Others
urlpatterns += [
    url(r'^unauthorized/$', TemplateView.as_view(template_name='unauthorized.html'), name='unauthorized'),
]
