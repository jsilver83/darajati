from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum, Q
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


class ExamSettingsView(SuccessMessageMixin, CoordinatorBaseView, UpdateView):
    template_name = 'exam/exam_settings.html'
    model = GradeFragment
    pk_url_kwarg = 'grade_fragment_id'
    form_class = ExamSettingsForm

    def dispatch(self, request, *args, **kwargs):
        self.fragment = get_object_or_404(GradeFragment, pk=self.kwargs['grade_fragment_id'])

        return super(ExamSettingsView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('exam:shifts', kwargs={'grade_fragment_id': self.fragment.pk})

    def get_form_kwargs(self):
        kwargs = super(ExamSettingsView, self).get_form_kwargs()
        kwargs['fragment'] = self.fragment
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ExamSettingsView, self).get_context_data(**kwargs)
        context['grade_fragment'] = self.fragment
        return context


class ExamShiftsView(CoordinatorBaseView, ModelFormSetView):
    template_name = 'exam/exam_shifts.html'
    model = ExamShift
    form_class = ExamShiftForm
    formset_class = ExamShiftsFormSet
    extra = 3
    can_delete = True

    def dispatch(self, request, *args, **kwargs):
        self.fragment = get_object_or_404(GradeFragment, pk=self.kwargs['grade_fragment_id'])
        if not self.fragment.exam_date:
            return redirect(reverse_lazy('exam:settings', kwargs={'grade_fragment_id': self.fragment.pk}))

        if ExamShift.get_shifts(self.fragment).count() == 0:
            ExamShift.create_shifts_for_fragment(self.fragment)

        return super(ExamShiftsView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('exam:exam_rooms', kwargs={'grade_fragment_id': self.fragment.pk})

    def get_queryset(self):
        return ExamShift.get_shifts(self.fragment)

    def get_context_data(self, **kwargs):
        context = super(ExamShiftsView, self).get_context_data(**kwargs)
        context['grade_fragment'] = self.fragment
        return context

    def get_extra_form_kwargs(self):
        kwargs = super(ExamShiftsView, self).get_extra_form_kwargs()
        kwargs['fragment'] = self.fragment
        return kwargs

    def formset_valid(self, formset):
        self.object_list = formset.save()
        ExamShift.create_exam_rooms_for_shifts(self.fragment)
        messages.success(self.request, _('Shifts were saved successfully.'))

        if 'next' in self.request.POST:
            return redirect(self.get_success_url())
        elif 'reset' in self.request.POST:
            pass
            # TODO: implement reset to original classes shifts
        else:
            return redirect(self.request.get_full_path())


class ExamRoomsView(CoordinatorBaseView, ModelFormSetView):
    template_name = 'exam/exam_rooms.html'
    model = ExamRoom
    form_class = ExamRoomForm
    formset_class = ExamRoomsFormSet
    extra = 3
    can_delete = True

    def dispatch(self, request, *args, **kwargs):
        self.fragment = get_object_or_404(GradeFragment, pk=self.kwargs['grade_fragment_id'])

        shifts = ExamShift.objects.filter(fragment=self.fragment)
        if not shifts.exists():
            return redirect(reverse_lazy('exam:shifts', kwargs={'grade_fragment_id': self.fragment.pk}))

        return super(ExamRoomsView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('exam:markers', kwargs={'grade_fragment_id': self.fragment.pk})

    def get_queryset(self):
        return ExamRoom.objects.filter(exam_shift__fragment=self.fragment)

    def get_context_data(self, **kwargs):
        context = super(ExamRoomsView, self).get_context_data(**kwargs)
        context['grade_fragment'] = self.fragment
        context['students_count'] = Enrollment.objects.filter(section__course_offering=self.fragment.course_offering,
                                                              active=True).count()
        context['rooms_capacity'] = ExamRoom.objects.filter(
            exam_shift__fragment=self.fragment
        ).aggregate(Sum('capacity')).get('capacity__sum', 0)
        context['rooms_capacity'] = context['rooms_capacity'] if context['rooms_capacity'] else 0
        context['can_proceed'] = context['students_count'] < context['rooms_capacity']
        return context

    def get_extra_form_kwargs(self):
        kwargs = super(ExamRoomsView, self).get_extra_form_kwargs()
        kwargs['fragment'] = self.fragment
        return kwargs

    def formset_valid(self, formset):
        self.object_list = formset.save()
        messages.success(self.request, _('Exam rooms were saved successfully.'))
        if 'next' in self.request.POST:
            Marker.create_markers_for_fragment(self.fragment)
            return redirect(self.get_success_url())
        else:
            return redirect(self.request.get_full_path())


class MarkersView(CoordinatorBaseView, ModelFormSetView):
    template_name = 'exam/markers.html'
    model = Marker
    form_class = MarkerForm
    formset_class = MarkersFormSet
    extra = 0
    can_delete = False

    def dispatch(self, request, *args, **kwargs):
        self.fragment = get_object_or_404(GradeFragment, pk=self.kwargs['grade_fragment_id'])
        markers = Marker.objects.filter(exam_room__exam_shift__fragment=self.fragment)
        if not markers.exists():
            return redirect(reverse_lazy('exam:exam_rooms', kwargs={'grade_fragment_id': self.fragment.pk}))

        return super(MarkersView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('exam:exam_rooms', kwargs={'grade_fragment_id': self.fragment.pk})

    def get_queryset(self):
        return Marker.objects.filter(exam_room__exam_shift__fragment=self.fragment)

    def get_context_data(self, **kwargs):
        context = super(MarkersView, self).get_context_data(**kwargs)
        context['grade_fragment'] = self.fragment
        context['number_of_markers'] = range(1, self.fragment.number_of_markers + 2)

        stats = []
        allowed_markers = get_allowed_markers_for_a_fragment(self.fragment)
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

    def get_extra_form_kwargs(self):
        kwargs = super(MarkersView, self).get_extra_form_kwargs()
        kwargs['fragment'] = self.fragment
        return kwargs

    def formset_valid(self, formset):
        self.object_list = formset.save()

        # we reworked the shuffle algorithm to make it more fair in terms of fairly distributing students in exam rooms
        if 'shuffle' in self.request.POST:
            # delete existing placements before performing the shuffle
            StudentPlacement.objects.filter(exam_room__exam_shift__fragment=self.fragment).delete()
            enrollments = Enrollment.objects.filter(section__course_offering=self.fragment.course_offering, active=True)
            exam_rooms = ExamRoom.objects.filter(exam_shift__fragment=self.fragment)

            if exam_rooms:
                cannot_be_placed = []
                placement_count = 0

                most_available_seats_in_any_room = 0
                for room in exam_rooms:
                    if room.remaining_seats > most_available_seats_in_any_room:
                        most_available_seats_in_any_room = room.remaining_seats

                for enrollment in enrollments:

                    available_rooms = []

                    for room in exam_rooms:
                        remaining_seats = room.remaining_seats
                        if room.can_place_enrollment(
                                enrollment) and remaining_seats >= most_available_seats_in_any_room:
                            available_rooms.append({'exam_room': room, 'remaining_seats': remaining_seats})
                            most_available_seats_in_any_room -= 1
                            break

                    if available_rooms:
                        available_rooms = sorted(available_rooms, key=lambda k: k['remaining_seats'], reverse=True)
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
                        cannot_be_placed.append(enrollment.student.university_id)

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
            import csv
            import io

            # Using memory buffer
            csv_file = io.StringIO()

            writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)

            # Write markers CSV header
            writer.writerow(['Room', 'Time', 'Teacher', 'Order', 'Is A Monitor?'])

            # Maximum 2000 records will be fetched anyways to make this code non-abusive
            markers = self.get_queryset()[:2000]

            if markers:
                current_exam_room = None

                for marker in markers:
                    if current_exam_room != marker.exam_room:
                        writer.writerow([
                            marker.exam_room.room.location,
                            marker.exam_room.exam_shift,
                            marker.instructor,
                            marker.order,
                            marker.is_a_monitor
                        ])
                    else:
                        writer.writerow([
                            '',
                            '',
                            marker.instructor,
                            marker.order,
                            marker.is_a_monitor
                        ])
                    current_exam_room = marker.exam_room

                writer.writerow([])
                writer.writerow([])

            # Write students' placement CSV header
            writer.writerow(['Student ID', 'Room', 'Time'])

            student_placements = StudentPlacement.objects.filter(
                exam_room__exam_shift__fragment=self.fragment
            ).order_by('exam_room', 'enrollment')[:2000]

            if student_placements:
                current_exam_room = None
                for student_placement in student_placements:
                    if current_exam_room != student_placement.exam_room:
                        writer.writerow([
                            student_placement.exam_room.room.location,
                            student_placement.exam_room.exam_shift,
                            student_placement.enrollment.student.university_id
                        ])
                    else:
                        writer.writerow([
                            '',
                            '',
                            student_placement.enrollment.student.university_id
                        ])
                    current_exam_room = student_placement.exam_room

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

            # check if user can mark
            if not (self.marker.instructor.user == self.request.user or self.request.user.is_superuser or \
                    Coordinator.is_coordinator_of_course_offering_in_this_semester(
                        Instructor.get_instructor(self.request.user),
                        self.marker.exam_room.exam_shift.fragment.course_offering)):
                messages.error(self.request, _('You are not authorised to mark this room.'))
                return redirect(reverse_lazy('enrollment:home'))

            # if no marks, redirect to main page with an error message
            if not self.get_queryset().exists():
                messages.error(self.request, _('There are no marks available at the moment. Check back later.'))
                return redirect(reverse_lazy('enrollment:home'))

        return super(StudentMarksView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StudentMarksView, self).get_context_data(**kwargs)
        context['grade_fragment'] = self.marker.exam_room.exam_shift.fragment
        context['should_take_attendance'] = self.marker.is_a_monitor
        context['total_number_of_students'] = StudentMark.objects.filter(
            marker__order=self.marker.order - 1,
            marker__exam_room=self.marker.exam_room,
            student_placement__is_present=True
        ).values('student_placement').distinct().count()
        context['previous_marker'] = Marker.objects.filter(order=self.marker.order - 1,
                                                           exam_room=self.marker.exam_room).first()
        return context

    def get_extra_form_kwargs(self):
        kwargs = super(StudentMarksView, self).get_extra_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('enrollment:home')

    def get_queryset(self):
        if self.marker.is_the_tiebreaker():
            return StudentMark.get_unaccepted_marks(self.marker.exam_room.exam_shift.fragment)
            # .filter(marker=self.marker, )  # TODO: find a more elegant solution for this issue
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


class UnacceptedStudentMarksView(CoordinatorBaseView, ModelFormSetView):
    template_name = 'exam/unaccepted_student_marks.html'
    model = StudentMark
    form_class = StudentMarkForm
    formset_class = StudentMarkFormSet
    extra = 0
    can_delete = False

    def dispatch(self, request, *args, **kwargs):
        self.fragment = get_object_or_404(GradeFragment, pk=self.kwargs['grade_fragment_id'])
        marks = StudentMark.objects.filter(student_placement__exam_room__exam_shift__fragment=self.fragment)
        if not marks.exists():
            return redirect(reverse_lazy('exam:settings', kwargs={'grade_fragment_id': self.fragment.pk}))

        return super(UnacceptedStudentMarksView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UnacceptedStudentMarksView, self).get_context_data(**kwargs)
        context['grade_fragment'] = self.fragment
        context['number_of_markers'] = range(1, self.fragment.number_of_markers + 2)
        return context

    def get_extra_form_kwargs(self):
        kwargs = super(UnacceptedStudentMarksView, self).get_extra_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return StudentMark.get_unaccepted_marks(self.fragment)
