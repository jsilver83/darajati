import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from django.db import transaction

from enrollment.utils import get_local_datetime_format
from enrollment.models import Section, Enrollment, Student, CourseOffering, Instructor
from attendance.models import ScheduledPeriod


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


def initial_roster_creation(course_offering, current_user, commit=False):
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
    semester_code = course_offering.semester.code
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
        if not Section.is_section_exists_in_course_offering(course_offering, section_code):
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
            student = Student(
                user=user,
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

    # ----------------------
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
        if not Section.is_section_exists_in_course_offering(course_offering, section_code):

            section = Section(course_offering=course_offering,
                              code=section_code,
                              crn=result['crn'],
                              active=True)
        else:
            section = Section.objects.get(course_offering__exact=course_offering,
                                          code__exact=section_code)

        if not Student.is_student_exists(result['email']):
            user, created = User.objects.get_or_create(username=result['email'][:10])
            student = Student(
                user=user,
                university_id=result['stu_id'],
                government_id=result['stu_id'],
                english_name=result['name_en'],
                arabic_name=result['name_ar'],
                mobile=result['mobile'],
                personal_email=result['email'],
                active=True)
        else:
            student = Student.objects.get(personal_email__exact=result['email'])
            user, created = User.objects.get_or_create(username=result['email'][:10])
            if not student.user:
                student.user = user
                student.save()

        # Enrollments
        if not Enrollment.is_enrollment_exists(student, section):
            enrollment = Enrollment(
                section=section,
                student=student,
                updated_by=current_user,
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
                    updated_by=current_user,
                    comment="Moved from section {}".format(move_enrollment.section.code)
                )
                code = 'MOVED'
                message = 'Moved from section {} to section {}'.format(
                    move_enrollment.section.code,
                    section.code)

            if str(result['grade']).lower() in ['w', 'wp', 'wf', 'ic', 'dn']:
                comment = 'Dropped with grade {}'.format(str(result['grade']).lower())
                enrollment = Enrollment(
                    section=section,
                    student=student,
                    register_date=result['reg_date'],
                    letter_grade=result['grade'],
                    comment=comment,
                    updated_by=current_user,
                    active=False
                )
                code = 'DROP'
                message = 'Dropped with grade {}'.format(str(result['grade']).lower())

            enrollments.append(enrollment)
            enrollment_report.append({'enrollment': enrollment, 'code': code, 'message': message})
        else:
            enrollment = Enrollment.objects.get(student=student, section=section)

            if not enrollment.active and str(result['grade']).lower() not in ['w', 'wp', 'wf', 'ic', 'dn']:
                enrollment.active = True

            if enrollment.letter_grade != result['grade']:
                if str(result['grade']).lower() in ['w', 'wp', 'wf', 'ic', 'dn']:
                    enrollment.comment = 'Dropped with grade {}'.format(str(result['grade']).lower())
                    enrollment.active = False
                    enrollment.letter_grade = result['grade']

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
            else:
                if str(result['grade']).lower() in ['w', 'wp', 'wf', 'ic', 'dn'] and enrollment.active:
                    enrollment.comment = 'Dropped with grade {}'.format(str(result['grade']).lower())
                    enrollment.active = False
                    enrollment.letter_grade = result['grade']

                    enrollment_report.append({'enrollment': enrollment,
                                              'code': 'DROP',
                                              'message': 'Dropped with grade {}'.format(str(result['grade']).lower())})
            if commit:
                enrollment.updated_by = current_user
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
    semester_code = course_offering.semester.code
    for section in sections:
        results = request_faculty_teaching(semester_code, section.crn)
        # Instructor and Periods Initialization
        for result in results['data']:
            if not result['email'] and not result['user']:
                continue
            if not Instructor.is_instructor_exists(result['email']):
                user, created = User.objects.get_or_create(username=result['user'])
                if commit:
                    instructor, created = Instructor.objects.get_or_create(
                        user=user,
                        university_id=result['fac_id'],
                        government_id=result['fac_id'],
                        english_name=result['name'],
                        arabic_name=result['name'],
                        personal_email=result['email'],
                        active=True)
                else:
                    instructor = Instructor(
                        user=user,
                        university_id=result['fac_id'],
                        government_id=result['fac_id'],
                        english_name=result['name'],
                        arabic_name=result['name'],
                        personal_email=result['email'],
                        active=True)

                instructors.append(instructor)
            else:
                instructor = Instructor.objects.get(personal_email__exact=result['email'])
                user, created = User.objects.get_or_create(username=result['user'])
                if not instructor.user:
                    instructor.user = user
                    instructor.save()

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


def get_format_section_code(course_code, section_code):
    return '{}-{}'.format(course_code, section_code)


class Synchronization(object):

    def __init__(self, course_offering, current_user, commit=False):
        self.course_offering = CourseOffering.get_course_offering(course_offering)
        self.current_user = current_user
        self.commit = commit
        if not self.course_offering:
            raise ValueError(_('Make sure provided Course Offering is a valid one'))

        self.course_code = self.course_offering.course.code
        self.semester_code = self.course_offering.semester.code

        # set global variables to be used
        self.roster_information = self.get_roster_information()
        self.sections = self.get_sections()
        self.non_created_sections = []
        self.changed_sections = []
        self.result = None
        self.section = None
        self.crns = []
        self.student = None
        self.enrollment = None
        self.new_enrollments = []
        self.current_enrollments = []
        self.old_enrollments = []
        self.inactive_enrollment = []

    def get_roster_information(self):
        """
        This will call banner-api to get students enrollment to a the assigned course offering
        :return: list of enrollments
        """
        url = settings.ROSTER_WEB_SERVICE + self.semester_code + '/' + self.course_code
        response = requests.get(url, auth=(settings.BANNER_API_USER, settings.BANNER_API_PASSWORD))
        response = response.json()
        return response.get('data')

    def get_section_faculties(self, section):
        """
        This will call banner-api to get faculty that are assigned to this given section
        :return: list of
        """
        url = settings.FACULTY_WEB_SERVICE + self.semester_code + '/' + section.crn
        response = requests.get(url, auth=(settings.BANNER_API_USER, settings.BANNER_API_PASSWORD))
        response = response.json()
        return response.get('data')

    def get_sections(self):
        """
        :return: list of all sections that belongs to this course offering
        """
        self.sections = self.course_offering.sections.all()
        return self.sections

    def get_enrollments(self):
        """
        :return:
        """
        return Enrollment.objects.filter(section__course_offering=self.course_offering)

    def get_inactive_sections(self):
        """
        Getting all sections for a given 'Course Offering' and check if each section
        do exists in the api result, if not than this section is inactive.
        :return: list of inactive sections
        """
        inactive_sections = self.sections
        for enrollment in self.roster_information:
            section_code = get_format_section_code(self.course_code, enrollment['sec'])
            if Section.is_section_exists_in_course_offering(self.course_offering, section_code):
                inactive_sections = inactive_sections.exclude(
                    course_offering=self.course_offering,
                    code=section_code
                )
        return inactive_sections

    def roaster_initiation(self):
        """
        This is the main enrollment assignment it has the main loop that most of other
        functions will be ran into.
        :return: none
        """

        for index, self.result in enumerate(self.roster_information):
            self.create_or_activate_sections()
            self.create_or_get_student()
            self.assign_or_change_enrollment()
            if index == 2: break

        if self.commit:
            self.commit_roaster_changes()

    def create_or_activate_sections(self):
        """
        :return:
        """
        section_code = get_format_section_code(self.course_code, self.result['sec'])
        if not Section.is_section_exists_in_course_offering(self.course_offering, section_code) and self.result['crn'] not in self.crns:
            self.section = Section(
                course_offering=self.course_offering,
                code=section_code,
                crn=self.result['crn'],
                active=True
            )
            self.non_created_sections.append(self.section)
            self.crns.append(self.result['crn'])

        else:
            if self.result['crn'] in self.crns:
                return
            self.section = Section.objects.get(
                course_offering__exact=self.course_offering,
                code__exact=section_code,
                crn=self.result['crn']
            )
            if not self.section.active and self.section.crn not in self.crns:
                self.section.active = True
                self.changed_sections.append(self.section)
                self.crns.append(self.section.crn)

    def create_or_get_student(self):
        """
        :return:
        """
        user, created = User.objects.get_or_create(username=self.result['email'][:10])
        self.student, created = Student.objects.get_or_create(
            user=user,
            university_id=self.result['stu_id']
        )
        self.student.government_id = self.result['stu_id']
        self.student.english_name = self.result['name_en']
        self.student.arabic_name = self.result['name_ar']
        self.student.mobile = self.result['mobile']
        self.student.personal_email = self.result['email']
        self.student.active = True
        self.student.save()

    def assign_or_change_enrollment(self):
        """
        :return:
        """
        if self.commit:
            self.section.save()
        if not Enrollment.is_enrollment_exists(self.student, self.section):
            self.enrollment = Enrollment(
                section=self.section,
                student=self.student,
                updated_by=self.current_user,
                register_date=get_local_datetime_format(self.result['reg_date']),
                letter_grade=self.result['grade']
            )
            current_old_enrollments = Enrollment.objects.filter(
                student=self.student,
                section__course_offering=self.course_offering,
                letter_grade__iexact="MOVED"
            )
            if current_old_enrollments:
                for old_enrollment in current_old_enrollments:
                    old_enrollment.comment = 'Moved to other section {}'.format(self.section)
                    old_enrollment.letter_grade = 'MOVED'
                    self.old_enrollments.append(old_enrollment)

            if self.is_grade_has_a_letter():
                self.enrollment.comment = 'Dropped with grade {}'.format(str(self.result['grade']).lower())
                self.enrollment.updated_by = self.current_user
                self.enrollment.active = False
                self.inactive_enrollment.append(self.enrollment)
            else:
                self.new_enrollments.append(self.enrollment)
        else:
            self.enrollment = Enrollment.objects.get(
                student=self.student,
                section=self.section
            )
            self.enrollment.letter_grade = self.result['grade']
            self.enrollment.active = True

            if self.is_grade_has_a_letter():
                self.enrollment.active = False
                self.enrollment.comment = 'Dropped with grade {}'.format(str(self.result['grade']).lower())
                self.inactive_enrollment.append(self.enrollment)
            else:
                self.current_enrollments.append(self.enrollment)

    def is_grade_has_a_letter(self):
        """
        :return:
        """
        current_letter_grade = str(self.result['grade']).lower()
        letter_grades = ['w', 'wp', 'wf', 'ic', 'dn']
        return True if current_letter_grade in letter_grades else False

    def commit_roaster_changes(self):
        with transaction.atomic():
            # Enrollment
            for new_enrollment in self.new_enrollments:
                new_enrollment.save()

            for current_enrollment in self.current_enrollments:
                current_enrollment.save()

            for moved_enrollment in self.old_enrollments:
                moved_enrollment.save()

            for inactive_enrollment in self.inactive_enrollment:
                inactive_enrollment.save()

    def roaster_report(self):
        print("Sections to be created: ", len(self.non_created_sections))
        print("Sections to be changed: ", len(self.changed_sections))
        print("New Enrollments: ", len(self.new_enrollments))
        print("Current Enrollments: ", len(self.current_enrollments))
        print("Old enrollments: ", len(self.old_enrollments))
        print("Inactive enrollments: ", len(self.inactive_enrollment))