from django.contrib import messages
from django.db.models import F, Sum
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import View, ListView, UpdateView, CreateView, FormView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.base import ContextMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from extra_views import ModelFormSetView

from .models import Section, Enrollment, Coordinator, CourseOffering, Instructor
from .tasks import get_students_enrollment_grades
from .forms import GradesImportForm
from .utils import now
from exam.models import Marker

from grade.forms import GradeFragmentForm, GradeFragmentsFormSet, BulkGradeFragmentForm

from grade.models import GradeFragment, StudentGrade


class HomeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        if Instructor.is_active_instructor(self.request.user):
            if Instructor.is_active_coordinator(self.request.user.instructor):
                return redirect('enrollment:coordinator')
            return redirect('enrollment:instructor')
        else:
            return redirect('enrollment:unauthorized')


class InstructorBaseView(LoginRequiredMixin, UserPassesTestMixin, ContextMixin):
    """
    :InstructorBaseView:
    - check if the current user is instructor or superuser
    - redirect the current user even if he is AnonymousUser
    """
    # TODO: add a check for the active user

    section_id = None
    section = None
    coordinator = None

    def dispatch(self, request, *args, **kwargs):
        """
         Assign section_id and get section object
        """
        if request.user.is_authenticated:
            if self.kwargs.get('section_id'):
                self.section_id = self.kwargs['section_id']
                self.section = Section.get_section(self.section_id)
            if Instructor.is_active_coordinator(self.request.user.instructor):
                self.coordinator = self.request.user.instructor.coordinators
        return super(InstructorBaseView, self).dispatch(request, *args, **kwargs)

    def test_func(self, **kwargs):
        is_instructor_section = self.section.is_instructor_section(self.request.user.instructor)
        is_coordinator = self.section.is_coordinator_section(self.request.user.instructor)

        if is_instructor_section or is_coordinator:
            return True
        messages.error(self.request,
                       _('The requested section do not belong to you, or it is out of this semester'))
        return False

    def get_context_data(self, **kwargs):
        context = super(InstructorBaseView, self).get_context_data(**kwargs)
        context['section'] = self.section
        context['section_id'] = self.section_id
        context['coordinator'] = self.coordinator
        return context

    def get_login_url(self):
        """
        
        :return: 
        """
        if self.request.user.is_authenticated:
            return reverse_lazy('enrollment:home')


class InstructorView(InstructorBaseView, ListView):
    template_name = 'enrollment/sections_list.html'
    model = Section
    ordering = 'code'
    context_object_name = 'sections'

    def test_func(self, **kwargs):
        return True if Instructor.is_active_instructor(self.request.user) else False

    def get_context_data(self, **kwargs):
        context = super(InstructorView, self).get_context_data(**kwargs)

        context['active_marking_assignments'] = Marker.objects.filter(
            instructor__user=self.request.user,
            exam_room__exam_shift__settings__fragment__entry_start_date__lte=now(),
            exam_room__exam_shift__settings__fragment__entry_end_date__gte=now(),
            order__lte=F('exam_room__exam_shift__settings__number_of_markers'),
        )

        context['tie_breaking_assignments'] = Marker.objects.filter(
            instructor__user=self.request.user,
            exam_room__exam_shift__settings__fragment__entry_start_date__lte=now(),
            exam_room__exam_shift__settings__fragment__entry_end_date__gte=now(),
            order__gt=F('exam_room__exam_shift__settings__number_of_markers'),
        ).first()

        return context

    def get_queryset(self):
        return Section.get_instructor_sections(self.request.user.instructor)


class SectionStudentView(InstructorBaseView, ListView):
    template_name = 'enrollment/instructor/section_students.html'
    model = Enrollment
    context_object_name = 'enrollments'

    def get_queryset(self):
        query = Enrollment.get_students_of_section(self.section_id)
        return query


# Coordinator views
class CoordinatorBaseView(LoginRequiredMixin, UserPassesTestMixin, ContextMixin):
    coordinator = None
    course_offering_id = None
    course_offering = None
    __attributes_initiated = False

    def init_class_attributes(self, request, *args, **kwargs):
        if self.__attributes_initiated:
            return

        if request.user.is_authenticated:
            if Coordinator.objects.filter(instructor=request.user.instructor).exists():
                self.coordinator = request.user

    def dispatch(self, request, *args, **kwargs):
        self.init_class_attributes(request, *args, **kwargs)
        return super(CoordinatorBaseView, self).dispatch(request, *args, **kwargs)

    def test_func(self):
        if not self.coordinator:
            messages.error(self.request,
                           _('You can not access this page'))
            return False
        return True

    def get_context_data(self, **kwargs):
        context = super(CoordinatorBaseView, self).get_context_data(**kwargs)
        context['coordinator'] = self.coordinator
        return context

    def get_login_url(self):
        if self.request.user != "AnonymousUser":
            return reverse_lazy('enrollment:home')
        return super(CoordinatorBaseView, self).get_login_url()


