from extra_views import FormSetView, ModelFormSetView
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .models import GradeBreakDown, StudentGrade

from enrollment.models import Enrollment, Section
from enrollment.utils import now


class InstructorBaseView(LoginRequiredMixin, UserPassesTestMixin):

    """
    :InstructorBaseView:
    - check if the current user is instructor or superuser
    - redirect the current user even if he is AnonymousUser
    """
    section_id = None
    section = None
    grade_break_down_id = None
    grade_break_down = None
    grade_break_down_deadline = None
    # TODO: add a check for the active user

    def test_func(self, **kwargs):
        self.section_id = self.kwargs['section_id']
        self.section = Section.get_section(self.section_id)
        if not self.section:
            messages.error(self.request, _('Please enter a valid section'))
            return self.section and self.request.user.profile.is_instructor

        if self.section.semester.grade_break_down_deadline <= now():  # or self.request.user.is_superuser:
            self.grade_break_down_deadline = True
        else:
            messages.error(self.request, _('You can not access grades currently'))

        return self.section and self.request.user.profile.is_instructor and self.grade_break_down_deadline

    def get_login_url(self):
        if self.request.user != "AnonymousUser":
            return reverse_lazy('enrollment:home')


class GradeBreakDownView(InstructorBaseView, ListView):
    template_name = 'grade/grade_break_down.html'
    context_object_name = 'grades_break_down'

    def get_queryset(self):
        return GradeBreakDown.get_section_grade_break_down(self.section)

    def get_context_data(self):
        context = super(GradeBreakDownView, self).get_context_data()
        context['section_id'] = self.section_id
        return context


class BreakDownGradesView(InstructorBaseView, ModelFormSetView):
    template_name = 'grade/enrollments_grades.html'
    model = StudentGrade
    fields = ['enrollment', 'grade_break_down', 'grade_quantity', 'remarks']
    extra = 0

    def test_func(self, **kwargs):
        test_roles = super(BreakDownGradesView, self).test_func(**kwargs)
        self.grade_break_down_id = self.kwargs['grade_break_down_id']
        self.grade_break_down = GradeBreakDown.get_grade_break_down(self.grade_break_down_id)
        if not self.grade_break_down:
            messages.error(self.request, _('Please enter a valid grade plan'))

        return test_roles and self.grade_break_down

    def get_queryset(self):
        return StudentGrade.get_section_break_down_grades(self.section_id, self.grade_break_down_id)

    def get_context_data(self, **kwargs):
        context = super(BreakDownGradesView, self).get_context_data(**kwargs)
        context['enrollment'] = Enrollment.get_students(self.section_id)
        return context
