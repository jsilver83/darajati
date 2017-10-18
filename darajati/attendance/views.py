from extra_views import FormSetView
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
    year = None
    month = None
    day = None
    date = None

    def dispatch(self, request, *args, **kwargs):
        self.date = today()
        if self.kwargs.get('year') and self.kwargs.get('month') and self.kwargs.get('day'):
            self.year = self.kwargs['year']
            self.month = self.kwargs['month']
            self.day = self.kwargs['day']
            self.date = parse_date('{}-{}-{}'.format(self.year, self.month, self.day))
        return super(AttendanceBaseView, self).dispatch(request, *args, **kwargs)

    def test_func(self, **kwargs):
        rule = super(AttendanceBaseView, self).test_func(**kwargs)
        if rule:
            offset_date, day = get_offset_day(today(), -self.section.course_offering.attendance_entry_window)

            if self.date <= today():
                if offset_date <= self.date and \
                                        self.section.course_offering.semester.start_date <= self.date <= self.section.course_offering.semester.end_date:
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
        return Enrollment.get_students_enrollment(self.section_id,
                                                  self.request.user.profile.instructor,
                                                  self.date)

    def formset_valid(self, formset):
        for form in formset:
            form.user = self.request.user
            saved_form = form.save(commit=False)
            if saved_form:
                saved_form.save()
        messages.success(self.request, _('Attendance were saved successfully'))
        return super(AttendanceView, self).formset_valid(formset)

    def get_context_data(self, **kwargs):
        context = super(AttendanceView, self).get_context_data(**kwargs)
        context['periods'], context['previous_week'], context[
            'next_week'] = ScheduledPeriod.get_section_periods_week_days(
            self.section,
            self.request.user.profile.instructor,
            self.date,
            today())

        day, period_date, context['current_periods'] = ScheduledPeriod.get_section_periods_of_nearest_day(
            self.section_id,
            self.request.user.profile.instructor,
            self.date)
        context['current_date'] = period_date
        context['today'] = today()
        context['enrollments'] = Attendance.get_student_attendance(self.section_id)
        context['section'] = self.section
        return context

    def get_extra_form_kwargs(self):
        kwargs = super(AttendanceView, self).get_extra_form_kwargs()
        kwargs.update({'request': self.request, 'section': self.section})
        return kwargs

    def get_success_url(self):
        if self.day:
            return reverse_lazy('attendance:section_day_attendance',
                                kwargs={'section_id': self.section_id, 'year': self.year, 'month': self.month,
                                        'day': self.day})

        return reverse_lazy('attendance:section_attendance',
                            kwargs={'section_id': self.section_id})
