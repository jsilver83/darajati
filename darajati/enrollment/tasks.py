from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery import task

from enrollment.models import Section, Enrollment
from grade.models import GradeBreakDown, StudentGrade


@shared_task()
def get_students_enrollment_grades(today):
    """
    :return:
    """

    count = 0
    enrollments = []
    sections = Section.get_sections(today)
    for section in sections:
        enrollment_list = Enrollment.get_students(section.id)
        tasks = GradeBreakDown.get_section_grade_break_down(section)
        for enrollment in enrollment_list:
            for task in tasks:
                created, grade = StudentGrade.objects.get_or_create(enrollment=enrollment, grade_break_down=task)
                enrollments += enrollments.append(grade)
                if created:
                    count += 1
    return enrollments
