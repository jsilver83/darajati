import requests, json
from django.conf import settings
from django.contrib.auth.models import User
from enrollment.models import Section, Enrollment, Student, CourseOffering, UserProfile, Instructor
from attendance.models import ScheduledPeriod
from django.db import transaction


def request_faculty_teaching(semester_code, section_code):
    response = requests.get(settings.FACULTY_WEB_SERVICE + semester_code + '/' + section_code,
                            auth=(settings.BANNER_API_USER, settings.BANNER_API_PASSWORD))
    response = response.json()
    return response


def request_class_roaster(semester_code, course_code):
    url = settings.ROSTER_WEB_SERVICE + semester_code + '/' + course_code
    response = requests.get(url, auth=(settings.BANNER_API_USER, settings.BANNER_API_PASSWORD))
    response = response.json()
    return response


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

    # Course offering
    course_offering = CourseOffering.get_course_offering(course_offering)
    inactive_sections = Section.objects.filter(course_offering=course_offering)
    inactive_enrollments = Enrollment.objects.filter(section__course_offering=course_offering)
    inactive_sections_count = 0

    # Web-service retrieval
    semester_code, semester_period = course_offering.semester.code.split('-')
    results = request_class_roaster(semester_code, course_offering.course.code)
    # Bulk Lists to commit
    students = []
    sections = []
    all_sections = []
    enrollments = []

    # Reports
    section_report = []
    student_report = []
    enrollment_report = []
    crn = []

    for result in results['data']:
        # Initialize non existing sections
        section_code = '{}-{}'.format(course_offering.course.code, result['sec'])
        if not Section.is_section_exists(course_offering, section_code):
            section = Section(course_offering=course_offering,
                              code=section_code,
                              crn=result['crn'],
                              active=True)
            if section.crn not in crn:
                sections.append(section)
                all_sections.append(section)
                section_report.append({'section': section, 'code': 'CREATE', 'message': 'New section to be created.'})
                crn.append(section.crn)
        else:
            section = Section.objects.get(course_offering__exact=course_offering,
                                          code__exact=section_code,
                                          crn=result['crn'])
            if not section.active:
                section.active = True
                if commit:
                    section.save()
                section_report.append(
                    {'section': section, 'code': 'ACTIVE', 'message': 'Existing section to re-activate'})
            if section.crn not in crn:
                all_sections.append(section)
                crn.append(section.crn)

        # Initialize non students sections
        if not Student.is_student_exists(result['email']):
            user, created = User.objects.get_or_create(username=result['email'][:10])
            profile, created = UserProfile.objects.get_or_create(user=user)
            student = Student(
                user_profile=profile,
                university_id=result['stu_id'],
                government_id=result['stu_id'],
                english_name=result['name_en'],
                arabic_name=result['name_ar'],
                mobile=result['mobile'],
                personal_email=result['email'],
                active=True)
            student_report.append({'section': student, 'code': 'CREATE', 'message': 'New student to be created'})
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
        section_code = '{}-{}'.format(course_offering.course.code, result['sec'])
        if not Section.is_section_exists(course_offering, section_code):

            section = Section(course_offering=course_offering,
                              code=section_code,
                              crn=result['crn'],
                              active=True)
        else:
            section = Section.objects.get(course_offering__exact=course_offering,
                                          code__exact=section_code)

        if not Student.is_student_exists(result['email']):
            user, created = User.objects.get_or_create(username=result['email'][:10])
            profile, created = UserProfile.objects.get_or_create(user=user)
            student = Student(
                user_profile=profile,
                university_id=result['stu_id'],
                government_id=result['stu_id'],
                english_name=result['name_en'],
                arabic_name=result['name_ar'],
                mobile=result['mobile'],
                personal_email=result['email'],
                active=True)
        else:
            student = Student.objects.get(personal_email__exact=result['email'])

        # Enrollments
        if not Enrollment.is_enrollment_exists(student, section):
            enrollment = Enrollment(
                section=section,
                student=student,
                register_date=result['reg_date'],
                letter_grade=result['grade']
            )
            code = 'CREATED'
            message = 'Enrollment to be created'
            # This is to check if this student has any enrollment in any section in this course offering
            move_enrollment = Enrollment.objects.filter(student=student,
                                                        section__course_offering=course_offering).first()

            if move_enrollment:
                if commit:
                    move_enrollment.active = False
                    move_enrollment.comment = "Moved to section {}".format(section.code)
                    move_enrollment.letter_grade = "MOVED"
                    move_enrollment.save()

                enrollment = Enrollment(
                    section=section,
                    student=student,
                    register_date=result['reg_date'],
                    letter_grade=result['grade'],
                    comment="Moved from section {}".format(move_enrollment.section.code)
                )
                code = 'MOVED'
                message = 'Moved from section {} to section {}'.format(
                    move_enrollment.section.code,
                    section.code)

            if str(result['grade']).lower() in ['w', 'wp', 'wf', 'ic']:
                comment = 'Dropped with grade {}'.format(str(result['grade']).lower())
                enrollment = Enrollment(
                    section=section,
                    student=student,
                    register_date=result['reg_date'],
                    letter_grade=result['grade'],
                    comment=comment,
                    active=False
                )
                code = 'DROP'
                message = 'Dropped with grade {}'.format(str(result['grade']).lower())

            enrollments.append(enrollment)
            enrollment_report.append({'enrollment': enrollment, 'code': code, 'message': message})
        else:
            enrollment = Enrollment.objects.get(student=student, section=section)
            if not enrollment.active:
                enrollment.active = True

            if enrollment.letter_grade != result['grade']:
                if str(result['grade']).lower() in ['w', 'wp', 'wf', 'ic']:
                    enrollment.comment = 'Dropped with grade {}'.format(str(result['grade']).lower())
                    enrollment.active = False
                    enrollment_report.append({'enrollment': enrollment,
                                              'code': 'DROP',
                                              'message': 'Dropped with grade {}'.format(str(result['grade']).lower())})
                else:
                    enrollment_report.append({'enrollment': enrollment,
                                              'code': 'Grade Changed',
                                              'message': 'Grade changed from {} to {}'.format(
                                                  enrollment.letter_grade,
                                                  str(result['grade']).lower())})
                    enrollment.letter_grade = result['grade']
            if commit:
                enrollment.save()

            inactive_enrollments = inactive_enrollments.exclude(student=student, section=section)

    inactive_enrollments = inactive_enrollments.exclude(letter_grade="MOVED")

    for inactive_enrollment in inactive_enrollments:
        enrollment_report.append(
            {'enrollment': inactive_enrollment, 'code': 'INACTIVE', 'message': 'enrollment will be de-activated'}
        )

    for inactive_section in inactive_sections:
        section_report.append(
            {'section': inactive_section, 'code': 'INACTIVE', 'message': 'section will be de-activated'}
        )

    if commit:
        inactive_enrollments.update(comment="Deleted without grade", active=False)
        with transaction.atomic():
            # # 1.3. Create enrollment or get it if exists
            Enrollment.objects.bulk_create(
                enrollments
            )
            # # 2.1 Delete the inactive sections with CASCADE
            if inactive_sections_count:
                inactive_sections.update(active=False)

    return section_report, student_report, enrollment_report, all_sections


