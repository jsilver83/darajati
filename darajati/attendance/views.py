from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, CreateView, TemplateView
from extra_views import FormSetView

from enrollment.models import Enrollment, Student, Instructor
from enrollment.utils import today, get_offset_day, now
from enrollment.views import InstructorBaseView
from .forms import AttendanceForm, ExcuseForm
from .models import ScheduledPeriod, Attendance, Excuse


class AttendanceBaseView(InstructorBaseView):
    """
    This is where handling date checking and attendance entry windows
    """
    year = None
    month = None
    day = None
    date = None

    def dispatch(self, request, *args, **kwargs):
        """
        We will set self.date to the passed year, month and date within the url so it can be used within all views. 
        """
        self.date = today()
        if self.kwargs.get('year') and self.kwargs.get('month') and self.kwargs.get('day'):
            self.year, self.month, self.day = self.kwargs['year'], self.kwargs['month'], self.kwargs['day']
            self.date = parse_date('{}-{}-{}'.format(self.year, self.month, self.day))
        return super(AttendanceBaseView, self).dispatch(request, *args, **kwargs)

    def test_func(self, **kwargs):
        rule = super(AttendanceBaseView, self).test_func(**kwargs)
        is_coordinator = self.section.is_coordinator_section(self.request.user.instructor)
        if rule:
            offset_date, day = get_offset_day(today(), -self.section.course_offering.attendance_entry_window)
            if self.date <= today():
                if self.section.course_offering.semester.check_is_accessible_date(self.date, offset_date) or \
                        is_coordinator:
                    return True
                else:
                    messages.error(self.request,
                                   _('You have passed the allowed time to be able to get to this day'))
                    return False
            else:
                messages.error(self.request,
                               _('You are trying to access a day in the future'))
                return False


class AttendanceView(AttendanceBaseView, FormSetView):
    template_name = 'attendance/attendance.html'
    form_class = AttendanceForm
    extra = 0

    def get_initial(self):
        if self.coordinator:
            return Enrollment.get_students_attendances_initial_data(self.section_id, self.date)
        return Enrollment.get_students_attendances_initial_data(self.section_id, self.date, self.request.user.instructor)

    def formset_valid(self, formset):
        for form in formset:
            form.save()
        messages.success(self.request, _('Attendances were saved successfully'))
        return super(AttendanceView, self).formset_valid(formset)

    def get(self, request, *args, **kwargs):
        all_messages_content = [msg.message for msg in list(messages.get_messages(request))]
        if _('Attendances were saved successfully') not in all_messages_content:
            messages.add_message(request, messages.WARNING,
                                 _('Make sure that you see the success message after submitting attendance. '
                                   'OR ELSE, attendance was NOT saved properly and you have to report it as a BUG'))
        return super().get(request, *args, **kwargs)

    # FIXME: I know i look nice-ish but i wanna be more nicer when you have time fix me please
    def get_context_data(self, **kwargs):
        context = super(AttendanceView, self).get_context_data(**kwargs)
        self.day, period_date = ScheduledPeriod.get_nearest_day_and_date(
            self.section_id,
            self.date,
            self.request.user.instructor.is_coordinator_or_instructor()
        )

        context['periods'], context['previous_week'], context[
            'next_week'] = ScheduledPeriod.get_section_periods_week_days(
            self.section,
            self.request.user.instructor.is_coordinator_or_instructor(),
            self.date,
            today())

        context['current_periods'] = ScheduledPeriod.get_section_periods_of_day(
            self.section_id,
            self.day,
            self.request.user.instructor.is_coordinator_or_instructor()).order_by('start_time')

        context['current_date'] = period_date
        context['today'] = today()

        enrollments = Enrollment.get_students_of_section(self.section_id).filter(active=True)
        context['students_attendances_summaries'] = [{
            'pk': enrollment.pk,
            'absences': enrollment.get_enrollment_total_absence,
            'lates': enrollment.get_enrollment_total_late,
            'excuses': enrollment.get_enrollment_total_excuses,
            'deduction': enrollment.get_enrollment_total_deduction
        } for enrollment in enrollments]
        context['section_id'] = self.section_id

        return context

    def get_extra_form_kwargs(self):
        kwargs = super(AttendanceView, self).get_extra_form_kwargs()
        kwargs.update({'request': self.request, 'section': self.section})
        return kwargs

    def get_success_url(self):
        kwargs = {'section_id': self.section_id}
        if self.day:
            kwargs = {'section_id': self.section_id,
                      'year': self.year,
                      'month': self.month,
                      'day': self.day}
            return reverse_lazy('attendance:section_day_attendance', kwargs=kwargs)
        return reverse_lazy('attendance:section_attendance', kwargs=kwargs)


