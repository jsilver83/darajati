from . import views
from django.views.generic import TemplateView
from django.conf.urls import url

app_name = 'grade'

urlpatterns = [
    url(r'^section/(?P<section_id>[0-9]+)/$', views.GradeBreakDownView.as_view(), name='section_grade'),
    url(r'^section/(?P<section_id>[0-9]+)/(?P<grade_break_down_id>[0-9]+)$', views.BreakDownGradesView.as_view(),
        name='plan_grades'),
]
