from . import views
from django.urls import re_path

app_name = 'grade'

urlpatterns = [
    re_path(r'^section/(?P<section_id>[0-9]+)/$',
            views.GradeFragmentView.as_view(),
            name='section_grade'),

    re_path(r'^section/(?P<section_id>[0-9]+)/(?P<grade_fragment_id>[0-9]+)/$',
            views.GradesView.as_view(),
            name='plan_grades'),

    re_path(r'^section/(?P<section_id>[0-9]+)/(?P<grade_fragment_id>[0-9]+)/view/$',
            views.DisplayGradesView.as_view(),
            name='view_grades'),

    re_path(r'^section/(?P<section_id>[0-9]+)/create-grade-plan/$',
            views.CreateGradeFragmentView.as_view(),
            name='create_grade_fragment'),

    # re_path(r'^section/(?P<section_id>[0-9]+)/grades-report/$',
    #         views.GradeReportView.as_view(),
    #         name='section_grade_report'),

    re_path(r'^letter-grades/(?P<course_offering_id>[0-9]+)/$',
            views.LetterGradesView.as_view(), name='letter_grades'),
]
