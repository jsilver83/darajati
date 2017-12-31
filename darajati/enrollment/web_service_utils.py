import json, requests
from django.conf import settings


def get_student_enrollments(semester_code=None, course_code=None):
    url = settings.ROSTER_WEB_SERVICE + semester_code + '/' + course_code
    response = requests.get(url, auth=(settings.BANNER_API_USER, settings.BANNER_API_PASSWORD))
    response = response.json()
    # result = json.load(open('/home/malnajdi/Projects/Django/darajati/enrollment.json'))
    return response['data']


def get_instructor_enrollments(semester_code=None, crn=None):
    response = requests.get(settings.FACULTY_WEB_SERVICE + semester_code + '/' + crn,
                            auth=(settings.BANNER_API_USER, settings.BANNER_API_PASSWORD))
    response = response.json()
    # result = json.load(open('/home/malnajdi/Projects/Django/darajati/periods.json'))
    return response['data']


def get_course_crn_list(semester_code=None, course_code=None):
    data = get_student_enrollments(semester_code, course_code)
    unique_section = []
    for item in data:
        unique_section.append(item['crn']) \
            if item['crn'] not in unique_section else False
    return unique_section


def get_course_sections_value(semester_code=None, course_code=None):
    list_of_crn = get_course_crn_list(semester_code, course_code)
    periods = []
    for crn in list_of_crn:
        periods += get_instructor_enrollments(semester_code, crn)

    sections = []
    sections_list = []
    for period in periods:
        if period['sec_code'] not in sections_list:
            sections_list.append(period['sec_code'])
            sections.append(period)

    sections = sorted(sections, key=lambda x: x['sec_code'])
    return sections


def get_courser_sections_list(semester_code=None, course_code=None):
    sections = get_course_sections_value(semester_code, course_code)
    sections_list = []
    for section in sections:
        sections_list.append(
            section['sec_code']
        ) if section['sec_code'] not in sections_list else False
    sections_list = sorted(sections_list, key=lambda x: x)
    return sections_list


def get_instructor_sections(semester_code=None, course_code=None, instructor=None):
    instructor_assignment = []
    sections = get_course_sections_value(semester_code, course_code)
    for section in sections:
        instructor_assignment.append(
            section['sec_code']
        ) if section['sec_code'] not in instructor_assignment and section['user'] == instructor else False
    return instructor_assignment


def get_section_periods(section_code, semester_code, crn):
    periods = get_instructor_enrollments(semester_code, crn)
    section_periods = []
    for period in periods:
        if period['sec_code'] == section_code:
            section_periods.append(
                period
            )
    return section_periods


def get_section(semester_code, crn):
    sections = get_instructor_enrollments(semester_code, crn)
    for section in sections:
        return section
