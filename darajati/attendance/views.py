from extra_views import FormSetView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .forms import AttendanceForm
from .models import ScheduledPeriod, Attendance
from enrollment.utils import *
from enrollment.models import Section, Enrollment


class InstructorBaseView(LoginRequiredMixin, UserPassesTestMixin):

    """
    :InstructorBaseView:
    - check if the current user is instructor or superuser
    - redirect the current user even if he is AnonymousUser
    """
    # TODO: add a check for the active user
    def test_func(self):
        return self.request.user.profile.is_instructor

    def get_login_url(self):
        if self.request.user != "AnonymousUser":
            return reverse_lazy('enrollment:home')


class AttendanceView(InstructorBaseView, FormSetView):
    template_name = 'attendance/attendance.html'
    form_class = AttendanceForm
    extra = 0

    def get_initial(self, **kwargs):
        section_id = self.kwargs['section_id']
        day = None
        if self.kwargs['day']:
            day = self.kwargs['day']
        return Enrollment.get_students_enrollment(section_id, today(), self.request.user.profile.instructor, day)

    def get_context_data(self, **kwargs):
        context = super(AttendanceView, self).get_context_data(**kwargs)
        section_id = self.kwargs['section_id']
        day = None
        if self.kwargs['day']:
            day = self.kwargs['day']

        context['periods'] = ScheduledPeriod.get_section_periods(section_id, self.request.user.profile.instructor)
        period_date, context['current_periods'] = ScheduledPeriod.get_section_periods_of_nearest_day(
            section_id, self.request.user.profile.instructor, today(), day)
        context['enrollments'] = Attendance.get_student_attendance(section_id)
        return context

    def formset_valid(self, formset):
        for form in formset:
            form.user = self.request.user
            form.save()
        messages.success(self.request, _('Attendance was saved successfully'))
        return super(AttendanceView, self).formset_valid(formset)

    def get(self, request, *args, **kwargs):
        section_id = self.kwargs['section_id']
        ScheduledPeriod.get_section_periods(section_id, self.request.user.profile.instructor)
        return super(AttendanceView, self).get(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        section_id = self.kwargs['section_id']
        day = None
        if self.kwargs['day']:
            day = self.kwargs['day']
            return reverse_lazy('attendance:section_day_attendance',
                                kwargs={'section_id': section_id, 'day': day})

        return reverse_lazy('attendance:section_attendance',
                            kwargs={'section_id': section_id})
