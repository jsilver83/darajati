from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import OuterRef, F, Subquery, Func, DecimalField
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from enrollment.models import Coordinator, Instructor, Section, ScheduledPeriod, Enrollment

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


class ExamShift(models.Model):
    fragment = models.ForeignKey('grade.GradeFragment', on_delete=models.CASCADE, related_name='exams_shifts',
                                 null=True, verbose_name=_('Fragment'), blank=False)
    start_date = models.DateTimeField(_('Shift Start Date'), null=True, blank=False)
    end_date = models.DateTimeField(_('Shift End Date'), null=True, blank=False)

    class Meta:
        ordering = ['fragment', 'start_date', ]

    def __str__(self):
        return '%s (%s - %s)' % (self.start_date.date(),
                                 self.start_date.astimezone().time(),
                                 self.end_date.astimezone().time())

    @staticmethod
    def get_shifts(fragment):
        return ExamShift.objects.filter(fragment=fragment)

    @staticmethod
    def get_exam_periods_at_exam_date(fragment):
        exam_day = fragment.exam_date.strftime('%A').lower()

        return ScheduledPeriod.objects.filter(section__course_offering=fragment.course_offering,
                                              day__iexact=exam_day).values('start_time', 'end_time').distinct()

    @staticmethod
    def get_exam_rooms_for_exam_shift(shift):
        exam_day = shift.fragment.exam_date.strftime('%A').lower()
        # TODO: make the location in ScheduledPeriod as an instance of Location(model) in enrollments app
        return ScheduledPeriod.objects.filter(section__course_offering=shift.fragment.course_offering,
                                              day__iexact=exam_day,
                                              start_time=shift.start_date.astimezone().time(),
                                              end_time=shift.end_date.astimezone().time()).values('location').distinct()

    @staticmethod
    def create_exam_rooms_for_shifts(fragment):
        ExamRoom.objects.filter(exam_shift__fragment=fragment).delete()
        shifts = ExamShift.get_shifts(fragment)

        for shift in shifts:
            rooms = ExamShift.get_exam_rooms_for_exam_shift(shift)
            for room in rooms:
                location = room.get('location')
                if location:
                    exam_room, created = Room.objects.get_or_create(location=location)
                    ExamRoom.objects.create(exam_shift=shift, room=exam_room, capacity=exam_room.capacity)

    @staticmethod
    def create_shifts_for_fragment(fragment):
        ExamShift.get_shifts(fragment).delete()

        exam_date = fragment.exam_date
        periods = ExamShift.get_exam_periods_at_exam_date(fragment)

        for period in periods:
            shift = ExamShift()
            shift.fragment = fragment
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
        return len(self.students.all())

    @property
    def remaining_seats(self):
        return self.capacity - self.students_count

    def get_markers(self):
        return self.markers.all()

    def can_place_enrollment(self, enrollment):
        # Check all the student periods (for the same course) in the exam date and make sure ...
        # the current exam shift falls in any of them
        exam_day = self.exam_shift.fragment.exam_date.strftime('%A').lower()

        student_periods_at_exam_day = enrollment.section.scheduled_periods.filter(
            section__course_offering=self.exam_shift.fragment.course_offering,
            day__iexact=exam_day
        ).values('start_time', 'end_time').distinct()

        no_issue_in_timing = False
        for period in student_periods_at_exam_day:
            if self.exam_shift.start_date.astimezone().time() >= period.get('start_time') and \
                    self.exam_shift.end_date.astimezone().time() >= period.get('end_time'):
                no_issue_in_timing = True
                break

        if no_issue_in_timing:
            number_of_markers = self.exam_shift.fragment.number_of_markers
            hospitable = True

            for marker in self.get_markers():
                if marker.order < number_of_markers:  # tiebreakers don't follow this rule
                    hospitable = hospitable and marker.can_mark_enrollment(enrollment)
            return hospitable
        else:
            return False


