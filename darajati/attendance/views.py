from extra_views import FormSetView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .forms import AttendanceForm
from .models import ScheduledPeriod, Attendance

from enrollment.utils import today
from enrollment.models import Enrollment, Section


class InstructorBaseView(LoginRequiredMixin, UserPassesTestMixin):

    """
    :InstructorBaseView:
    - check if the current user is instructor or superuser
    - redirect the current user even if he is AnonymousUser
    """
    section_id = None
    section = None
    day = None
    # TODO: add a check for the active user

    def test_func(self, **kwargs):
        self.section_id = self.kwargs['section_id']
        self.section = Section.get_section(self.section_id)
        if self.kwargs['day']:
            self.day = self.kwargs['day']
        return self.section and self.request.user.profile.is_instructor

    def get_login_url(self):
        if self.request.user != "AnonymousUser":
            return reverse_lazy('enrollment:home')


class AttendanceView(InstructorBaseView, FormSetView):
    template_name = 'attendance/attendance.html'
    form_class = AttendanceForm
    extra = 0

    def get_initial(self):
        return Enrollment.get_students_enrollment(self.section_id, today(), self.request.user.profile.instructor,
                                                  self.day)

    def get_context_data(self, **kwargs):
        context = super(AttendanceView, self).get_context_data(**kwargs)
        context['periods'] = ScheduledPeriod.get_section_periods(self.section_id, self.request.user.profile.instructor)
        day, period_date, context['current_periods'] = ScheduledPeriod.get_section_periods_of_nearest_day(
            self.section_id, self.request.user.profile.instructor, today(), self.day)
        context['current_day'] = day
        context['enrollments'] = Attendance.get_student_attendance(self.section_id)
        return context

    def get_extra_form_kwargs(self):
        kwargs = super(AttendanceView, self).get_extra_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def formset_valid(self, formset):
        for form in formset:
            form.user = self.request.user
            saved_form = form.save(commit=False)
            if saved_form:
                saved_form.save()
        messages.success(self.request, _('Attendance were saved successfully'))
        return super(AttendanceView, self).formset_valid(formset)

    def get(self, request, *args, **kwargs):
        ScheduledPeriod.get_section_periods(self.section_id, self.request.user.profile.instructor)
        return super(AttendanceView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        if self.day:
            return reverse_lazy('attendance:section_day_attendance',
                                kwargs={'section_id': self.section_id, 'day': self.day})

        return reverse_lazy('attendance:section_attendance',
                            kwargs={'section_id': self.section_id})
