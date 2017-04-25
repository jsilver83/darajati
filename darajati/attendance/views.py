import calendar

from extra_views import FormSetView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .forms import AttendanceForm
from .models import Attendance, ScheduledPeriod, AttendanceInstant
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
        return Enrollment.get_students_enrollment(section_id)

    def get_context_data(self, **kwargs):
        context = super(AttendanceView, self).get_context_data(**kwargs)
        section_id = self.kwargs['section_id']
        context['periods'] = ScheduledPeriod.get_section_periods(section_id, self.request.user.profile.instructor)
        return context

    def formset_invalid(self, formset):
        print(formset.errors)
        print("Invalid")
        exit()

    def formset_valid(self, formset):
        print(formset)
        print("Valid")
        exit()

    def get(self, request, *args, **kwargs):
        section_id = self.kwargs['section_id']
        ScheduledPeriod.get_section_periods(section_id, self.request.user.profile.instructor)
        return super(AttendanceView, self).get(request, *args, **kwargs)

