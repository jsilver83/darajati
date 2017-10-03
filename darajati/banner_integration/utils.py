import requests, json
from django.conf import settings
from django.contrib.auth.models import User
from enrollment.models import Section, Enrollment, Student, CourseOffering, UserProfile
from django.db import transaction


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


def initial_roster_creation(course_offering, commit=False):
    """
    Method Summary: 
    :param course_offering: an ID of the course offering
    :param commit
    
    Note: We are requesting these information via the web-service
    
    There are sections 1, 2 and 3 in this method when commit is True
        section 1: Will populate all new sections/students/enrollments.
        section 2: Will deactivate any record that was moved to other section/deleted.
        section 3: assigning instructors to their scheduled periods.
    """
    # Web-service retrieval
    # results = request_class_roaster('201630', 'ENGL02-SM')
    json_data = open('/home/malnajdi/Projects/Django/darajati/darajati/banner_integration/roaster.json')
    results = json.load(json_data)

    # Course offering
    course_offering = CourseOffering.get_course_offering(course_offering)
    inactive_sections = Section.objects.filter(course_offering__exact=course_offering)
    inactive_sections_count = 0

    # Bulk Lists to report and to commit
    students = []
    sections = []
    enrollments = []
    crn = []

    for result in results['data']:
        # Initialize non existing sections
        section_code = '{}-{}'.format(course_offering.course.code, result['sec_code'])
        if not Section.is_section_exists(course_offering, section_code):
            section = Section(course_offering=course_offering,
                              code=section_code,
                              crn=result['crn'])
            if section.crn not in crn:
                sections.append(section)
                crn.append(section.crn)
        else:
            section = Section.objects.get(course_offering__exact=course_offering,
                                          code__exact=section_code)

        # Initialize non students sections
        if not Student.is_student_exists(result['stu_email']):
            user, created = User.objects.get_or_create(username=result['stu_email'][:10])
            profile, created = UserProfile.objects.get_or_create(user=user)
            student = Student(
                user_profile=profile,
                university_id=result['stu_id'],
                government_id=result['stu_id'],
                english_name=result['stu_name_engl'],
                arabic_name=result['stu_name_arab'],
                mobile=result['stu_mobile'],
                personal_email=result['stu_email'],
                active=True)
            students.append(student)

        # Remove active sections from inactive list
        if section in inactive_sections:
            inactive_sections = inactive_sections.exclude(
                id=section.id
            )

    inactive_sections_count = len(inactive_sections)
    if commit:
        with transaction.atomic():
            """
            :param commit
            If the commit option was set to True we then only commit the changes.
            """
            # 1.1. Create section or get it if exists
            Section.objects.bulk_create(
                sections
            )
            # 1.2. Create student or get it if exists
            Student.objects.bulk_create(
                students
            )

        for result in results['data']:
            # Initialize non existing enrollments
            section_code = '{}-{}'.format(course_offering.course.code, result['sec_code'])
            section = Section.objects.get(course_offering__exact=course_offering,
                                          code__exact=section_code)
            student = Student.objects.get(personal_email__exact=result['stu_email'])

            if not Enrollment.is_enrollment_exists(student, section):
                enrollment = Enrollment(
                    section=section,
                    student=student,
                    register_date=result['reg_date']
                )
                enrollments.append(enrollment)
        with transaction.atomic():
            # # 1.3. Create enrollment or get it if exists
            Enrollment.objects.bulk_create(
                enrollments
            )
            # # 2.1 Delete the inactive sections with CASCADE
            if inactive_sections_count:
                inactive_sections.update()

    return sections, students, enrollments, inactive_sections_count
