from extra_views import FormSetView
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.utils.dateparse import parse_date
from .forms import AttendanceForm
from .models import ScheduledPeriod, Attendance

from enrollment.utils import today, day_string, get_offset_day
from enrollment.models import Enrollment
from enrollment.views import InstructorBaseView


class AttendanceBaseView(InstructorBaseView):
    """
    This is where handling date checking and attendance entry windows
    """
    year = None
    month = None
    day = None
    date = None

    def dispatch(self, request, *args, **kwargs):
        """
        We will set self.date to the passed year, month and date within the url so it can be used within all views. 
        """
        self.date = today()
        if self.kwargs.get('year') and self.kwargs.get('month') and self.kwargs.get('day'):
            self.year, self.month, self.day = self.kwargs['year'], self.kwargs['month'], self.kwargs['day']
            self.date = parse_date('{}-{}-{}'.format(self.year, self.month, self.day))
        return super(AttendanceBaseView, self).dispatch(request, *args, **kwargs)

    def test_func(self, **kwargs):
        rule = super(AttendanceBaseView, self).test_func(**kwargs)
        if rule:
            offset_date, day = get_offset_day(today(), -self.section.course_offering.attendance_entry_window)
            if self.date <= today():
                if self.section.course_offering.semester.check_is_accessible_date(self.date, offset_date):
                    return True
                else:
                    messages.error(self.request,
                                   _('You have passed the allowed time to be able to get to this day'))
                    return False
            else:
                messages.error(self.request,
                               _('You are trying to access a day in the future'))
                return False


class AttendanceView(AttendanceBaseView, FormSetView):
    template_name = 'attendance/attendance.html'
    form_class = AttendanceForm
    extra = 0

    def get_initial(self):
        if self.coordinator:
            return Enrollment.get_students_enrollment(self.section_id, self.date)
        return Enrollment.get_students_enrollment(self.section_id, self.date, self.request.user.instructor)

    def formset_valid(self, formset):
        for form in formset:
            form.user = self.request.user
            saved_form = form.save(commit=False)
            if saved_form:
                saved_form.save()
        messages.success(self.request, _('Attendance were saved successfully'))
        return super(AttendanceView, self).formset_valid(formset)

    # FIXME: I know i look nice-ish but i wanna be more nicer when you have time fix me please
    def get_context_data(self, **kwargs):
        context = super(AttendanceView, self).get_context_data(**kwargs)
        self.day, period_date = ScheduledPeriod.get_nearest_day_and_date(
            self.section_id,
            self.date,
            self.request.user.instructor.is_coordinator_or_instructor()
        )

        context['periods'], context['previous_week'], context[
            'next_week'] = ScheduledPeriod.get_section_periods_week_days(
            self.section,
            self.request.user.instructor.is_coordinator_or_instructor(),
            self.date,
            today())

        context['current_periods'] = ScheduledPeriod.get_section_periods_of_day(
            self.section_id,
            self.day,
            self.request.user.instructor.is_coordinator_or_instructor()).order_by('start_time')

        context['current_date'] = period_date
        context['today'] = today()
        return context

    def get_extra_form_kwargs(self):
        kwargs = super(AttendanceView, self).get_extra_form_kwargs()
        kwargs.update({'request': self.request, 'section': self.section})
        return kwargs

    def get_success_url(self):
        kwargs = {'section_id': self.section_id}
        if self.day:
            kwargs = {'section_id': self.section_id,
                      'year': self.year,
                      'month': self.month,
                      'day': self.day}
        return reverse_lazy('attendance:section_attendance', kwargs=kwargs)


class StudentAttendanceSummaryView(InstructorBaseView, ListView):
    template_name = 'attendance/student_attendance_summary.html'
    model = Attendance
    context_object_name = 'attendances'
    enrollment_id = None

    def test_func(self, **kwargs):
        rule = super(StudentAttendanceSummaryView, self).test_func(**kwargs)
        if rule:
            self.enrollment_id = self.kwargs['enrollment_id']
            return True
        return False

    def get_queryset(self):
        queryset = super(StudentAttendanceSummaryView, self).get_queryset()
        return queryset.filter(enrollment=self.enrollment_id, attendance_instance__period__section=self.section)

    def get_context_data(self, **kwargs):
        context = super(StudentAttendanceSummaryView, self).get_context_data(**kwargs)
        context.update({
            'enrollment': Enrollment.objects.get(id=self.enrollment_id),
            'section': self.section
        })
        return context
