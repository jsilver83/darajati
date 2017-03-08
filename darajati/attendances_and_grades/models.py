from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Person(models.Model):
    university_id = models.CharField(max_length=20, null=True, blank=True)
    government_id = models.CharField(max_length=20, null=True, blank=True)
    english_name = models.CharField(max_length=255, null=True, blank=False)
    arabic_name = models.CharField(max_length=255, null=True, blank=False)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    personal_email = models.EmailField(null=True, blank=False)

    class Meta:
        abstract = True


class Student(Person):
    user = models.ForeignKey(User, related_name='student', null=True, blank=True)

    def __str__(self):
        return self.arabic_name, self.user

        # :TODO Function to get the student ID from the USER_AUTH_MODEL.


class Instructor(Person):
    user = models.ForeignKey(User, related_name='instructor', null=True, blank=True)

    def __str__(self):
        return self.arabic_name, self.user

        # :TODO Function to get the email ID from the USER_AUTH_MODEL.


class Semester(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return self.code


class Department(models.Model):
    name = models.CharField(max_length=50, null=True, blank=False)
    code = models.CharField(max_length=10, null=True, blank=False)

    def __str__(self):
        return self.name, self.code


class Course(models.Model):
    department = models.ForeignKey(Department, related_name='courses', null=True, blank=False)
    code = models.CharField(max_length=20, null=True, blank=False)
    description = models.CharField(max_length=255, null=True, blank=False)

    def __str__(self):
        return self.code


class Section(models.Model):
    semester = models.ForeignKey(Semester, related_name='sections', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='sections', on_delete=models.CASCADE)
    code = models.CharField(max_length=20, null=True, blank=False)

    def __str__(self):
        return self.semester, self.course, self.code

'''
# TODO: What's the mechanism to get the letter grade of a student who have taken the course more than once. 
'''
class enrolllment(models.Model):
    student = models.ForeignKey(Student, related_name='enrollments', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='enrollments', on_delete=models.CASCADE)
    letter_grade = models.CharField(max_length=10, null=True, blank=False, default='UD')

    def __str__(self):
        return self.student, self.section


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
    instructor_assigned = models.ForeignKey(Instructor, related_name='assigned_periods', editable=False)
    day = models.CharField(max_length=3, null=True, blank=False, choices=Days.choices())
    title = models.CharField(max_length=20, null=True, blank=False)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=50, null=True, blank=False)
    late_deduction = models.FloatField(null=True, blank=False, default=0.0)
    absence_deduction = models.FloatField(null=True, blank=False, default=0.0)

    def __str__(self):
        return self.section, self.instructor_assigned, self.day, self.start_time, self.end_time


class AttendanceInstant(models.Model):
    period = models.ForeignKey(ScheduledPeriod, related_name='attendance_dates', editable=False)
    date = models.DateField()
    comment = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return self.period, self.date


class Attendance(models.Model):
    attendance_instant = models.ForeignKey(AttendanceInstant, related_name='attendances', editable=False)
    enrollment = models.ForeignKey(enrollment, related_name='attendances', editable=False)

    def __str__(self):
        return self.period_attendance_date, self.enrollment
