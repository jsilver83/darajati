import calendar

from extra_views import ModelFormSetView
from django.forms import formset_factory
from django.views.generic import ListView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .forms import AttendanceForm
from .models import Attendance, ScheduledPeriod
from enrollment.models import Section, Enrollment
from datetime import datetime


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


class AttendanceView(InstructorBaseView, ListView):
    template_name = 'attendance/attendance.html'
    context_object_name = 'periods'

    def get_context_data(self, **kwargs):
        context = super(AttendanceView, self).get_context_data(**kwargs)
        section_id = self.kwargs['section_id']
        # enrollments = Enrollment.get_students(section_id)
        # current_date = datetime.today()
        # cd_weekday = calendar.day_name[current_date.weekday()]
        # print(cd_weekday)
        attendance_form_set = formset_factory(AttendanceForm, extra=0)
        context['forms'] = attendance_form_set(initial=Enrollment.get_students_enrollment(section_id))
        return context

    def get_queryset(self, *args, **kwargs):
        section_id = self.kwargs['section_id']
        query = ScheduledPeriod.get_section_periods(section_id, self.request.user.profile.instructor)
        return query
