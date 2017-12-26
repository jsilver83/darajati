from extra_views import ModelFormSetView
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .models import GradeFragment, StudentGrade
from .forms import GradesForm, GradeFragmentForm, BaseGradesFormSet

from enrollment.models import Enrollment
from enrollment.views import InstructorBaseView


class GradeBaseView(InstructorBaseView):
    grade_fragment_id = None
    grade_fragment = None
    grade_fragment_deadline = None

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs.get('grade_fragment_id'):
            self.grade_fragment_id = self.kwargs['grade_fragment_id']
            self.grade_fragment = GradeFragment.get_grade_fragment(self.grade_fragment_id)
        return super(GradeBaseView, self).dispatch(request, *args, **kwargs)


class GradeFragmentView(GradeBaseView, ListView):
    template_name = 'grade/grade_fragments.html'
    context_object_name = 'grade_fragments'

    def get_queryset(self):
        return GradeFragment.get_section_grade_fragments(self.section)


class GradesView(GradeBaseView, ModelFormSetView):
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

            if not self.grade_fragment.is_entry_allowed():
                messages.error(self.request, _('You are not allowed to enter the marks'))
                return False
            return True
        return False

    def get_queryset(self):
        return StudentGrade.get_section_grades(self.section_id, self.grade_fragment_id)

    def get_context_data(self, **kwargs):
        context = super(GradesView, self).get_context_data(**kwargs)
        context.update({
            'enrollments': Enrollment.get_students_of_section(self.section_id),
            'section_average': StudentGrade.display_section_average(self.section, self.grade_fragment),
            'section_objective_average': StudentGrade.get_section_objective_average(self.section, self.grade_fragment),
            'course_average': StudentGrade.display_course_average(self.section, self.grade_fragment),
            'grade_fragment': self.grade_fragment,
            'boundary': self.grade_fragment.get_fragment_boundary(self.section)
        })
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


class DisplayGradesView(GradeBaseView, ListView):
    template_name = 'grade/view_grades.html'
    model = StudentGrade
    context_object_name = 'grades'

    def get_queryset(self):
        queryset = super(DisplayGradesView, self).get_queryset()
        return queryset.filter(
            grade_fragment=self.grade_fragment,
            enrollment__section=self.section,
            enrollment__active=True
        )

    def get_context_data(self, **kwargs):
        context = super(DisplayGradesView, self).get_context_data(**kwargs)
        context.update({
            'grade_fragment': self.grade_fragment,
            'boundary': self.grade_fragment.get_fragment_boundary(self.section)
        })
        return context


class CreateGradeFragmentView(GradeBaseView, CreateView):
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
