from extra_views import ModelFormSetView
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .models import GradeFragment, StudentGrade
from .forms import GradesForm, GradeFragmentForm, BaseGradesFormSet

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

        # Valid Section
        if not self.section:
            messages.error(self.request, _('Please enter a valid section'))
            return self.section and self.request.user.profile.is_instructor

        # Is this section belong to this instructor
        is_instructor_section = self.section.is_instructor_section(self.request.user.profile.instructor, now())
        if not is_instructor_section and not self.request.user.is_superuser:
            messages.error(self.request, _('The requested section do not belong to you, or it is out of this semester'))
            return self.section and self.request.user.profile.is_instructor and is_instructor_section

        return self.section and self.request.user.profile.is_instructor and is_instructor_section

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
        context['section'] = self.section
        return context


class GradesView(InstructorBaseView, ModelFormSetView):
    template_name = 'grade/grades.html'
    model = StudentGrade
    form_class = GradesForm
    formset_class = BaseGradesFormSet
    extra = 0

    def test_func(self, **kwargs):
        test_roles = super(GradesView, self).test_func(**kwargs)
        self.grade_fragment_id = self.kwargs['grade_fragment_id']
        self.grade_fragment = GradeFragment.get_grade_fragment(self.grade_fragment_id)

        if not self.grade_fragment:
            messages.error(self.request, _('Please enter a valid grade plan'))
            return test_roles and self.grade_fragment

        if not self.grade_fragment.allow_entry and not self.request.user.is_superuser:
            messages.error(self.request, _('You are not allowed to enter the marks'))
            return test_roles and self.grade_fragment.allow_entry

        return test_roles and self.grade_fragment

    def get_queryset(self):
        return StudentGrade.get_section_grades(self.section_id, self.grade_fragment_id)

    def get_context_data(self, **kwargs):
        context = super(GradesView, self).get_context_data(**kwargs)
        context['enrollments'] = Enrollment.get_students(self.section_id)
        context['section_average'] = StudentGrade.get_section_average(self.section, self.grade_fragment)
        context['section_objective_average'] = StudentGrade.get_section_objective_average(self.section)
        context['course_average'] = StudentGrade.get_course_average(self.section, self.grade_fragment)
        context['grade_fragment'] = self.grade_fragment
        context['section'] = self.section
        return context

    def formset_valid(self, formset):
        for form in formset:
            form.user = self.request.user.profile
            form.save(commit=False)
        messages.success(self.request, _('Grades were saved successfully'))
        return super(GradesView, self).formset_valid(formset)

    def get_formset_kwargs(self):
        kwargs = super(GradesView, self).get_formset_kwargs()
        kwargs['fragment'] = GradeFragment.get_grade_fragment(self.grade_fragment_id)
        kwargs['section'] = self.section
        return kwargs


class CreateGradeFragmentView(InstructorBaseView, CreateView):
    form_class = GradeFragmentForm
    model = GradeFragment
    template_name = 'grade/create_grade_fragment.html'

    def form_valid(self, form):
        form = form.save(commit=False)

        if not self.section.course_offering.coordinated:
            form.section = self.section

        form.course_offering = self.section.course_offering
        form.updated_by = self.request.user.profile
        form.save()
        messages.success(self.request, _('Grade plan created successfully'))
        return super(CreateGradeFragmentView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('grade:section_grade', kwargs={'section_id': self.section_id})
