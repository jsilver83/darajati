from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from enrollment.models import Coordinator, Instructor

User = settings.AUTH_USER_MODEL

"""
The motivation of this app is to separate the subjective exams for english 
this is more to the side of a testing policy that they want to convert all of their exams too.

Consider having rooms, and a defined exams that is connected to only and only grade fragment that their type is 
subjective exam. Each exam will have the same list of enrollment of students since we actually need this list.
Also an exam is assigned to list of instructors that they will be called markers since an exam can be mark by more than
one instructor.  
"""


class Room(models.Model):
    name = models.CharField(_('Room Name'), max_length=100, null=True, blank=False)
    location = models.CharField(_('Room location'), max_length=100, null=True, blank=False)
    capacity = models.PositiveIntegerField(_('Room Capacity'), null=True, blank=False)
    updated_by = models.ForeignKey(User, null=True, blank=True)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True)

    def __str__(self):
        return self.name


class Exam(models.Model):
    fragment = models.ForeignKey('grade.GradeFragment', on_delete=models.CASCADE, related_name='exams', null=True,
                                 blank=False)
    date_time = models.DateTimeField(_('Exam Date & Time'), null=True, blank=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='examiners', null=True, blank=False)
    updated_by = models.ForeignKey(User, null=True, blank=True)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True)

    def __str__(self):
        return str(self.fragment)


class Examiner(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, related_name='exams', null=True,
                                   blank=False)
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='examiners',
        null=True,
        blank=False
    )
    generosity_factor = models.IntegerField(_("Generosity"),
                                            help_text=_('Generosity for for this instructor, can be in minus.'
                                                        'Make sure it is in percent'),
                                            null=True, blank=False)
    order = models.PositiveIntegerField(
        _('Examiner Marking Order'),
        help_text=_('This is the order in which after a examiner 1 finish the marking examiner 2 will start..'),
        null=True,
        blank=False
    )
    updated_by = models.ForeignKey(User, null=True, blank=True)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True)

    def __str__(self):
        return str(self.instructor)


class ExamStudent(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='students',
        null=True,
        blank=False
    )

    enrollment = models.ForeignKey(
        'enrollment.Enrollment',
        on_delete=models.CASCADE,
        null=True,
        blank=False
    )
    updated_by = models.ForeignKey(User, null=True, blank=True)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True)


class AssignmentInstance(models.Model):
    # To be used as a second option where we will keep this app independent
    # where we will not add a new field to the StudentGrade model
    pass