class Marker(models.Model):
    instructor = models.ForeignKey('enrollment.Instructor', on_delete=models.SET_NULL, related_name='marking', null=True,
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

    def __str__(self):
        return str(self.instructor)

    class Meta:
        ordering = ['exam_room', 'order', 'instructor', ]

    def is_the_tiebreaker(self):
        return self.order == self.exam_room.exam_shift.fragment.number_of_markers + 1

    @staticmethod
    def create_markers_for_fragment(fragment):
        Marker.objects.filter(exam_room__exam_shift__fragment=fragment).delete()

        exam_day = fragment.exam_date.strftime('%A').lower()

        markers_count = fragment.number_of_markers
        markers_count = markers_count if markers_count else 0
        rooms = ExamRoom.objects.filter(exam_shift__fragment=fragment)
        for room in rooms:
            for i in range(1, markers_count + 2):
                marker = Marker(exam_room=room, order=i)
                if i == 1:
                    marker.is_a_monitor = True
                    instructors_assigned = ScheduledPeriod.objects.filter(
                        section__course_offering=fragment.course_offering,
                        day__iexact=exam_day,
                        start_time=room.exam_shift.start_date.astimezone().time(),
                        end_time=room.exam_shift.end_date.astimezone().time(),
                        location=room.room.location)
                    if instructors_assigned:
                        marker.instructor = instructors_assigned.first().instructor_assigned
                elif i == markers_count + 1:
                    marker.instructor = fragment.default_tie_breaking_marker
                marker.save()

    def can_mark_enrollment(self, enrollment):
        if self.exam_room.exam_shift.fragment.allow_markers_to_mark_own_students:
            return True
        else:
            return enrollment.section not in Section.get_instructor_sections(self.instructor)


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
    shuffled_by = models.ForeignKey(User, null=True, blank=True, verbose_name=_('Shuffled By'), on_delete=models.SET_NULL)
    shuffled_on = models.DateTimeField(_('Shuffled On'), auto_now=True)

    class Meta:
        ordering = ['enrollment', ]

    def __str__(self):
        return '%s %s' % (self.enrollment, self.exam_room)

    def are_marks_tolerable(self):
        difference_tolerance = self.exam_room.exam_shift.fragment.markings_difference_tolerance

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

    class Meta:
        ordering = ['student_placement', 'marker', ]

    def __str__(self):
        return '%s %s %s' % (self.student_placement, self.marker, self.mark)

    @property
    def weighted_mark(self):
        mark = self.mark if self.mark else Decimal(0)
        generosity_factor = self.marker.generosity_factor if self.marker.generosity_factor else Decimal(0)
        return mark + generosity_factor

    @staticmethod
    def get_unaccepted_marks(fragment):
        # NOTE: THIS IS THE MOST COMPLICATED QUERY I'VE EVER WRITTEN IN DJANGO ORM SO FAR
        # because of its complexity, I assumed it will be used in the case of 2 markers and a tiebreaker
        subquery_first_marker = StudentMark.objects.filter(student_placement=OuterRef('pk'), marker__order=1)\
            .annotate(weighted_mark=F('mark') + F('marker__generosity_factor'))
        subquery_second_marker = StudentMark.objects.filter(student_placement=OuterRef('pk'), marker__order=2)\
            .annotate(weighted_mark=F('mark') + F('marker__generosity_factor'))
        subquery_third_marker = StudentMark.objects.filter(student_placement=OuterRef('pk'), marker__order=3)\
            .annotate(weighted_mark=F('mark') + F('marker__generosity_factor'))

        student_placement_queryset = StudentPlacement.objects.filter(exam_room__exam_shift__fragment=fragment)\
            .annotate(
            first_mark=Subquery(subquery_first_marker.values('weighted_mark')[:1]),
            second_mark=Subquery(subquery_second_marker.values('weighted_mark')[:1]),
            third_mark=Subquery(subquery_third_marker.values('mark')[:1]), )\
            .annotate(
            marks_difference=Func(F('first_mark') - F('second_mark'), function='ABS', output_field=DecimalField()))\
            .filter(marks_difference__gt=fragment.markings_difference_tolerance)

        return StudentMark.objects.filter(student_placement__in=student_placement_queryset)