class StudentAttendanceSummaryView(InstructorBaseView, ListView):
    template_name = 'attendance/student_attendance_summary.html'
    model = Attendance
    context_object_name = 'attendances'
    enrollment_id = None

    def test_func(self, **kwargs):
        rule = super(StudentAttendanceSummaryView, self).test_func(**kwargs)
        if rule:
            self.enrollment_id = self.kwargs['enrollment_id']
            return True
        return False

    def get_queryset(self):
        queryset = super(StudentAttendanceSummaryView, self).get_queryset()
        return queryset.filter(enrollment=self.enrollment_id, attendance_instance__period__section=self.section)

    def get_context_data(self, **kwargs):
        context = super(StudentAttendanceSummaryView, self).get_context_data(**kwargs)
        context.update({
            'enrollment': get_object_or_404(Enrollment, pk=self.enrollment_id),
            'section': self.section
        })
        return context


class ExcuseEntryBaseView(UserPassesTestMixin):
    def test_func(self):
        return Instructor.can_give_excuses(self.request.user)


# TODO: implement search by ID and dates
class ExcusesListingView(ExcuseEntryBaseView, ListView):
    object = Excuse
    paginate_by = 10
    template_name = 'attendance/excuses_listing.html'

    def get_queryset(self):
        return Excuse.objects.all().order_by('-applied_on', '-created_on')


# TODO: implement excuse update view for changing fields: 'excuse_type', 'includes_exams', 'attachments', 'description'
class ExcuseEntryView(ExcuseEntryBaseView, CreateView):
    form_class = ExcuseForm
    template_name = 'attendance/excuse_entry.html'

    def form_valid(self, form):
        saved = form.save(commit=False)
        saved.created_by = self.request.user
        saved.save()

        messages.warning(self.request, _('You have to review the list of attendances (to be excused) and make sure '
                                         'they are ALL correct!'))
        return super(ExcuseEntryView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('attendance:excuse_entry_confirm', args=(self.object.pk, ))


class ExcuseEntryConfirm(ExcuseEntryBaseView, TemplateView):
    template_name = 'attendance/excuse_entry_confirm.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Excuse, pk=self.kwargs['pk'])

        return super(ExcuseEntryConfirm, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ExcuseEntryConfirm, self).get_context_data(**kwargs)
        context['student'] = get_object_or_404(Student, university_id=self.object.university_id)
        context['object'] = self.object
        context['form'] = ExcuseForm
        context['attendances_to_be_shown'] = self.object.get_excused_attendances() if self.object.applied_on \
            else self.object.get_attendances_to_be_excused()

        return context

    def post(self, *args, **kwargs):
        if 'confirm' in self.request.POST:
            self.object.applied_on = now()
            self.object.applied_by = self.request.user
            self.object.save()

            self.object.apply_excuse()

            messages.success(self.request, _('Excuse #%s has been applied successfully.') % self.object.pk)

        elif 'reject' in self.request.POST:
            self.object.delete()
            messages.warning(self.request, _('Excuse has been removed successfully...'))

        return redirect(reverse_lazy('attendance:excuses_listing'))