class CoordinatorEditBaseView(CoordinatorBaseView):

    def init_class_attributes(self, request, *args, **kwargs):
        super().init_class_attributes(request, *args, **kwargs)
        self.course_offering_id = self.kwargs['course_offering_id']
        self.course_offering = get_object_or_404(CourseOffering, pk=self.course_offering_id)

    def test_func(self):
        rules = super(CoordinatorEditBaseView, self).test_func()
        if rules:
            if not Coordinator.is_coordinator_of_course_offering_in_this_semester(
                    self.request.user.instructor,
                    self.course_offering):
                messages.error(self.request, _('You can not access this page'))
                return False

            return True
        return False


class CoordinatorView(CoordinatorBaseView, ListView):
    template_name = 'enrollment/coordinator/courses_list.html'
    model = Coordinator
    context_object_name = 'courses'

    def get_queryset(self):
        return Coordinator.objects.filter(instructor=self.coordinator.instructor,
                                          course_offering__in=CourseOffering.get_active_course_offerings())


class CoordinatorSectionView(CoordinatorEditBaseView, ListView):
    template_name = 'enrollment/sections_list.html'
    model = Section
    ordering = 'code'
    context_object_name = 'sections'

    def get_queryset(self):
        queryset = super(CoordinatorSectionView, self).get_queryset()
        return queryset.filter(course_offering=self.course_offering).exclude(
            scheduled_periods__isnull=True
        )


class CoordinatorGradeFragmentView(CoordinatorEditBaseView, ListView):
    template_name = 'enrollment/coordinator/grades_fragment_list.html'
    model = GradeFragment
    context_object_name = 'fragments'

    def get_queryset(self):
        queryset = super(CoordinatorGradeFragmentView, self).get_queryset()
        return queryset.filter(course_offering=self.course_offering)

    def get_context_data(self, **kwargs):
        context = super(CoordinatorGradeFragmentView, self).get_context_data(**kwargs)
        context['course_offering'] = self.course_offering
        context['can_create_fragment'] = self.course_offering.semester.can_create_grade_fragment()
        context['fragments_total_weight'] = self.get_queryset().aggregate(Sum('weight')).get('weight__sum')
        return context


class ImportGradeFragmentsView(CoordinatorEditBaseView, View):

    def test_func(self):
        rules = super(ImportGradeFragmentsView, self).test_func()
        if rules:
            if not self.course_offering.semester.can_create_grade_fragment():
                messages.error(self.request, _('The deadline to add grade fragments is over'))
                return False

            if self.course_offering.grade_fragments.count() > 0:
                messages.error(self.request, _('You can NOT import fragments from previous semester when you already '
                                               'have created fragments in this semester'))
                return False
            return True
        return False

    def get(self, request, *args, **kwargs):
        self.init_class_attributes(request, *args, **kwargs)
        latest_course_offering = CourseOffering.objects.filter(
            course=self.course_offering.course,
            semester__start_date__lte=self.course_offering.semester.start_date
        ).order_by('-semester__end_date').exclude(pk=self.course_offering_id).first()
        if latest_course_offering and len(latest_course_offering.grade_fragments.all()):
            for fragment in latest_course_offering.grade_fragments.all():
                fragment.pk = None
                fragment.course_offering = self.course_offering
                fragment.entry_start_date = self.course_offering.semester.start_date
                fragment.entry_end_date = self.course_offering.semester.start_date
                fragment.save()
            messages.success(self.request, _('%s fragments were imported from %s successfully') % (
                self.course_offering.grade_fragments.count(),
                str(latest_course_offering)
            ))
        else:
            messages.error(self.request,
                           _('There is no previous course offering or there are no fragments there to be imported'))
        return redirect(reverse_lazy('enrollment:grade_fragment_coordinator', args=(self.course_offering_id, )))


class BulkUpdateGradeFragmentsView(CoordinatorEditBaseView, ModelFormSetView):
    template_name = 'enrollment/coordinator/fragments_bulk_update.html'
    model = GradeFragment
    form_class = BulkGradeFragmentForm
    formset_class = GradeFragmentsFormSet
    extra = 0
    can_delete = False

    def get_success_url(self):
        return reverse_lazy('enrollment:grade_fragment_coordinator', args=(self.course_offering_id, ))

    def get_queryset(self):
        return self.course_offering.grade_fragments.all()

    def get_extra_form_kwargs(self):
        kwargs = super(BulkUpdateGradeFragmentsView, self).get_extra_form_kwargs()
        kwargs['semester'] = self.course_offering.semester
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(BulkUpdateGradeFragmentsView, self).get_context_data(**kwargs)
        context['course_offering'] = self.course_offering
        return context

    def formset_valid(self, formset):
        self.object_list = formset.save()
        messages.success(self.request, _('Grade Fragments were updated successfully.'))
        return redirect(self.get_success_url())


