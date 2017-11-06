from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import View, ListView, UpdateView, CreateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.base import ContextMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .models import Section, Enrollment, Coordinator, CourseOffering, Instructor
from .tasks import get_students_enrollment_grades
from .forms import GradesImportForm

from grade.forms import GradeFragmentForm

from grade.models import GradeFragment, StudentGrade


class HomeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        if Instructor.is_instructor(self.request.user):
            if Instructor.is_coordinator(self.request.user.instructor):
                return redirect('enrollment:coordinator')
            if Instructor.has_access(self.request.user):
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
        if self.kwargs.get('section_id'):
            self.section_id = self.kwargs['section_id']
            self.section = Section.get_section(self.section_id)
        if Instructor.is_coordinator(self.request.user.instructor):
            self.coordinator = self.request.user.instructor.coordinators
        return super(InstructorBaseView, self).dispatch(request, *args, **kwargs)

    def test_func(self, **kwargs):

        if not self.section:
            messages.error(self.request, _('This is not a valid section'))
            return False

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
        if self.request.user != "AnonymousUser":
            return reverse_lazy('enrollment:home')


class InstructorView(InstructorBaseView, ListView):
    template_name = 'enrollment/sections_list.html'
    model = Section
    context_object_name = 'sections'

    def test_func(self, **kwargs):
        return True if Instructor.is_instructor(self.request.user) else False

    def get_queryset(self):
        return Section.get_instructor_sections(self.request.user.instructor)


class SectionStudentView(InstructorBaseView, ListView):
    template_name = 'enrollment/instructor/section_students.html'
    model = Enrollment
    context_object_name = 'enrollments'

    def get_queryset(self):
        query = Enrollment.get_students(self.section_id).filter(active=True)
        return query


# Coordinator views
class CoordinatorBaseView(LoginRequiredMixin, UserPassesTestMixin, ContextMixin):
    coordinator = None
    course_offering_id = None
    course_offering = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if Coordinator.objects.filter(instructor=request.user.instructor).exists():
                self.coordinator = request.user
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
    def test_func(self):
        rules = super(CoordinatorEditBaseView, self).test_func()
        if rules:
            self.course_offering_id = self.kwargs['course_offering_id']
            self.course_offering = CourseOffering.objects.get(id=self.course_offering_id)

            if not self.course_offering:
                messages.error(self.request, _('No course offering found'))
                return False
            if not Coordinator.is_coordinator_course_offering(self.request.user.instructor, self.course_offering):
                messages.error(self.request, _('You can not access this page'))
                return False

            return True
        return False


class CoordinatorView(CoordinatorBaseView, ListView):
    template_name = 'enrollment/coordinator/courses_list.html'
    model = Coordinator
    context_object_name = 'courses'

    def get_queryset(self):
        queryset = super(CoordinatorView, self).get_queryset()
        return queryset.filter(instructor=self.coordinator.instructor)


class CoordinatorSectionView(CoordinatorEditBaseView, ListView):
    template_name = 'enrollment/sections_list.html'
    model = Section
    context_object_name = 'sections'

    def get_queryset(self):
        queryset = super(CoordinatorSectionView, self).get_queryset()
        return queryset.filter(course_offering=self.course_offering)


class CoordinatorGradeFragmentView(CoordinatorEditBaseView, ListView):
    template_name = 'enrollment/coordinator/grades_fragment_list.html'
    model = GradeFragment
    context_object_name = 'fragments'

    def get_queryset(self):
        queryset = super(CoordinatorGradeFragmentView, self).get_queryset()
        return queryset.filter(course_offering=self.course_offering)


class CoordinatorCreateGradeFragmentView(CoordinatorEditBaseView, CreateView):
    template_name = 'enrollment/coordinator/create_grade_fragment.html'
    model = GradeFragment
    form_class = GradeFragmentForm


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
        messages.success(self.request, _('Grade fragment updated successfully'))
        return super(CoordinatorEditGradeFragmentView, self).form_valid(form)

    def get_success_url(self, **kwargs):
        return reverse_lazy('enrollment:update_grade_fragment_coordinator',
                            kwargs={
                                'course_offering_id': self.course_offering_id,
                                'pk': self.kwargs['pk']
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
            form.cleaned_data['commit']
        )
        return self.render_to_response(context)


# Admin with superuser can access this only
class AdminControlsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'enrollment/admin_controls.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        if self.request.POST.get('create_grade'):
            get_students_enrollment_grades(self.request.user)
            # get_students_enrollment_grades.apply_async(args=[now()], eta=now())
        return render(request, self.template_name)

    def test_func(self):
        return self.request.user.is_superuser
