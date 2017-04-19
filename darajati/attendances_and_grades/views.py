from django.core.exceptions import ObjectDoesNotExist
from django.forms import modelformset_factory, BaseFormSet
from django.shortcuts import redirect
from extra_views import ModelFormSetView
from django.views.generic import FormView, View, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import *


class HomeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.profile.is_instructor or request.user.is_superuser:
            return redirect('attendances_and_grades:instructor')
        else:
            return redirect('attendances_and_grades:unauthorized')


class InstructorBaseView(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.profile.is_instructor or self.request.user.is_superuser


class InstructorView(InstructorBaseView, ListView):
    context_object_name = 'scheduled_periods'
    template_name = 'attendances_and_grades/instructor_sections.html'

    def get_queryset(self):

        if self.request.user.is_superuser:
            query = ScheduledPeriod.get_periods()
            return query
        if self.request.user.profile.is_instructor:
            query = ScheduledPeriod.get_instructor_period(self.request.user.profile.instructor)
            return query


class ScheduledPeriodView(InstructorBaseView, ListView):
    context_object_name = 'period'
    template_name = 'attendances_and_grades/period_details.html'

    def get_queryset(self, *args, **kwargs):
        period_id = self.kwargs['period_id']
        query = ScheduledPeriod.get_period(period_id)
        return query


class SectionStudentView(InstructorBaseView, ListView):
    pass

# Formset factory
# class HomeView(ModelFormSetView):
#     template_name = 'attendances_and_grades/attendance.html'
#     model = Attendance
#     form_class = AttendanceForm
#     success_url = '/'
#     can_delete = True
#     queryset = Attendance.objects.filter(id=5)
#     extra = 1
#
#     def formset_valid(self, formset):
#         return super(HomeView, self).formset_valid(formset)
