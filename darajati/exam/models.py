from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import OuterRef, F, Subquery, Func, DecimalField, Avg
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords

from enrollment.models import Coordinator, Instructor, Section, ScheduledPeriod, Enrollment
from darajati.utils import decimal
from .utils import get_allowed_markers_for_a_fragment

User = settings.AUTH_USER_MODEL

"""
The motivation of this app is to separate the subjective exams for english 
this is more to the side of a testing policy that they want to convert all of their exams too.

Consider having rooms, and a defined exams that is connected to only and only grade fragment that their type is 
subjective exam. Each exam will have the same list of enrollment of students since we actually need this list.
Also an exam is assigned to list of instructors that they will be called markers since an exam can be mark by more than
one instructor.  
"""


# TODO: remove from here and add it in the enrollment app
class Room(models.Model):
    name = models.CharField(_('Room Name'), max_length=100, null=True, blank=False)
    location = models.CharField(_('Room location'), max_length=100, null=True, blank=False)
    capacity = models.PositiveIntegerField(_('Room Capacity'), null=False, blank=False, default=0)
    # department = models.ForeignKey('enrollment.Department', related_name='rooms', null=True, blank=False)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True)

    class Meta:
        ordering = ['location', ]

    def __str__(self):
        return '%s - c(%d)' % (self.location, self.capacity)


class ExamSettings(models.Model):
    fragment = models.OneToOneField('grade.GradeFragment', on_delete=models.CASCADE,
                                    related_name='exam_settings', null=True, blank=False,
                                    verbose_name=_('Grade Fragment'), )
    exam_date = models.DateField(
        _('Exam Date'),
        null=True,
        blank=False,
    )
    allow_markers_from_other_courses = models.BooleanField(
        _('Allow Markers From Other Courses'),
        default=False,
        help_text=_('If checked, it means you can assign markers in the subjective marking module from other courses '
                    'within the same department')
    )
    allow_markers_to_mark_own_students = models.BooleanField(
        _('Allow Markers To Mark Own Students'),
        default=False,
        help_text=_('If checked, it means the marker can mark students that he actually teaches')
    )
    markings_difference_tolerance = models.DecimalField(
        _('Markings Difference Tolerance'),
        null=True,
        blank=False,
        help_text=_('The maximum difference allowed between different markings of a student paper before the '
                    'intervention of a tie-breaker'),
        max_digits=settings.MAX_DIGITS,
        decimal_places=settings.MAX_DECIMAL_POINT
    )
    number_of_markers = models.PositiveSmallIntegerField(
        _('Number Of Markers'),
        null=True,
        blank=False,
        default=2,
        help_text=_('Indicates the number of markers that will subjectively mark students papers. If the number is 2,'
                    'that means two markers will enter marks for each student paper and a third marker will break the '
                    'tie if needed')
    )
    default_tie_breaking_marker = models.ForeignKey('enrollment.Instructor', on_delete=models.SET_NULL,
                                                    related_name='third_marker', null=True, blank=False,
                                                    verbose_name=_('Default Tie-Breaking Marker'), )

    def __str__(self):
        return str(self.fragment)

    @property
    def overall_average(self):
        try:
            return decimal(StudentMark.objects.filter(
                marker__exam_room__exam_shift__settings=self).aggregate(Avg('mark')).get('mark__avg', 0.00))
        except:
            return 0.00


