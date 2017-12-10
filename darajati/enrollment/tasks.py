from __future__ import absolute_import, unicode_literals
from celery import shared_task
from enrollment.models import Section, Enrollment
from grade.models import GradeFragment, StudentGrade


@shared_task()
def get_students_enrollment_grades():
    """
    :return:
    """

    count = 0
    enrollments = []
    sections = Section.get_current_semesters_sections()
    messages = []
    if not sections:
        return "There is no sections available to create grades for - 'Scheduled Task - get_students_enrollment_grades'"
    for section in sections:
        enrollment_list = Enrollment.get_students_of_section(section.id)
        if not enrollment_list:
            messages.append('There are no enrollments for section {}'.format(section))
        else:
            fragments = GradeFragment.get_section_grade_fragments(section)
            if not fragments:
                messages.append('There are no grades fragments for section {}'.format(section))
            for enrollment in enrollment_list:
                for fragment in fragments:
                    grade, created = StudentGrade.objects.get_or_create(enrollment=enrollment,
                                                                        grade_fragment=fragment)
                    if created:
                        enrollments.append(
                            '{} | Grade was created for student {} in section {} for grade plan {}'.format(
                                count, enrollment.student.english_name, section.code, fragment
                            ))
                        count += 1
    if enrollments:
        return enrollments
    return messages
