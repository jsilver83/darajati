from __future__ import absolute_import, unicode_literals
from celery import shared_task
from enrollment.models import Section, Enrollment
from grade.models import GradeFragment, StudentGrade


# @shared_task()
def get_students_enrollment_grades():
    """
    :return:
    """

    count = 0
    enrollments = []
    sections = Section.get_sections()
    messages = []
    if not sections:
        return "There is no sections available to create grades for - 'Scheduled Task - get_students_enrollment_grades'"
    for section in sections:
        enrollment_list = Enrollment.get_students(section.id)
        if not enrollment_list:
            messages.append('There are no enrollments for section {}'.format(section))
        else:
            tasks = GradeFragment.get_section_grade_fragments(section)
            if not tasks:
                messages.append('There are no grades fragments for section {}'.format(section))
                return messages
            for enrollment in enrollment_list:
                for task in tasks:
                    grade, created = StudentGrade.objects.get_or_create(enrollment=enrollment, grade_fragment=task)
                    if created:
                        enrollments.append(
                            '{} | Grade was created for student {} in section {} for grade plan {}'.format(
                                count, enrollment.student.english_name, section.code, task
                            ))
                        count += 1
    if enrollments:
        return enrollments
    return messages
