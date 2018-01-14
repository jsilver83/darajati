from django.shortcuts import render

from django.views.generic import FormView
from django.urls import reverse_lazy


from .models import Room
from .forms import SubjectiveGradeFragmentForm

from enrollment.views import CoordinatorEditBaseView
from grade.models import GradeFragment

class SubjectiveMarkView(CoordinatorEditBaseView, FormView):
    template_name = 'exam/select_fragment.html'
    form_class = SubjectiveGradeFragmentForm

    def form_valid(self, form, **kwargs):
        rooms = list()
        for index in range(form.cleaned_data.get('number_of_rooms')):
            rooms.append(
                Room(
                    name='Room '+ str(index+1),
                    location=None,
                    capacity=None,
                    updated_by=None
                )
            )
            print('here')
        context = self.get_context_data(**kwargs)
        context.update({
            'rooms': rooms
        })
        return super(SubjectiveMarkView, self).form_valid(form, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(SubjectiveMarkView, self).get_form_kwargs(*args, **kwargs)
        kwargs.update({
            'fragments': GradeFragment.objects.filter(
                course_offering=self.course_offering,
                boundary_type=GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED
            ).values_list('id', 'description')
        })
        return kwargs

    def get_success_url(self):
        return reverse_lazy('exam:subjective_marking', kwargs={'course_offering_id': self.course_offering.id})