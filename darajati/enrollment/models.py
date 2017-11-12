from math import *

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.contrib.auth.models import User as User_model

from .types import RoundTypes
from .utils import to_string, now, today, attendance_boundary

from attendance.models import ScheduledPeriod, AttendanceInstance, Attendance

from simple_history.models import HistoricalRecords

User = settings.AUTH_USER_MODEL


class Person(models.Model):
    """
    an abstract class that will be inherited by Student and Instructor
    """

    university_id = models.CharField(_('university id'), max_length=20, null=True, blank=True)
    government_id = models.CharField(_('government id'), max_length=20, null=True, blank=True)
    english_name = models.CharField(_('english name'), max_length=255, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=255, null=True, blank=False)
    mobile = models.CharField(_('mobile'), max_length=20, null=True, blank=True)
    personal_email = models.EmailField(_('personal email'), null=True, blank=False)
    active = models.BooleanField(_('is_active'), blank=False, default=False)

    @property
    def in_student(self):
        """
        :return: True if the current user is a student else False
        """
        pass

    @staticmethod
    def has_access(user):
        return Instructor.is_active(user=user) or Student.is_active(user=user)

    @staticmethod
    def is_instructor(user):
        """
        :return: True if the current user is an instructor else False
        """
        return Instructor.get_instructor(user=user)

    @staticmethod
    def is_coordinator(instructor):
        """
        :return: True if the current user is an instructor else False
        """
        return Coordinator.get_coordinator(instructor=instructor)

    @property
    def is_active(self):
        """
        :return: True if the user is active else is False
        """
        pass

    class Meta:
        abstract = True


class Student(Person):
    user = models.OneToOneField(User, related_name='student', null=True, blank=True)

    def __str__(self):
        return to_string(self.english_name, self.university_id)

    @staticmethod
    def is_active(user=None):
        """
        :return: True if the user is active else is False
        """
        try:
            return Student.objects.get(user=user).active
        except:
            return False

    @staticmethod
    def get_student(user=None):
        """
        :param user: current login user
        :return: True if student else False
        """
        try:
            return Student.objects.get(user=user)
        except:
            return False

    @staticmethod
    def is_student_exists(email):
        return Student.objects.filter(personal_email__exact=email).exists()

    @staticmethod
    def get_create_student(username, university_id, government_id, english_name, arabic_name, mobile, personal_email):
        user, created = User_model.objects.get_or_create(username=username)

        return Student.objects.get_or_create(
            user=user,
            university_id=university_id,
            government_id=government_id,
            english_name=english_name,
            arabic_name=arabic_name,
            mobile=mobile,
            personal_email=personal_email,
            active=True
        )


class Instructor(Person):
    user = models.OneToOneField(User, related_name='instructor', null=True, blank=True)

    def __str__(self):
        return to_string(self.english_name)

        # :TODO Function to get the email ID from the USER_AUTH_MODEL.

    @staticmethod
    def is_active(user=None):
        """
        :return: True if the user is active else is False
        """
        try:
            return Instructor.objects.get(user=user).active
        except:
            return False

    @staticmethod
    def get_instructor(user=None):
        """
        :param user: current login user
        :return: True if instructor else False
        """
        return Instructor.objects.filter(user=user).exists()

    @staticmethod
    def is_instructor_exists(email):
        return Instructor.objects.filter(personal_email__exact=email).exists()


class Semester(models.Model):
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'))
    grade_fragment_deadline = models.DateField(_('Grade Break Down Deadline Date'),
                                               null=True, blank=False)
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return to_string(self.description, self.code)

    @property
    def can_create_grade_fragment(self):
        return True if self.grade_fragment_deadline >= today() else False


class Department(models.Model):
    name = models.CharField(_('english name'), max_length=50, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=50, null=True, blank=False)
    code = models.CharField(max_length=10, null=True, blank=False)

    def __str__(self):
        return to_string(self.name, self.code)


class Course(models.Model):
    # TODO: Attendance Deduction Formula
    name = models.CharField(_('english name'), max_length=255, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=255, null=True, blank=False)
    department = models.ForeignKey(Department, related_name='courses', null=True, blank=False)
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return to_string(self.name, self.code)


