from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords

from darajati.validators import validate_file_extension
from enrollment.utils import now
from enrollment.utils import to_string, day_string, get_offset_day, get_dates_in_between, get_previous_week, \
    get_next_week
from .media_handlers import upload_excuse_attachments

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

    section = models.ForeignKey('enrollment.Section',
                                related_name='scheduled_periods',
                                on_delete=models.CASCADE,
                                null=True,
                                blank=False
                                )
    instructor_assigned = models.ForeignKey('enrollment.Instructor', on_delete=models.SET_NULL, null=True, blank=False,
                                            related_name='assigned_periods')
    day = models.CharField(max_length=9, null=True, blank=False, choices=Days.choices())
    title = models.CharField(max_length=20, null=True, blank=False)
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))
    location = models.CharField(max_length=50, null=True, blank=False)

    def __str__(self):
        try:
            return to_string(self.section.course_offering,
                             self.section.code,
                             self.instructor_assigned.english_name,
                             self.day,
                             self.start_time,
                             self.end_time)
        except:
            return to_string(self.section.course_offering,
                             self.section.code,
                             '',
                             self.day,
                             self.start_time,
                             self.end_time)

    @staticmethod
    def get_period(period_id=None):
        """
        This function will get a specific period for a giving id.
        """
        try:
            return ScheduledPeriod.objects.get(id=period_id)
        except ScheduledPeriod.DoesNotExist:
            return None

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
    def get_section_periods_of_day(section_id, day, instructor):
        """
        :param section_id: giving section 
        :param day:
        :param instructor
        :return: all periods for a giving section and date and instructor
        """
        if instructor:
            return ScheduledPeriod.objects.filter(
                section=section_id,
                day__iexact=day,
                instructor_assigned=instructor
            )
        # coordinator
        return ScheduledPeriod.objects.filter(
            section=section_id,
            day__iexact=day
        )

    # FIXME: You should fix me to look more prettier and more efficient
    @staticmethod
    def get_nearest_day_and_date(section_id, date, instructor):
        """
        :param section_id: given section id 
        :param date: a date which to be accessed
        :param instructor: an instructor instance
        :return: nearest day in string, and it's date
        """
        days_offset = 0
        period_date = None
        day = None

        while days_offset <= 7:
            period_date, day = get_offset_day(date, -days_offset)
            periods = ScheduledPeriod.get_section_periods_of_day(section_id, day, instructor).values_list(
                'day').distinct('day')
            if periods:
                days_offset = 8
            days_offset += 1

        return day, period_date

    # FIXME: Oh no, such logic, i am structured so badly, consider breaking me down to smaller parts please.
    @staticmethod
    def get_section_periods_week_days(section, instructor, current_date, today):
        """
        :param section: 
        :param instructor: 
        :param current_date: 
        :param today: 
        :return: Will return a list of dates where they will be placed in the top of the attendance table
        This will construct which date is available from previous week and next week. 
        """
        dates = get_dates_in_between(current_date)
        period_dates = []
        previous_week = None
        next_week = None
        result_previous_week = None
        result_next_week = None
        last_accessible_date, last_accessible_day = get_offset_day(today,
                                                                   -section.course_offering.attendance_entry_window)
        # Get Periods Dates
        for date in dates:
            day = day_string(date)
            if last_accessible_date <= date and \
                    ScheduledPeriod.is_period_within_range(section, day, instructor) and \
                    date <= today:
                period_dates.append({'date': date, 'day': day, 'section_id': section.id})

        # Get Previous Week Periods Dates
        if current_date > last_accessible_date and \
                not any(item.get('date', None) == last_accessible_date for item in period_dates):
            previous_week = get_previous_week(current_date)
            previous_week = get_dates_in_between(previous_week)
            for date in previous_week:
                day = day_string(date)
                if last_accessible_date <= date and \
                        ScheduledPeriod.is_period_within_range(section, day, instructor) and \
                        date <= today:
                    day = day_string(date)
                    result_previous_week = {'date': date, 'day': day, 'section_id': section.id}

        if current_date < today and not any(
                item.get('date', None) == today for item in period_dates):
            next_week = get_next_week(current_date)
            next_week = get_dates_in_between(next_week)
            for date in next_week:
                day = day_string(date)
                if last_accessible_date <= date and \
                        ScheduledPeriod.is_period_within_range(section, day, instructor) and \
                        date <= today:
                    day = day_string(date)
                    result_next_week = {'date': date, 'day': day, 'section_id': section.id}
                    break

        return period_dates, result_previous_week, result_next_week

    @staticmethod
    def is_period_exists(section, instructor, day, start_time, end_time):
        """
        :param section: 
        :param instructor: 
        :param day: 
        :param start_time: 
        :param end_time: 
        :return: True if period with such input exists else False 
        """
        return ScheduledPeriod.objects.filter(section=section,
                                              instructor_assigned=instructor,
                                              day=day,
                                              start_time=start_time,
                                              end_time=end_time).exists()

    @staticmethod
    def is_period_within_range(section, day, instructor):
        """
        :param section: 
        :param day: 
        :param instructor: 
        :return: True if a period within the attendance_window boundary else False 
        """
        if instructor:
            return ScheduledPeriod.objects.filter(section=section.id,
                                                  day__iexact=day,
                                                  instructor_assigned=instructor
                                                  ).distinct('day').exists()

        return ScheduledPeriod.objects.filter(section=section.id,
                                              day__iexact=day
                                              ).distinct('day').exists()


