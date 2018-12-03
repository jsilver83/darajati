import csv
import io
from math import floor

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum, Q, Avg
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, UpdateView, CreateView
from extra_views import ModelFormSetView

from enrollment.views import CoordinatorBaseView
from .forms import *


class RoomListView(CoordinatorBaseView, ListView):
    template_name = 'exam/list_rooms.html'
    model = Room
    context_object_name = 'rooms'


class RoomAddView(CoordinatorBaseView, CreateView):
    template_name = 'exam/add_room.html'
    model = Room
    form_class = None


class RoomEditView(CoordinatorBaseView, UpdateView):
    template_name = 'exam/edit_room.html'
    model = Room
    form_class = None


class ExamSettingsBaseView:
    def dispatch(self, request, *args, **kwargs):
        self.fragment = get_object_or_404(GradeFragment, pk=self.kwargs['fragment_id'])
        self.exam_settings, created = ExamSettings.objects.get_or_create(fragment=self.fragment)

        return super(ExamSettingsBaseView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ExamSettingsBaseView, self).get_form_kwargs()
        kwargs['exam_settings'] = self.exam_settings
        return kwargs

    def get_extra_form_kwargs(self):
        kwargs = super(ExamSettingsBaseView, self).get_extra_form_kwargs()
        kwargs['exam_settings'] = self.exam_settings
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ExamSettingsBaseView, self).get_context_data(**kwargs)
        context['grade_fragment'] = self.fragment
        return context


class ExamSettingsView(SuccessMessageMixin, ExamSettingsBaseView, CoordinatorBaseView, UpdateView):
    template_name = 'exam/exam_settings.html'
    model = ExamSettings
    form_class = ExamSettingsForm
    success_message = _('Exam settings has been updated successfully')

    def get_object(self, queryset=None):
        return self.exam_settings

    def get_success_url(self):
        return reverse_lazy('exam:shifts', kwargs={'fragment_id': self.fragment.pk})


class ExamShiftsView(ExamSettingsBaseView, CoordinatorBaseView, ModelFormSetView):
    template_name = 'exam/exam_shifts.html'
    model = ExamShift
    form_class = ExamShiftForm
    formset_class = ExamShiftsFormSet
    extra = 3
    can_delete = True

    def dispatch(self, request, *args, **kwargs):
        dispatch = super(ExamShiftsView, self).dispatch(request, *args, **kwargs)
        if not self.exam_settings.exam_date:
            return redirect(reverse_lazy('exam:settings', kwargs={'fragment_id': self.fragment.pk}))

        if ExamShift.get_shifts(self.exam_settings).count() == 0:
            ExamShift.create_shifts_for_exam_settings(self.exam_settings)

        return dispatch

    def get_success_url(self):
        return reverse_lazy('exam:exam_rooms', kwargs={'fragment_id': self.fragment.pk})

    def get_queryset(self):
        return ExamShift.get_shifts(self.exam_settings)

    def formset_valid(self, formset):
        self.object_list = formset.save()
        ExamShift.create_exam_rooms_for_shifts(self.exam_settings)
        messages.success(self.request, _('Shifts were saved successfully.'))

        if 'next' in self.request.POST:
            return redirect(self.get_success_url())
        elif 'reset' in self.request.POST:
            pass
            # TODO: implement reset to original classes shifts
        else:
            return redirect(self.request.get_full_path())


class ExamRoomsView(ExamSettingsBaseView, CoordinatorBaseView, ModelFormSetView):
    template_name = 'exam/exam_rooms.html'
    model = ExamRoom
    form_class = ExamRoomForm
    formset_class = ExamRoomsFormSet
    extra = 3
    can_delete = True

    def dispatch(self, request, *args, **kwargs):
        dispatch = super(ExamRoomsView, self).dispatch(request, *args, **kwargs)

        shifts = ExamShift.objects.filter(settings=self.exam_settings)
        if not shifts.exists():
            return redirect(reverse_lazy('exam:shifts', kwargs={'fragment_id': self.fragment.pk}))

        return dispatch

    def get_success_url(self):
        return reverse_lazy('exam:markers', kwargs={'fragment_id': self.fragment.pk})

    def get_queryset(self):
        return ExamRoom.objects.filter(exam_shift__settings=self.exam_settings)

    def get_context_data(self, **kwargs):
        context = super(ExamRoomsView, self).get_context_data(**kwargs)
        context['students_count'] = Enrollment.objects.filter(section__course_offering=self.exam_settings.fragment.course_offering,
                                                              active=True).count()
        context['rooms_capacity'] = ExamRoom.objects.filter(
            exam_shift__settings=self.exam_settings
        ).aggregate(Sum('capacity')).get('capacity__sum', 0)
        context['rooms_capacity'] = context['rooms_capacity'] if context['rooms_capacity'] else 0
        context['can_proceed'] = context['students_count'] < context['rooms_capacity']
        return context

    def formset_valid(self, formset):
        self.object_list = formset.save()
        messages.success(self.request, _('Exam rooms were saved successfully.'))
        if 'next' in self.request.POST:
            Marker.create_markers_for_exam_settings(self.exam_settings)
            return redirect(self.get_success_url())
        else:
            return redirect(self.request.get_full_path())


