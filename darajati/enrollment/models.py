from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.contrib.auth.models import User as User_model
from .types import RoundTypes
from .utils import to_string, now

from attendance.models import ScheduledPeriod, AttendanceInstance, Attendance

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
    def has_access(self):
        return Instructor.is_active(user=self) or Student.is_active(user=self)

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
        return to_string(self.english_name, self.university_id)

    @staticmethod
    def is_active(user=None):
        """
        :return: True if the user is active else is False
        """
        try:
            return Student.objects.get(user_profile=user).active
        except:
            return False

    @staticmethod
    def get_student(user=None):
        """
        :param user: current login user
        :return: True if student else False
        """
        try:
            return Student.objects.get(user_profile=user)
        except:
            return False

    @staticmethod
    def is_student_exists(email):
        return Student.objects.filter(personal_email__exact=email).exists()

    @staticmethod
    def get_create_student(username, university_id, government_id, english_name, arabic_name, mobile, personal_email):
        user, created = User_model.objects.get_or_create(username=username)

        profile, created = UserProfile.objects.get_or_create(
            user=user
        )
        return Student.objects.get_or_create(
            user_profile=profile,
            university_id=university_id,
            government_id=government_id,
            english_name=english_name,
            arabic_name=arabic_name,
            mobile=mobile,
            personal_email=personal_email,
            active=True
        )


class Instructor(Person):
    user_profile = models.OneToOneField(UserProfile, related_name='instructor', null=True, blank=True)

    def __str__(self):
        return to_string(self.english_name, self.university_id)

        # :TODO Function to get the email ID from the USER_AUTH_MODEL.

    @staticmethod
    def is_active(user=None):
        """
        :return: True if the user is active else is False
        """
        try:
            return Instructor.objects.get(user_profile=user).active
        except:
            return False

    @staticmethod
    def get_instructor(user=None):
        """
        :param user: current login user
        :return: True if instructor else False
        """
        return True if Instructor.objects.filter(user_profile=user) else False

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
        return to_string(self.code, self.description)


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
    attendance_entry_window = models.IntegerField(_('attendance window'), null=True, blank=False, default=7)
    coordinated = models.BooleanField(blank=False, default=1)
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
        return to_string(self.course_offering.semester.code, self.course_offering.course.code, self.code)

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
        :return: a unique list of section objects for the login user and for the current semester
        """
        return True if Section.objects.filter(id=self.id, scheduled_periods__instructor_assigned=instructor,
                                              scheduled_periods__section__course_offering__semester__start_date__lte=now(),
                                              scheduled_periods__section__course_offering__semester__end_date__gte=now()
                                              ).distinct().first() else False

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
        return to_string(self.course_offering.semester, self.course_offering, self.instructor)


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

    def __str__(self):
        return to_string(self.student.english_name, self.section.code)

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
    def get_students_enrollment(section_id, instructor, date):
        """
        :param section_id: 
        :param date:
        :param instructor:
        :param given_day
        :return: list of enrollments for a giving section_id and a day and instructor
           If the giving day is not exist get the nearest one
        """

        enrollments = []
        index = 1
        day, period_date, periods = ScheduledPeriod.get_section_periods_of_nearest_day(section_id, instructor, date)
        enrollment_list = Enrollment.get_students(section_id)
        for enrollment in enrollment_list:
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
