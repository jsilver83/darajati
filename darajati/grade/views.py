from extra_views import ModelFormSetView
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .models import GradeFragment, StudentGrade
from .forms import GradesForm, GradeFragmentForm, BaseGradesFormSet

from enrollment.models import Enrollment
from enrollment.views import InstructorBaseView


class AttendanceBaseView(InstructorBaseView):
    grade_fragment_id = None
    grade_fragment = None
    grade_fragment_deadline = None

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs.get('grade_fragment_id'):
            self.grade_fragment_id = self.kwargs['grade_fragment_id']
            self.grade_fragment = GradeFragment.get_grade_fragment(self.grade_fragment_id)
        return super(AttendanceBaseView, self).dispatch(request, *args, **kwargs)


class GradeFragmentView(AttendanceBaseView, ListView):
    template_name = 'grade/grade_fragments.html'
    context_object_name = 'grade_fragments'

    def get_queryset(self):
        return GradeFragment.get_section_grade_fragments(self.section)


class GradesView(AttendanceBaseView, ModelFormSetView):
    template_name = 'grade/grades.html'
    model = StudentGrade
    form_class = GradesForm
    formset_class = BaseGradesFormSet
    extra = 0

    def test_func(self, **kwargs):
        rules = super(GradesView, self).test_func(**kwargs)

        if rules:
            if not self.grade_fragment:
                messages.error(self.request, _('Please enter a valid grade plan'))
                return False

            if not self.grade_fragment.is_entry_allowed and not self.request.user.is_superuser:
                messages.error(self.request, _('You are not allowed to enter the marks'))
                return False
            return True
        return False

    def get_queryset(self):
        return StudentGrade.get_section_grades(self.section_id, self.grade_fragment_id)

    def get_context_data(self, **kwargs):
        context = super(GradesView, self).get_context_data(**kwargs)
        context['enrollments'] = Enrollment.get_students(self.section_id)
        context['section_average'] = StudentGrade.get_section_average(self.section, self.grade_fragment)
        context['section_objective_average'] = StudentGrade.get_section_objective_average(self.section,
                                                                                          self.grade_fragment)
        context['course_average'] = StudentGrade.get_course_average(self.section, self.grade_fragment)

        if self.grade_fragment.entry_in_percentages:
            context['section_average'] = str(StudentGrade.get_section_average(self.section, self.grade_fragment)) + '%'
            context['section_objective_average'] = str(StudentGrade.get_section_objective_average(self.section,
                                                                                                  self.grade_fragment)) + '%'
            context['course_average'] = str(StudentGrade.get_course_average(self.section, self.grade_fragment)) + '%'
        context['grade_fragment'] = self.grade_fragment
        context['boundary'] = self.grade_fragment.get_fragment_boundary(self.section)
        return context

    def formset_valid(self, formset):
        for form in formset:
            form.user = self.request.user
            form.save(commit=False)
        messages.success(self.request, _('Grades were saved successfully'))
        return super(GradesView, self).formset_valid(formset)

    def get_formset_kwargs(self):
        kwargs = super(GradesView, self).get_formset_kwargs()
        kwargs['fragment'] = GradeFragment.get_grade_fragment(self.grade_fragment_id)
        kwargs['section'] = self.section
        return kwargs


class CreateGradeFragmentView(AttendanceBaseView, CreateView):
    form_class = GradeFragmentForm
    model = GradeFragment
    template_name = 'grade/create_grade_fragment.html'

    def test_func(self, **kwargs):
        rules = super(CreateGradeFragmentView, self).test_func(**kwargs)
        if rules:
            if self.section.course_offering.coordinated:
                messages.error(self.request, _('You can not create grade plans'))
                return False
            return True
        return False

    def form_valid(self, form):
        form = form.save(commit=False)

        if not self.section.course_offering.coordinated:
            form.section = self.section

        form.course_offering = self.section.course_offering
        form.updated_by = self.request.user
        form.save()
        messages.success(self.request, _('Grade plan created successfully'))
        return super(CreateGradeFragmentView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('grade:section_grade', kwargs={'section_id': self.section_id})
