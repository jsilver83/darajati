from extra_views import FormSetView, ModelFormSetView
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .models import GradeFragment, StudentGrade
from .forms import GradesForm

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
    grade_fragment_id = None
    grade_fragment = None
    grade_fragment_deadline = None

    # TODO: add a check for the active user

    def test_func(self, **kwargs):
        self.section_id = self.kwargs['section_id']
        self.section = Section.get_section(self.section_id)
        is_instructor_section = self.section.is_instructor_section(self.request.user.profile.is_instructor, now())

        if not self.section:
            messages.error(self.request, _('Please enter a valid section'))
            return self.section and self.request.user.profile.is_instructor

        if not self.section.is_instructor_section(self.request.user.profile.is_instructor, now()):
            messages.error(self.request, _('The requested section do not belong to you, or it is out of this semester'))

            return self.section and self.request.user.profile.is_instructor and is_instructor_section

        if self.section.course_offering.semester.grade_fragment_deadline <= now():
            self.grade_fragment_deadline = True

        else:
            messages.error(self.request, _('You can not access grades currently'))

        return self.section and self.request.user.profile.is_instructor and self.grade_fragment_deadline

    def get_login_url(self):
        if self.request.user != "AnonymousUser":
            return reverse_lazy('enrollment:home')


class GradeFragmentView(InstructorBaseView, ListView):
    template_name = 'grade/grade_fragments.html'
    context_object_name = 'grade_fragments'

    def get_queryset(self):
        return GradeFragment.get_section_grade_fragments(self.section)

    def get_context_data(self):
        context = super(GradeFragmentView, self).get_context_data()
        context['section_id'] = self.section_id
        return context


class GradesView(InstructorBaseView, ModelFormSetView):
    template_name = 'grade/grades.html'
    model = StudentGrade
    form_class = GradesForm
    extra = 0

    def test_func(self, **kwargs):
        test_roles = super(GradesView, self).test_func(**kwargs)
        self.grade_fragment_id = self.kwargs['grade_fragment_id']
        self.grade_fragment = GradeFragment.get_grade_fragment(self.grade_fragment_id)
        if not self.grade_fragment:
            messages.error(self.request, _('Please enter a valid grade plan'))
            return test_roles and self.grade_fragment

        if not self.grade_fragment.allow_entry:
            messages.error(self.request, _('You are not allowed to enter the marks'))
            return test_roles and self.grade_fragment.allow_entry

        return test_roles and self.grade_fragment and self.grade_fragment.allow_entry

    def get_queryset(self):
        return StudentGrade.get_section_grades(self.section_id, self.grade_fragment_id)

    def get_context_data(self, **kwargs):
        context = super(GradesView, self).get_context_data(**kwargs)
        context['enrollments'] = Enrollment.get_students(self.section_id)
        context['section_average'] = StudentGrade.get_section_average(self.section, self.grade_fragment)
        return context
