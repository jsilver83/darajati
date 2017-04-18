from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

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
        pass

    @property
    def is_instructor(self):
        return Instructor.get_instructor(user=self)


class Person(models.Model):
    university_id = models.CharField(max_length=20, null=True, blank=True)
    government_id = models.CharField(max_length=20, null=True, blank=True)
    english_name = models.CharField(max_length=255, null=True, blank=False)
    arabic_name = models.CharField(max_length=255, null=True, blank=False)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    personal_email = models.EmailField(null=True, blank=False)
    active = models.BooleanField(blank=False, default=False)

    class Meta:
        abstract = True

    def is_active(self):
        pass


class Student(Person):
    user_profile = models.OneToOneField(UserProfile, related_name='student', null=True, blank=True)

    def __str__(self):
        return self.arabic_name + ' ' + self.university_id

        # :TODO Function to get the student ID from the USER_AUTH_MODEL.

    def get_student(self):
        pass


class Instructor(Person):
    user_profile = models.OneToOneField(UserProfile, related_name='instructor', null=True, blank=True)

    def __str__(self):
        return self.arabic_name + ' - ' + self.university_id

        # :TODO Function to get the email ID from the USER_AUTH_MODEL.

    @staticmethod
    def get_instructor(user=None):
        return True if Instructor.objects.filter(user_profile=user) else False


class Semester(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return self.code


class Department(models.Model):
    name = models.CharField(max_length=50, null=True, blank=False)
    arabic_name = models.CharField(max_length=50, null=True, blank=False)
    code = models.CharField(max_length=10, null=True, blank=False)

    def __str__(self):
        return self.name + ' - ' + self.code


class Course(models.Model):
    name = models.CharField(max_length=255, null=True, blank=False)
    department = models.ForeignKey(Department, related_name='courses', null=True, blank=False)
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return self.code


class Section(models.Model):
    semester = models.ForeignKey(Semester, related_name='sections', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='sections', on_delete=models.CASCADE)
    # Add attendance_window which specifise the period the instructor is allowed to add/edit daily attendance
    code = models.CharField(max_length=20, null=True, blank=False)

    def __str__(self):
        return self.semester.code + ' - ' + self.course.code + ' - ' + self.code


class Enrollment(models.Model):
    student = models.ForeignKey(Student, related_name='enrolments', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='enrolments', on_delete=models.CASCADE)
    letter_grade = models.CharField(max_length=10, null=True, blank=False, default='UD')

    def __str__(self):
        return self.student.arabic_name + ' - ' + self.section.code


class ScheduledPeriod(models.Model):
    class Days:
        SUNDAY = 'sun'
        MONDAY = 'mon'
        TUESDAY = 'tue'
        WEDNESDAY = 'wed'
        THURSDAY = 'thu'
        FRIDAY = 'fri'
        SATURDAY = 'sat'

        @classmethod
        def choices(cls):
            return (
                (cls.SUNDAY, _('Sunday')),
                (cls.MONDAY, _('Monday')),
                (cls.TUESDAY, _('Tuesday')),
                (cls.WEDNESDAY, _('Wednesday')),
                (cls.THURSDAY, _('Thursday')),
                (cls.FRIDAY, _('Friday')),
                (cls.SATURDAY, _('Saturday')),
            )

    section = models.ForeignKey(Section, related_name='scheduled_periods', null=True, blank=False,
                                on_delete=models.CASCADE)
    instructor_assigned = models.ForeignKey(Instructor, related_name='assigned_periods')
    day = models.CharField(max_length=3, null=True, blank=False, choices=Days.choices())
    title = models.CharField(max_length=20, null=True, blank=False)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=50, null=True, blank=False)
    late_deduction = models.FloatField(null=True, blank=False, default=0.0)
    absence_deduction = models.FloatField(null=True, blank=False, default=0.0)

    def __str__(self):
        return self.section.code + ' - ' + self.instructor_assigned.english_name + ' - ' + str(self.day) + ' - ' + \
               str(self.start_time) + ' - ' + str(self.end_time)


class AttendanceInstant(models.Model):
    period = models.ForeignKey(ScheduledPeriod, related_name='attendance_dates')
    date = models.DateField()
    comment = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return str(self.period) + ' - ' + str(self.date)


class Attendance(models.Model):
    attendance_instant = models.ForeignKey(AttendanceInstant, related_name='attendances')
    enrolment = models.ForeignKey(Enrollment, related_name='attendances')

    def __str__(self):
        return str(self.attendance_instant.period) + ' - ' + self.enrolment.student.english_name
