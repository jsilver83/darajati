from django.forms import modelformset_factory, BaseFormSet
from django.shortcuts import redirect
from extra_views import ModelFormSetView
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from attendance.models import ScheduledPeriod
from .models import Section, Enrollment
from django.urls import reverse_lazy


class HomeView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        # TODO: redirect the new users to fill their information
        if request.user.profile.is_instructor:
            return redirect('enrollment:instructor')
        else:
            return redirect('enrollment:unauthorized')


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


class InstructorView(InstructorBaseView, ListView):

    context_object_name = 'sections'
    template_name = 'enrollment/instructor_sections.html'

    def get_queryset(self):

        # TODO: should be get all the currently in rolled section (For this year)
        query = Section.get_instructor_sections(self.request.user.profile.instructor)

        return query


class SectionStudentView(InstructorBaseView, ListView):
    context_object_name = 'enrollments'
    template_name = 'enrollment/section_students.html'

    def get_queryset(self, *args, **kwargs):
        section_id = self.kwargs['section_id']
        query = Enrollment.get_students(section_id)
        return query


class AttendanceView(InstructorBaseView, ListView):
    context_object_name = 'period'
    template_name = 'enrollment/period_details.html'

    def get_queryset(self, *args, **kwargs):
        period_id = self.kwargs['section_id']
        query = ScheduledPeriod.get_period(period_id)
        return query


# Formset factory
# class HomeView(ModelFormSetView):
#     template_name = 'enrollment/attendance.html'
#     model = Attendance
#     form_class = AttendanceForm
#     success_url = '/'
#     can_delete = True
#     queryset = Attendance.objects.filter(id=5)
#     extra = 1
#
#     def formset_valid(self, formset):
#         return super(HomeView, self).formset_valid(formset)