def initial_faculty_teaching_creation(course_offering, sections, commit=False):

    course_offering = CourseOffering.get_course_offering(course_offering)
    instructors = []
    periods_report = []
    inactive_periods = None
    semester_code, semester_period = course_offering.semester.code.split('-')
    for section in sections:
        results = request_faculty_teaching(semester_code, section.crn)
        # Instructor and Periods Initialization
        for result in results['data']:
            if not Instructor.is_instructor_exists(result['email']):
                user, created = User.objects.get_or_create(username=result['user'])
                profile, created = UserProfile.objects.get_or_create(user=user)
                if commit:
                    instructor, created = Instructor.objects.get_or_create(
                        user_profile=profile,
                        university_id=result['fac_id'],
                        government_id=result['fac_id'],
                        english_name=result['name'],
                        arabic_name=result['name'],
                        personal_email=result['email'],
                        active=True)
                else:
                    instructor = Instructor(
                        user_profile=profile,
                        university_id=result['fac_id'],
                        government_id=result['fac_id'],
                        english_name=result['name'],
                        arabic_name=result['name'],
                        personal_email=result['email'],
                        active=True)

                instructors.append(instructor)
            else:
                instructor = Instructor.objects.get(personal_email__exact=result['email'])

            # inactive_periods += ScheduledPeriod.objects.filter(section=section, instructor_assigned=instructor)
            for day in map(str, result['class_days']):
                current_day = None

                if day == 'U':
                    current_day = ScheduledPeriod.Days.SUNDAY
                if day == 'M':
                    current_day = ScheduledPeriod.Days.MONDAY
                if day == 'T':
                    current_day = ScheduledPeriod.Days.TUESDAY
                if day == 'W':
                    current_day = ScheduledPeriod.Days.WEDNESDAY
                if day == 'R':
                    current_day = ScheduledPeriod.Days.THURSDAY

                start_time = list(map(str, result['start_time']))
                start_time = start_time[0] + start_time[1] + ':' + start_time[2] + start_time[3]
                end_time = list(map(str, result['end_time']))
                end_time = end_time[0] + end_time[1] + ':' + end_time[2] + end_time[3]
                if not ScheduledPeriod.is_period_exists(section, instructor, current_day, start_time, end_time):
                    scheduled_period = ScheduledPeriod(
                        section=section,
                        instructor_assigned=instructor,
                        day=current_day,
                        title=result['activity'],
                        start_time=start_time,
                        end_time=end_time,
                        location=result['bldg'] + ' ' + result['room'],
                        late_deduction=1,
                        absence_deduction=1
                    )
                    if commit:
                        with transaction.atomic():
                            scheduled_period.save()
                    periods_report.append({
                        'period': scheduled_period, 'code': 'CREATE', 'message': 'New period to be created'
                    })
                else:
                    continue

    return instructors, periods_report
