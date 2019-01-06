from django.urls import re_path
from django.views.generic import TemplateView

from . import views

app_name = 'enrollment'

# Instructor
urlpatterns = [
    re_path(r'^$', views.HomeView.as_view(), name='home'),
    re_path(r'^instructor/$', views.InstructorView.as_view(), name='instructor'),
    re_path(r'^student/section/(?P<section_id>[0-9]+)/$', views.SectionStudentView.as_view(),
        name='section_students'),
]

# Coordinator
urlpatterns += [
    re_path(r'^coordinator/$', views.CoordinatorView.as_view(), name='coordinator'),
    re_path(r'^coordinator/course/(?P<course_offering_id>[0-9]+)/$', views.CoordinatorSectionView.as_view(),
            name='course_coordinator'),
    re_path(r'^coordinator/grade-fragment/(?P<course_offering_id>[0-9]+)/$',
            views.CoordinatorGradeFragmentView.as_view(),
            name='grade_fragment_coordinator'),
    re_path(r'^coordinator/grade-fragment/(?P<course_offering_id>[0-9]+)/import-fragments/$',
            views.ImportGradeFragmentsView.as_view(), name='import_fragments'),
    re_path(r'^coordinator/grade-fragment/(?P<course_offering_id>[0-9]+)/edit/(?P<pk>[0-9]+)/$',
            views.CoordinatorEditGradeFragmentView.as_view(),
            name='update_grade_fragment_coordinator'),
    re_path(r'^coordinator/grade-fragment/(?P<course_offering_id>[0-9]+)/delete/(?P<pk>[0-9]+)/$',
            views.CoordinatorDeleteGradeFragmentView.as_view(),
            name='delete_grade_fragment_coordinator'),
    re_path(r'^coordinator/grade-fragment/(?P<course_offering_id>[0-9]+)/create/$',
            views.CoordinatorCreateGradeFragmentView.as_view(),
            name='create_grade_fragment_coordinator'),
    re_path(r'^coordinator/section/(?P<section_id>[0-9]+)/$', views.CoordinatorView.as_view(),
            name='section_coordinator'),
    re_path(r'^coordinator/grades/(?P<course_offering_id>[0-9]+)/(?P<grade_fragment_id>[0-9]+)/import-grade/$',
            views.ImportGradesView.as_view(), name='import_grade'),
]

# Admin
urlpatterns += [
    re_path(r'^controls/$', views.AdminControlsView.as_view(), name='controls'),
]

# Others
urlpatterns += [
    re_path(r'^unauthorized/$', TemplateView.as_view(template_name='unauthorized.html'), name='unauthorized'),
]