# TODO: Consider changing start/end dates to date and start/end times
class ExamShift(models.Model):
    settings = models.ForeignKey('ExamSettings', on_delete=models.CASCADE, related_name='exams_shifts',
                                 null=True, verbose_name=_('Exam Settings'), blank=False)
    start_date = models.DateTimeField(_('Shift Start Date'), null=True, blank=False)
    end_date = models.DateTimeField(_('Shift End Date'), null=True, blank=False)

    class Meta:
        ordering = ['settings', 'start_date', ]

    def __str__(self):
        return '%s (%s - %s)' % (self.start_date.date(),
                                 self.start_date.astimezone().time(),
                                 self.end_date.astimezone().time())

    @staticmethod
    def get_exam_day(exam_settings):
        if exam_settings:
            return exam_settings.exam_date.strftime('%A').lower()

    @staticmethod
    def get_shifts(exam_settings):
        return ExamShift.objects.filter(settings=exam_settings)

    @staticmethod
    def get_exam_periods_at_exam_date(exam_settings):
        exam_day = ExamShift.get_exam_day(exam_settings)

        return ScheduledPeriod.objects.filter(section__course_offering=exam_settings.fragment.course_offering,
                                              day__iexact=exam_day).values('start_time', 'end_time').distinct()

    def get_exam_rooms_for_exam_shift(self):
        exam_day = ExamShift.get_exam_day(self.settings)
        # TODO: make the location in ScheduledPeriod as an instance of Location(model) in enrollments app
        return ScheduledPeriod.objects.filter(section__course_offering=self.settings.fragment.course_offering,
                                              day__iexact=exam_day,
                                              start_time=self.start_date.astimezone().time(),
                                              end_time=self.end_date.astimezone().time()).values('location').distinct()

    @staticmethod
    def create_exam_rooms_for_shifts(exam_settings):
        ExamRoom.objects.filter(exam_shift__settings=exam_settings).delete()
        shifts = ExamShift.get_shifts(exam_settings)

        for shift in shifts:
            rooms = shift.get_exam_rooms_for_exam_shift()
            for room in rooms:
                location = room.get('location')
                if location:
                    exam_room, created = Room.objects.get_or_create(location=location)
                    ExamRoom.objects.create(exam_shift=shift, room=exam_room, capacity=exam_room.capacity)

    @staticmethod
    def create_shifts_for_exam_settings(exam_settings):
        ExamShift.get_shifts(exam_settings).delete()

        exam_date = exam_settings.exam_date
        periods = ExamShift.get_exam_periods_at_exam_date(exam_settings)

        for period in periods:
            shift = ExamShift()
            shift.settings = exam_settings
            shift.start_date = timezone.datetime(year=exam_date.year,
                                                 month=exam_date.month,
                                                 day=exam_date.day,
                                                 hour=period.get('start_time', timezone.now().time()).hour,
                                                 minute=period.get('start_time', timezone.now().time()).minute)
            shift.end_date = timezone.datetime(year=exam_date.year,
                                               month=exam_date.month,
                                               day=exam_date.day,
                                               hour=period.get('end_time', timezone.now().time()).hour,
                                               minute=period.get('end_time', timezone.now().time()).minute)
            shift.save()

    # FIXME: very expensive function in terms of performance. Needs REWORK
    def check_issues_in_timing(self, enrollment):
        # Check all the student periods (for the same course) in the exam date and make sure ...
        # the current exam shift falls in any of them
        exam_day = self.settings.exam_date.strftime('%A').lower()

        student_periods_at_exam_day = enrollment.section.scheduled_periods.filter(
            section__course_offering=self.settings.fragment.course_offering,
            day__iexact=exam_day
        ).values('start_time', 'end_time').distinct()

        no_issues_in_timing = False
        for period in student_periods_at_exam_day:
            if self.start_date.astimezone().time() >= period.get('start_time') and \
                     self.end_date.astimezone().time() <= period.get('end_time'):
                no_issues_in_timing = True
                break

        return no_issues_in_timing

    @property
    def get_max_number_of_students_placements_possible(self):
        if self.settings:
            enrollments = Enrollment.objects.filter(section__course_offering=self.settings.fragment.course_offering,
                                                    active=True)
            count = 0
            for enrollment in enrollments:
                if self.check_issues_in_timing(enrollment=enrollment):
                    count += 1
            return count


class ExamRoom(models.Model):
    exam_shift = models.ForeignKey('ExamShift', on_delete=models.CASCADE, related_name='exams', null=True,
                                   verbose_name=_('Exam Shift'), blank=False)
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='exams', null=True,
                             verbose_name=_('Exam Room'), blank=False)
    capacity = models.PositiveIntegerField(_('Room Capacity'), null=True, blank=False)

    def __str__(self):
        return '%s c(%d) %s' % (self.room.location, self.capacity, self.exam_shift)

    class Meta:
        ordering = ['exam_shift', 'room', ]

    @property
    def students_count(self):
        try:
            return self.students.count()
        except:
            return 0

    @property
    def remaining_seats(self):
        return self.capacity - self.students_count

    @property
    def remaining_seats_percentage(self):
        return (self.capacity - self.students_count)/self.capacity * 100

    def get_markers(self):
        return self.markers.all()

    def can_place_enrollment(self, enrollment):
        if self.remaining_seats > 0:
            if self.exam_shift.check_issues_in_timing(enrollment):

                number_of_markers = self.exam_shift.settings.number_of_markers
                hospitable = True

                for marker in self.get_markers():
                    if marker.order <= number_of_markers:  # tiebreakers don't follow this rule
                        hospitable = hospitable and marker.can_mark_enrollment(enrollment)
                return hospitable
            else:
                return False


