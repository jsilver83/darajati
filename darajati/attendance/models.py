from django.db import models
from django.utils.translation import ugettext_lazy as _


class ScheduledPeriod(models.Model):
    class Days:
        SUNDAY = 'SUNDAY'
        MONDAY = 'MONDAY'
        TUESDAY = 'TUESDAY'
        WEDNESDAY = 'WEDNESDAY'
        THURSDAY = 'THURSDAY'
        FRIDAY = 'FRIDAY'
        SATURDAY = 'SATURDAY'

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

    section = models.ForeignKey('enrollment.Section', related_name='scheduled_periods', null=True, blank=False,
                                on_delete=models.CASCADE)

    instructor_assigned = models.ForeignKey('enrollment.Instructor', related_name='assigned_periods')
    day = models.CharField(max_length=9, null=True, blank=False, choices=Days.choices())
    title = models.CharField(max_length=20, null=True, blank=False)
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))
    location = models.CharField(max_length=50, null=True, blank=False)
    late_deduction = models.FloatField(_('late deduction'), null=True, blank=False, default=0.0)
    absence_deduction = models.FloatField(_('absence deduction'), null=True, blank=False, default=0.0)

    def __str__(self):
        return self.section.code + ' - ' + self.instructor_assigned.english_name + ' - ' + str(self.day) + ' - ' + \
               str(self.start_time) + ' - ' + str(self.end_time)

    @staticmethod
    def get_period(period_id=None):
        """
        This function will get a specific period for a giving id.
        """
        return ScheduledPeriod.objects.filter(id=period_id).first

    @staticmethod
    def get_periods():
        """
        This function will get all periods, Usually it's used for superuser.
        """
        return ScheduledPeriod.objects.all()

    @staticmethod
    def get_instructor_period(instructor=None):
        """
        This function will give back a list of periods that are associated to an instructor.
        """
        return ScheduledPeriod.objects.filter(instructor_assigned=instructor)

    @staticmethod
    def get_section_periods(section_id, instructor):
        """
        :param instructor: login user
        :param section_id: passed by the url
        :param current_day: current day string
        :return: a list of all periods for that section ID for that instructor
        """
        return ScheduledPeriod.objects.filter(section=section_id, instructor_assigned=instructor).values(
            'section_id', 'day').distinct()

    @staticmethod
    def get_section_periods_of_date(section_id, day, instructor):
        """
        :param section_id: giving section 
        :param day:
        :param instructor
        :return: all periods for a giving section and date and instructor
        """
        return ScheduledPeriod.objects.filter(section=section_id, day__iexact=day, instructor_assigned=instructor)


class AttendanceInstance(models.Model):
    period = models.ForeignKey(ScheduledPeriod, related_name='attendance_dates')
    date = models.DateField()
    comment = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return str(self.period) + ' - ' + str(self.date)

    @staticmethod
    def is_created(period, date):
        """
        :param period: 
        :param date
        :return: 
        """
        return True if AttendanceInstance.objects.filter(period=period, date=date) else False

    @staticmethod
    def get_attendance_instance_of_period(period, date):
        """
        :param period: 
        :param date
        :return: 
        """
        return AttendanceInstance.objects.filter(period=period, date=date)


class Attendance(models.Model):
    class Types:
        ABSENT = 'abs'
        LATE = 'lat'
        PRESENT = 'pre'
        EXCUSED = 'exc'

        @classmethod
        def choices(cls):
            return (
                (cls.PRESENT, _('Present')),
                (cls.ABSENT, _('Absent')),
                (cls.LATE, _('Late')),
                (cls.EXCUSED, _('Excused')),

            )

    attendance_instance = models.ForeignKey(AttendanceInstance, related_name='attendance')
    enrollment = models.ForeignKey('enrollment.Enrollment', related_name='attendance')
    status = models.CharField(_('Student attendance'), max_length=3, default=Types.PRESENT, choices=Types.choices())

    def __str__(self):
        return str(self.attendance_instance.period) + ' - ' + self.enrollment.student.english_name
