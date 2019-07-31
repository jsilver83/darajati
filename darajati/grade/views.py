import csv
import io
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum, Count
from django.forms import Form
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, CreateView, TemplateView, FormView
from extra_views import ModelFormSetView

from enrollment.models import Section
from enrollment.views import InstructorBaseView, CoordinatorEditBaseView
from .forms import GradesForm, GradeFragmentForm, BaseGradesFormSet, LetterGradeForm, LetterGradesFormSet
from .models import GradeFragment, StudentGrade, LetterGrade, StudentFinalDataView


class GradeBaseView(InstructorBaseView):
    grade_fragment_id = None
    grade_fragment = None
    grade_fragment_deadline = None

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs.get('grade_fragment_id'):
            self.grade_fragment_id = self.kwargs['grade_fragment_id']
            self.grade_fragment = GradeFragment.get_grade_fragment(self.grade_fragment_id)
        return super(GradeBaseView, self).dispatch(request, *args, **kwargs)


class GradeFragmentView(GradeBaseView, TemplateView):
    template_name = 'grade/grade_fragments.html'

    def get_context_data(self, **kwargs):
        context = super(GradeFragmentView, self).get_context_data(**kwargs)
        grade_fragments = GradeFragment.get_section_grade_fragments(self.section)
        grade_fragments_list = []
        for grade_fragment in grade_fragments:
            is_entry_allowed = grade_fragment.is_entry_allowed_for_instructor(self.section, self.request.user.instructor)
            is_viewable = grade_fragment.is_viewable_for_instructor(self.section, self.request.user.instructor)
            if is_entry_allowed:
                grade_fragments_list.append({'grade_fragment': grade_fragment, 'editable': True, 'viewable': True})
            elif is_viewable:
                grade_fragments_list.append({'grade_fragment': grade_fragment, 'editable': False, 'viewable': True})
        context['grade_fragments_objects'] = grade_fragments_list
        return context


class GradesView(GradeBaseView, ModelFormSetView):
    template_name = 'grade/grades.html'
    model = StudentGrade
    form_class = GradesForm
    formset_class = BaseGradesFormSet
    extra = 0

    is_change_allowed = False
    is_section_coordinator = False

    def dispatch(self, request, *args, **kwargs):
        grade_fragment = get_object_or_404(GradeFragment, pk=kwargs.get('grade_fragment_id'))
        section = get_object_or_404(Section, pk=kwargs.get('section_id'))

        self.is_change_allowed = grade_fragment.is_change_allowed_for_instructor(
            section, self.request.user.instructor
        )

        self.is_section_coordinator = section.is_coordinator_section(self.request.user.instructor)

        # SUBJECTIVE_BOUND require an average of objective exams if there is not show a validation error
        if grade_fragment.boundary_type == GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED:
            average_boundary = StudentGrade.get_section_objective_average(section, grade_fragment)
            if not average_boundary:
                messages.error(request, _('There is no objective average yet, make sure objective grades are entered'))
                return redirect(reverse_lazy('enrollment:home'))

        # SUBJECTIVE_BOUND_FIXED require boundary_fixed_average to not be null. If null show an error
        if (grade_fragment.boundary_type == GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED_FIXED
                and not grade_fragment.boundary_fixed_average):
            messages.error(request, _('There is no fixed average for this grade plan'))
            return redirect(reverse_lazy('enrollment:home'))

        return super().dispatch(request, *args, **kwargs)

    def test_func(self, **kwargs):
        rules = super(GradesView, self).test_func(**kwargs)
        if not (self.grade_fragment.is_entry_allowed_for_instructor(self.section, self.request.user.instructor)):
            messages.error(self.request, _('You are not allowed to enter the marks'))
            return False
        return True and rules

    def get_queryset(self):
        return StudentGrade.get_section_grades(
            self.section_id, self.grade_fragment_id
        ).select_related('grade_fragment', 'enrollment', 'enrollment__student', 'updated_by')

    def get_context_data(self, **kwargs):
        context = super(GradesView, self).get_context_data(**kwargs)
        context.update({
            'section_average': StudentGrade.display_section_average(self.section, self.grade_fragment),
            'section': self.section,
            'section_objective_average': StudentGrade.get_section_objective_average(self.section, self.grade_fragment),
            'course_average': StudentGrade.display_course_average(self.section, self.grade_fragment),
            'grade_fragment': self.grade_fragment,
            'is_change_allowed': self.is_change_allowed,
            'boundary': self.grade_fragment.get_fragment_boundary(self.section)
        })
        return context

    def formset_valid(self, formset):
        for form in formset:
            form.user = self.request.user
            form.save(commit=False)
        messages.success(self.request, _('Grades were saved successfully'))
        return HttpResponseRedirect(reverse_lazy(
            'grade:plan_grades',
            kwargs={
                'section_id': self.section_id,
                'grade_fragment_id': self.grade_fragment_id
            }
        ))
        # This used to save the same object 2 times
        # return super(GradesView, self).formset_valid(formset)

    def get_extra_form_kwargs(self):
        kwargs = super().get_extra_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['is_change_allowed'] = self.is_change_allowed
        return kwargs

    def get_formset_kwargs(self):
        kwargs = super(GradesView, self).get_formset_kwargs()
        kwargs['fragment'] = self.grade_fragment
        kwargs['section'] = self.section
        kwargs['is_coordinator'] = self.is_section_coordinator
        return kwargs


