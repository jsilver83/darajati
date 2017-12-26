from math import *
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import User as User_model
from .types import RoundTypes
from .utils import to_string, now, today, attendance_boundary
from attendance.models import ScheduledPeriod, AttendanceInstance, Attendance
from simple_history.models import HistoricalRecords

User = settings.AUTH_USER_MODEL


class Semester(models.Model):
    start_date = models.DateField(_('Start date'))
    end_date = models.DateField(_('End date'))
    grade_fragment_deadline = models.DateField(
        _('Grade break down deadline date'),
        null=True,
        blank=False
    )
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return to_string(self.description, self.code)

    def check_is_accessible_date(self, date, offset_date):
        """
        :param date: the date which coordinator or instructor trying to access for attendance 
        :param offset_date: the allowed offset days to view
        :return: True if the given offset date is less than or equal to the date
        """
        if offset_date <= date and self.start_date <= date <= self.end_date:
            return True
        return False

    def can_create_grade_fragment(self):
        """
        :return: True if the deadline date is greater or equal to the current date else False 
        """
        return True if self.grade_fragment_deadline >= today() else False


class Department(models.Model):
    name = models.CharField(_('english name'), max_length=50, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=50, null=True, blank=False)
    code = models.CharField(max_length=10, null=True, blank=False)

    def __str__(self):
        return to_string(self.name, self.code)


class Course(models.Model):
    name = models.CharField(_('english name'), max_length=255, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=255, null=True, blank=False)
    department = models.ForeignKey(Department, related_name='courses', null=True, blank=False)
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return to_string(self.name, self.code)


class CourseOffering(models.Model):
    semester = models.ForeignKey(Semester, related_name='offering', on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='offering',
        null=True,
        blank=False
    )
    attendance_entry_window = models.PositiveIntegerField(
        _('attendance window'),
        null=True,
        blank=False,
        default=7
    )
    coordinated = models.BooleanField(blank=False, default=1)
    formula = models.CharField(
        _('Deduction formula'),
        max_length=200,
        null=True,
        blank=True,
        help_text=_('Formula to calculate the deduction value from students attendance')
    )
    allow_change = models.BooleanField(
        _('Allow changing after submitting attendance?'),
        blank=False,
        default=1,
        help_text=
        _('This if checked will allow the instructors to change the attendances after submitting')
    )
    total_rounding_type = models.CharField(
        _('Total Rounding Type'), max_length=50,
        choices=RoundTypes.choices(),
        null=True,
        blank=False,
        default=RoundTypes.NONE,
        help_text=_('Total grade rounding method for letter grade calculation')
    )

    def __str__(self):
        return to_string(self.semester, self.course)

    @staticmethod
    def get_course_offering(course_offering_id):
        """
        :param course_offering_id: an integer number which represent a id of course_offering 
        :return: an instance of that id
        """
        try:
            return CourseOffering.objects.get(id=course_offering_id)
        except CourseOffering.DoesNotExist:
            return None

    @staticmethod
    def get_current_course_offerings():
        """
        :return: current semester course_offering_id and course code 
        """
        return CourseOffering.objects.filter(
            semester__start_date__lte=now(),
            semester__end_date__gte=now()
        ).values_list('id', 'course__code')


class Section(models.Model):
    course_offering = models.ForeignKey(
        CourseOffering,
        related_name='sections',
        on_delete=models.CASCADE
    )
    code = models.CharField(max_length=20, null=True, blank=False)
    rounding_type = models.CharField(
        _('Rounding Type'),
        max_length=50,
        choices=RoundTypes.choices(),
        null=True,
        blank=False,
        default=RoundTypes.NONE,
        help_text=_('Total grade rounding method for letter grade calculation')
    )
    crn = models.CharField(_('CRN'), max_length=100, null=True, blank=False)
    active = models.BooleanField(_('Active'), default=False)

    def __str__(self):
        return to_string(self.course_offering, self.code)

    @property
    def attendance_entry_window(self):
        """
        :return: a integer defined attendance window if the course coordinator else 0  
        """
        if self.course_offering.coordinated:
            return self.course_offering.attendance_entry_window
        else:
            return 0


class Coordinator(models.Model):
    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name='coordinators',
        null=True,
        blank=False
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='coordinators',
        null=True,
        blank=False
    )

    def __str__(self):
        return to_string(self.course_offering, self.instructor)

