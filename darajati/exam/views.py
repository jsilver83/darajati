from django.views.generic import FormView, ListView, UpdateView, CreateView
from django.urls import reverse_lazy
from django.views.generic.base import ContextMixin

from .models import Exam, Room
from .forms import *

from enrollment.views import CoordinatorEditBaseView
from grade.models import GradeFragment


class ExamMixin(CoordinatorEditBaseView):
    exam = None
    grade_fragment_id = None
    grade_fragment = None

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('exam_id'):
            self.exam = Exam.objects.get(id=kwargs.get('exam_id'))

        if kwargs.get('grade_fragment_id'):
            self.grade_fragment_id = kwargs['grade_fragment_id']
            self.grade_fragment = GradeFragment.get_grade_fragment(self.grade_fragment_id)

        return super(ExamMixin, self).dispatch(request, *args, **kwargs)


class ExamListView(ExamMixin, ListView):
    template_name = 'exam/list_exams.html'
    model = Exam
    context_object_name = 'exams'

    def get_queryset(self):
        queryset = super(ExamListView, self).get_queryset()
        return queryset.filter(
            fragment=self.grade_fragment
        )


class ExamAddView(CoordinatorEditBaseView, CreateView):
    template_name = 'exam/add_exam.html'
    model = Exam
    form_class = None


class ExamEditView(CoordinatorEditBaseView, UpdateView):
    template_name = 'exam/edit_exam.html'
    model = Exam
    form_class = None


class RoomListView(CoordinatorEditBaseView, ListView):
    template_name = 'exam/list_rooms.html'
    model = Room
    context_object_name = 'rooms'


class RoomAddView(CoordinatorEditBaseView, CreateView):
    template_name = 'exam/add_room.html'
    model = Room
    form_class = None


class RoomEditView(CoordinatorEditBaseView, UpdateView):
    template_name = 'exam/edit_room.html'
    model = Room
    form_class = None