class Marker(models.Model):
    instructor = models.ForeignKey('enrollment.Instructor', on_delete=models.SET_NULL, related_name='marking',
                                   null=True,
                                   verbose_name=_('Instructor'), blank=False)
    exam_room = models.ForeignKey('ExamRoom', on_delete=models.CASCADE, related_name='markers', null=True,
                                  verbose_name=_('Instructor'), blank=False)
    order = models.PositiveIntegerField(
        _('Marking Order'),
        help_text=_('This is the order in which after marker 1 finish the markings for marker 2 will start..'),
        null=True,
        blank=False
    )
    generosity_factor = models.DecimalField(
        _("Generosity Factor"),
        help_text=_('Generosity factor for this instructor, can be in minus. Make sure it is in percent'),
        null=True,
        blank=False,
        default=Decimal("0.00"),
        decimal_places=settings.MAX_DECIMAL_POINT,
        max_digits=settings.MAX_DIGITS,
        validators=(MinValueValidator(Decimal("-100.00")),
                    MaxValueValidator(Decimal("100.00")))
    )
    is_a_monitor = models.BooleanField(_('Is a Monitor?'), default=False)
    updated_by = models.ForeignKey(User, null=True, blank=True, verbose_name=_('Updated By'), on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True)

    history = HistoricalRecords()

    def __str__(self):
        return str(self.instructor)

    class Meta:
        ordering = ['exam_room', 'order', 'instructor', ]

    def is_the_tiebreaker(self):
        return self.order == self.exam_room.exam_shift.settings.number_of_markers + 1

    @staticmethod
    def create_markers_for_exam_settings(exam_settings):
        Marker.objects.filter(exam_room__exam_shift__settings=exam_settings).delete()

        exam_day = exam_settings.exam_date.strftime('%A').lower()

        markers_count = exam_settings.number_of_markers or 0
        rooms = ExamRoom.objects.filter(exam_shift__settings=exam_settings)
        allowed_markers_list = list(get_allowed_markers_for_a_fragment(exam_settings.fragment))

        for room in rooms:
            for i in range(1, markers_count + 2):
                marker = Marker(exam_room=room, order=i)
                if i == 1:
                    marker.is_a_monitor = True
                    instructors_assigned = ScheduledPeriod.objects.filter(
                        section__course_offering=exam_settings.fragment.course_offering,
                        day__iexact=exam_day,
                        start_time=room.exam_shift.start_date.astimezone().time(),
                        end_time=room.exam_shift.end_date.astimezone().time(),
                        location=room.room.location)
                    if instructors_assigned:
                        marker.instructor = instructors_assigned.first().instructor_assigned
                elif i == markers_count + 1:
                    if Marker.objects.filter(exam_room=room,
                                             instructor=exam_settings.default_tie_breaking_marker).count() == 0:
                        marker.instructor = exam_settings.default_tie_breaking_marker
                else:
                    for instructor_to_be_marker in allowed_markers_list:
                        if Marker.objects.filter(exam_room=room, instructor=instructor_to_be_marker).count() == 0 \
                                and instructor_to_be_marker != exam_settings.default_tie_breaking_marker:
                            marker.instructor = instructor_to_be_marker
                            allowed_markers_list.remove(instructor_to_be_marker)
                            break
                marker.save()

    def can_mark_enrollment(self, enrollment):
        if self.exam_room.exam_shift.settings.allow_markers_to_mark_own_students:
            return True
        else:
            return enrollment.section not in Section.get_instructor_sections(self.instructor)

    @property
    def marks_average(self):
        try:
            return decimal(self.markings.filter(
                student_placement__is_present=True).aggregate(Avg('mark')).get('mark__avg', 0.00))
        except:
            return 0.00

    @property
    def is_average_too_high_or_low(self):
        difference = self.exam_room.exam_shift.settings.overall_average - self.marks_average
        if abs(difference) >= self.exam_room.exam_shift.settings.markings_difference_tolerance:
            if difference < 0:
                return 'TOO-HIGH'
            else:
                return 'TOO-LOW'


