from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .models import Section, Enrollment
from .utils import now
from .tasks import get_students_enrollment_grades


class HomeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # TODO: redirect the new users to fill their information
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
        query = Section.get_instructor_sections(self.request.user.profile.instructor)
        return query


class SectionStudentView(InstructorBaseView, ListView):
    context_object_name = 'enrollments'
    template_name = 'enrollment/section_students.html'
    model = Enrollment

    def get_queryset(self):
        query = Enrollment.get_students(self.section_id)
        return query


class AdminControlsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'enrollment/admin_controls.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        if self.request.POST.get('create_grade'):
            get_students_enrollment_grades()
            # get_students_enrollment_grades.apply_async(args=[now()], eta=now())
        return render(request, self.template_name)

    def test_func(self):
        return self.request.user.is_superuser
