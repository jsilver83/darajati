from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from enrollment.models import Semester
from enrollment.models import Course
from enrollment.models import Enrollment
from enrollment.models import Section

class GradesPlan(models.Model):
    semester = models.ForeignKey( Semester, _('Semester'), related_name="grades_plan", null=True, blank=False)
    grade_category = models.CharField(_('Grade Category'), max_length=100, null=True, blank=False)
    grade_description = models.CharField(_('Grade Description'), max_length=100, null=True, blank=False)
    grade_quantity = models.FloatField(_('Grade Quantity'), null=True, blank=False, default=0.0)
    grade_type = models.CharField(_('Grade Type'), max_length=1)
    show_flag = models.BooleanField(_('Display'))
    display_order = models.CharField(_('Display Order'), max_length=50)
    show_in_teacher_report = models.BooleanField(_('Show in Teacher Report'))
    show_in_student_report = models.BooleanField(_('Show in Student Report'))
    grade_boundries_type = models.CharField(_('Boundry Type'), max_length=1)
    allow_grade_change = models.BooleanField(_('Allow Grade Change'))
    grade_boundries_value = models.FloatField(_('Grade Boundry Value'))
    grade_boundries_value2 = models.FloatField(_('Grade Boundry Value'))
    allow_subjective_marking = models.BooleanField(_('Allow Subjective Marking'))


class LetterGrade(models.Model):
    semester = models.ForeignKey(Semester, _('Semester'), related_name="letter_grade", null=True, blank=False)
    course = models.ForeignKey(Course, _('Course'), related_name="letter_grade", null=True, blank=False)
    letter_grade = models.CharField(_('Letter Grade'), max_length=2)
    cut_off_point = models.FloatField(_('Cut off Point'), null=True, blank=False, default=0.0)


class StudentGrade(models.Model):
    enrollment = models.ForeignKey(Enrollment, _('Enrolled Student'), related_name="student_grade", null=True, blank=False)
    grade_plan = models.ForeignKey(GradesPlan, _('Grade Plan'), related_name="student_grade", null=True, blank=False)
    grade = models.FloatField(_('Grade'), null=True, blank=False, default=0.0)
    instructor_remarks = models.CharField(_('Instructor Remarks'), max_length=1500)


class SectionGradePlan(models.Model):
    grade_plan = models.ForeignKey(GradesPlan, _('Grade Plan'), related_name="section_grade_plan", null=True, blank=False)
    course = models.ForeignKey(Course, _('Course'), related_name="section_grade_plan", null=True, blank=False)
    section = models.ForeignKey(Section, _('Section'), related_name="section_grade_plan")
