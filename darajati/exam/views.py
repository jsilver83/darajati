from django.views.generic import FormView, ListView
from django.urls import reverse_lazy

from .models import Exam
from .forms import SubjectiveGradeFragmentForm, ExamsForm

from enrollment.views import CoordinatorEditBaseView
from grade.models import GradeFragment


class SubjectiveMarkView(CoordinatorEditBaseView, FormView):
    template_name = 'exam/select_fragment.html'
    form_class = SubjectiveGradeFragmentForm

    def form_valid(self, form, **kwargs):
        fragment = GradeFragment.get_grade_fragment(form.cleaned_data.get('grade_fragment'))
        for index in range(form.cleaned_data.get('number_of_rooms')):
            f, c = Exam.objects.get_or_create(
                id=index,
                fragment=fragment,
                date_time=None,
                room=None,
                updated_by=self.request.user
            )
        self.success_url = reverse_lazy('exam:exams_list', kwargs={'course_offering_id': self.course_offering.id,
                                                                       'grade_fragment_id': fragment.id})
        return super(SubjectiveMarkView, self).form_valid(form)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(SubjectiveMarkView, self).get_form_kwargs(*args, **kwargs)
        kwargs.update({
            'fragments': GradeFragment.objects.filter(
                course_offering=self.course_offering,
                boundary_type=GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED
            ).values_list('id', 'description')
        })
        return kwargs


class ExamListView(CoordinatorEditBaseView, ListView):
    template_name = 'exam/exams_list.html'
    model = Exam
    context_object_name = 'exams'

    def get_queryset(self):
        queryset = super(ExamListView, self).get_queryset()
        return queryset.filter(
            fragment__id=self.kwargs.get('grade_fragment_id')
        )
