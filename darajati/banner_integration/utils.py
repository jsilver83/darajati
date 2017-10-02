import requests, json
from django.conf import settings
from django.contrib.auth.models import User
from enrollment.models import Section, Enrollment, Student, CourseOffering


def request_faculty_teaching(semester_code, section_code):
    semester_code = str(semester_code).upper()
    section_code = str(section_code).upper()

    response = requests.get(settings.FACULTY_WEB_SERVICE,
                            params={'semester_code': semester_code,
                                    'section': section_code},
                            auth=('', ''))
    response = response.json()
    return response['data'][0]


def request_class_roaster(semester_code, course_code):
    semester_code = str(semester_code).upper()
    course_code = str(course_code).upper()
    response = requests.get(settings.ROSTER_WEB_SERVICE,
                            params={'sem_code': semester_code,
                                    'crse_code': course_code},
                            auth=('', ''))
    response = response.json()
    return response['data'][0]


# "data" : [ {
#     "sem_code" : "201710",
#     "sem_name" : "First Semester 2017-18",
#     "crse_code" : "ENGL01-FH",
#     "crse_name" : "Prep. English I",
#     "sec_code" : "01",
#     "crn" : "15897",
#     "stu_id" : "201721930",
#     "stu_name_engl" : "ALMUKHTAR, HASSAN ALI",
#     "stu_name_arab" : "حسن بن علي بن حبيب المختار",
#     "stu_mobile" : "0541088145",
#     "stu_email" : "s201721930@kfupm.edu.sa",
#     "reg_date" : "2017-08-24T07:51:23.000+03:00",
#     "grade" : {
#       "@nil" : "true"
#     }

def initial_roster_creation(course_offering):
    # results = request_class_roaster('201630', 'ENGL02-SM')
    json_data = open('/home/malnajdi/Projects/Django/darajati/darajati/banner_integration/roaster.json')
    results = json.load(json_data)
    students = []
    sections = []
    enrollments = []
    total_student_in_section = 0

    course_offering = CourseOffering.get_course_offering(course_offering)

    for result in results['data']:
        section = '{}-{}'.format(course_offering.course.code, result['sec_code'])
        is_section_exists = Section.is_section_exists(course_offering, section)
        is_student_exists = Student.is_student_exists(result['stu_email'])
        student = None
        """
        If the current section do not exists.
        """
        if not is_section_exists:
            section, created = Section.get_create_section(course_offering, section, result['crn'])
            sections.append(section)

            student, created = Student.get_create_student(
                result['stu_email'][:10],
                result['stu_id'],
                result['stu_id'],
                result['stu_name_engl'],
                result['stu_name_arab'],
                result['stu_mobile'],
                result['stu_email'])
            students.append(
                {'student_id': result['stu_id'],
                 'student_name': result['stu_name_engl'],
                 'student_email': result['stu_email']}
            )

            Enrollment.get_create_enrollment(
                student=student,
                section=section,
                register_date=result['reg_date']
            )

            enrollments.append(
                {'student': result['stu_id'],
                 'section': section}
            )
        """
        If the current section do exists.
        """
        if is_section_exists:
            section = Section.objects.get(code__exact=section)

            if not is_student_exists:
                # Create Student
                student, created = Student.get_create_student(
                    result['stu_email'][:10],
                    result['stu_id'],
                    result['stu_id'],
                    result['stu_name_engl'],
                    result['stu_name_arab'],
                    result['stu_mobile'],
                    result['stu_email'])
                students.append(
                    {'student_id': result['stu_id'],
                     'student_name': result['stu_name_engl'],
                     'student_email': result['stu_email']}
                )

            # Get the enrollment if exists
            if not Enrollment.is_enrollment_exists(student, section):
                enrollment, created = Enrollment.get_create_enrollment(
                    student=student,
                    section=section,
                    register_date=result['reg_date']
                )
                enrollments.append(
                    {'student': result['stu_id'],
                     'section': section}
                )



        # TODO: Delete section
    return sections, students

# university_id
# government_id
# english_name =
# arabic_name =
# mobile = model
# personal_email
# active = model
