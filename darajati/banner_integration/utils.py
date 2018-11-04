import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from django.db import transaction

from enrollment.utils import get_local_datetime_format
from enrollment.models import Section, Enrollment, Student, CourseOffering, Instructor
from attendance.models import ScheduledPeriod


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
        self.none = None
        self.new_enrollments = []
        self.current_enrollments = []
        self.old_enrollments = []
        self.inactive_enrollment = []
        self.all_sections = []
        self.enrollment = None
        self.dropped_enrollments = self.get_enrollments().filter(active=True)
        # instructor
        self.instructor = None
        self.faculty_period = None

        # Periods
        self.current_day = None
        self.period = None
        self.non_created_periods = []
        self.periods_with_issues = []

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

        self.is_inactive_enrollment()
        if self.commit:
            self.commit_roaster_changes()

    def is_inactive_enrollment(self):
        for dropped_enrollment in self.dropped_enrollments:
            dropped_enrollment.active = False
            dropped_enrollment.comment = 'Dropped with no letter grade'
            dropped_enrollment.letter_grade = 'Dropped'
            dropped_enrollment.updated_by = self.current_user
            self.inactive_enrollment.append(dropped_enrollment)

    def create_or_activate_sections(self):
        """
        :return:
        """
        section_code = get_format_section_code(self.course_code, self.result['sec'])
        if not Section.is_section_exists_in_course_offering(self.course_offering, section_code) and \
                self.result['crn'] not in self.crns:
            self.section = Section(
                course_offering=self.course_offering,
                code=section_code,
                crn=self.result['crn'],
                active=True
            )
            self.all_sections.append(self.section)
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
                self.all_sections.append(self.section)
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
        self.dropped_enrollments = self.dropped_enrollments.exclude(
            section=self.section,
            student=self.student
        )
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
            )

            if current_old_enrollments:
                for old_enrollment in current_old_enrollments:
                    old_enrollment.comment = 'Moved to other section {}'.format(self.section)
                    old_enrollment.letter_grade = 'MOVED'
                    old_enrollment.updated_by = self.current_user
                    old_enrollment.active = False
                    self.old_enrollments.append(old_enrollment)

            if self.is_grade_has_a_letter() and self.enrollment.active:
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

            current_old_enrollments = Enrollment.objects.filter(
                student=self.student,
                section__course_offering=self.course_offering,
                active=True
            ).exclude(id=self.enrollment.id)

            for old_enrollment in current_old_enrollments:
                old_enrollment.comment = 'Moved to other section {}'.format(self.section)
                old_enrollment.letter_grade = 'MOVED'
                old_enrollment.updated_by = self.current_user
                old_enrollment.active = False
                self.old_enrollments.append(old_enrollment)

            self.enrollment.letter_grade = self.result['grade']

            # Case 1 When enrollment is active and has no letter grade
            # than the registrar update the letter grade with one of the 5 letter grades
            # ['w', 'wp', 'wf', 'ic', 'dn'] than deactivate the student
            if self.is_grade_has_a_letter() and self.enrollment.active:
                self.enrollment.active = False
                self.enrollment.comment = 'Dropped with grade {}'.format(str(self.result['grade']).lower())
                self.enrollment.updated_by = self.current_user
                self.inactive_enrollment.append(self.enrollment)

            # Case 2 if student was deactivated and he got changed back to active by
            # the registrar this means student do not have a letter grade from the 5
            # ['w', 'wp', 'wf', 'ic', 'dn'] so he should be activated
            elif not self.is_grade_has_a_letter() and not self.enrollment.active:
                self.enrollment.active = True
                self.current_enrollments.append(self.enrollment)

    def is_grade_has_a_letter(self):
        """
        :return:
        """
        current_letter_grade = str(self.enrollment.letter_grade).lower()
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

            for enrollment in self.inactive_enrollment:
                enrollment.save()

    def faculty_initiation(self):
        """
        :return:
        """
        for self.section in self.all_sections:
            faculties_periods = self.get_section_faculties(self.section)
            for self.faculty_period in faculties_periods:
                if not self.faculty_period['email'] and not self.faculty_period['user']:
                    continue
                self.create_or_get_instructor()
                self.create_or_get_periods()

        if self.commit:
            self.commit_faculties_periods()

    def create_or_get_instructor(self):
        """
        :return:
        """
        user, created = User.objects.get_or_create(username=self.faculty_period['user'])
        self.instructor, created = Instructor.objects.get_or_create(
            user=user,
            university_id=self.faculty_period['fac_id']
        )
        self.instructor.government_id = self.faculty_period['fac_id']
        self.instructor.english_name = self.faculty_period['name']
        self.instructor.arabic_name = self.faculty_period['name']
        self.instructor.personal_email = self.faculty_period['email']
        self.instructor.active = True
        self.instructor.save()

    def create_or_get_periods(self):
        """
        :return:
        """
        # ENGLEP there is something called virtual section this has to be handled.
        if self.faculty_period['class_days'] and \
                self.faculty_period['room'] and \
                self.faculty_period['activity']:
            for day in map(str, self.faculty_period['class_days']):
                self.current_day = self.get_period_current_day(day)
                start_time = self.get_period_start_time()
                end_time = self.get_period_end_time()
                if not ScheduledPeriod.is_period_exists(self.section, self.instructor, self.current_day, start_time,
                                                        end_time):
                    self.period = ScheduledPeriod(
                        section=self.section,
                        instructor_assigned=self.instructor,
                        day=self.current_day,
                        title=self.faculty_period['activity'],
                        start_time=start_time,
                        end_time=end_time,
                        location=self.faculty_period['bldg'] + ' ' + self.faculty_period['room'],
                    )
                    self.non_created_periods.append(self.period)
        else:
            if self.section not in self.periods_with_issues:
                self.periods_with_issues.append(self.section)

    def get_period_current_day(self, day):
        if day == 'U':
            return ScheduledPeriod.Days.SUNDAY
        if day == 'M':
            return ScheduledPeriod.Days.MONDAY
        if day == 'T':
            return ScheduledPeriod.Days.TUESDAY
        if day == 'W':
            return ScheduledPeriod.Days.WEDNESDAY
        if day == 'R':
            return ScheduledPeriod.Days.THURSDAY

    def get_period_start_time(self):
        start_time = list(map(str, self.faculty_period['start_time']))
        start_time = start_time[0] + start_time[1] + ':' + start_time[2] + start_time[3]
        return start_time

    def get_period_end_time(self):
        end_time = list(map(str, self.faculty_period['end_time']))
        end_time = end_time[0] + end_time[1] + ':' + end_time[2] + end_time[3]
        return end_time

    def commit_faculties_periods(self):
        with transaction.atomic():
            for new_period in self.non_created_periods:
                new_period.save()

    def sections_report(self):
        report = []
        for new_section in self.non_created_sections:
            report.append(
                {'section': new_section, 'code': 'CREATE', 'message': 'New section to be created.'}
            )
        for changed_section in self.changed_sections:
            report.append(
                {'section': changed_section, 'code': 'CHANGED', 'message': 'section has been changed.'}
            )
        return report

    def enrollments_report(self):
        report = []
        for new_enrollment in self.new_enrollments:
            report.append(
                {'enrollment': new_enrollment, 'code': 'CREATE', 'message': 'New enrollment to be created.'}
            )
        for old_enrollment in self.old_enrollments:
            report.append(
                {'enrollment': old_enrollment, 'code': 'CHANGED', 'message': 'Enrollment has been changed.'}
            )
        for current_enrollment in self.current_enrollments:
            report.append(
                {'enrollment': current_enrollment, 'code': 'CHANGED', 'message': 'Enrollment has been changed.'}
            )
        for inactive_enrollment in self.inactive_enrollment:
            report.append(
                {'enrollment': inactive_enrollment, 'code': 'INACTIVE',
                 'message': 'Enrollment will be set to inactive.'}
            )
        return report

    def faculties_periods_report(self):
        report = []
        for non_created_period in self.non_created_periods:
            report.append(
                {'period': non_created_period, 'code': 'CREATE', 'message': 'Period to be created.'}
            )
        for period_with_issue in self.periods_with_issues:
            report.append(
                {'period': period_with_issue, 'code': 'MI-VS',
                 'message': 'This period has missing information or it belongs to virtual section'}
            )
        return report
