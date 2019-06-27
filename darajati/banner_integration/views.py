from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from enrollment.models import CourseOffering, Coordinator
from grade.models import GradeFragment, StudentGrade
from enrollment.views import CoordinatorBaseView
from .forms import BannerSynchronizationForm, GradesImportForm
from .utils import synchronization


class BannerSynchronizationView(CoordinatorBaseView, FormView):
    form_class = BannerSynchronizationForm
    template_name = 'banner_integration/banner_synchronization.html'
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
        kwargs.update(choices=Coordinator.get_active_coordinated_course_offerings_choices(self.request.user.instructor))
        return kwargs

    def form_valid(self, form, **kwargs):
        context = self.get_context_data(**kwargs)

        if 'preview' in self.request.POST:
            sync_report = synchronization(course_offering_pk=form.cleaned_data['course_offering'],
                                          current_user=self.request.user,
                                          commit=False,
                                          first_week_mode=form.cleaned_data['first_week_mode'], )
            context['previewed'] = True

            context['enrollments_changes_report'] = sync_report[0]
            context['sections_changes_report'] = sync_report[1]
            context['periods_changes_report'] = sync_report[2]
            context['serious_issues'] = sync_report[3]
            messages.warning(self.request, _('Kindly review the synchronization report below carefully before '
                                             'committing the changes. If you commit the changes listed in the report '
                                             'below, you can NOT roll them back'))
            return self.render_to_response(context)

        else:  # if 'commit' in self.request.POST:
            try:
                synchronization(course_offering_pk=form.cleaned_data['course_offering'],
                                current_user=self.request.user,
                                commit=True,
                                first_week_mode=form.cleaned_data['first_week_mode'], )
                messages.success(self.request, _('The synchronization changes were committed successfully'))
            except:
                messages.error(self.request, _('We tried to commit the synchronization changes'))

            return redirect('banner_integration:synchronization')


class ImportGradesView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = GradesImportForm
    template_name = 'banner_integration/import_grades.html'
    success_url = reverse_lazy('banner_integration:home')

    def test_func(self):
        return self.request.user.is_superuser

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