class MarkersView(ExamSettingsBaseView, CoordinatorBaseView, ModelFormSetView):
    template_name = 'exam/markers.html'
    model = Marker
    form_class = MarkerForm
    formset_class = MarkersFormSet
    extra = 0
    can_delete = False

    def dispatch(self, request, *args, **kwargs):
        dispatch = super(MarkersView, self).dispatch(request, *args, **kwargs)

        markers = Marker.objects.filter(exam_room__exam_shift__settings=self.exam_settings)
        if not markers.exists():
            return redirect(reverse_lazy('exam:exam_rooms', kwargs={'fragment_id': self.fragment.pk}))

        return dispatch

    def get_success_url(self):
        return reverse_lazy('exam:exam_rooms', kwargs={'fragment_id': self.fragment.pk})

    def get_queryset(self):
        return Marker.objects.filter(exam_room__exam_shift__settings=self.exam_settings)

    def get_context_data(self, **kwargs):
        context = super(MarkersView, self).get_context_data(**kwargs)
        context['number_of_markers'] = range(1, self.exam_settings.number_of_markers + 2)

        stats = []
        allowed_markers = get_allowed_markers_for_a_fragment(self.exam_settings.fragment)
        for marker in allowed_markers:
            assignments = self.get_queryset().filter(instructor=marker, order__in=[1, 2])
            assignments_count = assignments.count()  # if assignments else 0
            # if assignments_count < 1 or assignments_count > 1:
            first_assignments = assignments.filter(order=1)
            second_assignments = assignments.filter(order=2)
            stats.append(({'marker': str(marker),
                           'assignments': assignments_count,
                           'first': first_assignments.count(),
                           'second': second_assignments.count()}))
        context['stats'] = sorted(stats, key=lambda k: k['assignments'], reverse=True)
        return context

    def formset_valid(self, formset):
        self.object_list = formset.save()

        # we reworked the shuffle algorithm to make it more fair in terms of fairly distributing students in exam rooms
        if 'shuffle' in self.request.POST:
            # delete existing placements before performing the shuffle
            StudentPlacement.objects.filter(exam_room__exam_shift__settings=self.exam_settings).delete()
            enrollments = Enrollment.objects.filter(
                section__course_offering=self.exam_settings.fragment.course_offering, active=True).order_by('?')
            enrollments_count = enrollments.count()
            exam_rooms = ExamRoom.objects.filter(exam_shift__settings=self.exam_settings).order_by('?')

            if exam_rooms:
                cannot_be_placed = []
                placement_count = 0

                for enrollment in enrollments:
                    most_available_seats_in_any_room = 0
                    for room in exam_rooms:
                        if room.remaining_seats_percentage > most_available_seats_in_any_room:
                            most_available_seats_in_any_room = room.remaining_seats_percentage

                    available_rooms = []

                    for room in exam_rooms:
                        remaining_seats_percentage = room.remaining_seats_percentage
                        if room.can_place_enrollment(
                                enrollment):
                            available_rooms.append({'exam_room': room,
                                                    'remaining_seats_percentage': remaining_seats_percentage})

                            if remaining_seats_percentage >= most_available_seats_in_any_room:
                                break

                    if available_rooms:
                        available_rooms = sorted(available_rooms, key=lambda k: k['remaining_seats_percentage'], reverse=True)
                        student_placement = StudentPlacement.objects.create(
                            enrollment=enrollment,
                            exam_room=available_rooms[0].get('exam_room'),
                            is_present=True,
                            shuffled_by=self.request.user
                        )

                        placement_count += 1

                        for marker in available_rooms[0].get('exam_room').get_markers():
                            student_mark, created = StudentMark.objects.get_or_create(
                                student_placement=student_placement,
                                marker=marker)
                    else:
                        cannot_be_placed.append((enrollment.student.university_id, enrollment.section.code))

                if cannot_be_placed:
                    messages.warning(
                        self.request,
                        _('%s out of %s were shuffled successfully. The following students were not placed: %s') %
                        (placement_count,
                         enrollments.count(),
                         cannot_be_placed)
                    )
                else:
                    messages.success(
                        self.request,
                        _('%s out of %s were shuffled successfully. Instructors can enter marks now') % (
                            placement_count,
                            enrollments.count())
                    )

        elif 'export' in self.request.POST:
            # Using memory buffer
            csv_file = io.StringIO()

            writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)

            # Write markers CSV header
            writer.writerow(['Room', 'Time', 'Teacher', 'Email', 'Order', 'Is A Monitor?', ])

            # Maximum 2000 records will be fetched anyways to make this code non-abusive
            markers = self.get_queryset()[:2000]

            if markers:
                for marker in markers:
                    writer.writerow([
                        marker.exam_room.room.location,
                        marker.exam_room.exam_shift,
                        marker.instructor,
                        marker.instructor.kfupm_email,
                        marker.order,
                        marker.is_a_monitor
                    ])

                writer.writerow([])
                writer.writerow([])

            # Write students' placement CSV header
            writer.writerow(['Room', 'Time', 'Student ID', 'Name', 'Email', 'Section', ])

            student_placements = StudentPlacement.objects.filter(
                exam_room__exam_shift__settings=self.exam_settings
            ).order_by('exam_room', 'enrollment')[:2000]

            if student_placements:
                for student_placement in student_placements:
                    writer.writerow([
                        student_placement.exam_room.room.location,
                        student_placement.exam_room.exam_shift,
                        student_placement.enrollment.student.university_id,
                        student_placement.enrollment.student.english_name,
                        student_placement.enrollment.student.kfupm_email,
                        student_placement.enrollment.section.code,
                    ])

            if student_placements or markers:
                response = HttpResponse()
                response.write(csv_file.getvalue())
                response['Content-Disposition'] = 'attachment; filename={0}'.format('the_shuffled_students.csv')
                return response
            else:
                messages.error(self.request, _('No records to export to CSV'))

        else:
            messages.success(self.request, _('Markers were saved successfully'))

        return redirect(self.request.get_full_path())