class CoordinatorCreateGradeFragmentView(CoordinatorEditBaseView, CreateView):
    template_name = 'enrollment/coordinator/create_grade_fragment.html'
    model = GradeFragment
    form_class = GradeFragmentForm
    grade_fragment_id = None

    def test_func(self):
        rules = super(CoordinatorCreateGradeFragmentView, self).test_func()
        if rules:
            return self.course_offering.semester.can_create_grade_fragment()
        messages.error(self.request, _('The deadline to add grade fragments is over'))
        return False

    def form_valid(self, form):
        form_saved = form.save(commit=False)
        form_saved.course_offering = self.course_offering
        form_saved.updated_by = self.request.user
        form_saved.save()
        messages.success(self.request, _('Grade fragment created successfully'))
        return super(CoordinatorCreateGradeFragmentView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(CoordinatorCreateGradeFragmentView, self).get_form_kwargs()
        kwargs['semester'] = self.course_offering.semester
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CoordinatorCreateGradeFragmentView, self).get_context_data(**kwargs)
        context['course_offering'] = self.course_offering
        return context

    def get_success_url(self, **kwargs):
        return reverse_lazy('enrollment:grade_fragment_coordinator',
                            kwargs={
                                'course_offering_id': self.course_offering_id,
                            })


class CoordinatorEditGradeFragmentView(CoordinatorEditBaseView, UpdateView):
    template_name = 'enrollment/coordinator/update_grade_fragment.html'
    model = GradeFragment
    form_class = GradeFragmentForm

    def test_func(self):
        rules = super(CoordinatorEditGradeFragmentView, self).test_func()
        if rules:
            if GradeFragment.get_grade_fragment(self.kwargs['pk']):
                return True
            messages.error(self.request, _('Invalid grade fragment'))
            return False
        return False

    def form_valid(self, form):
        form.course_offering = self.course_offering
        form.updated_by = self.request.user
        form.save()
        messages.success(self.request, _('Grade fragment updated successfully'))
        return super(CoordinatorEditGradeFragmentView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(CoordinatorEditGradeFragmentView, self).get_form_kwargs()
        kwargs['semester'] = self.course_offering.semester
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CoordinatorEditGradeFragmentView, self).get_context_data(**kwargs)
        context['can_delete_fragment'] = self.course_offering.semester.can_create_grade_fragment()
        return context

    def get_success_url(self, **kwargs):
        return reverse_lazy('enrollment:update_grade_fragment_coordinator',
                            kwargs={
                                'course_offering_id': self.course_offering_id,
                                'pk': self.kwargs['pk']
                            })


class CoordinatorDeleteGradeFragmentView(CoordinatorEditBaseView, DeleteView):
    model = GradeFragment
    template_name = 'enrollment/coordinator/delete_grade_fragment.html'

    def test_func(self):
        rules = super(CoordinatorDeleteGradeFragmentView, self).test_func()
        if rules:
            return self.course_offering.semester.can_create_grade_fragment()
        messages.error(self.request, _('You can not delete grade fragment at this time'))
        return False

    def get_success_url(self, **kwargs):
        messages.success(self.request, _('Grade fragment deleted successfully'))
        return reverse_lazy('enrollment:grade_fragment_coordinator',
                            kwargs={
                                'course_offering_id': self.course_offering_id,
                            })


class ImportGradesView(CoordinatorEditBaseView, FormView):
    form_class = GradesImportForm
    template_name = 'enrollment/coordinator/import_grades.html'
    success_url = reverse_lazy('enrollment:home')

    def form_valid(self, form, **kwargs):
        fragment = self.kwargs.get('grade_fragment_id')
        fragment = GradeFragment.objects.get(id=fragment)
        context = self.get_context_data(**kwargs)
        context['list'], context['errors'] = StudentGrade.import_grades_by_admin(
            form.cleaned_data['grade'],
            fragment,
            self.request.user,
            form.cleaned_data['commit']
        )
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(ImportGradesView, self).get_context_data(**kwargs)
        context['gradefragment'] = GradeFragment.get_grade_fragment(self.kwargs.get('grade_fragment_id'))
        return context


# Admin with superuser can access this only
class AdminControlsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'enrollment/admin/controls.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        if self.request.POST.get('create_grade'):
            get_students_enrollment_grades()
            # get_students_enrollment_grades.apply_async(eta=now())
        return render(request, self.template_name)

    def test_func(self):
        return self.request.user.is_superuser
