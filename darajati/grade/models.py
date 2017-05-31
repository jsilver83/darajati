from django.db import models
from django.db.models import Sum, Count
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from enrollment.utils import to_string

User = settings.AUTH_USER_MODEL


class GradeBreakDown(models.Model):
    class Meta:
        ordering = ['order']

    class GradesBoundaries:
        OBJECTIVE = 'OBJECTIVE'
        SUBJECTIVE_BOUNDED = 'SUBJECTIVE_BOUNDED'
        SUBJECTIVE_BOUNDED_FIXED = 'SUBJECTIVE_BOUNDED_FIXED'
        SUBJECTIVE_FREE = 'SUBJECTIVE_FREE'

        @classmethod
        def choices(cls):
            return (
                (cls.OBJECTIVE, _('Objective')),
                (cls.SUBJECTIVE_BOUNDED, _('Subjective Bounded')),
                (cls.SUBJECTIVE_BOUNDED_FIXED, _('Subjective Bounded Fixed')),
                (cls.SUBJECTIVE_FREE, _('Subjective Free')),
            )

    semester = models.ForeignKey('enrollment.Semester', related_name="grades_break_down", null=True, blank=False)
    course = models.ForeignKey('enrollment.Course', related_name="grades_break_down", null=True, blank=False)
    section = models.ForeignKey('enrollment.Section', related_name="grades_break_down", null=True, blank=True)
    category = models.CharField(_('Category'), max_length=100, null=True, blank=False,
                                help_text='Categories are like: Quiz, Midterm, Final Exam etc..')
    description = models.CharField(_('Description'), max_length=100, null=True, blank=False)
    weight = models.FloatField(_('Weight'), null=True, blank=False, default=0.0)
    allow_entry = models.BooleanField(_('Allow Entry'), null=False, blank=False, default=True,
                                      help_text=_('Allowing instructor to enter the marks for this grade break down'))
    order = models.PositiveSmallIntegerField(_('Display Order'), null=True, blank=False,
                                             help_text=_('The order of which grade break down should show up first'))
    show_teacher_report = models.BooleanField(_('Show in Teacher Report'), null=False, blank=False, default=True)
    show_student_report = models.BooleanField(_('Show in Student Report'), null=False, blank=False, default=True)
    boundary_type = models.CharField(_('Boundary Type'), max_length=20, choices=GradesBoundaries.choices(),
                                     null=True, blank=False, default=GradesBoundaries.SUBJECTIVE_FREE)
    boundary_range = models.FloatField(_('Boundary Range'), null=True, blank=True,
                                       help_text=_('When the type is subjective and it is not free, give a range +-'))
    boundary_fixed_average = models.FloatField(_('Boundary Fixed Average'), null=True, blank=True)
    allow_change = models.BooleanField(_('Allow Change After Submission'), null=False, blank=False, default=True)
    allow_subjective_marking = models.BooleanField(_('Allow Subjective Marking'), null=False, blank=False,
                                                   default=False)
    entry_in_percentages = models.BooleanField(_('Entry in Percentages'), null=False, blank=True, default=False,
                                               help_text=_('Checked when the course entered grades are in %'))
    updated_by = models.ForeignKey('enrollment.UserProfile', related_name='grades_break_down')
    updated_on = models.DateField(_('Updated On'), auto_now=True)

    @staticmethod
    def get_grade_break_down(grade_break_down_id):
        try:
            return GradeBreakDown.objects.get(id=grade_break_down_id)
        except:
            return None

    @staticmethod
    def get_section_grade_break_down(section):
        if section.course.coordinated:
            return GradeBreakDown.objects.filter(course=section.course, allow_entry=True)
        return GradeBreakDown.objects.filter(section=section.id, allow_entry=True)

    def __str__(self):
        return to_string(self.course, self.category, self.description)


class LetterGrade(models.Model):
    semester = models.ForeignKey('enrollment.Semester', related_name="letter_grades", null=True, blank=False)
    course = models.ForeignKey('enrollment.Course', related_name="letter_grades", null=True, blank=False)
    section = models.ForeignKey('enrollment.Section', related_name="letter_grades", null=True, blank=True)
    letter_grade = models.CharField(_('Letter Grade'), max_length=5, null=True, blank=False)
    cut_off_point = models.FloatField(_('Cut off Point'), null=True, blank=False, default=0.0)
    updated_by = models.ForeignKey('enrollment.UserProfile', related_name='letter_grade', default=0)
    updated_on = models.DateField(_('Updated On'), auto_now=True)

    def __str__(self):
        return to_string(self.course, self.section, self.letter_grade)


class StudentGrade(models.Model):
    class Meta:
        unique_together = ('enrollment', 'grade_break_down')

    enrollment = models.ForeignKey('enrollment.Enrollment', on_delete=models.CASCADE, related_name="grades", null=True,
                                   blank=False)
    grade_break_down = models.ForeignKey(GradeBreakDown, on_delete=models.CASCADE, related_name="grades", null=True,
                                         blank=False)
    grade_quantity = models.DecimalField(_('Student Grade Quantity'), null=True, blank=False,
                                         decimal_places=4,
                                         max_digits=7)
    remarks = models.CharField(_('Instructor Remarks'), max_length=100, null=True, blank=True)
    updated_by = models.ForeignKey('enrollment.UserProfile', related_name='grades', default=0)
    updated_on = models.DateField(_('Updated On'), auto_now=True)

    @staticmethod
    def get_section_break_down_grades(section_id, grade_break_down_id):
        return StudentGrade.objects.filter(enrollment__section=section_id, grade_break_down=grade_break_down_id)

    @staticmethod
    def get_section_average(section, grade_break_down):
        grades = StudentGrade.objects.filter(
            grade_break_down=grade_break_down, enrollment__section=section
        ).values().aggregate(
            sum=Sum('grade_quantity'),
            count=Count('id'),
        )
        return grades

    @staticmethod
    def get_section_objective_average(section):
        pass

    @staticmethod
    def get_course_average(section):
        pass

    def __str__(self):
        return to_string(self.enrollment, self.grade_break_down, self.remarks)