class CourseOffering(models.Model):
    semester = models.ForeignKey(Semester, related_name='offering', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offering', null=True, blank=False)
    attendance_entry_window = models.PositiveIntegerField(_('attendance window'), null=True, blank=False, default=7)
    coordinated = models.BooleanField(blank=False, default=1)
    formula = models.CharField(_('Deduction formula'), max_length=200, null=True, blank=True,
                               help_text=_('Formula to calculate the deduction value from students attendance'))
    allow_change = models.BooleanField(_('Allow changing after submitting attendance?'),
                                       blank=False,
                                       default=1,
                                       help_text=
                                       _('This if checked will allow the instructors'
                                         ' to change the attendances after submitting'))
    total_rounding_type = models.CharField(_('Total Rounding Type'), max_length=50, choices=RoundTypes.choices(),
                                           null=True,
                                           blank=False,
                                           default=RoundTypes.NONE,
                                           help_text=_('Total grade rounding method for letter grade calculation'))

    def __str__(self):
        return to_string(self.semester, self.course)

    @staticmethod
    def get_course_offering(course_offering_id):
        return CourseOffering.objects.get(id=course_offering_id)

    @staticmethod
    def get_current_course_offerings():
        return CourseOffering.objects.filter(
            semester__start_date__lte=now(),
            semester__end_date__gte=now()
        ).values_list('id', 'course__code')


class Section(models.Model):
    course_offering = models.ForeignKey(CourseOffering, related_name='sections', on_delete=models.CASCADE)
    code = models.CharField(max_length=20, null=True, blank=False)
    rounding_type = models.CharField(_('Rounding Type'), max_length=50, choices=RoundTypes.choices(), null=True,
                                     blank=False,
                                     default=RoundTypes.NONE,
                                     help_text=_('Total grade rounding method for letter grade calculation'))
    crn = models.CharField(_('CRN'), max_length=100, null=True, blank=False)
    active = models.BooleanField(_('Active'), default=False)

    def __str__(self):
        return to_string(self.course_offering, self.code)

    @property
    def attendance_entry_window(self):
        if self.course_offering.coordinated:
            return self.course_offering.attendance_entry_window
        else:
            return 0

    @staticmethod
    def get_section(section_id):
        """
        :param section_id:
        :return: an object of the giving section_id
        """
        try:
            return Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return None

    @staticmethod
    def get_sections():
        """
        :return: objects of all sections
        """
        return Section.objects.filter(course_offering__semester__start_date__lte=now(),
                                      course_offering__semester__end_date__gte=now()).distinct()

    @staticmethod
    def get_instructor_sections(instructor):
        """
        :param instructor: current login user
        :return: a unique list of section objects for the login user and for the current semester
        """
        return Section.objects.filter(scheduled_periods__instructor_assigned=instructor,
                                      scheduled_periods__section__course_offering__semester__start_date__lte=now(),
                                      scheduled_periods__section__course_offering__semester__end_date__gte=now()
                                      ).distinct()

    def is_instructor_section(self, instructor):
        """
        :param instructor: current login user
        :return: return true if this is the instructor of this section
        """
        return Section.objects.filter(id=self.id, scheduled_periods__instructor_assigned=instructor,
                                      scheduled_periods__section__course_offering__semester__start_date__lte=now(),
                                      scheduled_periods__section__course_offering__semester__end_date__gte=now()
                                      ).distinct().exists()

    def is_coordinator_section(self, instructor):
        """
        :param instructor: current login user
        :return: 
        """
        return Coordinator.objects.filter(
            instructor=instructor,
            course_offering=self.course_offering,
            course_offering__semester__start_date__lte=now(),
            course_offering__semester__end_date__gte=now()
        ).exists()

    @staticmethod
    def is_section_exists(course_offering, section_code):
        return Section.objects.filter(course_offering__exact=course_offering,
                                      code__exact=section_code).exists()

    @staticmethod
    def get_create_section(course_offering, code, crn):
        return Section.objects.get_or_create(
            course_offering=course_offering,
            code=code,
            crn=crn,
        )


class Coordinator(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='coordinators',
                                        null=True, blank=False)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='coordinators',
                                   null=True, blank=False)

    def __str__(self):
        return to_string(self.course_offering, self.instructor)

    @staticmethod
    def get_coordinator(instructor=None):
        return Coordinator.objects.filter(instructor=instructor).exists()

    @staticmethod
    def is_coordinator_course_offering(instructor, course_offering):
        return Coordinator.objects.filter(
            course_offering=course_offering,
            instructor=instructor,
            course_offering__semester__start_date__lte=now(),
            course_offering__semester__end_date__gte=now(),
        ).distinct().exists()


