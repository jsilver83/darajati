from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from enrollment.models import Coordinator, Instructor

User = settings.AUTH_USER_MODEL


class Room(models.Model):
    name = models.CharField(_('Room Name'), max_length=100, null=True, blank=False)
    location = models.CharField(_('Room location'), max_length=100, null=True, blank=False)
    capacity = models.PositiveIntegerField(_('Room Capacity'), null=True, blank=False)
    updated_by = models.ForeignKey(User, null=True, blank=True)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True)

    def __str__(self):
        return self.name


class Exam(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=False)
    date_time = models.DateTimeField(_('Exam Date & Time'), null=True, blank=False)
    coordinator = models.ForeignKey(Coordinator, on_delete=models.SET_NULL, null=True, blank=False)
    updated_by = models.ForeignKey(User, null=True, blank=True)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True)

    def __str__(self):
        return str(self.room)


class Assignment(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, null=True, blank=False)
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, blank=False)
    generosity_factor = models.IntegerField(_("Generosity"),
                                            help_text=_('Generosity for for this instructor, can be in minus.'
                                                        'Make sure it is in percent'),
                                            null=True, blank=False)
    updated_by = models.ForeignKey(User, null=True, blank=True)
    updated_on = models.DateTimeField(_('Updated On'), auto_now=True)

    def __str__(self):
        return str(self.exam)


class AssignmentInstance(models.Model):
    # To be used as a second option where we will keep this app independent
    # where we will not add a new field to the StudentGrade model
    pass
