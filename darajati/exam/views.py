from django.views.generic import FormView, ListView, UpdateView, CreateView
from django.urls import reverse_lazy
from django.views.generic.base import ContextMixin

from .models import Examiner, Room, Exam
from .forms import ExamForm, RoomForm, ExaminerForm

from enrollment.views import CoordinatorEditBaseView
from grade.models import GradeFragment


class ExaminerMixin(CoordinatorEditBaseView):
    exam = None
    grade_fragment_id = None
    grade_fragment = None

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('examiner_id'):
            self.exam = Examiner.objects.get(id=kwargs.get('examiner'))

        if kwargs.get('grade_fragment_id'):
            self.grade_fragment_id = kwargs['grade_fragment_id']
            self.grade_fragment = GradeFragment.get_grade_fragment(self.grade_fragment_id)

        return super(ExaminerMixin, self).dispatch(request, *args, **kwargs)


class ExaminerListView(ExaminerMixin, ListView):
    template_name = 'exam/list_examiner.html'
    model = Examiner
    context_object_name = 'examiners'

    def get_queryset(self):
        queryset = super(ExaminerListView, self).get_queryset()
        return queryset.filter(
            exam__fragment=self.grade_fragment
        )


class ExaminerAddView(ExaminerMixin, CreateView):
    template_name = 'exam/add_examiner.html'
    model = Examiner
    form_class = None


class ExaminerEditView(ExaminerMixin, UpdateView):
    template_name = 'exam/edit_examiner.html'
    model = Examiner
    form_class = ExaminerForm
    success_url = reverse_lazy('exam:examiner')

    def form_valid(self, form):
        saved_form = form.save(commit=False)
        saved_form.updated_by = self.request.user
        super(ExaminerEditView, self).form_valid(saved_form)

    def get_form_kwargs(self):
        kwargs = super(ExaminerEditView, self).get_form_kwargs()
        kwargs.update({
            'exams_list': self.grade_fragment.exams.all().values_list('id', 'fragment__description')
        })
        return kwargs


class RoomListView(ExaminerMixin, ListView):
    template_name = 'exam/list_rooms.html'
    model = Room
    context_object_name = 'rooms'


class RoomAddView(ExaminerMixin, CreateView):
    template_name = 'exam/add_room.html'
    model = Room
    form_class = None


class RoomEditView(ExaminerMixin, UpdateView):
    template_name = 'exam/edit_room.html'
    model = Room
    form_class = None

