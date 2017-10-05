from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .forms import CourseOfferingForm
from .utils import initial_roster_creation, initial_faculty_teaching_creation

from enrollment.models import CourseOffering


class PopulationRosterView(LoginRequiredMixin, FormView):
    form_class = CourseOfferingForm
    template_name = 'banner_integration/roster_populate.html'
    success_url = reverse_lazy('banner_integration:home')

    section_report = None
    student_report = None
    enrollment_report = None
    inactive_sections_count = None

    instructors = None
    periods = None

    def get_form_kwargs(self):
        """
        Passing the only current semester's Offering Courses List 
        """
        kwargs = super().get_form_kwargs()
        kwargs.update(choices=CourseOffering.get_current_course_offerings())
        return kwargs

    def form_valid(self, form, **kwargs):
        """
        This will consist of the creation of the sections and assigning students to these section
          From there Faculty will be assigned to that section.
        """
        self.section_report, \
        self.student_report, \
        self.enrollment_report, \
        self.inactive_sections_count = initial_roster_creation(
            form.cleaned_data['course_offering'],
            form.cleaned_data['commit_changes'])

        self.instructors, self.periods = initial_faculty_teaching_creation(
            form.cleaned_data['course_offering'],
            form.cleaned_data['commit_changes'])

        context = self.get_context_data(**kwargs)

        context['report'] = False
        context['comment'] = _("There are no changes")
        if self.section_report or self.student_report \
                or self.enrollment_report or self.inactive_sections_count:
            context['report'] = True
            context['section_report'] = self.section_report
            context['student_report'] = self.student_report
            context['enrollment_report'] = self.enrollment_report
            context['inactive_sections_count'] = self.inactive_sections_count
            context['detail_report'] = False
            if form.cleaned_data['detail_report']:
                context['detail_report'] = True

        if self.instructors or self.periods:
            context['instructors'] = self.instructors
            context['periods'] = self.periods

        return self.render_to_response(context)
