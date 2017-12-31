from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import View, ListView, UpdateView, CreateView, FormView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.base import ContextMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .models import Section, Coordinator, CourseOffering
# from .forms import GradesImportForm
# from .utils import now
#
# from grade.forms import GradeFragmentForm
# from grade.models import GradeFragment, StudentGrade
from .web_service_utils import *


class CourseSectionListView(ListView):
    template_name = 'enrollment/sections_list.html'
    context_object_name = 'sections'

    def get_queryset(self):
        return get_course_sections_value('201710-SH', 'ENGL01')
