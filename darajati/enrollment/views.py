from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import View, ListView, UpdateView, CreateView, FormView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.base import ContextMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .models import Section, Enrollment, Coordinator, CourseOffering, Instructor
from .tasks import get_students_enrollment_grades
from .forms import GradesImportForm
from .utils import now

from grade.forms import GradeFragmentForm

from grade.models import GradeFragment, StudentGrade