class Enrollment(models.Model):
    class Meta:
        unique_together = ('student', 'section')
        ordering = ['student__university_id']

    student = models.ForeignKey(Student, related_name='enrollments', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='enrollments', on_delete=models.CASCADE)
    active = models.BooleanField(_('Active'), blank=False, default=True)
    comment = models.CharField(_('Comment'), max_length=200, blank=True)
    letter_grade = models.CharField(_('letter grade'), max_length=20, null=True, blank=False, default='UD')
    register_date = models.DateTimeField(_('Enrollment Date'), null=True, blank=False)
    updated_by = models.ForeignKey(User, related_name='enrollment_creator', null=True, blank=False)
    updated_on = models.DateTimeField(_('Updated on'), auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return to_string(self.id)

    @property
    def _history_user(self):
        return self.updated_by

    @_history_user.setter
    def _history_user(self, value):
        self.updated_by = value

    @property
    def _history_date(self):
        return self.updated_on

    @_history_date.setter
    def _history_date(self, value):
        self.updated_on = value

    @property
    def get_letter_grade(self):
        return self.letter_grade if self.letter_grade else "UD"

    @staticmethod
    def get_students(section_id):
        """
        :return: list of all students for a giving section ID
        """
        return Enrollment.objects.filter(section=section_id)

    @staticmethod
    def is_enrollment_exists(student, section):
        return Enrollment.objects.filter(student=student, section=section).exists()

    @staticmethod
    def get_create_enrollment(student, section, register_date):
        return Enrollment.objects.get_or_create(
            student=student,
            section=section,
            register_date=parse_datetime(register_date)
        )

    @staticmethod
    def get_students_enrollment(section_id, date, instructor):
        """
        :param section_id: 
        :param date:
        :param instructor:
        :return: list of enrollments for a giving section_id and a day and instructor
           If the giving day is not exist get the nearest one
        """

        enrollments = []
        index = 1
        day, period_date, periods = ScheduledPeriod.get_section_periods_of_nearest_day(section_id, date, instructor)
        enrollment_list = Enrollment.get_students(section_id)
        count_index = 0
        for enrollment in enrollment_list:
            if enrollment.active is False:
                count_index += 1
                continue
            else:
                count_index += 1

            for period in periods:
                id = 0
                updated_by = None
                updated_on = None
                attendance_instance, created = AttendanceInstance.objects.get_or_create(period=period, date=period_date)
                try:
                    attendance = Attendance.objects.get(enrollment=enrollment, attendance_instance=attendance_instance)
                    status = attendance.status
                    updated_by = attendance.updated_by
                    updated_on = attendance.updated_on
                    id = attendance.id
                except Attendance.DoesNotExist:
                    status = Attendance.Types.PRESENT

                enrollments.append(dict(enrollment=enrollment,
                                        student_name=enrollment.student.english_name,
                                        enrollment_id=count_index,
                                        student_university_id=enrollment.student.university_id,
                                        period=period,
                                        attendance_instance=attendance_instance,
                                        status=status,
                                        id=id,
                                        index=index,
                                        updated_by=updated_by,
                                        updated_on=updated_on))
            index += 1
        return enrollments

    @property
    def get_enrollment_total_absence(self):
        return Attendance.objects.filter(
            enrollment__id=self.id,
            status=Attendance.Types.ABSENT).count()

    @property
    def get_enrollment_total_late(self):
        return Attendance.objects.filter(
            enrollment__id=self.id,
            status=Attendance.Types.LATE).count()

    def get_enrollment_period_total_absence(self, period_title):
        return Attendance.objects.filter(
            enrollment__id=self.id,
            attendance_instance__period__title=period_title,
            status=Attendance.Types.ABSENT).count()

    def get_enrollment_period_total_late(self, period_title):
        return Attendance.objects.filter(
            enrollment__id=self.id,
            attendance_instance__period__title=period_title,
            status=Attendance.Types.LATE).count()

    def get_enrollment_period_total_excused(self, period_title):
        return Attendance.objects.filter(
            enrollment__id=self.id,
            attendance_instance__period__title=period_title,
            status=Attendance.Types.EXCUSED).count()

    @property
    def get_enrollment_total_deduction(self):
        result = 0
        formula = self.section.course_offering.formula
        if formula:
            periods = ScheduledPeriod.objects.filter(section=self.section).distinct(
                'title'
            )
            for period in periods:
                title = period.title
                if title in formula:
                    formula = formula.replace(title + "_A", to_string(self.get_enrollment_period_total_absence(title)))
                    formula = formula.replace(title + "_L", to_string(self.get_enrollment_period_total_late(title)))
            result = eval(formula)
        return result
