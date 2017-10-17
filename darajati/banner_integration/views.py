from decimal import Decimal
from django.contrib import messages
from django.views.generic import FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .forms import CourseOfferingForm, GradesImportForm
from .utils import initial_roster_creation, initial_faculty_teaching_creation

from enrollment.models import CourseOffering
from grade.models import GradeFragment, StudentGrade


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'banner_integration/home.html'


class PopulationRosterView(LoginRequiredMixin, FormView):
    form_class = CourseOfferingForm
    template_name = 'banner_integration/roster_populate.html'
    success_url = reverse_lazy('banner_integration:home')

    section_report = None
    student_report = None
    enrollment_report = None

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
        self.section_report, self.student_report, self.enrollment_report, = initial_roster_creation(
            form.cleaned_data['course_offering'],
            form.cleaned_data['commit_changes'])

        self.instructors, self.periods = initial_faculty_teaching_creation(
            form.cleaned_data['course_offering'],
            self.section_report,
            form.cleaned_data['commit_changes'])

        context = self.get_context_data(**kwargs)
        context['sections_report'] = self.section_report
        context['enrollments_report'] = self.enrollment_report
        context['periods'] = self.periods

        context['detail_report'] = False
        context['report'] = False

        if context['sections_report'] or context['enrollments_report'] or context['periods']:
            context['report'] = True

        if form.cleaned_data.get('detail_report'):
            context['detail_report'] = True

        return self.render_to_response(context)


class ImportGradesView(LoginRequiredMixin, FormView):
    form_class = GradesImportForm
    template_name = 'banner_integration/import_grades.html'
    success_url = reverse_lazy('banner_integration:home')

    def get_form_kwargs(self):
        """
        Passing the only current semester's Offering Courses List 
        """
        kwargs = super().get_form_kwargs()
        kwargs.update(choices=GradeFragment.get_all_fragments_choices())
        return kwargs

    def form_valid(self, form, **kwargs):
        fragment = form.cleaned_data['grade_fragment']
        fragment = GradeFragment.objects.get(id=fragment)
        context = self.get_context_data(**kwargs)
        context['list'], context['errors'] = StudentGrade.import_grades_by_admin(
            form.cleaned_data['grade'],
            fragment,
            form.cleaned_data['commit']
        )

        return self.render_to_response(context)
