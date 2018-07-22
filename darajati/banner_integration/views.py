from django.views.generic import FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .forms import CourseOfferingForm, GradesImportForm
from .utils import Synchronization

from enrollment.models import CourseOffering
from grade.models import GradeFragment, StudentGrade


class PopulationRosterView(LoginRequiredMixin, FormView):
    form_class = CourseOfferingForm
    template_name = 'banner_integration/roster_populate.html'
    success_url = reverse_lazy('banner_integration:home')

    section_report = None
    student_report = None
    enrollment_report = None

    instructors = None
    periods = None
    sections = None

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
        sync = Synchronization(form.cleaned_data['course_offering'], self.sections, form.cleaned_data['commit_changes'])
        sync.roaster_initiation()
        sync.faculty_initiation()
        sync.faculties_periods_report()

        context = self.get_context_data(**kwargs)
        context['sections_report'] = sync.sections_report()
        context['enrollments_report'] = sync.enrollments_report()
        context['periods'] = sync.faculties_periods_report()

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
