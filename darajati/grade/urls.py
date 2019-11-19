from . import views
from django.urls import re_path, path

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

    re_path(r'^section/(?P<section_id>[0-9]+)/grades-report/$',
            views.GradeReportView.as_view(),
            name='section_grade_report'),

    re_path(r'^letter-grades/(?P<course_offering_id>[0-9]+)/$',
            views.LetterGradesView.as_view(), name='letter_grades'),

    path('letter-grades-promotion/<int:course_offering_id>/', views.LetterGradesPromotionView.as_view(),
         name='letter_grades_promotion'),

    path('letter-grades/<int:course_offering_id>/import/', views.ImportLetterGradesView.as_view(),
         name='letter_grades_import'),

    path('missing-grades-report/<int:course_offering_id>/', views.MissingGradesReportView.as_view(),
         name='missing_grades_report'),
]