class StudentMarksView(LoginRequiredMixin, ModelFormSetView):
    template_name = 'exam/student_marks.html'
    model = StudentMark
    form_class = StudentMarkForm
    formset_class = StudentMarkFormSet
    extra = 0
    can_delete = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.marker = get_object_or_404(Marker, pk=self.kwargs['marker_id'])
            self.is_coordinator = Coordinator.is_coordinator_of_course_offering_in_this_semester(
                Instructor.get_instructor(self.request.user),
                self.marker.exam_room.exam_shift.settings.fragment.course_offering
            )

            # check if user can mark
            if not (self.marker.instructor.user == self.request.user
                    or self.request.user.is_superuser or self.is_coordinator):
                messages.error(self.request, _('You are not authorised to mark this room.'))
                return redirect(reverse_lazy('enrollment:home'))

            queryset = self.get_queryset()

            # if no marks, redirect to main page with an error message
            if not queryset.exists():
                messages.error(self.request, _('There are no marks available at the moment. Check back later.'))
                return redirect(reverse_lazy('enrollment:home'))

            # if fragment doesnt allow change
            if not self.marker.exam_room.exam_shift.settings.fragment.allow_change:
                if queryset.filter(updated_by__isnull=False).exists() \
                        and not (self.request.user.is_superuser or self.is_coordinator):
                    messages.error(self.request, _('You are not allowed to change marks'))
                    return redirect(reverse_lazy('enrollment:home'))

        return super(StudentMarksView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StudentMarksView, self).get_context_data(**kwargs)
        context['grade_fragment'] = self.marker.exam_room.exam_shift.settings.fragment
        context['should_take_attendance'] = self.marker.is_a_monitor
        context['total_number_of_students'] = StudentMark.objects.filter(
            marker__order=self.marker.order - 1,
            marker__exam_room=self.marker.exam_room,
            student_placement__is_present=True
        ).values('student_placement').distinct().count()
        context['section_average'] = self.get_queryset().filter(
            mark__isnull=False, student_placement__is_present=True).aggregate(Avg('mark')).get('mark__avg')
        context['previous_marker'] = Marker.objects.filter(order=self.marker.order - 1,
                                                           exam_room=self.marker.exam_room).first()
        context['show_warning'] = self.get_queryset().count() > context['total_number_of_students'] \
                                  and not self.marker.is_the_tiebreaker() and context['previous_marker']
        return context

    def get_extra_form_kwargs(self):
        kwargs = super(StudentMarksView, self).get_extra_form_kwargs()
        kwargs['exam_settings'] = None
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        if self.is_coordinator or self.request.user.is_superuser:
            return reverse_lazy('exam:coordinator_markers_listing',
                                kwargs={'fragment_id': self.marker.exam_room.exam_shift.settings.fragment.pk})

        return reverse_lazy('enrollment:home')

    def get_queryset(self):
        if self.marker.is_the_tiebreaker():
            return StudentMark.get_unaccepted_marks(
                self.marker.exam_room.exam_shift.settings
            ).filter(marker__order__gt=F('student_placement__exam_room__exam_shift__settings__number_of_markers'))
        elif self.marker.order > 1:
            students_marked_by_previous_marker = StudentMark.objects.filter(
                Q(mark__isnull=False) | Q(student_placement__is_present=False),
                marker__order=self.marker.order - 1,
                marker__exam_room=self.marker.exam_room
            ).values('student_placement').distinct()
            return StudentMark.objects.filter(marker=self.marker,
                                              student_placement__in=students_marked_by_previous_marker)
        else:
            return StudentMark.objects.filter(marker=self.marker)

    def formset_valid(self, formset):
        self.object_list = formset.save()
        messages.success(self.request, _('Marks were submitted successfully'))
        return redirect(self.get_success_url())


