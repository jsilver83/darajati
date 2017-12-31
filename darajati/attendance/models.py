from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.dateparse import parse_time
from enrollment.utils import to_string, day_string, get_offset_day, get_dates_in_between, get_previous_week, \
    get_next_week, today

from enrollment.web_service_utils import get_student_enrollments, get_section_periods, get_section

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

    section = models.CharField(_('Section Code'), max_length=20, null=True, blank=False)
    day = models.CharField(max_length=9, null=True, blank=False, choices=Days.choices())
    title = models.CharField(max_length=20, null=True, blank=False)
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))
    location = models.CharField(max_length=50, null=True, blank=False)

    def __str__(self):
        return to_string(self.section,
                         self.day,
                         self.start_time,
                         self.end_time)


class AttendanceInstance(models.Model):
    period = models.ForeignKey(ScheduledPeriod, related_name='attendance_dates')
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

    student_id = models.CharField(_('Student university id'), max_length=20, null=True, blank=False)
    attendance_instance = models.ForeignKey(AttendanceInstance, related_name='attendance')
    status = models.CharField(_('Student attendance'), max_length=3, default=Types.PRESENT, choices=Types.choices())
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=False)
    updated_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('student_id', 'attendance_instance')
        permissions = (
            ('can_give_excused_status', _('Can change student status to excused')),
        )

    def __str__(self):
        return to_string(self.student_id, self.attendance_instance)

    @staticmethod
    def get_section_enrollment(crn, date):
        days = {ScheduledPeriod.Days.SUNDAY: 'U',
                ScheduledPeriod.Days.MONDAY: 'M',
                ScheduledPeriod.Days.TUESDAY: 'T',
                ScheduledPeriod.Days.WEDNESDAY: 'W',
                ScheduledPeriod.Days.THURSDAY: 'R',
                ScheduledPeriod.Days.FRIDAY: 'F',
                ScheduledPeriod.Days.SATURDAY: 'S'}

        enrollments = get_student_enrollments('201710-SH', 'ENGL01')
        section = get_section('201710-SH', crn)
        periods = get_section_periods(section['sec_code'], '201710-SH', crn)
        current_periods = []
        for period in periods:
            day = eval('ScheduledPeriod.Days.'+ day_string(date).upper())
            if days[day] in period['class_days']:
                start_time = parse_time(period['start_time'][:2] + ':' + period['start_time'][2:])
                end_time = parse_time(period['end_time'][:2] + ':' + period['end_time'][2:])
                period, created = ScheduledPeriod.objects.get_or_create(
                    section=section['sec_code'],
                    day=days[day],
                    title=period['activity'],
                    start_time=start_time,
                    end_time=end_time,
                    location=period['bldg'] + ', ' + period['room'],
                )
                current_periods.append(period)
        attendance_list = []
        count_total = 0
        count_valid = 0
        x = 0
        for enrollment in enrollments:
            enrollment_section = enrollment['crs'] + '-' + enrollment['sec']
            if section['sec_code'] in enrollment_section or section['sec_code'] == enrollment_section :
                count_total += 1
                if not enrollment['grade']:
                    count_valid += 1
                    for period in current_periods:
                        attendance_instance, created = AttendanceInstance.objects.get_or_create(
                            period=period,
                            date=date
                        )
                        try:
                            attendance = Attendance.objects.get(
                                student_id=enrollment['stu_id'],
                                attendance_instance=attendance_instance
                            )
                            attendance_list.append({
                                'id': attendance.id,
                                'student_id': enrollment['stu_id'],
                                'attendance_instance': attendance_instance,
                                'status': attendance.status
                            })
                            continue
                        except:
                            pass
                        attendance_list.append({
                            'student_id': enrollment['stu_id'],
                            'attendance_instance': attendance_instance,
                            'status': Attendance.Types.PRESENT
                        })
        return attendance_list
