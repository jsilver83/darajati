from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from enrollment.utils import to_string, get_offset_day

User = settings.AUTH_USER_MODEL


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
    late_deduction = models.DecimalField(_('late deduction'), null=True, blank=False, max_digits=settings.MAX_DIGITS,
                                         decimal_places=settings.MAX_DECIMAL_POINT)
    absence_deduction = models.DecimalField(_('absence deduction'), null=True, blank=False,
                                            max_digits=settings.MAX_DIGITS,
                                            decimal_places=settings.MAX_DECIMAL_POINT)

    def __str__(self):
        return to_string(self.section.code, self.instructor_assigned.english_name, self.day, self.start_time,
                         self.end_time)

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

    @staticmethod
    def get_section_periods_of_nearest_day(section_id, instructor, date, giving_day=None):
        """
        :param section_id: 
        :param giving_day: 
        :param instructor: 
        :param date
        :return: 
        """
        days_offset = 0
        period_date = None
        day = None
        if giving_day:
            while days_offset <= 7:
                period_date, day = get_offset_day(date, -days_offset)
                if str(day).lower() == str(giving_day).lower():
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

        return day, period_date, ScheduledPeriod.objects.filter(section=section_id, day__iexact=day,
                                                                instructor_assigned=instructor)


class AttendanceInstance(models.Model):
    period = models.ForeignKey(ScheduledPeriod, related_name='attendance_dates')
    date = models.DateField()
    comment = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return to_string(self.period, self.date)

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
    class Meta:
        permissions = (
            ('can_give_excused_status', _('Can change student status to excused')),
        )

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
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=False)
    updated_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL)

    def __str__(self):
        return to_string(self.attendance_instance.period, self.enrollment.student.english_name)

    @staticmethod
    def get_student_attendance(section_id):
        """
        :param section_id: 
        :return: 
        """
        return Attendance.objects.filter(enrollment__section=section_id).values('enrollment', 'status').annotate(
            total=models.Count('status')
        )