class AttendanceInstance(models.Model):
    period = models.ForeignKey(ScheduledPeriod, on_delete=models.CASCADE, related_name='attendance_dates')
    date = models.DateField()
    comment = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return to_string(self.period, self.date)

    @staticmethod
    def is_created(period, date):
        """
        :param period: 
        :param date
        :return: True if an instance exists else False
        """
        return AttendanceInstance.objects.filter(period=period, date=date).exists()


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

    attendance_instance = models.ForeignKey(AttendanceInstance, on_delete=models.CASCADE, related_name='attendance')
    enrollment = models.ForeignKey('enrollment.Enrollment', on_delete=models.CASCADE, related_name='attendance')
    status = models.CharField(_('Student attendance'), max_length=3, default=Types.PRESENT, choices=Types.choices())
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=False)
    updated_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL)

    history = HistoricalRecords()

    class Meta:
        permissions = (
            ('can_give_excused_status', _('Can change student status to excused')),
        )
        # important to prevent duplicated attendances for the same period/enrollment
        unique_together = ('attendance_instance', 'enrollment')

    def __str__(self):
        return to_string(self.attendance_instance.period, self.enrollment.student.english_name)


class Excuse(models.Model):
    class Types:
        CLINICS_MEDICAL = 'clinics_medical'
        OUTSIDE_MEDICAL = 'outside_medical'
        PERSONAL = 'personal'
        OTHER = 'other'

        @classmethod
        def choices(cls):
            return (
                (cls.CLINICS_MEDICAL, _('Medical (KFUPM Clinics)')),
                (cls.OUTSIDE_MEDICAL, _('Medical (Outside)')),
                (cls.PERSONAL, _('Personal Excuse')),
                (cls.OTHER, _('Other')),
            )

    start_date = models.DateTimeField(_('Start Date/Time'), null=True, blank=False)
    end_date = models.DateTimeField(_('End Date/Time'), null=True, blank=False)
    university_id = models.CharField(_('University ID'), max_length=20, null=True, blank=False)
    excuse_type = models.CharField(_('Excuse'), max_length=30, default=Types.CLINICS_MEDICAL,
                                   choices=Types.choices(), null=True, blank=False)
    includes_exams = models.BooleanField(_('Includes Exams?'), blank=False, default=False)
    attachments = models.FileField(_('Attachments'),
                                   null=True,
                                   blank=True,
                                   validators=[validate_file_extension],
                                   upload_to=upload_excuse_attachments, )
    description = models.CharField(_('Description'), max_length=2000, null=True, blank=True)
    created_on = models.DateTimeField(_('Created On'), auto_now_add=True, null=True, blank=False)
    created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL,
                                   verbose_name=_('Created By'), related_name='created_excuses')
    applied_on = models.DateTimeField(_('Applied On'), null=True, blank=True)
    applied_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                   verbose_name=_('Applied By'), related_name='applied_excuses')

    class Meta:
        permissions = (
            ('can_give_excuses', _('Can enter excuses for students')),
        )

    def __str__(self):
        return to_string(self.university_id, self.get_excuse_type_display())

    def clean(self):
        if self.start_date and self.end_date:
            if not self.end_date >= self.start_date:
                raise ValidationError("End date should be greater than start date")

            if self.end_date > now():
                raise ValidationError(_('End date can NOT be in the future'))

    @property
    def student(self):
        from enrollment.models import Student
        return Student.objects.filter(university_id=self.university_id).first()

    def get_attendances_to_be_excused(self):
        return self.get_attendances(self.university_id, self.start_date, self.end_date,
                                    [Attendance.Types.ABSENT, Attendance.Types.LATE, ])

    def get_excused_attendances(self):
        return self.get_attendances(self.university_id, self.start_date, self.end_date, [Attendance.Types.EXCUSED, ])

    def apply_excuse(self):
        attendances_and_lates_to_be_excused = self.get_attendances_to_be_excused()

        if attendances_and_lates_to_be_excused:
            for attendance in attendances_and_lates_to_be_excused:
                attendance.status = Attendance.Types.EXCUSED
                attendance.updated_by = self.applied_by
                attendance.save()

    @staticmethod
    def get_attendances(university_id, start_date, end_date, statuses):
        if university_id and start_date and end_date and statuses:
            all_attendances_in_the_same_dates = Attendance.objects.filter(
                enrollment__student__university_id=university_id,
                status__in=statuses,
                attendance_instance__date__gte=start_date,
                attendance_instance__date__lte=end_date,
            )

            attendances = []

            for attendance in all_attendances_in_the_same_dates:
                attendance_start_date_time = timezone.make_aware(
                    datetime.combine(attendance.attendance_instance.date, attendance.attendance_instance.period.start_time))
                attendance_end_date_time = timezone.make_aware(
                    datetime.combine(attendance.attendance_instance.date, attendance.attendance_instance.period.end_time))

                if attendance_start_date_time >= start_date and attendance_end_date_time <= end_date:
                    attendances.append(attendance)

            return attendances


class AttendanceDeductionView(models.Model):
    enrollment = models.OneToOneField('enrollment.Enrollment', on_delete=models.DO_NOTHING,
                                      related_name='attendance_deduction',
                                      primary_key=True)
    attendance_deduction = models.DecimalField(max_digits=settings.MAX_DIGITS,
                                               decimal_places=settings.MAX_DECIMAL_POINT)

    class Meta:
        managed = False
        db_table = 'enrollment_attendancededuction'

    def __str__(self):
        return str(self.attendance_deduction)