class UnacceptedStudentMarksView(ExamSettingsBaseView, CoordinatorBaseView, ModelFormSetView):
    template_name = 'exam/unaccepted_student_marks.html'
    model = StudentMark
    form_class = StudentMarkForm
    formset_class = StudentMarkFormSet
    extra = 0
    can_delete = False

    def dispatch(self, request, *args, **kwargs):
        # self.fragment = get_object_or_404(GradeFragment, pk=self.kwargs['grade_fragment_id'])
        dispatch = super(UnacceptedStudentMarksView, self).dispatch(request, *args, **kwargs)
        marks = StudentMark.objects.filter(student_placement__exam_room__exam_shift__settings=self.exam_settings)
        if not marks.exists():
            return redirect(reverse_lazy('exam:settings', kwargs={'exam_settings_id': self.exam_settings.pk}))

        return dispatch

    def get_context_data(self, **kwargs):
        context = super(UnacceptedStudentMarksView, self).get_context_data(**kwargs)
        # context['grade_fragment'] = self.fragment
        context['number_of_markers'] = range(1, self.exam_settings.number_of_markers + 2)
        return context

    def get_extra_form_kwargs(self):
        kwargs = super(UnacceptedStudentMarksView, self).get_extra_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return StudentMark.get_unaccepted_marks(self.exam_settings)


class CoordinatorMarkersListing(ExamSettingsBaseView, CoordinatorBaseView, ListView):
    model = Marker
    template_name = 'exam/coordinator_markers_listing.html'

    def get_queryset(self):
        return Marker.objects.filter(exam_room__exam_shift__settings__fragment=self.fragment.pk)

    def get_context_data(self, **kwargs):
        context = super(CoordinatorMarkersListing, self).get_context_data(**kwargs)
        context['overall_average'] = self.fragment.exam_settings.overall_average
        context['cell_width'] = floor(100/(self.fragment.exam_settings.number_of_markers+1))

        return context

    def post(self, request, *args, **kwargs):
        if 'export' in request.POST:
            # Using memory buffer
            csv_file = io.StringIO()

            writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)

            number_of_markers = self.fragment.exam_settings.number_of_markers

            temp = []
            for i in range(1, number_of_markers + 2):
                temp.append('Marker# ' + str(i))
                temp.append('Mark')
                temp.append('Weighted Mark')

            # Write markers CSV header
            writer.writerow(['Room', 'Time', 'Student Name', 'KFUPM ID', 'Is Present', 'FINAL MARK', ] + temp)

            student_placements = StudentPlacement.objects.filter(
                exam_room__exam_shift__settings__fragment=self.fragment
            ).order_by(
                'exam_room',
                'enrollment__student__university_id',
            )

            if student_placements:
                for student_placement in student_placements:
                    temp = [
                        student_placement.exam_room.room.location,
                        student_placement.exam_room.exam_shift,
                        student_placement.enrollment.student.name,
                        student_placement.enrollment.student.university_id,
                        student_placement.is_present,
                        student_placement.final_mark,
                    ]

                    for i in range(1, number_of_markers + 2):
                        temp.append(student_placement.marks.filter(marker__order=i).first().marker.instructor)
                        temp.append(student_placement.marks.filter(marker__order=i).first().mark)
                        temp.append(student_placement.marks.filter(marker__order=i).first().weighted_mark)

                    writer.writerow(temp)

                writer.writerow([])
                writer.writerow([])

            if student_placements:
                response = HttpResponse()
                response.write(csv_file.getvalue())
                response['Content-Disposition'] = 'attachment; filename={0}'.format('all_students_marks.csv')
                return response
            else:
                messages.error(self.request, _('No records to export to CSV'))

