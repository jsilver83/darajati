import math
from .models import *


def ordinal(n):
    return "%d%s" % (n, "tsnrhtdd"[(math.floor(n / 10) % 10 != 1) * (n % 10 < 4) * n % 10::4])


def if_null(var, val):
    if var is None:
        return val
    return var


def get_allowed_markers_for_a_fragment(fragment, all_department_instructors=False):
    if fragment.allow_markers_from_other_courses or all_department_instructors:
        department = fragment.course_offering.course.department
        return Instructor.objects.filter(
            assigned_periods__section__course_offering__course__department=department
        ).distinct()
    else:
        periods = ScheduledPeriod.objects.filter(section__course_offering=fragment.course_offering)
        return Instructor.objects.filter(
            pk__in=periods.values('instructor_assigned').distinct()
        )