class StudentPlacement(models.Model):
    enrollment = models.ForeignKey(
        'enrollment.Enrollment',
        on_delete=models.CASCADE,
        null=True,
        blank=False
    )
    exam_room = models.ForeignKey('ExamRoom', on_delete=models.CASCADE, related_name='students', null=True,
                                  verbose_name=_('Exam Room'), blank=False)
    is_present = models.BooleanField(_('Is Present?'), default=True)
    shuffled_by = models.ForeignKey(User, null=True, blank=True, verbose_name=_('Shuffled By'),
                                    on_delete=models.SET_NULL)
    shuffled_on = models.DateTimeField(_('Shuffled On'), auto_now=True)

    class Meta:
        ordering = ['enrollment', ]

    def __str__(self):
        return '%s %s' % (self.enrollment, self.exam_room)

    def are_marks_tolerable(self):
        difference_tolerance = self.exam_room.exam_shift.settings.markings_difference_tolerance

        first_mark = self.marks.filter(marker__order=1).first().weighted_mark
        second_mark = self.marks.filter(marker__order=2).first().weighted_mark

        return abs(first_mark - second_mark) <= difference_tolerance

    @property
    def final_mark(self):
        first_mark = self.marks.filter(marker__order=1).first().weighted_mark
        second_mark = self.marks.filter(marker__order=2).first().weighted_mark

        if first_mark and second_mark:
            if self.are_marks_tolerable():
                return (first_mark + second_mark) / 2
            else:
                third_mark = self.marks.filter(marker__order=3).first().weighted_mark
                if third_mark:
                    if abs(first_mark - third_mark) <= abs(second_mark - third_mark):
                        return (first_mark + third_mark) / 2
                    else:
                        return (second_mark + third_mark) / 2


class StudentMark(models.Model):
    student_placement = models.ForeignKey('StudentPlacement', on_delete=models.CASCADE, related_name='marks', null=True,
                                          verbose_name=_('Student Placement'), blank=False)
    marker = models.ForeignKey('Marker', on_delete=models.CASCADE, related_name='markings', null=True, blank=False)
    mark = models.DecimalField(
        _('Student Grade Quantity'),
        null=True,
        blank=True,
        decimal_places=settings.MAX_DECIMAL_POINT,
        max_digits=settings.MAX_DIGITS,
        validators=(MinValueValidator(Decimal("000.00")),
                    MaxValueValidator(Decimal("100.00")))
    )
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['student_placement', 'marker', ]

    def __str__(self):
        return '%s %s %s' % (self.student_placement, self.marker, self.mark)

    @property
    def weighted_mark(self):
        mark = self.mark or decimal(0)
        generosity_factor = self.marker.generosity_factor or decimal(0)

        if 0 <= mark + generosity_factor <= 100:
            return decimal(mark + generosity_factor)
        elif generosity_factor > 100:
            return decimal(100)
        else:
            return decimal(0)

    @staticmethod
    def get_unaccepted_marks(exam_settings):
        # NOTE: THIS IS THE MOST COMPLICATED QUERY I'VE EVER WRITTEN IN DJANGO ORM SO FAR
        # because of its complexity, I assumed it will be used in the case of 2 markers and a tiebreaker
        subquery_first_marker = StudentMark.objects.filter(student_placement=OuterRef('pk'), marker__order=1) \
            .annotate(weighted_mark=F('mark') + F('marker__generosity_factor'))
        subquery_second_marker = StudentMark.objects.filter(student_placement=OuterRef('pk'), marker__order=2) \
            .annotate(weighted_mark=F('mark') + F('marker__generosity_factor'))
        subquery_third_marker = StudentMark.objects.filter(student_placement=OuterRef('pk'), marker__order=3) \
            .annotate(weighted_mark=F('mark') + F('marker__generosity_factor'))

        student_placement_queryset = StudentPlacement.objects.filter(exam_room__exam_shift__settings=exam_settings) \
            .annotate(
            first_mark=Subquery(subquery_first_marker.values('weighted_mark')[:1]),
            second_mark=Subquery(subquery_second_marker.values('weighted_mark')[:1]),
            third_mark=Subquery(subquery_third_marker.values('mark')[:1]), ) \
            .annotate(
            marks_difference=Func(F('first_mark') - F('second_mark'), function='ABS', output_field=DecimalField())) \
            .filter(marks_difference__gt=exam_settings.markings_difference_tolerance)

        return StudentMark.objects.filter(student_placement__in=student_placement_queryset)