class DisplayGradesView(GradeBaseView, ListView):
    template_name = 'grade/view_grades.html'
    model = StudentGrade
    context_object_name = 'grades'

    def test_func(self, **kwargs):
        rules = super(DisplayGradesView, self).test_func(**kwargs)
        if not (self.grade_fragment.is_viewable_for_instructor(self.section, self.request.user.instructor)):
            messages.error(self.request, _('You are not allowed to enter the marks'))
            return False
        return True and rules

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
            'section_average': StudentGrade.display_section_average(self.section, self.grade_fragment),
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


class GradeReportView(GradeBaseView, TemplateView):
    template_name = 'grade/grade_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fragments = GradeFragment.objects.filter(
                course_offering=self.section.course_offering)

        context.update({
            'grades': StudentGrade.objects.filter(
                enrollment__section=self.section,
                enrollment__active=True,
            ).order_by('enrollment__student__university_id', 'grade_fragment__order'),
            'fragments': fragments
        })
        averages = []
        for fragment in fragments:
            averages.append(
                fragment.get_section_average(self.section)
            )
        context.update({
            'averages': averages
        })
        return context


class GradeCourseReport(GradeBaseView, TemplateView):
    pass


class LetterGradesView(CoordinatorEditBaseView, ModelFormSetView):
    template_name = 'grade/letter_grades.html'
    model = LetterGrade
    form_class = LetterGradeForm
    formset_class = LetterGradesFormSet
    extra = 3
    can_delete = True

    def get_success_url(self):
        return reverse_lazy('enrollment:grade_fragment_coordinator', args=(self.course_offering_id, ))

    def get_queryset(self):
        return self.course_offering.letter_grades.all()

    def get_extra_form_kwargs(self):
        kwargs = super(LetterGradesView, self).get_extra_form_kwargs()
        kwargs['course_offering'] = self.course_offering
        kwargs['upper_boundary'] = self.course_offering.grade_fragments.all().aggregate(Sum('weight')).get('weight__sum')
        kwargs['lower_boundary'] = Decimal('0.00')
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(LetterGradesView, self).get_context_data(**kwargs)
        context['course_offering'] = self.course_offering
        context['letter_grades_counts'] = StudentFinalDataView.objects.filter(
            course_offering=self.course_offering
        ).values('calculated_letter_grade').annotate(entries=Count('calculated_letter_grade'))
        return context

    def formset_valid(self, formset):
        self.object_list = formset.save()

        if 'save' in self.request.POST:
            messages.success(self.request, _('Letter Grades were saved successfully.'))
            return redirect(self.request.get_full_path())
        elif 'csv' in self.request.POST:
            csv_file = io.StringIO()

            writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)

            # Write CSV header
            writer.writerow(['semester_code',
                             'department_code',
                             'course_code',
                             'coordinated',
                             'section_code',
                             'letter_grade',
                             'active',
                             'university_id',
                             'english_name',
                             'arabic_name',
                             'total_weights',
                             'total',
                             'attendance_deduction',
                             'total_after_deduction',
                             'total_rounded',
                             'calculated_letter_grade', ])

            # Maximum 2000 records will be fetched anyways to make this code non-abusive
            final_data = StudentFinalDataView.objects.filter(course_offering=self.course_offering)[:2000]

            if final_data:
                for student in final_data:
                    writer.writerow([
                        student.semester_code,
                        student.department_code,
                        student.course_code,
                        student.coordinated,
                        student.section_code,
                        student.letter_grade,
                        student.active,
                        student.university_id,
                        student.english_name,
                        student.arabic_name,
                        student.total_weights,
                        student.total,
                        student.attendance_deduction,
                        student.total_after_deduction,
                        student.total_rounded,
                        student.calculated_letter_grade,
                    ])

                response = HttpResponse()
                response.write(csv_file.getvalue())
                response['Content-Disposition'] = 'attachment; filename={0}'.format('student_final_data.csv')
                return response
            else:
                messages.error(self.request, _('No records to export to CSV'))

        elif 'apply' in self.request.POST:
            count_of_students_changed_letter_grades = 0
            final_data = StudentFinalDataView.objects.filter(course_offering=self.course_offering)
            for student in final_data:
                if student.letter_grade is None:
                    student.enrollment.letter_grade = student.calculated_letter_grade
                    student.enrollment.save()
                    count_of_students_changed_letter_grades += 1

            messages.success(self.request,
                             _('Letter Grades were saved successfully. %s students had their letter grades been '
                               'changed' % (count_of_students_changed_letter_grades, )))

            return redirect(self.get_success_url())


class LetterGradesPromotionView(CoordinatorEditBaseView, FormView):
    template_name = 'grade/letter_grades_promotion.html'
    form_class = Form

    def get_success_url(self):
        return reverse_lazy('enrollment:grade_fragment_coordinator', args=(self.course_offering_id, ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_offering'] = self.course_offering
        context['promotion_cases'] = self.course_offering.get_all_letter_grade_promotion_cases()
        return context

    def form_valid(self, form):
        if 'promote' in self.request.POST:
            # TODO: IMPLEMENT
            messages.success(self.request, _('Cases were promoted successfully.'))
            return redirect(self.request.get_full_path())
        return super().form_valid(form)
