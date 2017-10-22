from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .models import Section, Enrollment, Coordinator, CourseOffering
from .tasks import get_students_enrollment_grades


class HomeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # TODO: redirect the new users to fill their information
        if request.user.profile.is_instructor:
            if request.user.profile.is_coordinator:
                return redirect('enrollment:coordinator')
            if request.user.profile.is_instructor & request.user.profile.has_access:
                return redirect('enrollment:instructor')
        else:
            return redirect('enrollment:unauthorized')


class InstructorBaseView(LoginRequiredMixin, UserPassesTestMixin):
    """
    :InstructorBaseView:
    - check if the current user is instructor or superuser
    - redirect the current user even if he is AnonymousUser
    """
    # TODO: add a check for the active user

    section_id = None
    section = None

    def dispatch(self, request, *args, **kwargs):
        """
         Assign section_id and get section object
        """
        if self.kwargs.get('section_id'):
            self.section_id = self.kwargs['section_id']
            self.section = Section.get_section(self.section_id)
        return super(InstructorBaseView, self).dispatch(request, *args, **kwargs)

    def test_func(self, **kwargs):

        if not self.section:
            messages.error(self.request, _('This is not a valid section'))
            return False

        is_instructor_section = self.section.is_instructor_section(
            self.request.user.profile.instructor)
        if not is_instructor_section:
            messages.error(self.request,
                           _('The requested section do not belong to you, or it is out of this semester'))
            return False

        return True

    def get_login_url(self):
        if self.request.user != "AnonymousUser":
            return reverse_lazy('enrollment:home')


class InstructorView(InstructorBaseView, ListView):
    context_object_name = 'sections'
    template_name = 'enrollment/instructor_sections.html'
    model = Section

    def test_func(self, **kwargs):
        return self.request.user.profile.is_instructor

    def get_queryset(self):
        return Section.get_instructor_sections(self.request.user.profile.instructor)


class SectionStudentView(InstructorBaseView, ListView):
    context_object_name = 'enrollments'
    template_name = 'enrollment/section_students.html'
    model = Enrollment

    def get_queryset(self):
        query = Enrollment.get_students(self.section_id)
        return query

    def get_context_data(self, **kwargs):
        context = super(SectionStudentView, self).get_context_data(**kwargs)
        context['section'] = self.section
        return context


class CoordinatorBaseView(LoginRequiredMixin, UserPassesTestMixin):
    coordinator = None
    course_offering_id = None
    course_offering = None

    def dispatch(self, request, *args, **kwargs):
        self.coordinator = self.request.user.profile.instructor.coordinators
        return super(CoordinatorBaseView, self).dispatch(request, *args, **kwargs)

    def test_func(self):
        if not self.coordinator:
            messages.error(self.request,
                           _('You can not access this page'))
            return False
        return True

    def get_login_url(self):
        if self.request.user != "AnonymousUser":
            return reverse_lazy('enrollment:home')


# Coordinator views
class CoordinatorView(CoordinatorBaseView, ListView):
    template_name = 'enrollment/coordinator_courses_list.html'
    model = Coordinator
    context_object_name = 'courses'

    def get_queryset(self):
        queryset = super(CoordinatorView, self).get_queryset()
        return queryset.filter(instructor=self.coordinator.instructor)


class CoordinatorSectionView(CoordinatorBaseView, ListView):
    template_name = 'enrollment/coordinator_course_sections_list.html'
    model = Section
    context_object_name = 'sections'

    def test_func(self):
        rules = super(CoordinatorSectionView, self).test_func()
        if rules:
            self.course_offering_id = self.kwargs['course_offering_id']
            self.course_offering = CourseOffering.objects.get(id=self.course_offering_id)

            if not self.course_offering:
                messages.error(self.request, _('No course offering found'))
                return False
            if not Coordinator.is_coordinator_course_offering(self.request.user.profile.instructor, self.course_offering):
                messages.error(self.request, _('You can not access this page'))
                return False

            return True
        return False

    def get_queryset(self):
        queryset = super(CoordinatorSectionView, self).get_queryset()
        return queryset.filter(course_offering=self.course_offering)


# Admin with superuser can access this only
class AdminControlsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'enrollment/admin_controls.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        if self.request.POST.get('create_grade'):
            get_students_enrollment_grades(self.request.user.profile)
            # get_students_enrollment_grades.apply_async(args=[now()], eta=now())
        return render(request, self.template_name)

    def test_func(self):
        return self.request.user.is_superuser
