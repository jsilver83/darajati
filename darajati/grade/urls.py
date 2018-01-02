from . import views
from django.conf.urls import url

app_name = 'grade'

urlpatterns = [
    url(r'^section/(?P<section_id>[0-9]+)/$',
        views.GradeFragmentView.as_view(),
        name='section_grade'),

    url(r'^section/(?P<section_id>[0-9]+)/(?P<grade_fragment_id>[0-9]+)/$',
        views.GradesView.as_view(),
        name='plan_grades'),

    url(r'^section/(?P<section_id>[0-9]+)/(?P<grade_fragment_id>[0-9]+)/view/$',
        views.DisplayGradesView.as_view(),
        name='view_grades'),

    url(r'^section/(?P<section_id>[0-9]+)/create-grade-plan/$',
        views.CreateGradeFragmentView.as_view(),
        name='create_grade_fragment'),

    url(r'^section/(?P<section_id>[0-9]+)/grades-report/$',
        views.GradeReportView.as_view(),
        name='section_grade_report'),
]
