from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.shortcuts import get_object_or_404
from attendance.models import ScheduledPeriod, AttendanceInstance, Attendance
from .utils import get_offset_day, number_of_days, day_string

User = settings.AUTH_USER_MODEL


class UserProfile(models.Model):
    class Language:
        ARABIC = 'ar'
        ENGLISH = 'en'

        @classmethod
        def choices(cls):
            return (
                (cls.ARABIC, _('Arabic')),
                (cls.ENGLISH, _('English')),
            )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    preferred_language = models.CharField(
        _('preferred language'), max_length=2, choices=Language.choices(),
        default=Language.ARABIC)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def in_student(self):
        """
        :return: True if the current user profile is a student else False
        """
        pass

    @property
    def is_instructor(self):
        """
        :return: True if the current user profile is an instructor else False
        """
        return Instructor.get_instructor(user=self)

    @property
    def is_active(self):
        """
        :return: True if the user is active else is False
        """
        pass


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

    class Meta:
        abstract = True


class Student(Person):
    user_profile = models.OneToOneField(UserProfile, related_name='student', null=True, blank=True)

    def __str__(self):
        return self.arabic_name + ' ' + self.university_id

    @staticmethod
    def get_student(user=None):
        """
        :param user: current login user
        :return: True if student else False
        """
        return True if Student.objects.filter(user_profile=user) else False


class Instructor(Person):
    user_profile = models.OneToOneField(UserProfile, related_name='instructor', null=True, blank=True)

    def __str__(self):
        return self.arabic_name + ' - ' + self.university_id

        # :TODO Function to get the email ID from the USER_AUTH_MODEL.

    @staticmethod
    def get_instructor(user=None):
        """
        :param user: current login user
        :return: True if instructor else False
        """
        return True if Instructor.objects.filter(user_profile=user) else False


class Semester(models.Model):
    start_date = models.DateTimeField(_('start date'))
    end_date = models.DateTimeField(_('end date'))
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return self.code


class Department(models.Model):
    name = models.CharField(_('english name'), max_length=50, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=50, null=True, blank=False)
    code = models.CharField(max_length=10, null=True, blank=False)

    def __str__(self):
        return self.name + ' - ' + self.code


class Course(models.Model):
    name = models.CharField(_('english name'), max_length=255, null=True, blank=False)
    arabic_name = models.CharField(_('arabic name'), max_length=255, null=True, blank=False)
    department = models.ForeignKey(Department, related_name='courses', null=True, blank=False)
    attendance_entry_window = models.IntegerField(_('attendance window'), null=True, blank=False, default=7)
    coordinated = models.BooleanField(blank=False, default=1)
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return self.code


class Section(models.Model):
    semester = models.ForeignKey(Semester, related_name='sections', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='sections', on_delete=models.CASCADE)
    code = models.CharField(max_length=20, null=True, blank=False)

    def __str__(self):
        return self.semester.code + ' - ' + self.course.code + ' - ' + self.code

    @property
    def attendance_entry_window(self):
        if self.course.coordinated:
            return self.course.attendance_entry_window
        else:
            return 0

    @staticmethod
    def get_section(section_id):
        """
        :param section_id:
        :return: a section object got the giving ID
        """
        return Section.objects.filter(id=section_id)

    @staticmethod
    def get_sections():
        """
        :return: list of section objects
        """
        return Section.objects.all()

    @staticmethod
    def get_instructor_sections(instructor):
        """
        :param instructor: current login user
        :return: a unique ist of section objects for the login user
        """
        return Section.objects.filter(scheduled_periods__instructor_assigned=instructor).distinct()


class Enrollment(models.Model):
    student = models.ForeignKey(Student, related_name='enrollments', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='enrollments', on_delete=models.CASCADE)
    letter_grade = models.CharField(_('letter grade'), max_length=10, null=True, blank=False, default='UD')

    def __str__(self):
        return self.student.arabic_name + ' - ' + self.section.code

    @staticmethod
    def get_students(section_id):
        """
        :param section_id:
        :return: list of all students for a giving section ID
        """
        return Enrollment.objects.filter(section=section_id)

    @staticmethod
    def get_students_enrollment(section_id, date, instructor, given_day=None):
        """
        :param section_id: 
        :param date:
        :param instructor:
        :param given_day
        :return: list of enrollments for a giving section_id and a day and instructor
           If the giving day is not exist get the nearest one
        """

        enrollments = []
        days_offset = 0
        periods = None
        period_date = None

        if given_day:
            periods = ScheduledPeriod.get_section_periods_of_date(section_id, given_day, instructor)
            while days_offset <= 7:
                period_date, day = get_offset_day(date, -days_offset)
                if str(day).lower() == str(given_day).lower():
                    days_offset = 8
                days_offset += 1
            """
            When a day is not giving, we provide the attendance of the nearest day.
            """
        else:
            while days_offset <= 7:
                period_date, day = get_offset_day(date, -days_offset)
                periods = ScheduledPeriod.get_section_periods_of_date(section_id, day, instructor)
                if periods:
                    days_offset = 8
                days_offset += 1

        for period in periods:
            attendance_instance, created = AttendanceInstance.objects.get_or_create(period=period, date=period_date)
            enrollment_list = Enrollment.objects.filter(section=section_id)
            for enrollment in enrollment_list:
                id = 0
                try:
                    attendance = Attendance.objects.get(enrollment=enrollment, attendance_instance=attendance_instance)
                    status = attendance.status
                    id = attendance.id
                except Attendance.DoesNotExist:
                    status = Attendance.Types.PRESENT

                enrollments.append(dict(enrollment=enrollment.id,
                                        student_name=enrollment.student.english_name,
                                        period=period,
                                        attendance_instance=attendance_instance.id,
                                        status=status,
                                        id=id))
        return enrollments
